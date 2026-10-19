from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
import json

import pytest

from golocal_data.demo import build_demo_events, load_demo_records, seed_demo_events
from golocal_data.normalization import CATEGORIES

FIXTURES = Path(__file__).resolve().parents[1] / "data/demo_events.json"
NOW = datetime(2026, 10, 19, tzinfo=timezone.utc)


def build(records=None, now=NOW):
    return build_demo_events(load_demo_records(FIXTURES) if records is None else records,
        base_date=date(2026, 10, 19), now=now, city_id=1, source_id=1, city_timezone="Asia/Tbilisi")


def test_handwritten_fixtures_validate_and_cover_demo_cases():
    events = build()
    assert len(events) == 25
    assert all(80 <= len(event.description.split()) <= 130 for event in events)
    assert len({e.external_id for e in events}) == 25
    assert {e.category for e in events} == CATEGORIES
    assert len({e.venue_name for e in events}) == 6
    assert all(e.venue_address.startswith("FICTIONAL:") for e in events)
    assert all(e.latitude is not None and e.longitude is not None for e in events)
    assert len({(e.latitude, e.longitude) for e in events}) == 6
    for venue in {e.venue_name for e in events}:
        assert len({(e.venue_address, e.latitude, e.longitude) for e in events if e.venue_name == venue}) == 1
    assert any(e.price_min is None for e in events)
    assert any(e.price_min == Decimal("0") for e in events)
    assert any(e.price_min and e.price_max > e.price_min for e in events)
    assert all(e.title.startswith("[DEMO]") and e.source_url.startswith("https://example.com/") for e in events)
    assert all(e.status == "active" and e.start_time > NOW for e in events)
    assert events[0].start_time == datetime(2026, 10, 20, 15, tzinfo=timezone.utc)


def test_build_is_deterministic_and_old_fixtures_are_expired():
    assert build() == build()
    assert all(e.status == "expired" for e in build(now=datetime(2027, 1, 1, tzinfo=timezone.utc)))


@pytest.mark.parametrize("field,value", [("title", "Real-looking title"),
    ("latitude", 91.0), ("longitude", None),
    ("description", "Not labeled"), ("price_min", "unknown"), ("end_local", "01:00")])
def test_invalid_fixture_is_rejected(field, value):
    records = load_demo_records(FIXTURES)
    records[0][field] = value
    with pytest.raises(ValueError):
        build(records)


@pytest.mark.parametrize("mode", ["duplicate", "count"])
def test_invalid_fixture_collection(tmp_path, mode):
    records = load_demo_records(FIXTURES)
    if mode == "duplicate":
        records[-1]["external_id"] = records[0]["external_id"]
    else:
        records.pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(records))
    with pytest.raises(ValueError):
        load_demo_records(path)


def test_existing_records_are_not_inserted_again():
    conn = MagicMock()
    def execute(sql, params=None):
        result = MagicMock()
        if "SELECT id, timezone" in sql:
            result.fetchone.return_value = (1, "Asia/Tbilisi")
        elif "INSERT INTO sources" in sql:
            result.fetchone.return_value = (1,)
        elif "SELECT event_id FROM event_sources" in sql:
            result.fetchone.return_value = (10,)
        elif "SELECT name, id FROM categories" in sql:
            result.fetchall.return_value = [(c, i) for i, c in enumerate(sorted(CATEGORIES), 1)]
        return result
    conn.execute.side_effect = execute
    assert seed_demo_events(conn, load_demo_records(FIXTURES), base_date=date(2026,10,19), now=NOW) == 0
    statements = [call.args[0] for call in conn.execute.call_args_list]
    assert not any("INSERT INTO events " in sql or "INSERT INTO raw_events" in sql for sql in statements)
    updates = [call for call in conn.execute.call_args_list if "UPDATE venues" in call.args[0]]
    assert len(updates) == 25
    assert updates[0].args[1] == ("FICTIONAL: 1 Demo Lantern Lane", 41.7151, 44.8271, 10, 1, "Demo Lantern Hall")
    description_updates = [call for call in conn.execute.call_args_list if "UPDATE events SET description" in call.args[0]]
    assert len(description_updates) == 25
    assert description_updates[0].args[1] == (build()[0].description, 10, build()[0].description)
    hash_updates = [call for call in conn.execute.call_args_list if "UPDATE event_embeddings" in call.args[0]]
    assert len(hash_updates) == 25
    assert hash_updates[0].args[1][2] == "demo-category-onehot-v1-NOT-SEMANTIC"
    conn.transaction.assert_called_once()
