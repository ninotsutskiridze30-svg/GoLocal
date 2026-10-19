"""Pure normalization. Source-specific formats must be parsed by collectors first."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from urllib.parse import urljoin, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
CATEGORIES = frozenset({"music", "nightlife", "exhibition", "theatre", "workshop",
    "technology", "sports", "festival", "market", "family", "talk", "film", "food", "social", "other"})
CATEGORY_ALIASES = {"concert": "music", "concerts": "music", "party": "nightlife",
    "parties": "nightlife", "theater": "theatre", "tech": "technology"}


def normalize_text(value: str, *, required: bool = True) -> str:
    """Normalize Unicode and whitespace, preserving case and treating text as inert data."""
    if not isinstance(value, str):
        raise ValueError("Expected text")
    value = unicodedata.normalize("NFC", value)
    if any(unicodedata.category(char) == "Cc" and not char.isspace() for char in value):
        raise ValueError("Text contains control characters")
    value = " ".join(value.split())
    if required and not value:
        raise ValueError("Text must not be empty")
    return value


def normalize_venue_name(value: str) -> str:
    return normalize_text(value)


def venue_match_key(value: str) -> str:
    """Candidate matching key only; city and event timing must also be considered."""
    return normalize_venue_name(value).casefold()


def normalize_category(value: str | None, *, aliases=None, allowed=CATEGORIES) -> str:
    if value is None:
        return "other"
    key = normalize_text(value).casefold()
    mapping = CATEGORY_ALIASES if aliases is None else aliases
    result = mapping.get(key, key)
    return result if result in allowed else "other"


def normalize_currency(value: str | None, *, allowed=None) -> str | None:
    """Validate code shape; optionally enforce the caller's configured currency registry.

    This does not infer currency from symbols, a city, or an event's language.
    """
    if value is None:
        return None
    code = normalize_text(value).upper()
    if not re.fullmatch(r"[A-Z]{3}", code) or (allowed is not None and code not in allowed):
        raise ValueError("Unsupported currency code")
    return code


def normalize_price(value: str | int | Decimal | None) -> Decimal | None:
    """Accept exact numeric amounts only. NULL is unknown; explicit zero is free.

    Reject floats, symbols, ranges, comma decimals, excess precision, and unknown
    words: collectors must interpret their verified source formats explicitly.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("Price must be exact decimal text, integer, or Decimal")
    if isinstance(value, str) and not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", value.strip()):
        raise ValueError("Price must be an unsigned decimal amount")
    try:
        amount = Decimal(value.strip() if isinstance(value, str) else value)
        if not amount.is_finite() or amount < 0 or amount > Decimal("9999999999.99"):
            raise ValueError("Price is outside database limits")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Price has more than two decimal places")
        return amount.quantize(Decimal("0.01"))
    except InvalidOperation as error:
        raise ValueError("Invalid price") from error


def normalize_datetime(value: datetime | str, *, source_timezone: str | None = None,
                       fold: int | None = None) -> datetime:
    """Convert ISO date-times to UTC; reject missing time, DST gaps and ambiguous times.

    Naive input requires an explicit IANA source timezone. For a repeated local time,
    fold=0/1 must come from verified source information, never a guessed default.
    """
    if fold is not None and (type(fold) is not int or fold not in (0, 1)):
        raise ValueError("fold must be 0 or 1")
    if isinstance(value, str):
        if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", value):
            raise ValueError("Expected an ISO date with an explicit time")
        try:
            value = datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError("Invalid ISO datetime") from error
    if not isinstance(value, datetime):
        raise ValueError("Expected datetime or ISO date-time string")
    if value.tzinfo is not None and value.utcoffset() is not None:
        # Also reject imaginary local times constructed with ZoneInfo.
        result = value.astimezone(UTC)
        if result.astimezone(value.tzinfo).replace(tzinfo=None) != value.replace(tzinfo=None):
            raise ValueError("Nonexistent local time")
        return result
    if not source_timezone:
        raise ValueError("Naive datetime requires source_timezone")
    try:
        zone = ZoneInfo(source_timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Unknown IANA timezone") from error
    options = {}
    for candidate_fold in (0, 1):
        aware = value.replace(tzinfo=zone, fold=candidate_fold)
        utc = aware.astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) == value:
            options[candidate_fold] = utc
    if not options:
        raise ValueError("Nonexistent local time")
    if len(set(options.values())) > 1 and fold is None:
        raise ValueError("Ambiguous local time: explicit fold is required")
    return options[fold if fold is not None else next(iter(options))]


def normalize_url(value: str, *, base_url: str | None = None) -> str:
    """HTTP(S) provenance URL, preserving path/query semantics and removing fragments.

    Syntactic validation only: this function never fetches or authorizes a URL.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("URL must not be empty")
    value = value.strip()
    if any(char.isspace() or unicodedata.category(char) == "Cc" for char in value) or "\\" in value:
        raise ValueError("URL contains whitespace or invalid characters")
    if base_url:
        value = urljoin(normalize_url(base_url), value)
    try:
        url = urlsplit(value)
        if url.scheme.lower() not in {"http", "https"} or not url.hostname:
            raise ValueError("Expected absolute HTTP(S) URL")
        if url.username is not None or url.password is not None:
            raise ValueError("URL must not contain credentials")
        host = url.hostname.encode("idna").decode("ascii").lower()
        port = url.port  # Triggers validation of malformed ports.
        if ":" in host:
            import ipaddress
            ipaddress.IPv6Address(host)
            host = f"[{host}]"
        elif not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
            raise ValueError("Invalid URL hostname")
        scheme = url.scheme.lower()
        if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
            host += f":{port}"
        return urlunsplit((scheme, host, url.path or "/", url.query, ""))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Invalid HTTP(S) URL") from error
