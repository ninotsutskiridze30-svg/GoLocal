"""Hand-written extractions exercise the uncertain-result path offline."""

from datetime import date

from golocal_data.poster_checks import decide, safe_draft
from test_poster_extraction import event, extraction, f


TODAY = date(2026, 10, 20)


def test_clean_event_is_accepted():
    result = decide(extraction([event()]), TODAY)
    assert result.route == "accepted"
    assert result.flags == ()


def test_degraded_date_requires_review_and_clears_field():
    poster = extraction([event()])
    poster.events[0].date_iso = f()
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.kind == "missing" and flag.field == "events[0].date_iso" for flag in decision.flags)
    assert safe_draft(poster, decision)["events"][0]["date_iso"]["value"] is None


def test_ambiguous_date_requires_confirmation_without_prefilling():
    poster = extraction([event()])
    poster.events[0].date_iso = f("2026-10-25", "25 or 26 October 2026", 0.4)
    decision = decide(poster, TODAY)
    assert decision.route == "confirm"
    assert any(flag.kind == "low_confidence" for flag in decision.flags)
    assert safe_draft(poster, decision)["events"][0]["date_iso"]["value"] is None


def test_book_is_rejected_and_creates_no_event_draft():
    poster = extraction([], document_type="other")
    decision = decide(poster, TODAY)
    assert decision.route == "rejected"
    assert safe_draft(poster, decision)["events"] == []


def test_year_without_visible_support_is_reviewed():
    poster = extraction([event()])
    poster.events[0].date_iso = f("2026-10-25", "25 October", 0.95)
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.kind == "year_not_visible" for flag in decision.flags)


def test_normalized_date_must_match_printed_day_and_month():
    poster = extraction([event()])
    poster.events[0].date_iso = f("2026-10-26", "25 October 2026", 0.95)
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.kind == "date_mismatch" for flag in decision.flags)


def test_doors_open_is_not_treated_as_event_start():
    poster = extraction([event()])
    poster.events[0].time_role = f("doors_open", "Doors open 19:00", 0.95)
    poster.events[0].doors_open_time = f("19:00", "Doors open 19:00", 0.95)
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.kind == "start_time_missing" for flag in decision.flags)


def test_logo_cannot_become_an_unprinted_source_url():
    poster = extraction([event()])
    poster.source_url = f("https://example.com/event", "TKT.GE", 0.95)
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.kind == "unverified_url" for flag in decision.flags)
    assert safe_draft(poster, decision)["source_url"]["value"] is None


def test_multi_session_poster_checks_each_session():
    second = event("Second Session")
    second.venue = f()
    poster = extraction([event(), second])
    decision = decide(poster, TODAY)
    assert decision.route == "review"
    assert any(flag.field == "events[1].venue" for flag in decision.flags)
    assert safe_draft(poster, decision)["events"][0]["venue"]["value"] == "City Hall"
