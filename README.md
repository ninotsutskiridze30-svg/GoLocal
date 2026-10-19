# goLocal: database and AI layer

This package owns PostgreSQL/PostGIS/pgvector, ingestion, embeddings, query parsing,
and ranked search. Frontend, FastAPI endpoints, and authentication belong to teammates.
The project specification PDF in the repository root is the source of truth.

## Phase 1: local foundation

Requires Python 3.11+, Docker Desktop running Linux containers, and Git.
Run these PowerShell commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
notepad .env
```

Set a unique local `POSTGRES_PASSWORD` and put the same password in `DATABASE_URL`.
URL-encode special characters in the URL password. Do not paste credentials into chat.
Compose reads `.env`; the migration CLI also reads it, with existing environment
variables taking precedence. No API key is needed for this phase.

```powershell
docker compose up -d --build --wait
.\.venv\Scripts\python.exe scripts/migrate.py
.\.venv\Scripts\python.exe scripts/migrate.py
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: the database becomes healthy; the first migration run prints
`Applied: 001_schema.sql, 002_seed.sql`; the second prints
`Database is up to date.` Tests run offline without PostgreSQL or API keys.
The first Docker build and Python dependency installation require internet access.

Verify the running database:

```powershell
.\.venv\Scripts\python.exe scripts/verify_db.py
```

Expected: `Verified: postgis + vector; migrations 1, 2; Tbilisi (Asia/Tbilisi, GEL); 15+ categories.` No real events or approved sources are seeded.
If a command fails, share the command and redacted error, plus `docker compose ps`
and `docker compose logs --tail 60 db`. Never share `.env` or `docker compose config`
output, which can contain passwords.

Use `docker compose stop` to stop the database and keep its data. The database binds
only to localhost and persists in a named Docker volume. Changing `.env` credentials
after the volume is initialized does not change the existing database credentials.

## Schema contracts

- `cities` owns city, IANA timezone, and default currency; Tbilisi is only seed data.
- `venues` owns city membership and optional coordinates, with a generated PostGIS
  geography point and spatial index. Coordinate order is longitude, latitude.
- `events` holds canonical facts; `event_sources` holds source-specific provenance.
  Prices use `NULL` for unknown and `0` for free. Known prices require currency.
- All instants use `timestamptz`; database sessions default to UTC in Docker.
  Supply timezone-aware timestamps. Missing end-time expiry policy follows in phase 4.
- `sources` defaults to unapproved. Ingestion requires active status, explicit
  approval, review timestamp, and review notes. Database triggers guard writes to
  `raw_events` and `event_sources`. Phase 3 also checks approval before any fetch.
  Review notes must cover terms, robots, reuse/licensing, and attribution.
- `raw_events` retains original JSON records, validation errors, and load status.
- `event_embeddings` stores model, dimension, content hash, and vector. Dimension
  is deliberately flexible until model selection; queries must match model/dimension.
  A dimension-specific vector index will be added in phase 5.
- User-related tables provide storage contracts only. No auth or HTTP routes exist.
- `search_log` is reserved for later use. Do not log credentials or private source data;
  query retention/privacy policy must be agreed before enabling production logging.
- Expire events by status, rather than deleting them. No deletion jobs are supplied.

## Migrations and testing

Add immutable, numbered files such as `003_description.sql` to `migrations/`.
Never edit an applied migration: the runner rejects checksum drift, missing history,
and inserting an earlier version. SQL files are trusted repository code, never LLM
or scraped output. A transaction and advisory lock protect application and ledger.
Schema migration credentials are local development/admin credentials; production
runtime roles and permissions need separate provisioning.

`requirements-dev.lock` records the versions used for this phase (Python 3.11 on Windows).

Offline tests parse PostgreSQL SQL and exercise ordering, history checks, idempotent
runner behavior, and rollback using a transaction double. They do not prove PostGIS
or pgvector runtime behavior. Run the Docker/migration checks above before integration.

## Layout and next phases

`docker/` builds PostGIS plus pgvector; `compose.yaml` runs it. `migrations/` defines
schema and seeds. `src/golocal_data/` exposes Python building blocks; `scripts/`
provides local commands; `tests/` holds offline tests.

Phases 2-8 add normalization, two approved collectors, loading/deduplication/expiry,
embeddings, validated LLM parsing, hybrid ranking, and teammate integration docs.
Each phase stops for review after tests and a small feature-branch commit.

Docker references checked during implementation: [PostGIS image](https://github.com/postgis/docker-postgis) and [pgvector build instructions](https://github.com/pgvector/pgvector).

## Phase 2: pure normalization and validation

`golocal_data.normalization` exposes:

- `normalize_datetime(value, *, source_timezone=None, fold=None)` -> UTC datetime.
  Accepts a datetime or ISO date-time with an explicit time. Naive input requires
  an IANA timezone supplied from source/city configuration. Repeated DST times
  need an explicit fold; nonexistent local times and date-only input are rejected.
- `normalize_price(value)` -> Decimal or None. Accepts decimal text, integers,
  and Decimal; rejects floats, negative/nonfinite amounts, and precision that
  cannot fit `numeric(12,2)`. None means unknown; explicit zero means free.
- `normalize_currency(value, *, allowed=None)` -> uppercase code or None.
  Validates three-letter syntax; `allowed` can restrict to the caller's configured
  registry. Syntax alone does not prove a code is an assigned currency.
- `normalize_url(value, *, base_url=None)` -> absolute HTTP(S) URL. Resolves
  relative links only with an explicit base, removes fragments/default ports,
  and preserves path/query data. Rejects credentials and malformed URLs.
  It does not fetch, check robots, approve hosts, or establish network safety.
- `normalize_text(value, *, required=True)`, `normalize_venue_name(value)`,
  `venue_match_key(value)` -> Unicode/whitespace-normalized text and a casefolded
  candidate key. No translation, HTML execution, or destructive venue merging.
- `normalize_category(value, *, aliases=None, allowed=CATEGORIES)` -> canonical
  category; unknown labels become `other`. Default aliases are product mappings;
  verified source-specific mappings belong in collector configuration.

Collectors must parse verified source formats before calling these functions.
Do not guess whether `03/04` means March 4 or April 3, infer currency from `$`,
turn an unknown price into zero, or invent a time for a date-only event.
These functions raise `ValueError` for invalid or insufficient input.

`golocal_data.models.NormalizedEvent` provides the canonical event contract.
It forbids extra fields and accidental type coercion, validates provenance,
normalizes aware instants to UTC, checks price/end-time ordering and coordinate
pairs, and is immutable. It raises Pydantic `ValidationError` on invalid records.
It carries city/source identifiers; the future loader verifies their database
existence and source approval. Text is inert, untrusted data: rendering consumers
must escape it, and LLM consumers must not treat it as instructions.

Example with synthetic data (no network or database needed):

```python
from datetime import datetime, timezone
from golocal_data.models import NormalizedEvent
from golocal_data.normalization import normalize_datetime, normalize_price

event = NormalizedEvent(
    title="Example concert", city_id=1, venue_name="Example Hall",
    start_time=normalize_datetime("2026-10-20T19:00", source_timezone="Asia/Tbilisi"),
    price_min=normalize_price("0"), currency="GEL", category="music",
    source_id=1, source_name="Synthetic example",
    source_url="https://example.com/events/1",
    fetched_at=datetime.now(timezone.utc),
)
```

`event_has_finished(event, *, now)` returns True when the known end time is
reached, False before it, and None when the end is unknown. It never reads the
system clock or changes event status. The loader phase will define the policy
for events missing an end time before implementing automatic expiry.

Run all offline checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Phase 2 requires no migration, database restart, API key, or source access.

## Current milestone: 25 fictional events

Real-source collection and later AI phases are paused. The current deliverable is
schema + Docker PostgreSQL + a small fictional dataset for browsing and integration.

`data/demo_events.json` contains 25 hand-written fictional records with 15 categories,
six fictional venues, and free, paid, and unknown prices. All titles begin `[DEMO]`;
descriptions also identify the fiction and contain 80-130 words each. URLs are placeholders on `example.com`.
No real events, real venue claims, source fetching, or embeddings are included.
Each demo venue has a fictional address and illustrative map coordinates. These
coordinates are test points, not verified locations of the invented venues.

Load them after migrations:

```powershell
.\.venv\Scripts\python.exe scripts/seed_demo.py
```

Expected first run: `Demo events inserted: 25; already present: 0.`
Rerunning prints `Demo events inserted: 0; already present: 25.`
The seed uses a transaction and lock, validates with `NormalizedEvent`, and records
source provenance plus original fixture JSON. A dedicated approved `manual` source
identifies these owner-authorized fixtures; no external source is approved.
Dates are anchored to 2026-10-19, with events 1-25 days later in the seeded city's
timezone. For a fresh dataset later, supply `--base-date YYYY-MM-DD`. This affects
only missing fixtures; existing event dates are deliberately left unchanged.
Reruns refresh event descriptions and the demo venues' addresses and coordinates, including for events
already loaded. PostgreSQL regenerates their PostGIS geography automatically.
Existing raw audit payloads retain the original records from their initial load.
Synthetic category-vector content hashes are refreshed for updated demo descriptions;
real model embeddings are not changed.

In pgAdmin connect to localhost port **5433** using your `.env` credentials, then
open `golocal > Schemas > public > Tables`. Right-click `events`, choose
**View/Edit Data > All Rows**, or run this in Query Tool:

```sql
SELECT e.id, e.title, c.name AS category, v.name AS venue,
       v.address, v.latitude, v.longitude,
       e.start_time AT TIME ZONE city.timezone AS local_start,
       e.price_min, e.price_max, e.currency, e.status, e.source_url
FROM events e
JOIN categories c ON c.id = e.category_id
JOIN venues v ON v.id = e.venue_id
JOIN cities city ON city.id = v.city_id
WHERE e.source_name = 'goLocal fictional demo fixtures'
ORDER BY e.start_time;
```

Actual data lives in the PostgreSQL Docker volume, not in Python model files.
`events`, `venues`, `event_sources`, `raw_events`, and `sources` now support this
demo dataset; related user/activity tables can be populated with the optional command below.
No new migration or API key is required. The seed is optional and is never run by
migrations automatically.

## Fictional users and related table data

```powershell
.\.venv\Scripts\python.exe scripts/seed_demo.py --with-activity
```

This optional command loads the events and related fixtures in one transaction.
It is safe to rerun: existing matching rows are skipped. It adds:

| Table | Demo rows |
| --- | ---: |
| users | 5 |
| user_preferences | 15 |
| saved_events | 15 |
| user_interactions | 25 |
| search_log | 5 |
| event_embeddings | 25 |

`data/demo_users.json` defines the fictional names, example.com addresses,
preferences, saved-event references, and example searches. These users have no
passwords or login functionality. Interaction timestamps and search timestamps
are fixed at 2026-10-19 for repeatability. Search results refer to actual demo event
IDs but are hand-written examples, not outputs of an implemented search service.
`latency_ms=0` is synthetic and is not a performance measurement.

Vectors are 15-dimensional category indicators labeled
`demo-category-onehot-v1-NOT-SEMANTIC`. No LLM/embedding API is called; these are only
for inspecting relationships and pgvector storage. Future semantic queries must
filter by model and dimensions, and a real embedding job must explicitly replace
these test vectors. Existing embedding rows are never overwritten by the demo seed.

Every application table now has demo or foundation seed rows. `schema_migrations`
is the genuine migration history and is not filled with fake entries. PostGIS-owned
tables in `tiger`, `topology`, and other extension schemas are outside this dataset.
In pgAdmin refresh `public > Tables`, then use **View/Edit Data > All Rows**.
