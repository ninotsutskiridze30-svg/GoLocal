"""Schema, provider boundary, and safe parsing without paid model calls."""

from io import BytesIO
import json

import httpx
import pytest
from PIL import Image

from golocal_data.llm import PosterModelError, complete_json
from golocal_data.poster_extraction import (
    ListField, PosterEvent, PosterExtraction, TextField, extract,
)


def f(value=None, evidence=None, confidence=0.0):
    return TextField(value=value, evidence=evidence, confidence=confidence)


def items(value=None, evidence=None, confidence=0.0):
    return ListField(value=value, evidence=evidence, confidence=confidence)


def event(title="Music Night"):
    return PosterEvent(
        title=f(title, title, 0.95),
        date_text=f("25 October 2026", "25 October 2026", 0.95),
        date_iso=f("2026-10-25", "25 October 2026", 0.95),
        displayed_time=f("19:00", "19:00", 0.95),
        time_role=f("event_start", "Starts 19:00", 0.95),
        doors_open_time=f(), venue=f("City Hall", "City Hall", 0.95),
        city=f(), organizer=f(), performers=items(), special_guests=items(),
        lineup=items(), program_items=items(), films_named_on_poster=items(),
        ticket_price=f(),
    )


def extraction(events=None, document_type="event_poster"):
    return PosterExtraction(
        document_type=f(document_type, "Music Night" if events is not None else "Book cover", 0.95),
        festival_title=f(), festival_date_range=f(), ticket_platform=f(),
        contact_phone=f(), source_url=f(), events=events or [],
    )


def image_bytes():
    output = BytesIO()
    Image.new("RGB", (1600, 400), "white").save(output, format="JPEG")
    return output.getvalue()


def test_extract_sends_downscaled_image_and_json_schema():
    seen = []

    def fake(prompt, image, schema):
        seen.append((prompt, image, schema))
        return extraction([event(), event("Second Session")]).model_dump()

    result = extract(image_bytes(), complete=fake)
    assert len(seen) == 1
    with Image.open(BytesIO(seen[0][1])) as sent:
        assert sent.size == (1024, 256)
    assert seen[0][2]["properties"]["events"]["type"] == "array"
    assert [item.title.value for item in result.events] == ["Music Night", "Second Session"]


def test_extract_rejects_invalid_model_shape():
    with pytest.raises(PosterModelError):
        extract(image_bytes(), complete=lambda *_: {"events": []})


def test_field_rejects_malformed_confidence_and_null_evidence():
    with pytest.raises(ValueError):
        TextField(value="date", evidence="date", confidence=1.2)
    with pytest.raises(ValueError):
        TextField(value=None, evidence="date", confidence=0.0)


def test_provider_sends_one_vision_request_and_logs_usage(tmp_path):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={
            "modelVersion": "gemini-3.1-flash-lite",
            "usageMetadata": {"promptTokenCount": 100, "totalTokenCount": 120},
            "candidates": [{"content": {"parts": [{"text": json.dumps({"ok": True})}]}}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = complete_json("read", b"jpeg", {"type": "object"},
                               api_key="secret-for-test", client=client,
                               log_path=tmp_path / "usage.jsonl")
    assert result == {"ok": True}
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/jpeg"
    assert body["generationConfig"]["responseFormat"]["text"]["schema"] == {"type": "object"}
    usage = json.loads((tmp_path / "usage.jsonl").read_text())
    assert usage["tokens_in"] == 100
    assert usage["tokens_out"] == 20
    assert usage["estimated_cost_usd"] is not None
    assert "secret-for-test" not in (tmp_path / "usage.jsonl").read_text()


def test_provider_failure_does_not_expose_response_or_key(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(503, text="internal detail secret-for-test")
    )) as client:
        with pytest.raises(PosterModelError) as info:
            complete_json("read", b"jpeg", {"type": "object"},
                          api_key="secret-for-test", client=client,
                          log_path=tmp_path / "usage.jsonl")
    assert "secret-for-test" not in str(info.value)
    assert "internal detail" not in str(info.value)
    failure_log = (tmp_path / "usage.jsonl").read_text()
    assert json.loads(failure_log)["status"] == "failed"
    assert "secret-for-test" not in failure_log
