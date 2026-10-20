# AGENTS.md · goLocal-AI (working repository name)

AI coding agents work on goLocal-AI, a local discovery application for people across Georgia. The data layer and three discovery functions exist; no HTTP application is implemented. Feature source of truth: `docs/spec.md`. `docs/api-contract.md` remains a team-review draft where it differs from the implemented discovery slice.

## Commands

- Install: `python -m venv .venv`, then `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock` and `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`.
- Run database: `docker compose up -d --wait`; then `scripts/migrate.py`, `scripts/seed_demo.py`, and `scripts/verify_db.py` with the venv Python. Try discovery with `.\.venv\Scripts\python.exe scripts/recommend.py "ჯაზი"` after local configuration. No HTTP app exists.
- Test: `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`.
- Lint/format: PENDING — no configuration or verified command exists.

## Conventions

- Python is in use. The inherited plan says Django, while the team plan proposes FastAPI; no HTTP framework has been selected for this repository.
- First slice: natural-language request, PostgreSQL rows loaded from the committed local JSON fixture, at most one Gemini call, and at most three unique fixture-backed recommendations with nonempty reasons. Empty or whitespace-only requests fail before the model call; HTTP 400 still requires an endpoint.
- Treat fixtures as synthetic until verified. TKT.ge and Biletebi.ge are planned real sources; neither has a live integration here.
- `parse_query` and `search_events` are deterministic; `explain` sends one batch to Gemini 3.1 Flash-Lite, validates structured output, and discards IDs absent from the retrieved candidates. No real semantic embedding call exists. Usage logging and the public HTTP contract are PENDING.
- The HTTP 400 error body, public response shape, and broader date/time rules are PENDING. Do not silently choose a public contract.
- Changed behavior needs a test that would fail if it broke. Automated tests must not depend on live event sites or paid model calls.
- Poster extraction is a separate vision slice. Downscale before a model request; require a schema and validate the reply; every populated field needs image evidence. Missing poster facts remain null, and a printed doors-open time is not an event start.
- Route uncertain poster fields through the pure `decide()` function. Never prefill a low-confidence or unsupported model value into a form. The five reviewed poster images are evaluation references, not automatically trusted database rows.

## Always

- Before creating or editing any repository file, agree on the exact file-by-file changes and every substantive detail with the person requesting the work. Do not write drafts into files, stage, commit, or push changes before that person's explicit approval.
- Read `docs/spec.md` and relevant existing files, then propose exact file-by-file changes and wait for human approval before implementation.
- Keep changes within the approved slice; inspect existing patterns before adding abstractions or refactoring other work.
- Add or update relevant tests, run the verified test command when one exists, and report the actual result or why verification was unavailable.

## Ask first

- Add, remove, or upgrade a dependency; change the approved Gemini provider/model or add an agent framework or external service.
- Change acceptance criteria, a public response shape, the event schema's public contract, or significant architecture.
- Edit CI configuration; add scraping or new integration sources; request GPS; introduce long-term personalization, Watches, notifications, or ticket purchasing.

## Never

- Read, write, commit, or print `.env` or secrets.
- Delete, skip, or weaken a test to make code pass.
- Fabricate event details or source URLs, or return a model-selected event ID absent from validated source data.
