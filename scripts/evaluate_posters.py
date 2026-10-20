"""Run all five user-supplied posters against the manually reviewed reference."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.llm import PosterModelError  # noqa: E402
from golocal_data.poster_checks import decide  # noqa: E402
from golocal_data.poster_extraction import extract  # noqa: E402


def compare(reference: dict, observed) -> dict:
    """Return factual differences for review, not a claim of model accuracy."""
    issues: list[str] = []
    expected_events = reference["events"]
    if len(observed.events) != len(expected_events):
        issues.append(f"event_count: expected {len(expected_events)}, observed {len(observed.events)}")
    for index, (expected, actual) in enumerate(zip(expected_events, observed.events)):
        for reference_name, model_name in (
            ("title", "title"), ("date_text", "date_text"),
            ("date_iso", "date_iso"), ("displayed_time", "displayed_time"),
            ("time_role", "time_role"), ("doors_open_time", "doors_open_time"),
            ("venue", "venue"), ("city", "city"),
        ):
            want = expected[reference_name]
            got = getattr(actual, model_name).value
            if (want or "").casefold() != (got or "").casefold():
                issues.append(f"events[{index}].{reference_name}: expected {want!r}, observed {got!r}")
        for name in (
            "performers", "special_guests", "lineup", "program_items",
            "films_named_on_poster",
        ):
            wanted = {item.casefold() for item in expected[name]}
            observed_values = getattr(actual, name).value or []
            got = {item.casefold() for item in observed_values}
            if wanted != got:
                issues.append(f"events[{index}].{name}: expected {sorted(wanted)!r}, observed {sorted(got)!r}")
    if (reference["ticket_platform"] or "").casefold() != (observed.ticket_platform.value or "").casefold():
        issues.append("ticket_platform differs")
    if (reference["contact_phone"] or "").replace(" ", "") != (observed.contact_phone.value or "").replace(" ", ""):
        issues.append("contact_phone differs")
    if observed.source_url.value is not None:
        issues.append("source_url: poster has no printed URL")
    if reference["ticket_price"] is None and any(
        event.ticket_price.value is not None for event in observed.events
    ):
        issues.append("ticket_price: poster has no printed price")
    return {"poster_id": reference["poster_id"], "issues": issues}


def evaluate(corpus: dict, image_dir: Path, *, today: date, extractor=extract) -> dict:
    rows = []
    for reference in corpus["posters"]:
        image_path = image_dir / reference["image_file"]
        try:
            observed = extractor(image_path.read_bytes())
            row = compare(reference, observed)
            decision = decide(observed, today)
            row["route"] = decision.route
            row["flag_kinds"] = sorted({flag.kind for flag in decision.flags})
        except (OSError, PosterModelError, ValueError) as exc:
            row = {"poster_id": reference["poster_id"], "error": type(exc).__name__}
        rows.append(row)
    return {"posters_checked": len(rows), "results": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", type=date.fromisoformat)
    args = parser.parse_args(argv)
    today = args.today or datetime.now(ZoneInfo("Asia/Tbilisi")).date()
    image_dir = ROOT / "data" / "posters"
    corpus = json.loads((image_dir / "posters.json").read_text(encoding="utf-8"))
    report = evaluate(corpus, image_dir, today=today)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any("error" in row or row.get("issues") for row in report["results"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
