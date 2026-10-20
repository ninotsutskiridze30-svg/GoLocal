"""Hybrid vector and lexical retrieval over source-backed chunks."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from collections import Counter
from typing import Callable

from .rag_index import IndexedChunk, RagIndex, _vector


DEFAULT_K = 5
DEFAULT_MIN_SCORE = 0.45
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class SearchHit:
    row: IndexedChunk
    score: float
    vector_score: float
    lexical_score: float


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    numerator = sum(x * y for x, y in zip(a, b))
    denominator = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return numerator / denominator if denominator else 0.0


def retrieve(index: RagIndex, question: str, *,
             embedder: Callable[[str], list[float]], k: int = DEFAULT_K,
             min_score: float = DEFAULT_MIN_SCORE) -> list[SearchHit]:
    """Return only hits above threshold, scored in [0, 1]."""
    if not question.strip() or len(question) > 2000:
        raise ValueError("Question must be 1-2000 nonblank characters")
    if not 1 <= k <= 20 or not 0 <= min_score <= 1:
        raise ValueError("Invalid retrieval settings")
    query = _vector(embedder(question), index.dimensions)
    terms = set(_tokens(question))
    document_terms = [Counter(_tokens(row.chunk.text)) for row in index.rows]
    n = len(index.rows)
    df = Counter(term for doc in document_terms for term in doc)
    average_length = sum(sum(doc.values()) for doc in document_terms) / n
    raw_bm25 = []
    for doc in document_terms:
        length = sum(doc.values())
        score = 0.0
        for term in terms:
            frequency = doc[term]
            if frequency:
                idf = math.log1p((n - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * frequency * 2.2 / (
                    frequency + 1.2 * (0.25 + 0.75 * length / average_length))
        raw_bm25.append(score)
    maximum = max(raw_bm25, default=0.0)
    hits = []
    for row, lexical_raw in zip(index.rows, raw_bm25):
        vector_score = max(0.0, min(1.0, _cosine(query, row.vector)))
        lexical_score = lexical_raw / maximum if maximum else 0.0
        score = 0.75 * vector_score + 0.25 * lexical_score
        if score >= min_score:
            hits.append(SearchHit(row, score, vector_score, lexical_score))
    hits.sort(key=lambda hit: (-hit.score, hit.row.chunk.id))
    return hits[:k]
