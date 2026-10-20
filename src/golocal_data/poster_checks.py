"""Pure, conservative routing for model-read posters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from urllib.parse import urlsplit

from .poster_extraction import PosterExtraction, TextField


REQUIRED = ("title", "date_text", "date_iso", "displayed_time", "venue")
TIME_ROLES = {
    "doors_open", "event_start", "listed_time_not_explicitly_labeled",
    "listed_session_time",
}
MONTH_STEMS = {
    1: ("jan", "იან"), 2: ("feb", "თებ"), 3: ("mar", "მარ"),
    4: ("apr", "აპრ"), 5: ("may", "მაი"), 6: ("jun", "ივნ"),
    7: ("jul", "ივლ"), 8: ("aug", "აგვ"), 9: ("sep", "სექ"),
    10: ("oct", "ოქტ"), 11: ("nov", "ნოე"), 12: ("dec", "დეკ"),
}


@dataclass(frozen=True)
class Flag:
    kind: str
    field: str
    message: str
    hard: bool


@dataclass(frozen=True)
class Decision:
    route: str
    flags: tuple[Flag, ...]

    @property
    def fields_to_clear(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(flag.field for flag in self.flags))


def _flag(kind: str, field: str, message: str, *, hard: bool) -> Flag:
    return Flag(kind, field, message, hard)


def _time_valid(value: str) -> bool:
    if not re.fullmatch(r"\d{2}:\d{2}", value):
        return False
    hour, minute = map(int, value.split(":"))
    return hour <= 23 and minute <= 59


def _printed_day_month(value: str) -> tuple[int, int] | None:
    """Read common Georgian/English poster dates without inventing a year."""
    iso = re.fullmatch(r"\d{4}-(\d{1,2})-(\d{1,2})", value.strip())
    if iso:
        return int(iso.group(2)), int(iso.group(1))
    numeric = re.search(r"(?<!\d)(\d{1,2})[./-](\d{1,2})(?!\d)", value)
    if numeric:
        return int(numeric.group(1)), int(numeric.group(2))
    lowered = value.casefold()
    month = next((number for number, stems in MONTH_STEMS.items()
                  if any(stem in lowered for stem in stems)), None)
    day = next((int(part) for part in re.findall(r"(?<!\d)\d{1,2}(?!\d)", lowered)
                if 1 <= int(part) <= 31), None)
    return (day, month) if day is not None and month is not None else None


def decide(extraction: PosterExtraction, today: date) -> Decision:
    """Decide without file, clock, network, or model access."""
    if extraction.document_type.value != "event_poster" or not extraction.events:
        return Decision("rejected", (_flag(
            "not_event", "document_type", "ეს სურათი ღონისძიების აფიშა არ არის.", hard=True
        ),))

    flags: list[Flag] = []
    if extraction.document_type.evidence is None:
        flags.append(_flag("no_evidence", "document_type", "აფიშის ტიპს დასტური აკლია.", hard=True))

    for index, event in enumerate(extraction.events):
        prefix = f"events[{index}]"
        for name in REQUIRED:
            field: TextField = getattr(event, name)
            path = f"{prefix}.{name}"
            if field.value is None:
                flags.append(_flag("missing", path, f"{name}: აფიშაზე ვერ იკითხება.", hard=True))
            elif field.evidence is None:
                flags.append(_flag("no_evidence", path, f"{name}: წაკითხულ მნიშვნელობას ციტატა არ ახლავს.", hard=True))
            elif field.confidence < 0.6:
                flags.append(_flag("low_confidence", path, f"{name}: მნიშვნელობა გადაამოწმეთ ფოტოზე.", hard=False))

        # Optional values still need visible evidence; the model cannot fill them by guess.
        for name in (
            "time_role", "doors_open_time", "city", "organizer", "performers",
            "special_guests", "lineup", "program_items", "films_named_on_poster",
            "ticket_price",
        ):
            field = getattr(event, name)
            if field.value is not None and field.evidence is None:
                flags.append(_flag("no_evidence", f"{prefix}.{name}",
                                   f"{name}: მნიშვნელობას ფოტოზე ტექსტი არ ამყარებს.", hard=True))
            elif field.value is not None and field.confidence < 0.6:
                flags.append(_flag("low_confidence", f"{prefix}.{name}",
                                   f"{name}: მნიშვნელობა გადაამოწმეთ ფოტოზე.", hard=False))

        if event.date_iso.value is not None:
            path = f"{prefix}.date_iso"
            try:
                parsed = date.fromisoformat(event.date_iso.value)
            except ValueError:
                flags.append(_flag("invalid_date", path, "თარიღი YYYY-MM-DD ფორმატში არ არის.", hard=True))
            else:
                visible = " ".join(filter(None, (
                    event.date_iso.evidence,
                    extraction.festival_date_range.evidence,
                )))
                if str(parsed.year) not in visible:
                    flags.append(_flag("year_not_visible", path,
                                       "თარიღის წელი ფოტოზე არ ჩანს.", hard=True))
                printed = _printed_day_month(event.date_text.value or "")
                if printed is not None and printed != (parsed.day, parsed.month):
                    flags.append(_flag("date_mismatch", path,
                                       "თარიღი აფიშაზე დაწერილ დღეს ან თვეს არ ემთხვევა.", hard=True))
                if parsed < today:
                    flags.append(_flag("past_date", path,
                                       "მითითებული თარიღი უკვე გასულია; გადაამოწმეთ.", hard=False))

        if event.displayed_time.value is not None and not _time_valid(event.displayed_time.value):
            flags.append(_flag("invalid_time", f"{prefix}.displayed_time",
                               "დრო HH:MM ფორმატში არ არის.", hard=True))
        role = event.time_role.value
        if role is not None and role not in TIME_ROLES:
            flags.append(_flag("invalid_time_role", f"{prefix}.time_role",
                               "დროის მნიშვნელობა გაურკვეველია.", hard=True))
        elif role == "doors_open":
            if (event.doors_open_time.value is not None and event.displayed_time.value is not None
                    and event.doors_open_time.value != event.displayed_time.value):
                flags.append(_flag("doors_time_mismatch", f"{prefix}.doors_open_time",
                                   "კარის გაღების დრო სხვა მითითებულ დროს არ ემთხვევა.", hard=True))
            flags.append(_flag("start_time_missing", f"{prefix}.displayed_time",
                               "აფიშაზე მხოლოდ კარის გაღების დრო ჩანს; დაწყების დრო დასაზუსტებელია.", hard=True))
        elif role == "listed_time_not_explicitly_labeled":
            flags.append(_flag("unlabeled_time", f"{prefix}.time_role",
                               "დაადასტურეთ, რას ნიშნავს მითითებული დრო.", hard=False))
        elif role is None:
            flags.append(_flag("missing_time_role", f"{prefix}.time_role",
                               "დროის ტიპი ვერ განისაზღვრა.", hard=True))

    for name in ("festival_title", "festival_date_range", "ticket_platform", "contact_phone", "source_url"):
        field = getattr(extraction, name)
        if field.value is not None and field.evidence is None:
            flags.append(_flag("no_evidence", name, f"{name}: ფოტოზე ტექსტი არ ჩანს.", hard=True))
        elif field.value is not None and field.confidence < 0.6:
            flags.append(_flag("low_confidence", name, f"{name}: მნიშვნელობა გადაამოწმეთ.", hard=False))
    if extraction.source_url.value is not None:
        url = extraction.source_url.value
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or url not in (extraction.source_url.evidence or ""):
            flags.append(_flag("unverified_url", "source_url",
                               "ბმული სრულად არ ჩანს ფოტოზე.", hard=True))

    if any(flag.hard for flag in flags):
        route = "review"
    elif flags:
        route = "confirm"
    else:
        route = "accepted"
    return Decision(route, tuple(flags))


def safe_draft(extraction: PosterExtraction, decision: Decision) -> dict:
    """Never prefill a flagged model value into a review/confirmation form."""
    data = extraction.model_dump()
    if decision.route == "rejected":
        data["events"] = []
        for name in ("festival_title", "festival_date_range", "ticket_platform", "contact_phone", "source_url"):
            data[name]["value"] = None
        return data
    for path in decision.fields_to_clear:
        if path.startswith("events["):
            index_text, name = path.split("].", 1)
            index = int(index_text[7:])
            data["events"][index][name]["value"] = None
        elif path in data and isinstance(data[path], dict):
            data[path]["value"] = None
    return data
