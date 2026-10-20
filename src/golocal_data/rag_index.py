"""A versioned local embedding index; PostgreSQL is not changed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Callable

from .rag_corpus import Chunk, load_corpus


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "corpus"
INDEX = ROOT / "logs" / "rag_index.json"
INDEX_VERSION = 1


class StaleIndexError(ValueError):
    """Index must be rebuilt after a corpus, model, or format change."""


@dataclass(frozen=True)
class IndexedChunk:
    chunk: Chunk
    vector: tuple[float, ...]


@dataclass(frozen=True)
class RagIndex:
    model: str
    dimensions: int
    corpus_hashes: dict[str, str]
    rows: tuple[IndexedChunk, ...]


def _vector(values: list[float], dimensions: int | None = None) -> tuple[float, ...]:
    if not isinstance(values, list) or not values or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) for value in values
    ):
        raise ValueError("Embedding must contain finite numeric values")
    if dimensions is not None and len(values) != dimensions:
        raise ValueError("Embedding dimensions do not match the index")
    vector = tuple(float(value) for value in values)
    if not any(vector):
        raise ValueError("Embedding cannot be zero")
    return vector


def build_index(corpus_root: Path = CORPUS, index_path: Path = INDEX, *,
                model: str, embedder: Callable[[str], list[float]]) -> RagIndex:
    """Embed all chunks and atomically replace the local index on success."""
    chunks, hashes = load_corpus(corpus_root)
    rows: list[IndexedChunk] = []
    dimensions = None
    for chunk in chunks:
        vector = _vector(embedder(chunk.text), dimensions)
        dimensions = len(vector)
        rows.append(IndexedChunk(chunk, vector))
    index = RagIndex(model, dimensions or 0, hashes, tuple(rows))
    payload = {
        "version": INDEX_VERSION,
        "model": model,
        "dimensions": index.dimensions,
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corpus_hashes": hashes,
        "rows": [{"chunk": row.chunk.to_dict(), "vector": list(row.vector)} for row in rows],
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(index_path)
    finally:
        temporary.unlink(missing_ok=True)
    return index


def load_index(corpus_root: Path = CORPUS, index_path: Path = INDEX, *,
               model: str) -> RagIndex:
    """Refuse stale, mismatched, or corrupted indexes before answering."""
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        chunks, hashes = load_corpus(corpus_root)
        if data["version"] != INDEX_VERSION or data["model"] != model:
            raise StaleIndexError("Index format or embedding model changed; rebuild it")
        if data["corpus_hashes"] != hashes:
            raise StaleIndexError("Corpus changed; rebuild the RAG index")
        dimensions = data["dimensions"]
        if not isinstance(dimensions, int) or dimensions <= 0:
            raise ValueError("Invalid index dimensions")
        serialized = data["rows"]
        if not isinstance(serialized, list) or len(serialized) != len(chunks):
            raise ValueError("Index row count differs from corpus")
        rows = []
        for item, trusted_chunk in zip(serialized, chunks):
            if item["chunk"] != trusted_chunk.to_dict():
                raise ValueError("Index chunk differs from corpus")
            rows.append(IndexedChunk(trusted_chunk, _vector(item["vector"], dimensions)))
        return RagIndex(model, dimensions, hashes, tuple(rows))
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, StaleIndexError):
            raise
        raise StaleIndexError("RAG index unavailable or invalid; rebuild it") from exc
