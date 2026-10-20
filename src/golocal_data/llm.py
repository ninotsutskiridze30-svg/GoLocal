"""One Gemini vision request, structured JSON, and minimal usage accounting."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any

import httpx

from .discovery import MODEL, MODEL_URL


USAGE_LOG = Path(__file__).resolve().parents[2] / "logs" / "poster_usage.jsonl"
PRICE_INPUT_PER_MILLION_USD = 0.25
PRICE_OUTPUT_PER_MILLION_USD = 1.50


class PosterModelError(RuntimeError):
    """Safe, credential-free error for a failed poster model call."""


def _usage_record(body: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    usage = body.get("usageMetadata") or {}
    tokens_in = usage.get("promptTokenCount")
    total = usage.get("totalTokenCount")
    candidates = usage.get("candidatesTokenCount")
    thoughts = usage.get("thoughtsTokenCount")
    tokens_out = None
    if isinstance(total, int) and isinstance(tokens_in, int):
        tokens_out = max(0, total - tokens_in)
    elif isinstance(candidates, int):
        tokens_out = candidates + (thoughts if isinstance(thoughts, int) else 0)
    cost = None
    if isinstance(tokens_in, int) and isinstance(tokens_out, int):
        cost = round(
            (tokens_in * PRICE_INPUT_PER_MILLION_USD
             + tokens_out * PRICE_OUTPUT_PER_MILLION_USD) / 1_000_000,
            7,
        )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": body.get("modelVersion", MODEL),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out if isinstance(tokens_out, int) else None,
        "estimated_cost_usd": cost,
        "latency_ms": elapsed_ms,
    }


def _append_usage(destination: Path, record: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def complete_json(
    prompt: str,
    image: bytes,
    schema: dict[str, Any],
    *,
    api_key: str | None = None,
    client: httpx.Client | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Send one image and schema; never log the key, image, prompt, or response."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise PosterModelError("Gemini is not configured")
    payload = {
        "contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inlineData": {
                "mimeType": "image/jpeg",
                "data": base64.b64encode(image).decode("ascii"),
            }},
        ]}],
        "generationConfig": {
            "responseFormat": {"text": {
                "mimeType": "APPLICATION_JSON",
                "schema": schema,
            }},
            "temperature": 0,
        },
    }
    started = time.perf_counter()
    destination = log_path or USAGE_LOG
    logged = False
    try:
        if client is None:
            with httpx.Client(timeout=45) as owned:
                response = owned.post(MODEL_URL, headers={"x-goog-api-key": key}, json=payload)
        else:
            response = client.post(MODEL_URL, headers={"x-goog-api-key": key}, json=payload)
        response.raise_for_status()
        body = response.json()
        parts = body["candidates"][0]["content"]["parts"]
        raw_text = "".join(part.get("text", "") for part in parts)
        _append_usage(destination, _usage_record(
            body, int((time.perf_counter() - started) * 1000)
        ))
        logged = True
        result = json.loads(raw_text)
        if not isinstance(result, dict):
            raise ValueError("Expected JSON object")
        return result
    except (httpx.HTTPError, AttributeError, KeyError, IndexError, TypeError, ValueError, OSError) as exc:
        if not logged:
            try:
                failure = _usage_record({}, int((time.perf_counter() - started) * 1000))
                failure["status"] = "failed"
                _append_usage(destination, failure)
            except OSError:
                pass
        raise PosterModelError("Gemini poster extraction failed") from exc
