# goLocal data layer

Database schema, Docker PostgreSQL, event normalization, and fictional demo data for goLocal.
This package includes no frontend, FastAPI endpoints, or authentication.

## Status

Available: versioned schema, Docker PostgreSQL with PostGIS and pgvector,
normalization/validation functions, 25 fictional events with six demo venues,
and optional fictional users and activity.

Not implemented yet: real-source collectors, real embeddings, LLM query parser,
and a search function.

**All demo data is fictional.** Event titles start with `[DEMO]`, URLs are
placeholders on `example.com`, coordinates are test points, and optional demo
embeddings are fake category vectors. They are not real recommendations.

## Quick start for teammates

Requires Python 3.11+, Docker Desktop running Linux containers, and Git.
Run from the repository root in PowerShell. Installation and the first Docker
build need internet access; no API key is needed.

1. Create the environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
   .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
   ```

   Expected: `.venv` exists and both installs complete without errors. Package
   installation messages vary; a clean-clone installation is unverified here.

2. On first setup only, create your local configuration:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   Expected: `.env` opens. Replace the password placeholder in `POSTGRES_PASSWORD`
   and `DATABASE_URL` with the same local password, then save. URL-encode special
   characters in the URL password. Do not paste credentials into chat or commit
   `.env`. Do not overwrite an existing `.env`.

3. Open Docker Desktop and wait for its engine, then run:

   ```powershell
   docker compose up -d --build --wait
   .\.venv\Scripts\python.exe scripts/migrate.py
   .\.venv\Scripts\python.exe scripts/seed_demo.py
   .\.venv\Scripts\python.exe scripts/verify_db.py
   ```

   Expected: database becomes healthy; first migration run prints
   `Applied: 001_schema.sql, 002_seed.sql`; first seed prints
   `Demo events inserted: 25; already present: 0.` Verification prints
   `Verified: postgis + vector; migrations 1, 2; Tbilisi (Asia/Tbilisi, GEL); 15+ categories.`
   Reruns print `Database is up to date.` and
   `Demo events inserted: 0; already present: 25.` Verification checks extensions
   and foundation seeds, not the event count; the query below shows the events.

4. When you're done, stop the database while keeping its data:

   ```powershell
   docker compose stop
   ```

   Expected: the database container stops; its data remains in the Docker volume.

Full implementation details are in [the data layer reference](docs/data-layer.md).

## Connecting

Repository defaults are **localhost:5432**, database/user **golocal**:

```text
DATABASE_URL=postgresql://golocal:YOUR_URL_ENCODED_PASSWORD@localhost:5432/golocal
```

Compose uses `POSTGRES_PORT` from `.env` for the host port; PostgreSQL inside the
container always listens on 5432. This workspace overrides the host port to 5433.
If the default is unavailable, set both `POSTGRES_PORT` and the port in
`DATABASE_URL` to the same available port. Use that host port in pgAdmin too.
Existing environment variables take precedence over `.env`.

In desktop pgAdmin: **Servers > Register > Server**; name it `goLocal`. Under
**Connection**, use the host/port above (or your `.env` override), maintenance
database `golocal`, username `golocal`, and your local password. Save, then expand
**Databases > golocal > Schemas > public > Tables**. Right-click a table and choose
**View/Edit Data > All Rows**. These clicks were not retested in this documentation pass.

## Read events

Starting point for the backend's event queries; run in pgAdmin Query Tool:

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

For a Python connection and parameterized query, see the
[backend example](docs/data-layer.md#python-database-connection-example).

Expected after demo seeding: 25 rows. The displayed `local_start` is converted to
the venue city's timezone; stored event instants remain timezone-aware timestamps.

## Optional demo users and activity

```powershell
.\.venv\Scripts\python.exe scripts/seed_demo.py --with-activity
```

On a fresh dataset this adds the following related rows; reruns insert zero rows
for fixtures already present. The command also seeds events if they are missing.

| Table | Demo rows |
| --- | ---: |
| users | 5 |
| user_preferences | 15 |
| saved_events | 15 |
| user_interactions | 25 |
| search_log | 5 |
| event_embeddings | 25 |

Fake users have no login credentials. Search examples are hand-written; vectors
are 15-dimensional category indicators, not semantic embeddings.

## Refreshing the demo dates

The default anchor is 2026-10-19; events run from 20 October through 13 November
2026. These are events 1 to 25 days after the anchor date. After that they are past events. Rerunning the seed refreshes descriptions
and venue locations, but **never changes existing event dates or status**.
`--base-date YYYY-MM-DD` affects only missing event fixtures.

For a fresh dataset without deleting the existing database, stop the current
project and create a separately named Compose project with its own volume:

```powershell
docker compose stop
docker compose -p golocal-fresh up -d --build --wait
.\.venv\Scripts\python.exe scripts/migrate.py
.\.venv\Scripts\python.exe scripts/seed_demo.py --base-date (Get-Date).ToString('yyyy-MM-dd') --with-activity
.\.venv\Scripts\python.exe scripts/verify_db.py
```

Use an unused project name if `golocal-fresh` already exists. Keep the same `.env`
connection settings: the old database is stopped, freeing its host port. Expected
for a fresh project: both migrations applied, 25 events inserted with future dates,
and the optional related rows above. This fresh-project workflow is **unverified**
in this documentation pass. Restart/refresh pgAdmin's connection to inspect it.

To return to the original database, stop the new project with
`docker compose -p golocal-fresh stop`, then run `docker compose up -d --wait`.
Both volumes remain. **Removing a database volume erases everything in that
database**, including users and saved events. No volume deletion is needed here.

## What teammates can rely on

Events expose IDs, title/description, category/venue relationships, start/end times,
price range/currency, status, source name/URL, and creation/update timestamps.
Addresses and coordinates are in `venues`; city timezone is in `cities`.
`NULL` price means unknown; `0` means free. Known prices require currency.
Instants use `timestamptz`, normalized to UTC; Docker sessions default to UTC.
PostGIS points use **longitude, latitude** order. Text remains untrusted input.

See [the data layer reference](docs/data-layer.md) for schema contracts,
normalization functions, migration rules, security details, and planned backend functions.

## If something fails

Share the failed command and its redacted error, plus:

```powershell
docker compose ps
docker compose logs --tail 60 db
```

For the separate fresh project, add `-p golocal-fresh` after `compose` in both
commands. Never share `.env` or `docker compose config` output, which can contain
passwords. Never paste credentials into chat. Changing `.env` credentials after a
volume is initialized does not change the existing database credentials.
`docker compose stop` stops the default database while keeping its data.

## Layout

| Folder | Purpose |
| --- | --- |
| `docker/` | Database image with PostGIS and pgvector |
| `migrations/` | Versioned schema and city/category seeds |
| `src/golocal_data/` | Normalization, validation, migrations, demo loading |
| `scripts/` | Migration, seed, and verification commands |
| `tests/` | Offline checks |
| `data/` | Fictional event and user fixtures |
