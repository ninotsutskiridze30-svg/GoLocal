"""Grounding rules and actual service orchestration with deterministic embeddings."""

import json

import pytest

from golocal_data.rag_answer import ModelReply, answer, check_citations
from golocal_data.llm import PosterModelError
from golocal_data.rag_corpus import Chunk
from golocal_data.rag_index import IndexedChunk, RagIndex
from golocal_data.rag_retrieve import retrieve


@pytest.fixture
def index():
    first = Chunk("events/piano#1", "events/piano", "Piano", "Time",
                  "https://example.org/piano", "Piano | Time\nPiano concert starts at 20:00.")
    second = Chunk("events/pool#1", "events/pool", "Pool", "Rules",
                   "https://example.org/pool", "Pool | Rules\nPool opens at 09:00.")
    return RagIndex("test", 3, {}, (
        IndexedChunk(first, (1.0, 0.0, 0.0)),
        IndexedChunk(second, (0.0, 1.0, 0.0)),
    ))


def test_retrieve_ranks_relevant_chunk_and_respects_k(index):
    hits = retrieve(index, "Piano concert time", embedder=lambda _: [1.0, 0.0, 0.0], k=1)
    assert len(hits) == 1
    assert hits[0].row.chunk.doc_id == "events/piano"
    assert 0.45 <= hits[0].score <= 1.0


def test_low_score_refuses_before_generation_and_logs_once(index, tmp_path):
    calls = []
    log = tmp_path / "answers.jsonl"
    result = answer(index, "Unrelated astronomy", embedder=lambda _: [0.0, 0.0, 1.0],
                    completer=lambda *a, **k: calls.append(1), log_path=log)
    assert result.status == "refused"
    assert result.reason == "low_retrieval_score"
    assert calls == []
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["reason"] == "low_retrieval_score"


def test_answer_maps_marker_to_retrieved_source_url(index, tmp_path):
    calls = []

    def complete(prompt, image, schema, **kwargs):
        calls.append((prompt, image, schema))
        return {"answer": "კონცერტი 20:00-ზე იწყება [1].", "citations": [1], "grounded": True}

    result = answer(index, "Piano concert time", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=complete, k=1, log_path=tmp_path / "log")
    assert result.status == "answered"
    assert len(calls) == 1 and calls[0][1] is None
    assert result.citations == [{
        "n": 1, "chunk_id": "events/piano#1", "doc_id": "events/piano",
        "title": "Piano", "section": "Time", "source_url": "https://example.org/piano",
    }]
    assert json.loads((tmp_path / "log").read_text(encoding="utf-8"))["status"] == "answered"


@pytest.mark.parametrize("reply,reason", [
    ({"answer": "არასწორი [2].", "citations": [2], "grounded": True}, "unknown_citation"),
    ({"answer": "ტექსტი [1].", "citations": [2], "grounded": True}, "citation_list_mismatch"),
    ({"answer": "ფაქტი [1]. მეორე ფაქტი.", "citations": [1], "grounded": True}, "uncited_sentence"),
    ({"answer": "ტექსტი [x].", "citations": [1], "grounded": True}, "invalid_marker"),
    ({"answer": "ტექსტი [1].", "citations": [], "grounded": True}, "missing_citation"),
])
def test_bad_citation_causes_refusal(index, tmp_path, reply, reason):
    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=lambda *a, **k: reply, k=1, log_path=tmp_path / "log")
    assert result.status == "refused"
    assert result.reason == reason
    assert result.citations == []
    assert len((tmp_path / "log").read_text(encoding="utf-8").splitlines()) == 1


def test_model_says_source_does_not_answer(index, tmp_path):
    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=lambda *a, **k: {"answer": "Unknown", "citations": [], "grounded": False},
                    log_path=tmp_path / "log")
    assert result.status == "refused" and result.reason == "source_does_not_answer"


def test_malformed_model_reply_refuses_without_leaking_content(index, tmp_path):
    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=lambda *a, **k: {"answer": "secret", "citations": [1], "grounded": "yes"},
                    log_path=tmp_path / "log")
    assert result.status == "refused"
    assert result.reason == "invalid_model_reply"
    assert "secret" not in (tmp_path / "log").read_text(encoding="utf-8")


def test_provider_status_is_separate_from_invalid_reply(index, tmp_path, monkeypatch):
    monkeypatch.setattr("golocal_data.rag_answer.time.sleep", lambda _: None)
    calls = []

    def unavailable(*args, **kwargs):
        calls.append(1)
        raise PosterModelError("Gemini JSON completion failed", failure_kind="http_status",
                               http_status=503)

    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=unavailable, log_path=tmp_path / "log")
    assert result.status == "refused" and result.reason == "model_http_503"
    assert len(calls) == 3
    record = json.loads((tmp_path / "log").read_text(encoding="utf-8"))
    assert record["reason"] == "model_http_503" and record["generation_attempts"] == 3


def test_transient_503_retries_then_answers_with_one_answer_log(index, tmp_path, monkeypatch):
    delays = []
    monkeypatch.setattr("golocal_data.rag_answer.time.sleep", delays.append)
    calls = []

    def complete(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise PosterModelError("temporary", failure_kind="http_status", http_status=503)
        return {"answer": "კონცერტი 20:00-ზე იწყება [1].", "citations": [1], "grounded": True}

    log = tmp_path / "answers.jsonl"
    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=complete, k=1, log_path=log)
    assert result.status == "answered"
    assert len(calls) == 2 and delays == [2]
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1 and records[0]["generation_attempts"] == 2


def test_permanent_400_does_not_retry(index, tmp_path, monkeypatch):
    monkeypatch.setattr("golocal_data.rag_answer.time.sleep", lambda _: pytest.fail("must not sleep"))
    calls = []

    def complete(*args, **kwargs):
        calls.append(1)
        raise PosterModelError("invalid request", failure_kind="http_status", http_status=400)

    result = answer(index, "Piano concert", embedder=lambda _: [1.0, 0.0, 0.0],
                    completer=complete, log_path=tmp_path / "answers.jsonl")
    assert result.status == "refused" and result.reason == "model_http_400"
    assert len(calls) == 1


def test_georgian_multisentence_citations_are_checked(index):
    hits = retrieve(index, "Piano", embedder=lambda _: [1.0, 0.0, 0.0], k=1)
    valid = ModelReply(answer="კონცერტია [1]. დრო ცნობილია [1].", citations=[1], grounded=True)
    assert check_citations(valid, hits) is None
    invalid = ModelReply(answer="კონცერტია [1]. დრო უცნობია.", citations=[1], grounded=True)
    assert check_citations(invalid, hits) == "uncited_sentence"
