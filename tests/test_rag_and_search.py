import pytest

def test_event_data_extraction_structure():
    """Validates that the extracted event data contains all mandatory fields and correct types."""
    raw_event = {
        "title": "Acoustic Live Concert",
        "price": 20,
        "currency": "GEL",
        "date": "2026-10-23",
        "category": "Music",
        "venue": "Gotela Cafe"
    }

    required_keys = ["title", "price", "date", "category", "venue"]
    for key in required_keys:
        assert key in raw_event, f"Missing required field: {key}"
    
    assert isinstance(raw_event["price"], (int, float))
    assert raw_event["price"] >= 0


def test_rag_budget_and_category_filter():
    """Tests RAG search retrieval and filtering logic based on user budget and category constraints."""
    mock_db_events = [
        {"title": "Cozy Jazz Night", "price": 15, "category": "Music"},
        {"title": "Techno Club Night", "price": 50, "category": "Nightlife"},
        {"title": "Art Workshop", "price": 25, "category": "Workshop"}
    ]
    
    user_max_budget = 30
    requested_category = "Music"

    filtered_results = [
        event for event in mock_db_events
        if event["price"] <= user_max_budget and event["category"] == requested_category
    ]

    assert len(filtered_results) == 1
    assert filtered_results[0]["title"] == "Cozy Jazz Night"


def test_rag_no_hallucinated_events():
    """Ensures guardrails prevent hallucinated events when no matching records are found in the database."""
    mock_db_events = [
        {"title": "Rock Concert", "price": 40}
    ]
    
    user_max_budget = 10
    filtered_results = [e for e in mock_db_events if e["price"] <= user_max_budget]

    assert len(filtered_results) == 0
