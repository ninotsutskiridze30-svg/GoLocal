# Confidence policy · Poster extraction

`decide(extraction, today)` in `src/golocal_data/poster_checks.py` implements this table without model calls, files, or its own clock. The caller supplies today's date. All flagged fields are cleared in `safe_draft`; the raw model value is not prefilled into a form.

## Routes

| Route | Meaning | Next action |
| --- | --- | --- |
| `accepted` | Required fields have values, evidence, consistent formats, and no flags | Human can use the reviewed JSON; database import remains separate |
| `confirm` | Soft uncertainty only | Ask a person to read the image and supply/confirm the cleared field |
| `review` | Missing, unsupported, or contradictory required information | Show the image to a reviewer; flagged fields stay empty |
| `rejected` | Image is not an event poster or has no visible event | Create no event draft |

## Signals

| Field | Condition | Flag | Severity |
| --- | --- | --- | --- |
| Title, printed date, ISO date, time, venue | `value is null` | `missing` | hard |
| Any populated field | `evidence is null` | `no_evidence` | hard |
| Any populated field | `confidence < 0.6` | `low_confidence` | soft |
| ISO date | Invalid `YYYY-MM-DD` | `invalid_date` | hard |
| ISO date | Year absent from date or festival evidence | `year_not_visible` | hard |
| ISO date | Day or month differs from the printed date | `date_mismatch` | hard |
| ISO date | Date is before caller-supplied today | `past_date` | soft |
| Time | Invalid `HH:MM` | `invalid_time` | hard |
| Time role | `doors_open` with no separate event start | `start_time_missing` | hard |
| Time role | Printed time has no explicit label | `unlabeled_time` | soft |
| Source URL | Invalid URL or not fully quoted on image | `unverified_url` | hard |
| Document type | Nonposter or zero events | `not_event` | rejected |

Evidence is checked before the model's confidence number. A model value without evidence is a hard problem even if it reports confidence 0.99. A low-confidence value may be mentioned in a question to a reviewer but is never prefilled into the draft. Human-facing messages name the affected field in Georgian; raw confidence numbers are internal.

## Tests and measurement

Offline tests cover accepted, missing/degraded, ambiguous/low-confidence, nonposter, absent year, doors-open, unsupported URL, and a poster with two sessions. They use hand-written model outputs and make no API calls. The five real posters are checked against SHA-256-linked manual records; a successful live run and measured route distribution are still pending. After at least twenty real images, review wrong accepts and wrong reviews before changing thresholds.
