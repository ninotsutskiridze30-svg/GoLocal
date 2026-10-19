# goLocal Team Plan

How the goLocal team works together to build the AI-Powered Event & Activity Discovery Platform. This plan sits beside the Project Specification and answers a different question: not *what* we build, but *who* builds it, *in what order*, and *how we stay in sync*.

**Team rule (from the spec):** every member has one primary owner area, but integration is shared. No feature is complete until it works end to end on the deployed branch.

## 1. Goals of this plan

- Everyone knows exactly what they own and what they hand to someone else.
- Nobody is blocked waiting for another person's finished work: we agree interfaces first and build in parallel.
- Every week ends with a working integration demo, not isolated components.
- The AI never invents event facts. The database is the source of truth.

## 2. Roles and ownership

| # | Role | Owner | Owns | Hands to others |
| --- | --- | --- | --- | --- |
| 1 | Data Engineer | Nino | PostgreSQL schema, collectors, parsing, normalization, deduplication, scheduled pipeline, data quality | A populated, clean database and the schema docs |
| 2 | AI/ML Engineer | Nino | LLM query parser, embeddings, semantic search, ranking, explanations, hallucination guardrails | Python functions the backend calls (see section 6) |
| 3 | Backend Engineer | Archill | FastAPI endpoints, auth, search service, event service, interaction tracking | A documented REST API |
| 4 | Frontend Engineer | Ani | Homepage, search UI, event cards, filters, map, detail page, saved events, responsive design | The working web app |
| 5 | Product / Full-Stack / QA |  | Requirements, user flow, testing, UI polish, integration, deployment support, documentation, demo | Test reports, deployment, final presentation |

### Backup owners

Each area has a named backup who can review its pull requests and take over if the owner is unavailable.

| Area | Owner | Backup |
| --- | --- | --- |
| Database and pipeline | Nino | [name] |
| LLM and search | Nino | [name] |
| Backend API | Archil | [name] |
| Frontend | Ani | [name] |
| QA and deployment | [name] | [name] |

## 3. Order of work and dependencies

The database comes first, but only the schema and a small set of sample events. After that the three tracks run in parallel.

| Step | Who | What | Done when |
| --- | --- | --- | --- |
| 1 | Everyone | Agree the event shape and the API contract | `docs/api-contract.md` merged |
| 2 | Data | Schema, Docker Postgres, 20 to 30 hand-written sample events loaded | Teammates can run the database and query events |
| 2 | Backend | FastAPI skeleton, database connection, `GET /events` and `GET /events/{id}` | Endpoints return the sample events |
| 2 | Frontend | Next.js skeleton, wireframes, event cards built on mock JSON in the agreed shape | Pages render with mock data |
| 3 | Data | Real collectors, normalization, deduplication | 100+ real events from two sources |
| 3 | Backend and Frontend | Connect the frontend to the real API; filters, map, detail page | Product works without AI |
| 4 | Data/AI | Query parser, embeddings, ranking, explanations | Search works on real data |
| 4 | Backend | `POST /search` calls the AI functions | Natural-language search works end to end |
| 5 | Backend and Frontend | Saved events, interaction tracking, preferences | Users can save and unsave events |

Who waits for whom:

- **Frontend** never waits for the database. It builds on mock JSON and switches to the real API later.
- **Backend** waits only for the schema, not for real data.
- **Data/AI** waits for nobody. The sample events from step 2 are what let the others start.

## 4. Shared agreements

### 4.1 Event shape (the one thing that must not drift)

Agreed in `docs/api-contract.md` and reviewed by every member.

- Times are always UTC with a `Z`. The frontend converts to local time.
- Price: `null` means unknown, `0` means free. Currency is a three-letter code.
- Every event carries `source_name` and `source_url`.
- Every field is marked either always present or nullable.
- A change to this shape needs a pull request that all three tracks approve.

### 4.2 API contract

| Endpoint | Request | Response |
| --- | --- | --- |
| `GET /events` | Optional query: category, date range, max price, page | A page of events with a total count |
| `GET /events/{id}` | Event id | One event |
| `POST /search` | `{ "query": "..." }` | The parsed filters plus ranked results, each with a score and an explanation |
| `POST /events/{id}/save`, `DELETE /events/{id}/save`, `GET /saved-events` | Authenticated | Save state and saved list |
| `POST /interactions` | Event id and interaction type | Acknowledgement |

### 4.3 Environment and secrets

- Keys and database credentials live only in environment variables.
- The repo contains `.env.example` with placeholder values. `.env` is in `.gitignore`.
- Nobody pastes keys into chat, issues, pull requests or commits. If a key leaks, rotate it the same day.

## 5. GitHub workflow

- Repository: [https://github.com/ninotsutskiridze30-svg/GoLocal](https://github.com/ninotsutskiridze30-svg/GoLocal)
- Branch per task, named `<area>-<short-description>`, for example `data-collectors` or `fe-event-cards`.
- Nothing is pushed directly to `main`.
- Every change goes through a pull request. A teammate reviews and approves; the author does not merge their own work.
- Pull request description says what changed, how to test it, and which issue it closes.
- Small pull requests: aim for something a reviewer can read in 15 minutes.
- Issues track tasks, bugs and data-quality failures. Label them `data`, `ai`, `backend`, `frontend` or `qa`.
- Schema and API changes are documented in the same pull request that makes them.
- Tag the commit that is submitted for each course deliverable.

### Suggested repository layout

| Folder | Contents | Owner |
| --- | --- | --- |
| `docs/` | Spec, this plan, API contract, decisions | Everyone |
| `db/` | Schema and migrations | Data |
| `pipeline/` | Collectors, normalization, loading, embedding | Data |
| `llm/` | Query parser and model client | AI |
| `backend/` | FastAPI app | Backend |
| `frontend/` | Next.js app | Frontend |
| `tests/` | Offline tests for each area | Each owner |

Agree this layout before anyone creates folders, so two people do not create competing structures.

## 6. Interfaces between tracks

The Data/AI owner provides plain Python functions. The backend calls them and does not reach into the database internals.

| Function (working names) | Input | Output | Used by |
| --- | --- | --- | --- |
| `parse_query(text, today)` | A natural-language request | Validated filters, or `None` if parsing failed | `POST /search` |
| `search_events(filters, query_embedding)` | Filters and an embedding | Event ids with score components | `POST /search` |
| `explain(event_record)` | One database record | A short explanation that uses only that record | `POST /search` |

Guardrails every member must respect:

- The LLM never invents events, prices, dates, venues or links. Candidates come only from the database.
- All LLM output is validated against a strict schema before use.
- No raw LLM-generated SQL is ever run. Queries are parameterized.
- Scraped text is untrusted input.

## 7. Eight-week plan by person

| Week | Data / AI | Backend | Frontend | QA / Product |
| --- | --- | --- | --- | --- |
| 1 | Schema, Docker Postgres, sample events | FastAPI skeleton, database connection | Next.js skeleton, wireframes | Requirements, user flow, API contract draft |
| 2 | First two sources, 100+ real events | `GET /events`, `GET /events/{id}` | Event cards, browse page on mock data | Test plan, review the data |
| 3 | Normalization, deduplication, expiry, validation tests | Filters in the API | Filters UI, detail page | Data-quality checks |
| 4 | Fix data issues, schema docs | Auth skeleton | Map, responsive UI, switch to real API | Product works without AI |
| 5 | Query parser | `POST /search`, hard filters | Natural-language search UI | Parser test queries |
| 6 | Embeddings, ranking, explanations | Integrate semantic search | Result cards with explanations | Evaluation set of 20 to 30 queries |
| 7 | Ranking tuning from evaluation | Saved events, interactions | Saved events UI | End-to-end testing, UI polish |
| 8 | Monitoring, demo dataset | Deployment, error handling | Final polish | README, architecture diagram, presentation |

## 8. Weekly rhythm

| When | What |
| --- | --- |
| Start of week | 20-minute planning: each person states their goal for the week and what they need from others |
| Mid-week | 10-minute async check-in in the team chat: done, blocked, next |
| End of week | Integration demo on the shared branch, then a short retro |

A blocker is posted in the team chat the same day it appears, not at the next meeting.

### Definition of done (weekly)

- Work is merged through reviewed pull requests.
- The week's integration demo runs on the shared branch.
- New bugs and data-quality failures are open as issues.
- API and schema changes are documented.

## 9. Decisions

- Small decisions inside someone's area: the owner decides and tells the team.
- Anything that touches another area (event shape, API, schema, ranking weights): proposed in a pull request or issue, approved by the affected owners.
- Disagreements the owners cannot settle in a day go to the whole team and are decided by majority.
- Important decisions are recorded in `docs/decisions/`, one short file each: context, decision, alternatives, consequences.

## 10. Team risks

| Risk | Effect | Mitigation | Owner |
| --- | --- | --- | --- |
| Event shape changes late | Frontend and backend break | Lock it in step 1; changes need all three tracks to approve | Everyone |
| Real sources are slow to integrate | No real data for the frontend or AI | Sample events from day 3 so others are never blocked | Data |
| A source forbids scraping or changes its page | Pipeline fails | Check terms and robots first; prefer official APIs; keep a backup source | Data |
| One person is overloaded | Missed deadlines | Backups named in section 2; raise it in the weekly check-in | QA / Product |
| A key leaks into git | Account abuse and cost | `.env` ignored, rotate keys immediately | Everyone |
| AI invents event details | Users lose trust | Grounded explanations, schema validation, evaluation set | AI |
| Integration left to the last week | Demo fails | Weekly integration demo | QA / Product |
| Cost of LLM calls grows | Budget overrun | Log tokens and cost per call; cache repeated queries | AI |

## 11. Course milestones

Taken from the course materials; confirm against the course repository before relying on them.

| What | Who | Due |
| --- | --- | --- |
| HW1 "Spec to Ship" | Individual | Tuesday 20 October 2026, 23:59 (Tbilisi) |
| Design Review (`docs/DESIGN-REVIEW.md` on `main`, tag `design-review`, team form) | Team, submitted by the repo keeper | Tuesday 20 October 2026, 23:59 (Tbilisi) |
| Quiz 1 | Individual, no AI tools allowed | Tuesday 27 October 2026, 23:59 (Tbilisi) |

Assign a **repo keeper** who submits the team form and creates the tag.

## 12. First-week checklist

- [ ]  Names filled in for every role and backup
- [ ]  Repository layout agreed
- [ ]  `docs/api-contract.md` drafted and approved by all tracks
- [ ]  Schema and sample events available to the backend
- [ ]  Mock JSON available to the frontend
- [ ]  `.env.example` and `.gitignore` in place
- [ ]  Issue labels created
- [ ]  Repo keeper chosen
- [ ]  Weekly meeting time fixed