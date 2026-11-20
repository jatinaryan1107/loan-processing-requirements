"""Successful document ingestion keeps its evidence and review state across restarts."""

import io

import pytest
from docx import Document
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from backend.app import create_app


STATEMENT = "The system shall record each approval with an actor and timestamp."
TABLE_STATEMENT = "The system shall reject an application missing its required identifier."


def document_bytes(extension):
    if extension == "txt":
        return b"\xef\xbb\xbf" + STATEMENT.encode("utf-8")
    if extension == "docx":
        document = Document()
        document.add_paragraph(STATEMENT)
        document.add_table(rows=1, cols=1).cell(0, 0).text = TABLE_STATEMENT
        stream = io.BytesIO()
        document.save(stream)
        return stream.getvalue()

    # A real one-page text PDF, built using the already-required parser library.
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 10 Tf 40 740 Td ({STATEMENT}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = content
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def login(client):
    response = client.post("/api/session", json={"role": "ba"})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


@pytest.mark.parametrize("extension", ["txt", "pdf", "docx"])
def test_document_upload_analysis_and_review_survive_restart(tmp_path, monkeypatch, extension):
    monkeypatch.setenv("ENABLE_DEMO_LOGIN", "true")
    monkeypatch.setenv("ENABLE_LLM", "false")
    database = tmp_path / f"{extension}-upload.db"
    filename = f"synthetic-workshop.{extension}"
    with TestClient(create_app(str(database), seed=False)) as client:
        headers = login(client)
        created = client.post("/api/projects", headers=headers, json={"name": "Upload provenance"})
        assert created.status_code in (200, 201), created.text
        project_id = created.json()["id"]
        uploaded = client.post(
            f"/api/projects/{project_id}/upload",
            headers=headers,
            files={"file": (filename, document_bytes(extension))},
        )
        assert uploaded.status_code == 200, uploaded.text
        data = uploaded.json()
        assert len(data["sources"]) == 1
        assert data["requirements"] == []
        source = data["sources"][0]
        assert source["source_name"] == filename
        assert source["text"].startswith(STATEMENT)
        assert source["created_at"]
        assert source["stakeholder"] == "Business Analyst"
        assert source["extracted"] is False
        if extension == "docx":
            assert TABLE_STATEMENT in source["text"], "Table cell evidence must survive DOCX parsing."

        analysed = client.post(f"/api/projects/{project_id}/analyse", headers=headers, json={})
        assert analysed.status_code == 200, analysed.text
        data = analysed.json()
        source_id = source["id"]
        source_text = source["text"]
        assert data["sources"][0]["extracted"] is True
        requirements = data["requirements"]
        assert len(requirements) == (2 if extension == "docx" else 1)
        assert all(r["source_id"] == source_id for r in requirements)
        assert all(r["original_text"] in source_text for r in requirements)
        assert all(r["status"] == "draft" for r in requirements)
        requirement_ids = [r["id"] for r in requirements]
        reviewed = client.post(
            f"/api/projects/{project_id}/requirements/{requirement_ids[0]}/review",
            headers=headers,
            json={"decision": "approved", "note": "Checked the original synthetic workshop evidence."},
        )
        assert reviewed.status_code == 200, reviewed.text
        assert any(a["action"] == "document_uploaded" for a in reviewed.json()["audit"])

    assert database.is_file()
    with TestClient(create_app(str(database), seed=False)) as restarted:
        headers = login(restarted)
        loaded = restarted.get(f"/api/projects/{project_id}", headers=headers)
        assert loaded.status_code == 200, loaded.text
        restored = loaded.json()
        assert restored["sources"][0]["id"] == source_id
        assert restored["sources"][0]["text"] == source_text
        assert restored["sources"][0]["source_name"] == filename
        assert [r["id"] for r in restored["requirements"]] == requirement_ids
        first = restored["requirements"][0]
        assert first["status"] == "approved"
        assert first["history"][-1]["decision"] == "approved"
        assert first["history"][-1]["note"] == "Checked the original synthetic workshop evidence."
        assert any(source_id in run["input_ids"] for run in restored["runs"])

        repeated = restarted.post(f"/api/projects/{project_id}/analyse", headers=headers, json={})
        assert repeated.status_code == 200, repeated.text
        assert [r["id"] for r in repeated.json()["requirements"]] == requirement_ids

        exported = restarted.get(f"/api/projects/{project_id}/export?format=json", headers=headers)
        assert exported.status_code == 200, exported.text
        assert exported.json()["sources"][0]["id"] == source_id
        assert exported.json()["requirements"][0]["history"][-1]["decision"] == "approved"
