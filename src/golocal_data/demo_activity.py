"""Fictional relational fixtures and synthetic category vectors, without API calls."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from .demo import SOURCE_NAME
from .normalization import CATEGORIES

SYNTHETIC_MODEL = "demo-category-onehot-v1-NOT-SEMANTIC"
VECTOR_CATEGORIES = tuple(sorted(CATEGORIES))
FIXTURE_TIME = datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
INTERACTIONS = ("view", "click", "save", "share", "external_click")


def synthetic_embedding(category: str) -> list[float]:
    """15-dimensional category indicator; never claim this is an AI embedding."""
    if category not in VECTOR_CATEGORIES:
        raise ValueError("Unknown demo category")
    return [float(item == category) for item in VECTOR_CATEGORIES]


def embedding_content_hash(title: str, description: str) -> str:
    return sha256(json.dumps([title, description], ensure_ascii=False).encode("utf-8")).hexdigest()


def load_demo_users(path: Path, event_records: list[dict]) -> list[dict]:
    users = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(users, list) or len(users) != 5:
        raise ValueError("Expected five fictional users")
    known_events = {event["external_id"] for event in event_records}
    emails = set()
    for user in users:
        email = user["email"]
        if not email.startswith("demo.") or not email.endswith("@example.com") or email in emails:
            raise ValueError("Demo emails must be unique, reserved fixture addresses")
        emails.add(email)
        if not user["name"].startswith("[DEMO] ") or not user["query"].startswith("[DEMO] "):
            raise ValueError("User and search text must identify the demo")
        if len(user["saved"]) != len(set(user["saved"])):
            raise ValueError("Duplicate saved fixture")
        if not set(user["saved"] + user["results"]) <= known_events:
            raise ValueError("Unknown event reference")
        for category, score in user["preferences"].items():
            if category not in CATEGORIES or type(score) not in (int, float) or not 0 <= score <= 1:
                raise ValueError("Invalid preference")
    return users


def seed_demo_activity(connection, users):
    """Add related demo records atomically; avoid overwriting existing real embeddings."""
    from psycopg.types.json import Jsonb

    counts = dict.fromkeys(("users", "user_preferences", "saved_events", "user_interactions",
                            "search_log", "event_embeddings"), 0)
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(7340192027)")
        rows = connection.execute(
            """SELECT es.external_id, e.id, c.name, e.title, e.description
            FROM event_sources es JOIN sources s ON s.id = es.source_id
            JOIN events e ON e.id = es.event_id JOIN categories c ON c.id = e.category_id
            WHERE s.name = %s""", (SOURCE_NAME,),
        ).fetchall()
        events = {slug: (event_id, category, title, description)
                  for slug, event_id, category, title, description in rows}
        if len(events) != 25:
            raise ValueError("Load the 25 demo events first")
        categories = dict(connection.execute("SELECT name, id FROM categories").fetchall())
        for index, user in enumerate(users):
            timestamp = FIXTURE_TIME + timedelta(minutes=index * 10)
            result = connection.execute(
                """INSERT INTO users (email, name, created_at) VALUES (%s, %s, %s)
                ON CONFLICT (lower(email)) DO NOTHING""",
                (user["email"], user["name"], timestamp),
            )
            counts["users"] += result.rowcount
            user_id = connection.execute("SELECT id FROM users WHERE lower(email) = lower(%s)",
                                         (user["email"],)).fetchone()[0]
            for category, score in user["preferences"].items():
                result = connection.execute(
                    """INSERT INTO user_preferences (user_id, category_id, preference_score)
                    VALUES (%s, %s, %s) ON CONFLICT (user_id, category_id) DO NOTHING""",
                    (user_id, categories[category], score),
                )
                counts["user_preferences"] += result.rowcount
            for slug in user["saved"]:
                result = connection.execute(
                    """INSERT INTO saved_events (user_id, event_id, created_at)
                    VALUES (%s, %s, %s) ON CONFLICT (user_id, event_id) DO NOTHING""",
                    (user_id, events[slug][0], timestamp),
                )
                counts["saved_events"] += result.rowcount
            for offset, kind in enumerate(INTERACTIONS):
                event_id = events[user["saved"][offset % len(user["saved"]) ]][0]
                # A save interaction should correspond to an actual saved event.
                at = timestamp + timedelta(seconds=offset)
                result = connection.execute(
                    """INSERT INTO user_interactions (user_id, event_id, interaction_type, timestamp)
                    SELECT %s, %s, %s, %s WHERE NOT EXISTS (
                        SELECT 1 FROM user_interactions WHERE user_id = %s AND event_id = %s
                            AND interaction_type = %s AND timestamp = %s)""",
                    (user_id, event_id, kind, at, user_id, event_id, kind, at),
                )
                counts["user_interactions"] += result.rowcount
            result_ids = [events[slug][0] for slug in user["results"]]
            result = connection.execute(
                """INSERT INTO search_log (user_id, query, parsed_filters, results, latency_ms, created_at)
                SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS (
                    SELECT 1 FROM search_log WHERE user_id = %s AND query = %s AND created_at = %s)""",
                (user_id, user["query"], Jsonb(user["filters"]), Jsonb(result_ids),
                 0, timestamp, user_id, user["query"], timestamp),
            )
            counts["search_log"] += result.rowcount
        for event_id, category, title, description in events.values():
            vector = json.dumps(synthetic_embedding(category))
            result = connection.execute(
                """INSERT INTO event_embeddings (event_id, embedding, model, dimensions, content_hash, created_at)
                VALUES (%s, %s::vector, %s, %s, %s, %s) ON CONFLICT (event_id) DO NOTHING""",
                (event_id, vector, SYNTHETIC_MODEL, len(VECTOR_CATEGORIES),
                 embedding_content_hash(title, description), FIXTURE_TIME),
            )
            counts["event_embeddings"] += result.rowcount
    return counts
