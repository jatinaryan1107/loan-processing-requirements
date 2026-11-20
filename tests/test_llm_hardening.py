"""Bounded model transport and structured-output tests, without network calls."""

import json
from contextlib import closing, contextmanager

import httpx
import pytest
from pydantic import ValidationError

from backend import llm


@pytest.mark.parametrize(
    "base",
    [
        "http://localhost:8000@evil.example/v1",
        "http://127.0.0.1:8000@evil.example/v1",
        "http://localhost.evil.example/v1",
        "http://remote.example/v1",
        "http://localhost\\@evil.example/v1",
        "https://user:password@provider.example/v1",
        "https://provider.example/v1?key=secret",
        "https://provider.example/v1#fragment",
        "https:///v1",
        "https://provider.example:invalid/v1",
        "file:///tmp/model",
        " https://provider.example/v1",
    ],
)
def test_invalid_or_disguised_endpoint_is_rejected(base):
    with pytest.raises(ValueError, match="LLM endpoint"):
        llm.endpoint_url(base)


@pytest.mark.parametrize(
    "base",
    [
        "https://provider.example/v1",
        "http://localhost:8080/v1",
        "http://127.0.0.1:8080/v1",
        "http://[::1]:8080/v1",
    ],
)
def test_explicit_https_and_loopback_endpoints_are_supported(base):
    assert llm.endpoint_url(base) == base + "/chat/completions"


def model_item():
    return {
        "statement": "The system shall authenticate staff.",
        "evidence": "The system shall authenticate staff.",
        "kind": "functional",
        "categories": ["security"],
        "priority": "Must",
        "acceptance_criteria": ["Verify unauthenticated access is denied."],
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("categories", ["security" * 1000]),
        ("categories", ["unrecognised"]),
        ("acceptance_criteria", [""]),
        ("acceptance_criteria", ["     "]),
        ("acceptance_criteria", ["x" * 3001]),
        ("statement", " " * 20),
        ("evidence", 12345),
        ("confidence", 0.99),
    ],
)
def test_model_fields_are_strict_bounded_and_reject_extra_keys(field, value):
    item = model_item()
    item[field] = value
    with pytest.raises(ValidationError):
        llm.Extraction.model_validate_json(json.dumps({"requirements": [item]}))


@pytest.mark.parametrize("question", ["", "  ", "x" * 1001, 12345])
def test_model_questions_are_bounded_nonempty_strings(question):
    with pytest.raises(ValidationError):
        llm.Extraction.model_validate_json(
            json.dumps({"requirements": [model_item()], "questions": [question]})
        )


class ChunkedBody(httpx.SyncByteStream):
    def __iter__(self):
        for _ in range(4):
            yield b"x" * 65536


def test_streamed_response_is_rejected_at_size_limit_without_content_length(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "MAX_RESPONSE_BYTES", 100000)
    captured = {}

    @contextmanager
    def stream(method, url, **kwargs):
        captured.update(kwargs)
        with closing(
            httpx.Response(200, request=httpx.Request(method, url), stream=ChunkedBody())
        ) as response:
            yield response

    monkeypatch.setattr(llm.httpx, "stream", stream)
    with pytest.raises(ValueError, match="size limit"):
        llm.response_json("https://provider.example/v1/chat/completions", {})
    assert captured["follow_redirects"] is False


def test_declared_oversize_response_is_rejected_before_reading_body(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    class Unreadable(httpx.SyncByteStream):
        def __iter__(self):
            pytest.fail("Oversized provider body should not be read")
            yield b""

    @contextmanager
    def stream(method, url, **kwargs):
        with closing(
            httpx.Response(
                200,
                request=httpx.Request(method, url),
                headers={"Content-Length": str(llm.MAX_RESPONSE_BYTES + 1)},
                stream=Unreadable(),
            )
        ) as response:
            yield response

    monkeypatch.setattr(llm.httpx, "stream", stream)
    with pytest.raises(ValueError, match="size limit"):
        llm.response_json("https://provider.example/v1/chat/completions", {})
