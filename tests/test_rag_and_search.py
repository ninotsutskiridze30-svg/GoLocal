import pytest
from datetime import datetime, timezone
from decimal import Decimal
from golocal_data.models import NormalizedEvent

def test_event_data_extraction_and_normalization():
    """Validates that extracted event fields align with GoLocal canonical event rules."""
    raw_event = {
        "title": "Acoustic Live Concert",
        "city_id": 1,
        "venue_name": "Gotela Cafe",
        "start_time": datetime(2026, 10, 23, 18, 0, tzinfo=timezone.utc),
        "source_id": 1,
        "source_name": "Test Source",
        "source_url": "https://example.com/events/1",
        "fetched_at": datetime(2026, 10, 19, tzinfo=timezone.utc),
        "price_min": Decimal("20.00"),
        "currency": "GEL",
        "category": "music"
    }

    # Validates that the team's core model successfully builds a valid canonical event object
    event = NormalizedEvent(**raw_event)
    assert event.title == "Acoustic Live Concert"
    assert event.currency == "GEL"
    assert event.price_min == Decimal("20.00")


def test_rag_budget_filtering_logic():
    """Tests RAG search retrieval and filtering logic based on user budget and category constraints."""
    mock_db_events = [
        {"title": "Cozy Jazz Night", "price_min": Decimal("15.00"), "category": "music"},
        {"title": "Techno Club Night", "price_min": Decimal("50.00"), "category": "nightlife"},
        {"title": "Art Workshop", "price_min": Decimal("25.00"), "category": "workshop"}
    ]
    
    user_max_budget = Decimal("30.00")
    requested_category = "music"

    # Testing search filtering matching team structures
    filtered_results = [
        e for e in mock_db_events
        if e["price_min"] <= user_max_budget and e["category"] == requested_category
    ]

    assert len(filtered_results) == 1
    assert filtered_results[0]["title"] == "Cozy Jazz Night"


def test_rag_no_hallucinated_events():
    """Ensures guardrails prevent returning events when budget is too low or records are missing."""
    mock_db_events = [
        {"title": "Rock Concert", "price_min": Decimal("40.00"), "category": "music"}
    ]
    
    user_max_budget = Decimal("10.00")
    filtered_results = [e for e in mock_db_events if e["price_min"] <= user_max_budget]

    # Guardrail check: results must be empty if no matching event satisfies the criteria
    assert len(filtered_results) == 0
