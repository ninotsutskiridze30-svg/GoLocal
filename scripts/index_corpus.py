"""Build the local RAG index from data/corpus (requires GOOGLE_API_KEY)."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.llm import EMBEDDING_MODEL, EmbeddingModelError, embed  # noqa: E402
from golocal_data.rag_index import build_index  # noqa: E402


def main() -> int:
    try:
        index = build_index(model=EMBEDDING_MODEL, embedder=embed)
    except (OSError, ValueError, EmbeddingModelError) as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Indexed {len(index.corpus_hashes)} documents, {len(index.rows)} chunks "
          f"with {index.model} ({index.dimensions} dimensions).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
