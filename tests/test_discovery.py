"""Behavior tests for the three discovery boundaries, without live model calls."""

from datetime import date, datetime, timezone
from decimal import Decimal
import json

import httpx
import pytest

from golocal_data.discovery import (
    EventCandidate, Filters, ModelServiceError, explain, parse_query, recommend,
    search_events,
)


NOW = datetime(2026, 10, 19, 12, tzinfo=timezone.utc)


def candidate(event_id=1):
    return EventCandidate(
        id=event_id, title="[DEMO] Paper Lantern Jazz Night",
        description="FICTIONAL DEMO EVENT. An acoustic jazz concert.",
        category="music", venue="Demo Lantern Hall", city="Tbilisi",
        start_time=datetime(2026, 10, 20, 15, tzinfo=timezone.utc), end_time=None,
        price_min=Decimal("20"), price_max=Decimal("35"), currency="GEL",
        source_name="goLocal fictional demo fixtures",
        source_url="https://example.com/golocal-demo/paper-lantern-jazz",
    )


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self

    def fetchall(self):
        return self.rows


def row(event):
    return (event.id, event.title, event.description, event.category,
            event.venue, event.city, event.start_time, event.end_time,
            event.price_min, event.price_max, event.currency, event.source_name,
            event.source_url)


def model_client(picks, calls):
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [
            {"text": json.dumps({"recommendations": picks}, ensure_ascii=False)}]}}]})
    return httpx.Client(transport=httpx.MockTransport(respond))


def test_parser_extracts_georgian_date_price_and_topic():
    filters = parse_query("ხვალ თბილისში 30 ლარამდე ჯაზი", today=date(2026, 10, 19))
    assert filters.categories == ("music",)
    assert filters.keywords == ("jazz",)
    assert filters.city_name == "Tbilisi"
    assert filters.max_price == Decimal("30")
    assert filters.currency == "GEL"
    assert filters.start_time == datetime(2026, 10, 19, 20, tzinfo=timezone.utc)
    assert filters.end_time == datetime(2026, 10, 20, 20, tzinfo=timezone.utc)


@pytest.mark.parametrize("query", ["", "  \t  ", "x" * 2001])
def test_parser_rejects_invalid_text(query):
    with pytest.raises(ValueError):
        parse_query(query)


def test_search_uses_parameters_and_only_fixture_backed_active_events():
    event = candidate()
    db = FakeConnection([row(event)])
    filters = Filters(categories=("music",), keywords=("jazz' OR true --",),
                      max_price=Decimal("30"), currency="GEL", city_name="Tbilisi")
    assert search_events(filters, connection=db, now=NOW) == [event]
    sql, params = db.calls[0]
    assert "e.source_name = %s" in sql
    assert "FROM event_sources es" in sql
    assert "es.external_id = ANY(%s)" in sql
    assert "e.status = 'active'" in sql
    assert "jazz' OR true --" not in sql
    assert "jazz' OR true --" in params
    assert "goLocal fictional demo fixtures" in params
    assert "paper-lantern-jazz" in next(value for value in params if isinstance(value, list))


def test_search_rejects_fake_semantic_vectors():
    with pytest.raises(ValueError, match="embeddings"):
        search_events(Filters(), [1.0, 0.0], connection=FakeConnection([]))


def test_explain_uses_one_call_and_discards_unknown_or_duplicate_ids():
    events = [candidate(1), candidate(2)]
    calls = []
    with model_client([
        {"event_id": 1, "reason": "  ეს ჯაზის კონცერტია.  "},
        {"event_id": 999, "reason": "გამოგონილი ღონისძიება"},
        {"event_id": 1, "reason": "დუბლიკატი"},
    ], calls) as client:
        results = explain("მინდა ჯაზი", events, api_key="test-only", client=client)
    assert len(calls) == 1
    assert calls[0].url.path.endswith("gemini-3.1-flash-lite:generateContent")
    assert [result.event.id for result in results] == [1]
    assert results[0].reason == "ეს ჯაზის კონცერტია."


def test_no_candidates_means_no_model_call():
    calls = []
    with model_client([], calls) as client:
        assert explain("კონცერტი", [], api_key="test-only", client=client) == []
        assert recommend("კონცერტი", connection=FakeConnection([]), client=client,
                         today=date(2026, 10, 19), now=NOW) == []
        with pytest.raises(ValueError):
            recommend("   ", connection=FakeConnection([]), client=client)
    assert calls == []


def test_recommend_calls_model_once_for_three_or_fewer_trusted_results(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-only")
    event = candidate()
    calls = []
    with model_client([{"event_id": event.id, "reason": "ჯაზის საღამოა."}], calls) as client:
        results = recommend("ჯაზი", connection=FakeConnection([row(event)]),
                            client=client, today=date(2026, 10, 19), now=NOW)
    assert len(calls) == 1
    assert len(results) == 1
    assert results[0].event == event


def test_malformed_model_output_is_a_safe_error():
    def respond(_request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [
            {"text": "not JSON"}]}}]})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ModelServiceError, match="Gemini recommendation failed"):
            explain("ჯაზი", [candidate()], api_key="test-only", client=client)
