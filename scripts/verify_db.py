"""Read-only phase 1 database verification; no secrets printed."""
from pathlib import Path
import os
import sys

import psycopg
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL in .env or the environment.", file=sys.stderr)
        return 1
    try:
        with psycopg.connect(url) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            extensions = {row[0] for row in conn.execute("SELECT extname FROM pg_extension")}
            if not {"postgis", "vector"} <= extensions:
                raise ValueError("Missing database extensions")
            versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
            city = conn.execute("SELECT timezone, currency FROM cities WHERE name = %s AND country_code = %s",
                                ("Tbilisi", "GE")).fetchone()
            categories = conn.execute("SELECT count(*) FROM categories").fetchone()[0]
            if versions != [1, 2] or city != ("Asia/Tbilisi", "GEL") or categories < 15:
                raise ValueError("Unexpected migration or seed state")
            # Ensure PostGIS geography and pgvector functions work, not just catalog entries.
            conn.execute("SELECT ST_Distance('SRID=4326;POINT(0 0)'::geography, 'SRID=4326;POINT(0 0)'::geography)")
            conn.execute("SELECT '[1,0]'::vector <=> '[1,0]'::vector")
    except (psycopg.Error, ValueError) as error:
        print(f"Database verification failed ({type(error).__name__}). Check setup and migration status.", file=sys.stderr)
        return 1
    print("Verified: postgis + vector; migrations 1, 2; Tbilisi (Asia/Tbilisi, GEL); 15+ categories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
