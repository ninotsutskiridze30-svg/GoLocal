# goLocal data layer

Database schema, Docker PostgreSQL, event normalization, and fictional demo data for goLocal.
This package includes no frontend, FastAPI endpoints, or authentication.

## Status

Available: versioned schema, Docker PostgreSQL with PostGIS and pgvector,
normalization/validation functions, 25 fictional events with six demo venues,
and optional fictional users and activity.

Not implemented yet: real-source collectors and an HTTP application.
The bounded Python discovery path uses a deterministic query parser, PostgreSQL
search over demo rows, and one Gemini call for up to three Georgian reasons.
The separate RAG path uses 13 reviewed public-listing snapshots, Gemini text
embeddings, a local file index, and source-cited answers or refusals. The first
three live golden runs passed 3/10, 7/10 and 9/10 under the original scorer.
The third run used bounded retries; its remaining answer failure was Gemini
HTTP 503. One refusal counted as a pass after a provider timeout, so the
source-based audit of that run is 8/10, still above the 0.70 threshold.

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

## Try the Python discovery slice

The discovery functions are in `src/golocal_data/discovery.py`:
`parse_query(query)` extracts conservative hard filters;
`search_events(filters)` reads up to 12 active demo candidates from PostgreSQL;
`explain(query, candidates)` sends them in one Gemini 3.1 Flash-Lite request and
keeps only unique IDs returned from those candidates. `recommend(query)` connects
the three. No real embedding request is made. Gemini uses `GOOGLE_API_KEY` from
the process environment; for the local CLI, put it in ignored `.env` and run:

```powershell
.\.venv\Scripts\python.exe scripts/recommend.py "ჯაზი"
```

The command prints up to three labeled demo results. It makes no model request for
blank input or zero database candidates. Each nonempty candidate set makes at
most one request; a model failure returns a sanitized error. The source links are
`example.com` placeholders and must not be presented as ticket links. This CLI
is not an HTTP service; the HTTP 400 acceptance criterion remains open.

## Ask source-grounded questions locally

The RAG service reads `data/corpus/events/*.md`. Each document has a public source
URL and is a snapshot, not a live ticket feed. Set `GOOGLE_API_KEY` in your shell
environment (do not print or commit it), then from the repository root run:

```powershell
.\.venv\Scripts\python.exe scripts/index_corpus.py
.\.venv\Scripts\python.exe scripts/ask_corpus.py "ვალერიან შიუკაშვილის კონცერტზე კარი როდის იღება?"
.\.venv\Scripts\python.exe evals/run_golden.py
```

The first command makes one embedding call per chunk and writes the ignored
`logs/rag_index.json`. Rebuild after any Markdown edit or embedding-model change.
The second embeds the question, retrieves up to five chunks, and returns JSON
with an answer, numbered citations and original source URLs; it refuses when
the available evidence is insufficient or citations fail validation. The third
runs ten fixed golden questions live and writes `evals/results/<run>.json`; it
requires a 0.70 pass rate. These commands do not use PostgreSQL or load `.env`.
Usage and answer/refusal logs live under ignored `logs/`. Automated tests use
fakes and make no paid calls. See `docs/retrieval-spec.md` for scoring, grounding
rules, limitations and evaluation status.

## Read event posters locally

The five manually reviewed poster images live in `data/posters/` beside
`posters.json`. They are not demo database rows. The image reader uses the same
Gemini 3.1 Flash-Lite model and `GOOGLE_API_KEY` process variable as discovery.
Set the variable in your own shell before running these commands; the commands
do not inspect or print your key:

```powershell
.\.venv\Scripts\python.exe scripts/extract_poster.py data/posters/336c12f0-7211-4a56-8eab-112ef07816a8.jpg
.\.venv\Scripts\python.exe scripts/evaluate_posters.py
```

The first command prints a route, human-readable flags, and a draft with
uncertain fields empty. The second makes one model call for each of the five
images and compares each result with the manually reviewed JSON. Differences
are reported rather than hidden; the command exits nonzero if any differ.
Usage lines are written to ignored `logs/poster_usage.jsonl` with tokens,
estimated cost, and latency. Offline tests use fake model responses and need
no key. The expected live behavior remains unverified until a successful run.

The three additional phone photos are in `tests/images/candidates/`. The
blurred poster is a degraded candidate; the handwritten poster has an unknown
day, and the book cover includes a real author's name. They are not yet the
four formal Lab 3 test images. See `docs/multimodal-spec.md` and
`docs/confidence-policy.md` for fields, limitations, and review behavior.

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
