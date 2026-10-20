"use client";

import { useSyncExternalStore } from "react";
import type { EventItem } from "@/types/event";

const KEY = "golocal-saved-events";
const EVENT = "golocal-saved-change";

/** Saved listings stored as full objects, so the saved page works after a new search. */
let cache: EventItem[] | null = null;

function read(): EventItem[] {
  if (cache) return cache;
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(KEY) ?? "[]");
    cache = Array.isArray(parsed) ? (parsed as EventItem[]).filter((item) => Number.isInteger(item?.id)) : [];
  } catch {
    cache = [];
  }
  return cache;
}

function write(next: EventItem[]) {
  cache = next;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Storage can be blocked; the list then lasts for this page visit only.
  }
  window.dispatchEvent(new Event(EVENT));
}

const EMPTY: EventItem[] = [];

function subscribe(onChange: () => void) {
  window.addEventListener(EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** Saved events shared across the whole app, kept in sync between tabs. */
export function useSavedEvents() {
  const saved = useSyncExternalStore(subscribe, read, () => EMPTY);
  const ids = new Set(saved.map((item) => item.id));
  const toggle = (event: EventItem) => {
    const current = read();
    write(current.some((item) => item.id === event.id) ? current.filter((item) => item.id !== event.id) : [...current, event]);
  };
  return { saved, ids, toggle };
}
