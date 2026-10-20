"""Real corpus boundaries and index drift checks, without provider calls."""

import json

import pytest

from golocal_data.rag_corpus import chunks_for_document, load_corpus
from golocal_data.rag_index import CORPUS, StaleIndexError, build_index, load_index


def test_real_corpus_has_source_backed_chunks():
    chunks, hashes = load_corpus(CORPUS)
    assert len(hashes) == 13
    assert len(chunks) >= 13
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(chunk.source_url.startswith("https://") for chunk in chunks)
    assert all(chunk.title in chunk.text and chunk.section in chunk.text for chunk in chunks)


def test_long_section_splits_and_keeps_trusted_url(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    path = root / "sample.md"
    path.write_text("# Example\n- Source: https://example.org/show\n"
                    "## Details\n" + ("A meaningful sentence. " * 150), encoding="utf-8")
    chunks = chunks_for_document(path, root)
    assert len(chunks) > 1
    assert [chunk.id for chunk in chunks] == [f"sample#{n}" for n in range(1, len(chunks) + 1)]
    assert {chunk.source_url for chunk in chunks} == {"https://example.org/show"}


@pytest.mark.parametrize("source", ["", "http://example.org/x", "https://user:pass@example.org/x"])
def test_corpus_rejects_missing_or_untrusted_source(tmp_path, source):
    path = tmp_path / "bad.md"
    path.write_text(f"# Example\n- Source: {source}\n## Details\nText", encoding="utf-8")
    with pytest.raises(ValueError):
        chunks_for_document(path, tmp_path)


def _sample_corpus(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    path = root / "show.md"
    path.write_text("# Show\n- Source: https://example.org/show\n## Time\nFriday at 20:00.",
                    encoding="utf-8")
    return root, path


def test_index_roundtrip_and_rejects_model_or_corpus_drift(tmp_path):
    root, path = _sample_corpus(tmp_path)
    destination = tmp_path / "rag.json"
    built = build_index(root, destination, model="test-embedding", embedder=lambda _: [1.0, 0.0])
    loaded = load_index(root, destination, model="test-embedding")
    assert loaded == built
    with pytest.raises(StaleIndexError, match="model"):
        load_index(root, destination, model="other-model")
    path.write_text(path.read_text(encoding="utf-8") + "\nChanged.", encoding="utf-8")
    with pytest.raises(StaleIndexError, match="Corpus"):
        load_index(root, destination, model="test-embedding")


def test_failed_rebuild_does_not_replace_existing_index(tmp_path):
    root, _ = _sample_corpus(tmp_path)
    destination = tmp_path / "rag.json"
    build_index(root, destination, model="test-embedding", embedder=lambda _: [1.0, 0.0])
    old = destination.read_bytes()
    with pytest.raises(ValueError, match="dimensions"):
        _mismatched_build(root, destination)
    assert destination.read_bytes() == old


def _mismatched_build(root, destination):
    # Force a second chunk to exercise a dimension change mid-build.
    (root / "second.md").write_text(
        "# Second\n- Source: https://example.org/second\n## Detail\nOther.", encoding="utf-8")
    calls = iter([[1.0, 0.0], [1.0]])
    build_index(root, destination, model="test-embedding", embedder=lambda _: next(calls))


def test_index_rejects_tampered_source_mapping(tmp_path):
    root, _ = _sample_corpus(tmp_path)
    destination = tmp_path / "rag.json"
    build_index(root, destination, model="test-embedding", embedder=lambda _: [1.0, 0.0])
    payload = json.loads(destination.read_text(encoding="utf-8"))
    payload["rows"][0]["chunk"]["source_url"] = "https://malicious.example/x"
    destination.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(StaleIndexError):
        load_index(root, destination, model="test-embedding")
