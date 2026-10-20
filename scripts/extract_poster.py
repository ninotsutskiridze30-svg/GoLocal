"""Read one poster: python scripts/extract_poster.py path/to/poster.jpg."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.llm import PosterModelError  # noqa: E402
from golocal_data.poster_checks import decide, safe_draft  # noqa: E402
from golocal_data.poster_extraction import extract  # noqa: E402
from golocal_data.poster_images import InvalidPosterImage  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--today", type=date.fromisoformat,
                        help="Date for reproducible review decisions (YYYY-MM-DD)")
    args = parser.parse_args(argv)
    today = args.today or datetime.now(ZoneInfo("Asia/Tbilisi")).date()
    try:
        image_bytes = args.image.read_bytes()
        extraction = extract(image_bytes)
        decision = decide(extraction, today)
    except (OSError, InvalidPosterImage) as exc:
        print(f"Cannot read image: {exc}", file=sys.stderr)
        return 2
    except PosterModelError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({
        "image_file": args.image.name,
        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "route": decision.route,
        "flags": [asdict(flag) for flag in decision.flags],
        "draft": safe_draft(extraction, decision),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
