"""Gemini text-only boundaries and course golden-set structure."""

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from golocal_data.llm import (
    EMBEDDING_DIMENSIONS, EmbeddingModelError, PosterModelError, complete_json, embed,
)


ROOT = Path(__file__).resolve().parents[1]


def test_golden_refusal_requires_source_based_reason():
    from evals.run_golden import score

    item = {"expect": "refused", "must_cite": [], "must_mention": []}
    for reason in ("low_retrieval_score", "source_does_not_answer"):
        result = SimpleNamespace(status="refused", reason=reason, citations=[], answer="")
        assert score(item, result) == []
    for reason in ("model_timeout", "model_http_503", "embedding_unavailable"):
        result = SimpleNamespace(status="refused", reason=reason, citations=[], answer="")
        assert score(item, result) == [f"refusal was not source-based: {reason}"]


def test_embedding_request_model_dimensions_and_safe_log(tmp_path):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={
            "embedding": {"values": [1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1)},
            "usageMetadata": {"promptTokenCount": 7},
        })

    log = tmp_path / "usage.jsonl"
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        vector = embed("Piano concert", api_key="test-secret", client=client, log_path=log)
    body = json.loads(requests[0].content)
    assert body["model"] == "models/gemini-embedding-2"
    assert body["output_dimensionality"] == EMBEDDING_DIMENSIONS
    assert body["content"]["parts"] == [{"text": "Piano concert"}]
    assert len(vector) == EMBEDDING_DIMENSIONS
    logged = log.read_text(encoding="utf-8")
    assert "test-secret" not in logged and "Piano concert" not in logged
    assert json.loads(logged)["tokens_in"] == 7


def test_embedding_failure_sanitizes_provider_response(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(503, text="secret from provider")
    )) as client:
        with pytest.raises(EmbeddingModelError) as info:
            embed("question", api_key="test-secret", client=client, log_path=tmp_path / "log")
    assert "secret" not in str(info.value)
    assert json.loads((tmp_path / "log").read_text(encoding="utf-8"))["status"] == "failed"


def test_text_only_completion_omits_inline_image(tmp_path):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={
            "candidates": [{"content": {"parts": [{"text": '{"grounded":false}'}]}}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = complete_json("Use source", None, {"type": "object"},
                               api_key="test-secret", client=client,
                               log_path=tmp_path / "usage.jsonl")
    assert result == {"grounded": False}
    assert json.loads(requests[0].content)["contents"][0]["parts"] == [{"text": "Use source"}]


def test_completion_records_safe_http_status_without_provider_body(tmp_path):
    log = tmp_path / "usage.jsonl"
    with httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(429, text="private provider details")
    )) as client:
        with pytest.raises(PosterModelError) as info:
            complete_json("question", None, {"type": "object"}, api_key="test-secret",
                          client=client, log_path=log)
    assert info.value.failure_kind == "http_status"
    assert info.value.http_status == 429
    record = json.loads(log.read_text(encoding="utf-8"))
    assert record["http_status"] == 429
    assert record["failure_kind"] == "http_status"
    assert "private provider details" not in log.read_text(encoding="utf-8")
    assert "test-secret" not in log.read_text(encoding="utf-8")


def test_golden_set_has_required_mix_and_real_document_ids():
    spec = json.loads((ROOT / "evals" / "golden.yaml").read_text(encoding="utf-8"))
    items = spec["items"]
    assert spec["threshold"] == 0.70
    assert len(items) >= 5
    assert len({item["id"] for item in items}) == len(items)
    types = [item["type"] for item in items]
    assert types.count("factual") >= 2
    assert "reasoning" in types and "edge" in types and "refusal" in types
    for item in items:
        assert item["question"] and item["why"]
        assert item["expect"] in {"answered", "refused"}
        for doc_id in item["must_cite"]:
            assert (ROOT / "data" / "corpus" / f"{doc_id}.md").is_file()
