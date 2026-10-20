"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { normalizeApiEvent } from "@/lib/event-utils";
import { fetchEvents, searchEvents } from "@/lib/api";
import type { EventItem, EventSearchStatus } from "@/types/event";

function findPreviewMatches(events: EventItem[], query: string): EventItem[] {
  const normalized = query.toLowerCase();
  const stopWords = new Set(["a", "an", "the", "and", "or", "i", "im", "my", "me", "for", "with", "want", "looking", "find", "something", "under", "below", "less", "than", "up", "to", "night", "out", "today", "tomorrow", "tonight", "friday", "saturday", "sunday", "weekend", "gel", "lari", "free"]);
  const words = (normalized.match(/[a-z]+/g) ?? []).filter((word) => word.length > 2 && !stopWords.has(word));
  const expanded = new Set(words);
  const addIntent = (pattern: RegExp, terms: string[]) => { if (pattern.test(normalized)) terms.forEach((term) => expanded.add(term)); };
  addIntent(/party|nightlife|club|dance|dj|bar|after dark/, ["nightlife", "music", "dance", "dj"]);
  addIntent(/\bjazz\b/, ["jazz"]);
  addIntent(/concert|\bgig\b|live music/, ["music", "concert", "gig", "live"]);
  addIntent(/\bmusic\b/, ["music"]);
  addIntent(/art|gallery|museum|exhibition|culture/, ["exhibition", "art", "gallery", "culture"]);
  addIntent(/workshop|class|make something|ceramics|craft/, ["workshop", "ceramics", "studio", "craft"]);
  addIntent(/market|food|local makers|shopping/, ["market", "food", "makers"]);
  addIntent(/tech|technology|startup|innovation|design/, ["technology", "tech", "design"]);
  addIntent(/social|friends|meet people/, ["music", "market", "nightlife", "meet people"]);

  const budgetMatch = normalized.match(/(?:under|below|less than|up to|max(?:imum)?(?: budget)?(?: of)?)\s*(?:[$€£]\s*)?(\d{1,4})/i)
    ?? normalized.match(/(\d{1,4})\s*(?:gel|lari)/i);
  const maxPrice = budgetMatch ? Number(budgetMatch[1]) : null;
  const freeOnly = /\bfree\b|no cost|without paying/.test(normalized);
  const hasTopic = expanded.size > 0;

  return events.filter((event) => {
    const price = event.price_min;
    if (maxPrice !== null && (price === null || price > maxPrice)) return false;
    if (freeOnly && price !== 0) return false;
    if (!hasTopic) return true;
    const haystack = `${event.title} ${event.description} ${event.category} ${event.venue}`.toLowerCase();
    return [...expanded].some((word) => new RegExp(`\\b${word}\\b`, "i").test(haystack));
  });
}

export function useEventEngine(initialEvents: EventItem[]) {
  const [events, setEvents] = useState(initialEvents);
  const [status, setStatus] = useState<EventSearchStatus>("demo");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const requestRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    requestRef.current = controller;
    fetchEvents(controller.signal)
      .then((items) => {
        setEvents(items.map((item) => normalizeApiEvent(item)));
        setStatus("live");
        setMessage("");
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || (error instanceof DOMException && error.name === "AbortError")) return;
        setStatus("demo");
        setMessage("Preview mode · connect the FastAPI service to load verified local events.");
      });
    return () => {
      controller.abort();
      if (requestRef.current === controller) requestRef.current = null;
    };
  }, []);

  const search = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setMessage("");
    try {
      const payload = await searchEvents(trimmed, controller.signal);
      if (controller.signal.aborted) return;
      const hits = payload.results ?? [];
      setEvents(hits.map((hit) => normalizeApiEvent(hit.event, {
        score: typeof hit.score === "number" ? hit.score : undefined,
        explanation: typeof hit.explanation === "string" ? hit.explanation : undefined,
        demo: payload.mode === "demo",
      })));
      setStatus(payload.mode === "demo" ? "demo" : "live");
    } catch {
      if (controller.signal.aborted) return;
      const previews = findPreviewMatches(initialEvents, trimmed);
      setEvents(previews);
      setStatus("demo");
      setMessage("The event service is unavailable. Showing matching sample ideas only.");
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }, [initialEvents]);

  const restoreEvents = useCallback(async () => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setMessage("");
    try {
      const items = await fetchEvents(controller.signal);
      if (controller.signal.aborted) return;
      setEvents(items.map((item) => normalizeApiEvent(item)));
      setStatus("live");
    } catch {
      if (controller.signal.aborted) return;
      setEvents(initialEvents);
      setStatus("demo");
      setMessage("Preview mode · connect the FastAPI service to load verified local events.");
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }, [initialEvents]);

  return { events, setEvents, status, loading, message, search, restoreEvents };
}
