"""Gemini JSON completion, text embeddings, and minimal usage accounting."""

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
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768
EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{EMBEDDING_MODEL}:embedContent"
)
RAG_USAGE_LOG = Path(__file__).resolve().parents[2] / "logs" / "rag_usage.jsonl"


class PosterModelError(RuntimeError):
    """Safe, credential-free error for a failed poster model call."""

    def __init__(self, message: str, *, failure_kind: str = "unknown",
                 http_status: int | None = None) -> None:
        super().__init__(message)
        self.failure_kind = failure_kind
        self.http_status = http_status


class EmbeddingModelError(RuntimeError):
    """Safe, credential-free error for a failed embedding call."""


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


def _failure_details(error: Exception) -> tuple[str, int | None]:
    """Classify a provider failure without logging response bodies or credentials."""
    if isinstance(error, httpx.HTTPStatusError):
        return "http_status", error.response.status_code
    if isinstance(error, httpx.TimeoutException):
        return "timeout", None
    if isinstance(error, httpx.TransportError):
        return "transport", None
    if isinstance(error, (KeyError, IndexError, AttributeError, TypeError)):
        return "response_format", None
    if isinstance(error, ValueError):
        return "invalid_json", None
    return "io", None


def complete_json(
    prompt: str,
    image: bytes | None,
    schema: dict[str, Any],
    *,
    api_key: str | None = None,
    client: httpx.Client | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Send text, optionally one image, and schema without logging sensitive content."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise PosterModelError("Gemini is not configured", failure_kind="configuration")
    parts = [{"text": prompt}]
    if image is not None:
        parts.append({"inlineData": {
            "mimeType": "image/jpeg",
            "data": base64.b64encode(image).decode("ascii"),
        }})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
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
        failure_kind, http_status = _failure_details(exc)
        if not logged:
            try:
                failure = _usage_record({}, int((time.perf_counter() - started) * 1000))
                failure["status"] = "failed"
                failure["failure_kind"] = failure_kind
                if http_status is not None:
                    failure["http_status"] = http_status
                _append_usage(destination, failure)
            except OSError:
                pass
        raise PosterModelError("Gemini JSON completion failed",
                               failure_kind=failure_kind, http_status=http_status) from exc


def embed(text: str, *, api_key: str | None = None,
          client: httpx.Client | None = None,
          log_path: Path | None = None) -> list[float]:
    """Embed one text through Gemini; the model and dimensions are fixed."""
    if not text.strip():
        raise ValueError("Cannot embed blank text")
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise EmbeddingModelError("Gemini is not configured")
    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text}]},
        "output_dimensionality": EMBEDDING_DIMENSIONS,
    }
    started = time.perf_counter()
    destination = log_path or RAG_USAGE_LOG
    try:
        if client is None:
            with httpx.Client(timeout=45) as owned:
                response = owned.post(EMBEDDING_URL, headers={"x-goog-api-key": key}, json=payload)
        else:
            response = client.post(EMBEDDING_URL, headers={"x-goog-api-key": key}, json=payload)
        response.raise_for_status()
        body = response.json()
        values = body["embedding"]["values"]
        from .rag_index import _vector
        vector = _vector(values, EMBEDDING_DIMENSIONS)
        _append_usage(destination, {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "tokens_in": (body.get("usageMetadata") or {}).get("promptTokenCount"),
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "status": "ok",
        })
        return list(vector)
    except (httpx.HTTPError, AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        try:
            _append_usage(destination, {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model": EMBEDDING_MODEL,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "status": "failed",
            })
        except OSError:
            pass
        raise EmbeddingModelError("Gemini embedding failed") from exc
