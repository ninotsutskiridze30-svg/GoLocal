"""Explicit local demo seeding, never a real-source collector."""
from datetime import date, datetime, timedelta
import json
from pathlib import Path

from .models import NormalizedEvent
from .normalization import normalize_datetime, normalize_price

SOURCE_NAME = "goLocal fictional demo fixtures"
SOURCE_URL = "https://example.com/golocal-demo/"


def load_demo_records(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) != 25:
        raise ValueError("Expected exactly 25 demo records")
    ids = [record["external_id"] for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Demo identifiers must be unique")
    return records


def build_demo_events(records, *, base_date: date, now: datetime, city_id: int,
                      source_id: int, city_timezone: str) -> list[NormalizedEvent]:
    events = []
    for record in records:
        if not record["title"].startswith("[DEMO] ") or not record["description"].startswith("FICTIONAL DEMO EVENT."):
            raise ValueError("Every demo record must be visibly fictional")
        day = base_date + timedelta(days=record["day_offset"])
        start = normalize_datetime(f"{day.isoformat()}T{record['start_local']}", source_timezone=city_timezone)
        end = normalize_datetime(f"{day.isoformat()}T{record['end_local']}", source_timezone=city_timezone)
        events.append(NormalizedEvent(
            title=record["title"], description=record["description"], category=record["category"],
            city_id=city_id, venue_name=record["venue_name"], start_time=start, end_time=end,
            venue_address=record["venue_address"], latitude=record["latitude"], longitude=record["longitude"],
            price_min=normalize_price(record["price_min"]), price_max=normalize_price(record["price_max"]),
            currency=record["currency"], source_id=source_id, source_name=SOURCE_NAME,
            source_url=SOURCE_URL + record["external_id"], external_id=record["external_id"],
            fetched_at=now, status="expired" if end <= normalize_datetime(now) else "active",
        ))
    return events


def seed_demo_events(connection, records, *, base_date: date, now: datetime):
    """Atomically add missing fixtures; refresh demo descriptions and locations, retaining existing IDs and dates."""
    from psycopg.types.json import Jsonb
    from .demo_activity import SYNTHETIC_MODEL, embedding_content_hash

    inserted = 0
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(7340192027)")
        city = connection.execute(
            "SELECT id, timezone FROM cities WHERE name = %s AND country_code = %s",
            ("Tbilisi", "GE"),
        ).fetchone()
        if not city:
            raise ValueError("Apply city/category migrations first")
        source_id = connection.execute(
            """INSERT INTO sources (name, url, source_type, status, ingestion_approved,
                compliance_checked_at, compliance_notes)
            VALUES (%s, %s, 'manual', 'active', true, %s, %s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id""",
            (SOURCE_NAME, SOURCE_URL, now,
             "Hand-written fictional local fixtures authorized by the project owner. No external fetch, terms, robots, or licensing dependency."),
        ).fetchone()[0]
        events = build_demo_events(records, base_date=base_date, now=now,
                                  city_id=city[0], source_id=source_id, city_timezone=city[1])
        categories = dict(connection.execute("SELECT name, id FROM categories").fetchall())
        for record, event in zip(records, events, strict=True):
            existing = connection.execute(
                "SELECT event_id FROM event_sources WHERE source_id = %s AND external_id = %s",
                (source_id, event.external_id),
            ).fetchone()
            if existing:
                connection.execute(
                    """UPDATE events SET description = %s WHERE id = %s
                        AND description IS DISTINCT FROM %s""",
                    (event.description, existing[0], event.description),
                )
                # Category-only demo vectors remain valid when prose changes.
                # Never relabel a real model's embedding as up to date.
                connection.execute(
                    """UPDATE event_embeddings SET content_hash = %s
                    WHERE event_id = %s AND model = %s
                        AND content_hash IS DISTINCT FROM %s""",
                    (embedding_content_hash(event.title, event.description), existing[0],
                     SYNTHETIC_MODEL, embedding_content_hash(event.title, event.description)),
                )
                # Refresh only the venue linked to this specific fictional source record.
                connection.execute(
                    """UPDATE venues SET address = %s, latitude = %s, longitude = %s
                    WHERE id = (SELECT venue_id FROM events WHERE id = %s)
                        AND city_id = %s AND name = %s""",
                    (event.venue_address, event.latitude, event.longitude,
                     existing[0], event.city_id, event.venue_name),
                )
                continue
            venue = connection.execute(
                "SELECT id FROM venues WHERE city_id = %s AND name = %s ORDER BY id LIMIT 1",
                (event.city_id, event.venue_name),
            ).fetchone()
            venue_id = venue[0] if venue else connection.execute(
                "INSERT INTO venues (city_id, name) VALUES (%s, %s) RETURNING id",
                (event.city_id, event.venue_name),
            ).fetchone()[0]
            connection.execute(
                "UPDATE venues SET address = %s, latitude = %s, longitude = %s WHERE id = %s",
                (event.venue_address, event.latitude, event.longitude, venue_id),
            )
            event_id = connection.execute(
                """INSERT INTO events (title, description, category_id, venue_id, start_time,
                    end_time, price_min, price_max, currency, source_url, source_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (event.title, event.description, categories[event.category], venue_id,
                 event.start_time, event.end_time, event.price_min, event.price_max,
                 event.currency, event.source_url, event.source_name, event.status),
            ).fetchone()[0]
            connection.execute(
                """INSERT INTO event_sources (event_id, source_id, external_id, source_url, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (event_id, source_id, event.external_id, event.source_url, now, now),
            )
            connection.execute(
                """INSERT INTO raw_events (source_id, external_id, source_url, fetched_at, payload, status, event_id)
                VALUES (%s, %s, %s, %s, %s, 'loaded', %s)""",
                (source_id, event.external_id, event.source_url, now, Jsonb(record), event_id),
            )
            inserted += 1
    return inserted
