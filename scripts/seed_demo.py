"""Load 25 fictional events into the configured database; safe to rerun."""
from datetime import date, datetime, timezone
from pathlib import Path
import argparse
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
import psycopg
from golocal_data.demo import load_demo_records, seed_demo_events
from golocal_data.demo_activity import load_demo_users, seed_demo_activity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-date", type=date.fromisoformat, default=date(2026, 10, 19),
                        help="Anchor date for new fixtures only (default: 2026-10-19)")
    parser.add_argument("--with-activity", action="store_true",
                        help="Also load fake users, related activity, and synthetic vectors")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL in .env or environment.", file=sys.stderr)
        return 1
    try:
        records = load_demo_records(ROOT / "data/demo_events.json")
        users = load_demo_users(ROOT / "data/demo_users.json", records) if args.with_activity else None
        activity = None
        with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
            with connection.transaction():
                count = seed_demo_events(connection, records, base_date=args.base_date,
                                         now=datetime.now(timezone.utc))
                if users is not None:
                    activity = seed_demo_activity(connection, users)
    except (psycopg.Error, ValueError, KeyError, OSError) as error:
        print(f"Demo load failed ({type(error).__name__}); transaction rolled back. Check database, migrations, and fixtures.", file=sys.stderr)
        return 1
    print(f"Demo events inserted: {count}; already present: {len(records) - count}.")
    if activity is not None:
        print("Demo related rows inserted: " + ", ".join(f"{name}={count}" for name, count in activity.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
