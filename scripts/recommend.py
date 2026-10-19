"""Try the bounded discovery slice locally: python scripts/recommend.py 'ჯაზი'."""

from pathlib import Path
import argparse
import json
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golocal_data.discovery import ModelServiceError, recommend  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Natural-language event request")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    try:
        results = recommend(args.query)
    except ValueError:
        print("Enter a nonempty request of at most 2000 characters.", file=sys.stderr)
        return 2
    except ModelServiceError:
        print("Gemini is unavailable or returned an invalid response.", file=sys.stderr)
        return 1
    except Exception:
        # Driver errors can contain connection credentials; never print them.
        print("Search is unavailable. Check the database and local configuration.", file=sys.stderr)
        return 1
    print(json.dumps([{
        "id": item.event.id, "title": item.event.title,
        "reason": item.reason, "source_url": item.event.source_url,
        "demo": True,
    } for item in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
