# goLocal API and Data/AI contract

Status: **DRAFT FOR TEAM REVIEW**, version 0.1. Proposed by Data/AI from the team
plan and project specification. Archil (backend), Ani (frontend), and Nino (Data/AI)
must review before treating it as agreed. This document defines proposed interfaces;
it does not implement endpoints, AI functions, or authentication.

## Shared conventions

- JSON field names use snake_case. Unknown request fields are rejected.
- All response fields listed below are present; nullable fields use JSON `null`.
- IDs are positive JSON integers, mapped to PostgreSQL bigint. Booleans are not IDs.
  Current demo IDs are small; JavaScript clients must not silently round large IDs.
- Timestamp strings use UTC ISO 8601 with `Z`, for example `2026-10-20T15:00:00Z`.
  Python functions use timezone-aware datetime objects; the backend serializes them.
- JSON prices are numbers with at most two decimal places; Python uses Decimal.
  `null` means unknown, `0` means free. No currency conversion is implied.
- Source URLs and descriptions are untrusted data. Escape text in the UI; never
  treat scraped descriptions as executable instructions or construct SQL from them.
- Demo results must be labeled as demo. Placeholder links are not real ticket links.

## Filters: exact Data/AI input object

Every key is required in the normalized filter object. Defaults below are filled
by code, never inferred by downstream consumers. Optional constraints use null or
an empty list. The same structure is returned by the parser and consumed by search.

| Field | Type | Default | Validation and meaning |
| --- | --- | --- | --- |
| `start_time` | UTC timestamp or null | null | Inclusive lower bound on event start |
| `end_time` | UTC timestamp or null | null | Exclusive upper bound on event start; greater than start_time if both exist |
| `time_of_day` | string or null | null | `morning`, `afternoon`, `evening`, or `night` |
| `timezone` | string | `UTC` | Valid IANA timezone for local time-of-day filtering |
| `max_price` | number or null | null | Nonnegative, at most 9999999999.99, at most two decimal places |
| `currency` | string or null | null | Three uppercase letters; required with max_price |
| `categories` | array of strings | [] | Unique canonical categories; OR within this list |
| `city_id` | integer or null | null | Positive city ID; null means no city restriction |
| `latitude` | number or null | null | Between -90 and 90 |
| `longitude` | number or null | null | Between -180 and 180 |
| `radius_km` | number or null | null | Greater than zero, at most 200; requires both coordinates |
| `keywords` | array of strings | [] | Up to 20 unique nonempty strings, each at most 100 characters |
| `limit` | integer | 20 | 1-100 |
| `offset` | integer | 0 | Nonnegative |

Coordinates are supplied together; a coordinate pair can support distance ranking
without a radius. All numeric values must be finite. Different constraint types
combine with AND. A city ID is data, not a hard-coded city name.

Canonical categories (from the current seeds): `music`, `nightlife`, `exhibition`,
`theatre`, `workshop`, `technology`, `sports`, `festival`, `market`, `family`, `talk`,
`film`, `food`, `social`, `other`. Empty categories impose no category restriction.

Time-of-day windows use event start in `timezone`: morning [06:00,12:00), afternoon
[12:00,17:00), evening [17:00,22:00), night [22:00,24:00) or [00:00,06:00).
These windows and numeric limits are proposed product decisions, not existing code.
Date bounds are resolved in Python before search. Relative dates use `today` in the
filter timezone; the backend must provide the appropriate local date explicitly.

A budget excludes unknown prices and other currencies and checks `price_min <=
max_price`. This means an advertised starting price fits, not that every ticket
fits. Radius filtering excludes venues without coordinates. Keywords match
case-insensitive literal substrings in title/description, with OR within the list;
no raw SQL wildcard syntax is accepted from users. Search returns active events
that have not ended: a known end must be later than the request time; with an
unknown end, the start must be at or after the request time. Automatic database
expiry remains separate future work. These are proposed search semantics.

## Event: shared response object

Every field below is required in the response object. Nullability describes the
wire format, which is separate from the NormalizedEvent ingestion model.

| Field | Type | Nullable | Meaning / source |
| --- | --- | --- | --- |
| `id` | integer | no | events.id |
| `title` | string | no | Event title |
| `description` | string | no | Plain untrusted text; may be empty |
| `short_description` | string | yes | Optional shorter text |
| `category` | object | yes | `{ "id": integer, "name": string }`; null if uncategorized |
| `venue` | object | no | Venue object defined below |
| `start_time` | UTC timestamp | no | Event start |
| `end_time` | UTC timestamp | yes | Unknown end remains null |
| `price_min` | number | yes | Starting price |
| `price_max` | number | yes | Highest known price; not below price_min |
| `currency` | string | yes | Required when either price is known |
| `image_url` | string | yes | HTTP(S) image URL; null if absent |
| `source_name` | string | no | Primary event attribution |
| `source_url` | string | no | HTTP(S) primary source link |
| `language` | string | yes | Source-provided language label |
| `age_restriction` | integer | yes | Nonnegative minimum age |
| `status` | string | no | `active`, `expired`, or `cancelled` |
| `created_at` | UTC timestamp | no | Record creation |
| `updated_at` | UTC timestamp | no | Record update |

`venue` has exactly `id` (positive integer), `name` (string), `address` (string or
null), `latitude` (number or null), `longitude` (number or null), and `city`.
Coordinate values are both null or both present. `city` has exactly `id` (positive
integer), `name` (string), `country_code` (two uppercase letters), and `timezone`
(IANA name). These all come from database records. GeoJSON/PostGIS coordinate
arrays use longitude first; the named latitude/longitude fields remain explicit.

## Functions the backend will call

These signatures and structures are proposed stable boundaries. **All three
functions are NOT IMPLEMENTED YET.** Future stubs must identify their fake output.
Type names below describe contract types, not classes that already exist.

```python
parse_query(text: str, today: date) -> Filters | None
search_events(filters: Filters, query_embedding: list[float] | None) -> list[SearchHit]
explain(event_record: Event) -> str
```

- `parse_query`: text is trimmed, nonempty, at most 2000 characters. Returns all
  filter keys above, or None on malformed/unsupported extraction. It performs no
  SQL and invents no event facts. Relative date expressions are resolved by code.
  In this initial signature the parser defaults timezone to UTC unless the query
  explicitly supplies a supported timezone; it must not guess a city timezone.
  A richer request context requires a reviewed signature change.
- `search_events`: accepts validated filters. Embedding values must be finite,
  nonempty, and match the configured model and dimension; None enables keyword /
  structured-only retrieval. Model selection is application configuration, not
  inferred from vector length. Do not mix synthetic and real embedding models.
  Returns unique event IDs after filtering, scoring and pagination; [] is valid.
  Invalid arguments raise ValueError. Operational errors propagate to the backend
  for sanitized handling. It exposes no HTTP behavior and returns no invented IDs.
- `explain`: receives one complete Event object retrieved from PostgreSQL; returns
  a nonempty explanation based only on its fields. Missing facts stay unknown.
  With this signature it cannot claim a match to user interests or budget, since
  it receives no filters. Personalized explanations need a reviewed extension.

### SearchHit and scoring

Each SearchHit has exactly `event_id` (positive integer), `score` (number in [0,1]),
and `score_components` (object containing exactly the six numbers below).
Components are normalized raw signals in [0,1], not weighted contributions.

| Component | Default weight |
| --- | ---: |
| `semantic` | 0.30 |
| `price` | 0.20 |
| `date` | 0.20 |
| `category` | 0.15 |
| `distance` | 0.10 |
| `popularity` | 0.05 |

`score` is the weighted sum. Missing/unrequested signals use 0.5 as a proposed
neutral value. Weights are configurable, nonnegative, and sum to 1. Ties break by
event_id ascending; pagination is applied after ordering by score descending.
Signal calculation/calibration still needs implementation and evaluation. Initial
stubs can use fixed component values but must label the enclosing response as demo.

```json
{
  "event_id": 1,
  "score": 0.8,
  "score_components": {
    "semantic": 0.8, "price": 0.8, "date": 0.8,
    "category": 0.8, "distance": 0.8, "popularity": 0.8
  }
}
```

This ID and score are illustrative, not a promise that event 1 exists in every
installation. Stubs must resolve fixture external_ids against the local database,
or use an explicitly isolated mock dataset with its own matching Event records.

## POST /search

Request body has exactly one field, `query`: trimmed nonempty string, max 2000
characters. No authentication is required for this proposed public search endpoint.
The backend supplies today's date explicitly; API callers do not control the clock.

```json
{"query": "Find free music events"}
```

Success: HTTP 200 with exactly these keys:

| Field | Type | Meaning |
| --- | --- | --- |
| `query` | string | Trimmed original request |
| `parsed_filters` | Filters or null | null if parser failed |
| `mode` | string | `demo`, `hybrid`, or `keyword` |
| `results` | array of RankedEvent | Ordered results; empty is a successful no-match response |
| `count` | integer | Number returned, not total matching rows |
| `limit` | integer | Effective limit, 20 when parsing failed |
| `offset` | integer | Effective offset, 0 when parsing failed |

RankedEvent has exactly `event` (the full Event object), `score` (number),
`score_components` (the same six-component object), and `explanation` (string).
Event IDs are inside `event.id`, not duplicated at the RankedEvent level.
The backend hydrates SearchHit IDs from the database and preserves ranking order.
If no parser result exists, mode is `keyword`, parsed_filters stays null, and the
backend builds default filters with keywords from the trimmed original query:
split on whitespace, casefold, truncate each token to 100 characters, deduplicate
in first-occurrence order, and keep at most 20 tokens.
A demo implementation always returns mode `demo`, even if parsing was simulated.

A complete no-match example, also defining the failure-to-parse wire shape:

```json
{
  "query": "Something unusual",
  "parsed_filters": null,
  "mode": "keyword",
  "results": [],
  "count": 0,
  "limit": 20,
  "offset": 0
}
```

A parsed-filter example (used as the value of `parsed_filters`):

```json
{
  "start_time": null,
  "end_time": null,
  "time_of_day": null,
  "timezone": "UTC",
  "max_price": 0,
  "currency": "GEL",
  "categories": ["music"],
  "city_id": null,
  "latitude": null,
  "longitude": null,
  "radius_km": null,
  "keywords": [],
  "limit": 20,
  "offset": 0
}
```

The currency in this illustration is explicitly selected, not inferred from the
word "free". A real parser needs currency context or must leave the budget unset.

## Browse endpoints and errors

These are proposed for backend ownership, not implemented by this package.

- `GET /events`: optional category (one canonical name), start_time, end_time,
  max_price, currency, city_id, page (default 1, minimum 1), page_size (default 20,
  range 1-100). The corresponding constraints follow Filters semantics. Returns
  HTTP 200: `{ "items": [Event], "total": integer, "page": integer,
  "page_size": integer }`. total is all matching rows before pagination; order
  is start_time then id ascending. Browse returns active upcoming/ongoing events.
- `GET /events/{id}`: HTTP 200 with one Event, including expired/cancelled records
  when requested by ID; HTTP 404 if no record exists.
- Invalid request/filter: HTTP 422, proposed envelope
  `{ "error": { "code": "validation_error", "message": "Invalid request" } }`.
  Missing event: HTTP 404, same envelope with code `not_found`.
  Dependency/database outage: HTTP 503 with code `service_unavailable`.
  Unexpected internal errors: HTTP 500 with code `internal_error`.
  Messages are sanitized, never driver exception text, credentials, or source secrets.
  FastAPI's default validation body differs: the backend must explicitly adopt
  this envelope or propose a contract revision before frontend integration.
- Parser failure itself is not an HTTP error; it triggers the keyword fallback.

Saved-event, interaction, authentication, and `GET /recommendations` contracts
remain to be agreed separately. The last endpoint is in the project specification
but omitted from the team plan's endpoint summary. This document does not define
or implement those routes.

## Review and acceptance

- Nino: filter validation, ID hydration, ranking components, stub/real separation.
- Archil: Python call boundaries, embedding ownership, endpoint serialization and
  error handling. Backend prepares the query embedding using the configured model;
  a helper for that step is future work, not one of the three functions above.
- Ani: nullable fields, timestamp display, pagination and no-match rendering.
- All three: approve proposed defaults, time windows, price semantics, neutral
  scores, currency/timezone context, and the error envelope before implementation.

The existing schema and demo fixtures need no migration for this proposed contract.
Implementation status is described in [the data layer reference](data-layer.md).
