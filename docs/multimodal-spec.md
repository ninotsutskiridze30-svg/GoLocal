# Multimodal spec · Poster to evidenced event data

## 1 · Input

- A user or curator has a phone photo or JPEG/PNG/WebP of an event poster.
- The local CLI accepts one image path. The evaluator reads the five user-supplied images in `data/posters/` against their manually reviewed `posters.json` reference.
- Images may be printed, photographed at an angle, handwritten, blurred, or advertise several sessions. JPEG, PNG, and WebP up to 10 MB and 24 megapixels are accepted; orientation is corrected and the longest side is reduced to 1024 px before sending.
- For the four formal Lab 3 test photos, no faces, real personal names, or ID documents are accepted. The separate real-poster reference corpus contains public promotional material and is not the formal four-photo set.

## 2 · Extracted fields

Every extracted field has `{value, evidence, confidence}`. `evidence` is a short visible quote. If absent or unreadable, `value` and `evidence` are both `null`, not a guess. Lists are `null` when absent and nonempty arrays when present.

| Scope | Field | Normalized value | Required to accept | Example evidence |
| --- | --- | --- | --- | --- |
| Poster | `document_type` | `event_poster` or `other` | yes | `THE MUSIC OF ANIMATION IN CONCERT` |
| Poster | `festival_title`, `festival_date_range` | visible text | no | `18–25 ოქტომბერი / 2026` |
| Poster | `ticket_platform`, `contact_phone`, `source_url` | visible text; URL must be printed in full | no | `TKT.GE` |
| Each session | `title` | visible title | yes | `UCNOBI` |
| Each session | `date_text` | printed day/month text | yes | `23 OCTOBER` |
| Each session | `date_iso` | `YYYY-MM-DD` only when the image prints the year | yes | `18 ოქტომბერი / 2026` |
| Each session | `displayed_time` | `HH:MM` | yes | `19:00` |
| Each session | `time_role` | `doors_open`, `event_start`, `listed_time_not_explicitly_labeled`, `listed_session_time` | yes | `DOORS OPEN — 23:00` |
| Each session | `doors_open_time` | `HH:MM` if marked as doors | no | `DOORS OPEN — 23:00` |
| Each session | `venue` | visible venue text | yes | `AT SERE` |
| Each session | `city`, `organizer`, `ticket_price` | visible text only | no | `20 ₾` |
| Each session | `performers`, `special_guests`, `lineup`, `program_items`, `films_named_on_poster` | lists of visible names | no | `COCO, FROZEN, ...` |

One poster can contain multiple `events`. The festival reference contains two visibly described sessions; its date range does not imply more event records.

## 3 · Schema and request

The Pydantic request schema is generated from these model declarations in `src/golocal_data/poster_extraction.py`:

```python
class TextField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | None
    evidence: str | None
    confidence: float = Field(ge=0, le=1)

class ListField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: list[str] | None
    evidence: str | None
    confidence: float = Field(ge=0, le=1)

class PosterEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: TextField
    date_text: TextField
    date_iso: TextField
    displayed_time: TextField
    time_role: TextField
    doors_open_time: TextField
    venue: TextField
    city: TextField
    organizer: TextField
    performers: ListField
    special_guests: ListField
    lineup: ListField
    program_items: ListField
    films_named_on_poster: ListField
    ticket_price: TextField

class PosterExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type: TextField
    festival_title: TextField
    festival_date_range: TextField
    ticket_platform: TextField
    contact_phone: TextField
    source_url: TextField
    events: list[PosterEvent] = Field(max_length=12)
```

The implementation also validates null/evidence consistency and restricts `document_type` to `event_poster` or `other`. `PosterExtraction.model_json_schema()` is sent in `generationConfig.responseFormat.text.schema` with JSON MIME type. The response is validated again with Pydantic. The prompt is in the same source file so the schema and code cannot silently diverge.

## 4 · Acceptance criteria

1. A clear poster with title, printed full date, start time, and venue yields evidenced fields and validates. No more than one model call is made per image.
2. A blurred or partly missing date routes to `review` or `confirm` with the affected field named. Its value is empty in the draft.
3. A nonposter image routes to `rejected` and its draft has no events.
4. A poster without a printed year keeps `date_iso.value=null`; a ticket logo never becomes a source URL. A printed `DOORS OPEN` time is not accepted as event start.
5. A festival poster with two visibly described sessions yields two event records, and the twelve named films on the animation poster remain available to compare with the reviewed reference.
6. The 1024 px request's usage line records input/output tokens, estimated USD cost, and latency. The pilot target is under $0.02 and 45 seconds per image; actual compliance requires a live run and is not yet claimed.

## 5 · Photos and reference corpus

| Case | Current candidate | Expected route | Formal Lab 3 status |
| --- | --- | --- | --- |
| Clean | none yet | accepted | needs a clear phone photo with printed year, start time, venue, no names/faces |
| Degraded | `tests/images/candidates/photo_2026-10-20_15-24-41.jpg` | confirm or review | image supplied; live route unverified |
| Ambiguous | `tests/images/candidates/photo_2026-10-20_15-24-46.jpg` has `??` day | review for missing date | a separate photo with two plausible dates is needed for `confirm` |
| Not applicable | `tests/images/candidates/photo_2026-10-20_15-24-35.jpg` is a book cover | rejected | its printed author name conflicts with the formal test-photo rule; a replacement is needed |

The five images in `data/posters/` and six visible sessions in `data/posters/posters.json` are the real-poster reference corpus. Their data was manually transcribed; it is not a model run or database seed. `scripts/evaluate_posters.py` processes all five with one Gemini call per image and reports differences, including missing films or invented year, price, and URL.

## 6 · Model and budget

- The repository's existing direct Gemini provider and `gemini-3.1-flash-lite` model are reused with `GOOGLE_API_KEY` from the process environment. Google's model card lists image input and structured output support. This has not yet been verified with this project's own live call.
- Estimated cost uses published standard paid rates of $0.25 per million input tokens and $1.50 per million output tokens (including thinking). The usage line is an estimate, not a billing invoice. No measured per-image cost is available until a successful live run.
- For planning only, 20 images/day × 30 days × $0.02 maximum target = $12/month ceiling. This is an assumed pilot volume, not observed demand.
- Official references: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite and https://ai.google.dev/gemini-api/docs/pricing.

## 7 · Out of scope

No automatic insertion into PostgreSQL: the existing `events` table requires a venue, exact start time, and source URL, which several real posters do not provide. Accepted/confirmed/reviewed extraction is returned as JSON for human handling. There is no HTTP upload endpoint or live event-site integration in this slice.

## 8 · Stretch

- Run the same image twice and flag disagreeing fields.
- Add a UI review queue after the team's HTTP contract is agreed.
