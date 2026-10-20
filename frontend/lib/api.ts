import type { EventSearchHit, EventSearchResponse } from "@/types/event";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`Event service returned ${response.status}`);
  return response.json() as Promise<T>;
}

export async function fetchEvents(signal?: AbortSignal): Promise<unknown[]> {
  const response = await fetch(`${API_BASE}/events?page=1&page_size=30`, { signal });
  const payload = await readJson<{ items?: unknown[] }>(response);
  return Array.isArray(payload.items) ? payload.items : [];
}

export async function searchEvents(query: string, signal?: AbortSignal): Promise<EventSearchResponse> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query } satisfies EventSearchParams),
    signal,
  });
  const payload = await readJson<EventSearchResponse>(response);
  return { ...payload, results: Array.isArray(payload.results) ? payload.results as EventSearchHit[] : [] };
}

export interface EventSearchParams { query: string }

export async function fetchEventById(id: number, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(`${API_BASE}/events/${id}`, { signal });
  return readJson<unknown>(response);
}
