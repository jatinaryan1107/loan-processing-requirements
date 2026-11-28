"""Exercise the same analysis and verification entry points as the workspace."""

import pytest
from fastapi.testclient import TestClient

from backend import retrieval
from backend.agents import extraction_agent, risk_agent
from backend.app import create_app


def test_risk_follows_the_category_in_the_draft_and_preserves_prior_approval():
    draft = extraction_agent.make_requirement(
        "The application shall mask identifiers in exported files.",
        {"id": "SRC-1"},
        {"categories": ["privacy"]},
    )
    assert draft["risk"] == "high"
    reviewed = dict(draft, id="REQ-OLD", status="approved", risk="medium")
    risk_agent.assess({"requirements": [draft, reviewed], "runs": []})
    assert reviewed["risk"] == "medium"


@pytest.fixture
def demo(tmp_path):
    with TestClient(create_app(tmp_path / "review.db")) as client:
        token = client.post("/api/session", json={"role": "ba"}).json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        path = "/api/projects/" + client.get("/api/projects").json()[0]["id"]
        yield client, path


def submit(client, path, text):
    client.post(path + "/sources", json={"source_name": "Workshop", "text": text}).raise_for_status()
    response = client.post(path + "/analyse", json={})
    response.raise_for_status()
    return response.json()


def test_vector_only_evidence_and_unrelated_input(demo):
    client, path = demo
    paraphrase = (
        "Staff must prove their identity before they can view restricted loan application information."
    )
    unrelated = "The cafeteria menu shall list vegetarian dishes."
    project = submit(client, path, paraphrase + "\n" + unrelated)
    requirements = {r["statement"]: r["id"] for r in project["requirements"]}
    for _ in range(2):  # A repeat verification reuses the persistent policy collection.
        response = client.post(path + "/compliance", json={})
        response.raise_for_status()
        mappings = response.json()["mappings"]
        auth = next(m for m in mappings if m["control"] == "Authentication")
        match = next(m for m in auth["matches"] if m["requirement_id"] == requirements[paraphrase])
        assert auth["source"]["id"] == "DEMO-SEC-1" and auth["status"] == "proposed"
        assert match["keywords"] == [] and 0 <= match["cosine_distance"] <= retrieval.MAX_DISTANCE
        assert all(requirements[unrelated] not in m["requirement_ids"] for m in mappings)


def test_vector_failure_preserves_previous_review(demo, monkeypatch):
    client, path = demo
    before = client.get(path).json()

    def unavailable(*args):
        raise retrieval.SearchUnavailable("Local model unavailable")

    monkeypatch.setattr(retrieval, "search", unavailable)
    assert client.post(path + "/compliance", json={}).status_code == 503
    after = client.get(path).json()
    assert before["mappings"] == after["mappings"] and before["updated_at"] == after["updated_at"]


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("Approvals should be instant, but a credit officer should check every application.", True),
        (
            "Approvals should be instant after review, and a credit officer should check every application.",
            False,
        ),
    ],
)
def test_officer_review_order(demo, ordering, expected):
    client, path = demo
    project = submit(
        client,
        path,
        "Our bank wants an online system where customers can apply for personal loans and get approved fast. It should be secure and easy to use, and work with our existing systems. "
        + ordering,
    )
    flags = [f for f in project["flags"] if f["type"] == "workflow_ambiguity"]
    assert bool(flags) == expected
    if expected:
        assert any(q["text"] == flags[0]["question"] for q in project["questions"])
    assert any(r["agent"] == "RiskAgent" for r in project["runs"])
