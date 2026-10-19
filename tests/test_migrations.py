from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pglast import parse_sql

from golocal_data.migrations import (
    apply_migrations, discover_migrations, pending_migrations,
)

ROOT = Path(__file__).resolve().parents[1]


def test_real_migrations_parse_as_postgresql():
    migrations = discover_migrations(ROOT / "migrations")
    assert [item.version for item in migrations] == [1, 2]
    for item in migrations:
        assert parse_sql(item.sql)


@pytest.mark.parametrize("filename, content", [
    ("bad.sql", "SELECT 1"), ("000_bad.sql", "SELECT 1"), ("001_empty.sql", "  "),
])
def test_reject_invalid_files(tmp_path, filename, content):
    (tmp_path / filename).write_text(content)
    with pytest.raises(ValueError):
        discover_migrations(tmp_path)


def test_duplicate_numeric_version(tmp_path):
    for name in ("001_a.sql", "0001_b.sql"):
        (tmp_path / name).write_text("SELECT 1;")
    with pytest.raises(ValueError, match="duplicate"):
        discover_migrations(tmp_path)


def test_no_migrations(tmp_path):
    with pytest.raises(ValueError, match="No SQL"):
        discover_migrations(tmp_path)


def test_numeric_order_and_stable_checksum(tmp_path):
    for name in ("1000_last.sql", "999_first.sql"):
        (tmp_path / name).write_text("SELECT 1;")
    items = discover_migrations(tmp_path)
    assert [m.version for m in items] == [999, 1000]
    assert items == discover_migrations(tmp_path)


def test_only_unapplied_are_pending():
    items = discover_migrations(ROOT / "migrations")
    first = items[0]
    assert pending_migrations(items, {first.version: (first.name, first.checksum)}) == items[1:]


@pytest.mark.parametrize("change", ["checksum", "name", "missing", "out_of_order"])
def test_reject_migration_history_changes(change):
    items = discover_migrations(ROOT / "migrations")
    first, second = items
    applied = {first.version: (first.name, first.checksum)}
    if change == "checksum":
        applied[first.version] = (first.name, "changed")
    elif change == "name":
        applied[first.version] = ("renamed.sql", first.checksum)
    elif change == "missing":
        items = items[1:]
    else:
        applied = {second.version: (second.name, second.checksum)}
    with pytest.raises(ValueError):
        pending_migrations(items, applied)


class MemoryConnection:
    """Transaction double: exercise runner failure, rerun, and ledger behavior."""
    def __init__(self, failing_sql=None):
        self.rows = []
        self.executed = []
        self.failing_sql = failing_sql
        self.rolled_back = False

    @contextmanager
    def transaction(self):
        before = self.rows.copy()
        try:
            yield
        except Exception:
            self.rows = before
            self.rolled_back = True
            raise

    def execute(self, sql, params=None, **kwargs):
        self.executed.append((sql, params))
        if sql == self.failing_sql:
            raise RuntimeError("simulated database failure")
        if sql.startswith("INSERT INTO schema_migrations"):
            self.rows.append(params)
        result = MagicMock()
        result.fetchall.return_value = self.rows.copy()
        return result


def test_apply_and_rerun_without_executing_sql_twice():
    items = discover_migrations(ROOT / "migrations")
    conn = MemoryConnection()
    assert apply_migrations(conn, items) == [m.name for m in items]
    assert apply_migrations(conn, items) == []
    for item in items:
        assert sum(sql == item.sql for sql, _ in conn.executed) == 1
    assert conn.executed[0][0].startswith("SELECT pg_advisory_xact_lock")


def test_failed_migration_rolls_back_ledger():
    items = discover_migrations(ROOT / "migrations")
    conn = MemoryConnection(failing_sql=items[1].sql)
    with pytest.raises(RuntimeError):
        apply_migrations(conn, items)
    assert conn.rolled_back
    assert conn.rows == []


def test_drift_is_detected_before_any_migration_executes():
    items = discover_migrations(ROOT / "migrations")
    conn = MemoryConnection()
    conn.rows = [(1, items[0].name, "wrong checksum")]
    with pytest.raises(ValueError):
        apply_migrations(conn, items)
    assert not any(sql == item.sql for sql, _ in conn.executed for item in items)
