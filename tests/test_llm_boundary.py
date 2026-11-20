"""Provider behavior is mocked: these tests never send data to an external model."""

import json
from contextlib import contextmanager

import httpx
import pytest

from backend import llm


def mock_stream(monkeypatch, make_response):
    @contextmanager
    def stream(method, url, **kwargs):
        response = make_response(url, **kwargs)
        try:
            yield response
        finally:
            response.close()

    monkeypatch.setattr(llm.httpx, "stream", stream)


def enable(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM", "true")
    monkeypatch.setenv("LLM_ALLOW_EXTERNAL", "true")
    monkeypatch.setenv("LLM_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")


def test_no_call_without_both_opt_ins(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("LLM_ALLOW_EXTERNAL", "false")
    monkeypatch.setattr(llm.httpx, "stream", lambda *args, **kwargs: pytest.fail("Unexpected external call"))
    with pytest.raises(ValueError, match="disabled"):
        llm.extract("The system shall require authentication.")


def test_masked_input_and_literal_evidence_validation(monkeypatch):
    enable(monkeypatch)
    captured = {}
    statement = "The system shall require authentication."

    def response(*args, **kwargs):
        captured.update(kwargs["json"])
        content = json.dumps(
            {
                "requirements": [
                    {
                        "statement": statement,
                        "evidence": statement,
                        "kind": "functional",
                        "categories": ["security"],
                        "priority": "Must",
                        "acceptance_criteria": ["Unauthenticated access is denied."],
                    }
                ],
                "questions": [],
            }
        )
        return httpx.Response(
            200, request=httpx.Request("POST", args[0]), json={"choices": [{"message": {"content": content}}]}
        )

    mock_stream(monkeypatch, response)
    result, meta = llm.extract(statement + "\nContact: analyst@example.org\nAccount holder: Synthetic Person")
    assert len(result.requirements) == 1
    outgoing = captured["messages"][1]["content"]
    assert "analyst@example.org" not in outgoing
    assert "Synthetic Person" not in outgoing
    assert "UNTRUSTED" in outgoing
    assert meta["model"] == "test-model"


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"choices": []}, {"choices": None}, {"choices": [{"message": {"content": "not json"}}]}],
)
def test_malformed_provider_response_has_safe_error(monkeypatch, payload):
    enable(monkeypatch)
    mock_stream(
        monkeypatch,
        lambda *args, **kwargs: httpx.Response(200, request=httpx.Request("POST", args[0]), json=payload),
    )
    with pytest.raises(ValueError, match="failed|invalid"):
        llm.extract("The system shall require authentication.")


def test_invented_evidence_is_rejected(monkeypatch):
    enable(monkeypatch)
    content = json.dumps(
        {
            "requirements": [
                {
                    "statement": "The system shall retain data for 100 years.",
                    "evidence": "A regulation requires 100 years of retention.",
                    "kind": "non-functional",
                    "categories": ["compliance"],
                    "priority": "Must",
                    "acceptance_criteria": ["Verify 100 years of retention."],
                }
            ]
        }
    )
    mock_stream(
        monkeypatch,
        lambda *args, **kwargs: httpx.Response(
            200, request=httpx.Request("POST", args[0]), json={"choices": [{"message": {"content": content}}]}
        ),
    )
    with pytest.raises(ValueError, match="invalid evidence"):
        llm.extract("The system shall require authentication.")
