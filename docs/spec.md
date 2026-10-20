# goLocal-AI · Development spec

Status: development slice in progress. This is the feature source of truth named by `AGENTS.md`. The three Python discovery functions are implemented, but the HTTP acceptance criteria and a live end-to-end model run are not yet verified. `docs/api-contract.md` remains a separate draft for team review where its proposed HTTP and search details differ from this slice.

## Problem and users

People in Georgia looking for local experiences may need to search ticket sites, venues, cultural organizations, and community sources separately. The product is intended for people who want a small set of relevant local options without comparing many listings themselves. A narrower initial user group and broader-product success criteria are PENDING team decisions.

## Product direction

Build an AI-assisted local discovery application: a person describes what they want in natural language, and the application suggests relevant events or places with short, grounded reasons. The broader vision includes verified local sources, source-grounded answers to follow-up questions, and eventually stable preferences and future-experience watches. Those later capabilities are plans, not implemented features or requirements of the first slice.

The product name is goLocal-AI. This repository currently contains a data-layer foundation for that product, not a running application.

## Current development-repository state

- PostgreSQL schema and migrations, with PostGIS and pgvector support, are present.
- `data/demo_events.json` contains 25 visibly fictional event fixtures; `scripts/seed_demo.py` can load them into PostgreSQL. Placeholder source URLs and illustrative coordinates are not real event evidence or ticket links.
- Event normalization and validation code, optional fictional user/activity fixtures, and offline tests are present.
- Optional category indicator vectors are synthetic, not semantic model embeddings. Example search logs are fixtures, not results from a live search service.
- `src/golocal_data/discovery.py` now provides conservative rule-based `parse_query`, parameterized PostgreSQL `search_events`, one-call Gemini `explain`, and a `recommend` orchestrator. `scripts/recommend.py` is a local CLI. A separate RAG service indexes manually compiled source documents with real Gemini embeddings into an ignored local file. There is no HTTP endpoint or live source collector. Three live RAG golden runs scored 3/10, 7/10 and 9/10 under the original scorer. The third run used bounded retries; one refusal was caused by a provider timeout, so its source-based audit is 8/10. Remaining answer failures were transient Gemini HTTP 503 responses.
- `pyproject.toml` and `requirements-dev.lock` are dependency manifests, and `tests/` contains tests. The inherited `AGENTS.md` command entries saying these do not exist are stale for this repository; use the actual files and README when planning work.

## Approved first working slice

Natural-language request → deterministic hard filters → validated database rows loaded from the committed local JSON fixture → one Gemini 3.1 Flash-Lite request for selection and short Georgian reasons → up to three validated recommendations.

The running Python slice reads only database rows with the fictional fixture source name. The committed fixture is synthetic; its placeholder URLs and locations are not evidence about real events. The CLI demonstrates the Python path but does not fulfill the HTTP acceptance criterion.

### Acceptance criteria

1. A valid request returns no more than 3 unique recommendations. Every returned event must exist in the local fixture, and each recommendation must include a nonempty reason.
2. A missing, empty, or whitespace-only request returns HTTP 400 and makes zero model calls.
3. A valid request makes at most one external model API call.

Python tests cover empty-input rejection, one call for a valid candidate set, no call when no candidates exist, and model ID validation. HTTP 400 remains unimplemented because this repository has no HTTP application. The model's event IDs are checked against retrieved database candidates; factual claims inside free-text reasons still require evaluation and must not be presented as independently verified. No model-generated source URL, price, date, or venue is used as a canonical record.

## Data, source grounding, and local RAG

TKT.ge and Biletebi.ge are planned real sources. Neither has a live integration in this repository. Real-source collection, attribution, storage, and permission checks need separate implementation and review. The current fictional fixtures can support local development tests but must be labeled as demo data.

The separate RAG path reads 13 curated public-listing Markdown snapshots from `data/corpus/events/`, chunks and embeds them with Gemini `gemini-embedding-2`, and stores the generated index in ignored `logs/rag_index.json`. Hybrid retrieval selects scored chunks; Gemini 3.1 Flash-Lite generates a JSON answer, which is refused if sources are weak, missing or incorrectly cited. Source links come from the curated documents, not the model. This path is a Python service and CLI; it does not insert documents into PostgreSQL or change the discovery slice. The event pages are snapshots, so current ticket availability and changed prices must be checked at the source. See `docs/retrieval-spec.md` for the detailed contract and live evaluation.

## First-slice exclusions

Live TKT.ge scraping; live Biletebi.ge scraping; GPS; notifications; Watches; long-term personalization; conversation history; ticket purchasing; and a production UI are out of scope for the first working slice.

## Unresolved implementation decisions

- `AGENTS.md` inherited a Django preference, while the team plan and draft API contract describe FastAPI. No framework has been selected for this repository's HTTP endpoint.
- The approved first slice requires HTTP 400 and up to three results. The draft `docs/api-contract.md` proposes HTTP 422, a default limit of 20, embeddings, and individual `explain(event_record)` calls. The implemented Python boundary instead uses `parse_query(query)`, `search_events(filters, query_embedding=None)`, and batched `explain(query, candidates)` so at most one Gemini call is needed. The public HTTP route, error body, and response shape still need team agreement.
- Gemini 3.1 Flash-Lite is the chosen model for batched selection and Georgian reasons. `GOOGLE_API_KEY` is read from the process environment by the library; the discovery CLI loads it from `.env`. The implementation uses the already declared `httpx` dependency. The discovery path has no embeddings or usage/cost log. The separate RAG path has embedding and usage logging code, and its live golden set reached the 0.70 threshold; this does not verify the separate database-backed discovery path or an HTTP endpoint.
- The parser intentionally understands a bounded subset of Georgian/English category, keyword, price, city, and relative-day wording. Unsupported wording remains in the Gemini request but is not converted into a guessed hard constraint. Search is restricted to the fictional demo source, active records, and at most 12 candidates. Broader dates, search ranking, real-source data, and factual evaluation of model prose remain future work.

## Verification needed before calling the slice complete

Keep offline tests for actual Python behavior: unique fixture-backed IDs with reasons, invalid input making zero model calls, and a valid candidate set making one call. The current offline suite passed 135 tests on 2026-10-19, and a local DB query for Georgian `ჯაზი` returned one fixture-backed candidate. A controlled live Gemini smoke test was attempted but the provider returned HTTP 503; model output remains unverified. Add HTTP tests for 400 and serialization when an endpoint is built. Automated tests must not require live event sites or paid calls; neither CI success nor first-slice completion is claimed here.

## Poster-image extraction slice

The repository also contains five real event-poster images with six visibly described sessions and a manually reviewed reference in `data/posters/posters.json`. These images are inputs and evaluation evidence; they are not automatically database events. Three additional phone photos are stored in `tests/images/candidates/` for uncertainty and nonposter experiments.

The separate image path in `src/golocal_data/poster_extraction.py` accepts JPEG, PNG, or WebP, corrects orientation, reduces the longest side to 1024 px, and asks the existing Gemini 3.1 Flash-Lite provider for schema-constrained fields. Each extracted field has value, quoted evidence, and confidence; missing data stays null. `src/golocal_data/poster_checks.py` makes the deterministic accepted/confirm/review/rejected decision and clears flagged values from a safe draft. `scripts/extract_poster.py` reads one image, while `scripts/evaluate_posters.py` processes all five reference images and reports differences. Model usage logs record tokens, estimated USD cost, and latency without storing image bytes or credentials.

This slice currently returns JSON from local commands. It does not insert poster records into PostgreSQL: the existing event table requires a source URL, venue, and exact start time, which several posters lack. A successful live vision run, four compliant formal Lab 3 photos, and any database import design remain to be verified before claiming end-to-end course completion. Details and review rules are in `docs/multimodal-spec.md` and `docs/confidence-policy.md`.
