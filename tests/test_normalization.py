from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from golocal_data.models import NormalizedEvent, event_has_finished
from golocal_data.normalization import (
    normalize_category, normalize_currency, normalize_datetime, normalize_price,
    normalize_text, normalize_url, normalize_venue_name, venue_match_key,
)


@pytest.mark.parametrize("value, expected", [(None, None), (0, Decimal("0.00")),
    (" 12.50 ", Decimal("12.50")), (Decimal("10.1"), Decimal("10.10")),
    ("9999999999.99", Decimal("9999999999.99"))])
def test_prices(value, expected):
    assert normalize_price(value) == expected


@pytest.mark.parametrize("value", [True, 1.2, -1, "free", "", "30 GEL", "10-20",
    "1,20", "1.001", Decimal("NaN"), Decimal("Infinity"), Decimal("0.001"),
    "10000000000", "1e2"])
def test_invalid_prices(value):
    with pytest.raises(ValueError):
        normalize_price(value)


def test_currency_is_not_inferred():
    assert normalize_currency(None) is None
    assert normalize_currency(" gel ", allowed={"GEL"}) == "GEL"
    for value in ("$", "EURO", "12X", "USD"):
        with pytest.raises(ValueError):
            normalize_currency(value, allowed={"GEL"})


def test_text_and_venue_keys_preserve_identity():
    assert normalize_venue_name("  Cafe\t CENTRAL ") == "Cafe CENTRAL"
    assert venue_match_key(" Cafe CENTRAL ") == "cafe central"
    assert normalize_text("Cafe\u0301") == "Caf\u00e9"
    assert normalize_text("\u10d7\u10d1\u10d8\u10da\u10d8\u10e1\u10d8") == "\u10d7\u10d1\u10d8\u10da\u10d8\u10e1\u10d8"
    assert normalize_text("<script>alert(1)</script>") == "<script>alert(1)</script>"
    for text in ("  ", "bad\x00text", 12):
        with pytest.raises(ValueError):
            normalize_text(text)


def test_category_mapping_is_explicit():
    assert normalize_category(" Concerts ") == "music"
    assert normalize_category("new unknown label") == "other"
    assert normalize_category(None) == "other"
    assert normalize_category("custom", aliases={"custom": "film"}) == "film"


@pytest.mark.parametrize("value, kwargs, expected", [
    ("2026-10-19T18:00:00+04:00", {}, "2026-10-19T14:00:00+00:00"),
    ("2026-10-19T18:00", {"source_timezone": "Asia/Tbilisi"}, "2026-10-19T14:00:00+00:00"),
    ("2026-10-19T18:00Z", {}, "2026-10-19T18:00:00+00:00"),
    ("2026-10-19T18:00", {"source_timezone": "Asia/Tokyo"}, "2026-10-19T09:00:00+00:00"),
])
def test_datetime_to_utc(value, kwargs, expected):
    assert normalize_datetime(value, **kwargs).isoformat() == expected


@pytest.mark.parametrize("value, kwargs", [
    ("2026-10-19", {}), ("19/10/2026 18:00", {}),
    ("2026-02-30T18:00Z", {}), ("2026-10-19T18:00", {}),
    ("2026-10-19T18:00", {"source_timezone": "Made/Up"}),
    ("2026-03-08T02:30", {"source_timezone": "America/New_York"}),
    ("2026-11-01T01:30", {"source_timezone": "America/New_York"}),
    ("2026-10-19T18:00Z", {"fold": True}),
])
def test_reject_dates_without_enough_information(value, kwargs):
    with pytest.raises(ValueError):
        normalize_datetime(value, **kwargs)


def test_repeated_hour_requires_choice_and_gap_cannot_be_overridden():
    first = normalize_datetime("2026-11-01T01:30", source_timezone="America/New_York", fold=0)
    second = normalize_datetime("2026-11-01T01:30", source_timezone="America/New_York", fold=1)
    assert (second-first).total_seconds() == 3600
    imaginary = datetime(2026, 3, 8, 2, 30, tzinfo=ZoneInfo("America/New_York"))
    with pytest.raises(ValueError):
        normalize_datetime(imaginary)


@pytest.mark.parametrize("value, expected", [
    ("HTTPS://EXAMPLE.COM:443/events?id=2#tickets", "https://example.com/events?id=2"),
    ("http://example.com:8080/", "http://example.com:8080/"),
    ("https://example.com", "https://example.com/"),
    ("https://[::1]:8080/e", "https://[::1]:8080/e"),
    ("https://example.com/e?a=1&a=2", "https://example.com/e?a=1&a=2"),
])
def test_urls(value, expected):
    assert normalize_url(value) == expected
    assert normalize_url(expected) == expected


def test_relative_url_needs_explicit_base():
    assert normalize_url("../events/1", base_url="https://example.com/calendar/") == "https://example.com/events/1"
    with pytest.raises(ValueError):
        normalize_url("/events/1")


@pytest.mark.parametrize("value", ["", "javascript:alert(1)", "file:///etc/passwd",
    "https://user:secret@example.com/", "https://example.com:bad/e",
    "https://example.com/a b", "https://example.com\n/", "https://bad_host/e",
    "https://example.com:99999", "https://example.com\\evil"])
def test_invalid_urls(value):
    with pytest.raises(ValueError):
        normalize_url(value)


@pytest.fixture
def event_values():
    return dict(title=" Live music ", city_id=1, venue_name=" Example Hall ",
        start_time=datetime(2026, 10, 20, 18, tzinfo=timezone.utc),
        end_time=datetime(2026, 10, 20, 20, tzinfo=timezone.utc),
        source_id=1, source_name="Synthetic test fixture",
        source_url="https://example.com/events/1", fetched_at=datetime(2026, 10, 19, tzinfo=timezone.utc))


def test_canonical_event(event_values):
    event = NormalizedEvent(**event_values, price_min=Decimal("0"), currency="gel")
    assert event.title == "Live music"
    assert event.currency == "GEL"
    assert event.price_min == Decimal("0.00")
    assert event_has_finished(event, now=event.end_time) is True
    assert event_has_finished(event, now=event.start_time) is False
    assert NormalizedEvent.model_validate_json(event.model_dump_json()) == event
    with pytest.raises(ValidationError):
        event.title = "changed"


@pytest.mark.parametrize("changes", [
    {"city_id": True}, {"source_id": "1"}, {"title": " "}, {"source_name": ""},
    {"source_url": "javascript:evil"}, {"start_time": datetime(2026, 10, 20)},
    {"start_time": "2026-10-20T18:00Z"}, {"price_min": 10},
    {"price_min": Decimal("10")}, {"price_min": Decimal("NaN"), "currency": "GEL"},
    {"price_min": Decimal("20"), "price_max": Decimal("10"), "currency": "GEL"},
    {"end_time": datetime(2026, 10, 19, tzinfo=timezone.utc)},
    {"latitude": 42.0}, {"latitude": 91.0, "longitude": 0.0},
    {"latitude": float("nan"), "longitude": 0.0},
    {"category": "concerts"}, {"unexpected": "not allowed"}, {"status": "deleted"},
])
def test_invalid_canonical_events(event_values, changes):
    with pytest.raises(ValidationError):
        NormalizedEvent(**(event_values | changes))


def test_unknown_end_does_not_invent_expiry(event_values):
    event = NormalizedEvent(**(event_values | {"end_time": None}))
    assert event_has_finished(event, now=datetime(2027, 1, 1, tzinfo=timezone.utc)) is None


def test_required_provenance(event_values):
    for field in ("source_id", "source_url", "source_name", "fetched_at"):
        data = event_values.copy()
        del data[field]
        with pytest.raises(ValidationError):
            NormalizedEvent(**data)
