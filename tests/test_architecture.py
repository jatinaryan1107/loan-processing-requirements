"""Concurrency and recovery behavior at the HTTP boundary."""

import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend import services, storage


@pytest.fixture
def api(tmp_path):
    with TestClient(create_app(tmp_path / "architecture.db", seed=False)) as client:
        token = client.post("/api/session", json={"role": "ba"}).json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        yield client


def test_stale_tab_cannot_overwrite_newer_work(api):
    p = api.post("/api/projects", json={"name": "Concurrent review"}).json()
    path = f"/api/projects/{p['id']}/sources"
    body = {"source_name": "Interview", "text": "The system shall require authentication."}
    assert api.post(path, json=body, headers={"If-Match": p["updated_at"]}).status_code == 200
    stale = api.post(path, json=body, headers={"If-Match": p["updated_at"]})
    assert stale.status_code == 409
    assert len(api.get(f"/api/projects/{p['id']}").json()["sources"]) == 1


def test_logout_revokes_server_token(api):
    assert api.delete("/api/session").status_code == 200
    assert api.get("/api/projects").status_code == 401


def test_project_context_changes_reopen_review_and_preserve_sources(api):
    p = api.post("/api/projects", json={"name": "Project review", "jurisdiction": "India"}).json()
    path = f"/api/projects/{p['id']}"
    api.post(
        path + "/sources", json={"source_name": "Operations", "text": "The system shall record approvals."}
    )
    api.post(path + "/analyse", json={})
    baseline = api.post(path + "/compliance", json={}).json()
    assert baseline["mappings"]
    fields = {key: baseline[key] for key in ("name", "description", "jurisdiction")}
    renamed = api.put(path + "/context", json={**fields, "name": "Intake project"}).json()
    assert renamed["mappings"] == baseline["mappings"]
    fields.update(name=renamed["name"], jurisdiction="United Kingdom")
    stale = api.put(path + "/context", json=fields, headers={"If-Match": baseline["updated_at"]})
    assert stale.status_code == 409
    changed = api.put(path + "/context", json=fields, headers={"If-Match": renamed["updated_at"]}).json()
    assert changed["jurisdiction"] == "United Kingdom"
    assert changed["sources"] == baseline["sources"] and changed["requirements"] == baseline["requirements"]
    assert not changed["mappings"] and not changed["final_ready"]
    assert changed["audit"][-1]["action"] == "project_edited"
    for role in ("developer", "pm", "compliance"):
        token = api.post("/api/session", json={"role": role}).json()["token"]
        denied = api.put(path + "/context", json=fields, headers={"Authorization": "Bearer " + token})
        assert denied.status_code == 403


def test_failed_source_can_be_excluded_without_losing_evidence(api):
    p = api.post("/api/projects", json={"name": "Recovery example"}).json()
    path = f"/api/projects/{p['id']}"
    text = "\n".join(f"The system shall display status field {i}." for i in range(151))
    p = api.post(path + "/sources", json={"source_name": "Too large", "text": text}).json()
    assert api.post(path + "/analyse", json={}).status_code == 422
    sid = p["sources"][0]["id"]
    p = api.post(path + f"/sources/{sid}/exclude", json={"note": "Split into smaller inputs."}).json()
    assert p["sources"][0]["text"] == text and p["sources"][0]["excluded"]
    api.post(
        path + "/sources",
        json={"source_name": "Focused requirement", "text": "The system shall require authentication."},
    )
    result = api.post(path + "/analyse", json={})
    assert result.status_code == 200
    assert len(result.json()["requirements"]) == 1


def test_snapshot_computation_does_not_hold_writer_lock(tmp_path):
    token = storage.active_database.set(str(tmp_path / "transactions.db"))
    try:
        storage.init_db()
        p = storage.new_project("Concurrent edit", "", "India")
        with storage.transaction() as conn:
            storage.save_project(conn, p)
        with pytest.raises(Exception) as conflict:
            with services.edit_project(p["id"]) as old:
                with services.edit_project(p["id"]) as newer:
                    newer["description"] = "Newer value"
                old["description"] = "Stale value"
        assert conflict.value.status_code == 409
        with storage.connect() as conn:
            assert storage.get_project(conn, p["id"])["description"] == "Newer value"
    finally:
        storage.active_database.reset(token)
