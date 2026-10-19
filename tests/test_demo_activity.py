from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from golocal_data.demo import load_demo_records
from golocal_data.demo_activity import (
    VECTOR_CATEGORIES, embedding_content_hash, load_demo_users,
    seed_demo_activity, synthetic_embedding,
)

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    events = load_demo_records(ROOT / "data/demo_events.json")
    users = load_demo_users(ROOT / "data/demo_users.json", events)
    return events, users


def test_relational_fixtures_and_search_examples_are_consistent():
    events, users = fixtures()
    by_slug = {e["external_id"]: e for e in events}
    assert len(users) == 5
    assert sum(len(u["preferences"]) for u in users) == 15
    assert sum(len(u["saved"]) for u in users) == 15
    for user in users:
        for slug in user["results"]:
            event = by_slug[slug]
            assert event["category"] in user["filters"]["categories"]
            if "max_price" in user["filters"]:
                assert event["price_min"] is not None
                assert float(event["price_min"]) <= user["filters"]["max_price"]


@pytest.mark.parametrize("category", VECTOR_CATEGORIES)
def test_synthetic_vectors_have_valid_dimensions_and_nonzero_norm(category):
    vector = synthetic_embedding(category)
    assert len(vector) == 15
    assert sum(vector) == 1.0
    assert vector[VECTOR_CATEGORIES.index(category)] == 1.0


def test_content_hash_detects_changes():
    assert embedding_content_hash("title", "text") == embedding_content_hash("title", "text")
    assert embedding_content_hash("title", "text") != embedding_content_hash("title", "changed")
    assert len(embedding_content_hash("title", "text")) == 64


@pytest.mark.parametrize("change", ["email", "name", "event", "preference", "duplicate", "count"])
def test_invalid_user_fixtures_are_rejected(tmp_path, change):
    events, original = fixtures()
    users = deepcopy(original)
    if change == "email":
        users[0]["email"] = "someone@real-site.test"
    elif change == "name":
        users[0]["name"] = "Unmarked"
    elif change == "event":
        users[0]["saved"] = ["missing-event"]
    elif change == "preference":
        users[0]["preferences"]["music"] = 2.0
    elif change == "duplicate":
        users[1]["email"] = users[0]["email"]
    else:
        users.pop()
    path = tmp_path / "users.json"
    path.write_text(json.dumps(users))
    with pytest.raises(ValueError):
        load_demo_users(path, events)


def test_missing_event_dataset_rejects_before_related_writes():
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = []
    with pytest.raises(ValueError, match="25 demo events"):
        seed_demo_activity(conn, fixtures()[1])
    assert not any("INSERT" in call.args[0] for call in conn.execute.call_args_list)
    assert conn.transaction.return_value.__exit__.call_args.args[0] is ValueError
