"""Ask the grounded RAG service a question from the terminal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.llm import EMBEDDING_MODEL  # noqa: E402
from golocal_data.rag_answer import answer  # noqa: E402
from golocal_data.rag_index import StaleIndexError, load_index  # noqa: E402
from golocal_data.rag_retrieve import DEFAULT_K, DEFAULT_MIN_SCORE  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    args = parser.parse_args(argv)
    try:
        index = load_index(model=EMBEDDING_MODEL)
        result = answer(index, args.question, k=args.k, min_score=args.min_score)
    except (StaleIndexError, OSError, ValueError) as exc:
        print(f"RAG request failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "answered" else 1


if __name__ == "__main__":
    raise SystemExit(main())
