"""Run the committed golden questions live and write a reviewable result."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.llm import EMBEDDING_MODEL, MODEL  # noqa: E402
from golocal_data.rag_answer import answer  # noqa: E402
from golocal_data.rag_index import StaleIndexError, load_index  # noqa: E402
from golocal_data.rag_retrieve import DEFAULT_K, DEFAULT_MIN_SCORE  # noqa: E402

GOLDEN = ROOT / "evals" / "golden.yaml"
RESULTS = ROOT / "evals" / "results"


def score(item: dict, result) -> list[str]:
    failures = []
    if result.status != item["expect"]:
        failures.append(f"expected {item['expect']}, got {result.status}: {result.reason}")
    if item["expect"] == "refused" and result.status == "refused" and result.reason not in {
        "low_retrieval_score", "source_does_not_answer"
    }:
        failures.append(f"refusal was not source-based: {result.reason}")
    if item["expect"] == "answered":
        cited = {source["doc_id"] for source in result.citations}
        failures.extend(f"missing citation: {doc_id}" for doc_id in item["must_cite"] if doc_id not in cited)
        failures.extend(f"missing phrase: {phrase}" for phrase in item["must_mention"]
                        if phrase.casefold() not in result.answer.casefold())
    return failures


def run(*, k: int = DEFAULT_K, min_score: float = DEFAULT_MIN_SCORE,
        golden_path: Path = GOLDEN, results_dir: Path = RESULTS) -> dict:
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY is not configured in the process environment")
    # JSON is a valid YAML 1.2 subset; this keeps the evaluator dependency free.
    spec = json.loads(golden_path.read_text(encoding="utf-8"))
    index = load_index(model=EMBEDDING_MODEL)
    rows = []
    for item in spec["items"]:
        result = answer(index, item["question"], k=k, min_score=min_score)
        failures = score(item, result)
        rows.append({
            "id": item["id"], "type": item["type"], "passed": not failures,
            "failures": failures, "status": result.status, "reason": result.reason,
            "answer": result.answer,
            "cited": [source["doc_id"] for source in result.citations],
        })
        print(f"{'PASS' if not failures else 'FAIL'} {item['id']} {item['type']}")
        for failure in failures:
            print(f"  {failure}")
    passed = sum(row["passed"] for row in rows)
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "live", "embedding_model": EMBEDDING_MODEL, "answer_model": MODEL,
        "k": k, "min_score": min_score,
        "passed": passed, "total": len(rows),
        "pass_rate": round(passed / len(rows), 3), "threshold": spec["threshold"],
        "items": rows,
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    (results_dir / f"{stamp}-live-k{k}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{passed}/{len(rows)} passed; threshold {spec['threshold']:.2f}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    args = parser.parse_args(argv)
    try:
        report = run(k=args.k, min_score=args.min_score)
    except (OSError, StaleIndexError, ValueError) as exc:
        print(f"Golden run unavailable: {exc}", file=sys.stderr)
        return 2
    return 0 if report["pass_rate"] >= report["threshold"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
