"""Run from the repository root: python scripts/migrate.py."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from golocal_data.migrations import main

if __name__ == "__main__":
    raise SystemExit(main())
