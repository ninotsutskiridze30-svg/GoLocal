"""Ordered, checksummed SQL migrations applied atomically under a database lock."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str
    checksum: str


def discover_migrations(directory: Path) -> list[Migration]:
    migrations = []
    versions = set()
    for path in sorted(directory.glob("*.sql")):
        match = re.fullmatch(r"([0-9]{3,})_([a-z0-9_]+)\.sql", path.name)
        if not match:
            raise ValueError(f"Invalid migration filename: {path.name}")
        version = int(match[1])
        if version < 1 or version in versions:
            raise ValueError(f"Invalid or duplicate migration version: {version}")
        versions.add(version)
        content = path.read_bytes()
        sql = content.decode("utf-8")
        if not sql.strip():
            raise ValueError(f"Empty migration: {path.name}")
        migrations.append(Migration(version, path.name, sql, sha256(content).hexdigest()))
    if not migrations:
        raise ValueError("No SQL migrations found")
    return sorted(migrations, key=lambda item: item.version)


def pending_migrations(migrations, applied):
    known = {item.version: item for item in migrations}
    for version, (name, checksum) in applied.items():
        if version not in known or (known[version].name, known[version].checksum) != (name, checksum):
            raise ValueError(f"Applied migration {version} is missing or changed; restore it")
    pending = [item for item in migrations if item.version not in applied]
    if applied and any(item.version < max(applied) for item in pending):
        raise ValueError("Cannot insert a migration before an applied version")
    return pending


def apply_migrations(connection, migrations):
    # A single transaction also rolls back the ledger if any SQL fails.
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(7340192026)")
        connection.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version integer PRIMARY KEY, name text NOT NULL, checksum text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now())""")
        rows = connection.execute("SELECT version, name, checksum FROM schema_migrations").fetchall()
        pending = pending_migrations(migrations, {v: (n, c) for v, n, c in rows})
        for migration in pending:
            # Only trusted, local version-controlled SQL is executed here.
            connection.execute(migration.sql, prepare=False)
            connection.execute(
                "INSERT INTO schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
                (migration.version, migration.name, migration.checksum),
            )
    return [item.name for item in pending]


def main():
    import os
    import psycopg
    from dotenv import load_dotenv

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env", override=False)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL in .env or the environment.", file=__import__('sys').stderr)
        return 1
    try:
        migrations = discover_migrations(root / "migrations")
        with psycopg.connect(url, autocommit=True) as connection:
            names = apply_migrations(connection, migrations)
    except (psycopg.Error, ValueError, OSError) as error:
        # Driver errors can include credentials; do not print them.
        print(f"Migration failed ({type(error).__name__}). Check database health, credentials, and migration files.",
              file=__import__('sys').stderr)
        return 1
    print("Applied: " + ", ".join(names) if names else "Database is up to date.")
    return 0
