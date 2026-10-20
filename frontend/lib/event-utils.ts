import type { EventItem } from "@/types/event";

export function safeUrl(value: unknown, fallback = "#"): string {
  try {
    const parsed = new URL(String(value));
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : fallback;
  } catch {
    return fallback;
  }
}

function finiteCoordinate(value: unknown, min: number, max: number): number | null {
  const numberValue = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numberValue) && numberValue >= min && numberValue <= max ? numberValue : null;
}

export function normalizeApiEvent(
  value: unknown,
  extra: { score?: number; explanation?: string; demo?: boolean } = {},
): EventItem {
  const raw = value && typeof value === "object" ? value as Record<string, unknown> : {};
  const venue = raw.venue && typeof raw.venue === "object" ? raw.venue as Record<string, unknown> : {};
  const city = venue.city && typeof venue.city === "object" ? venue.city as Record<string, unknown> : {};
  const category = raw.category && typeof raw.category === "object" ? raw.category as Record<string, unknown> : {};
  const latitude = finiteCoordinate(venue.latitude ?? raw.latitude, -90, 90);
  const longitude = finiteCoordinate(venue.longitude ?? raw.longitude, -180, 180);
  const hasCoordinatePair = latitude !== null && longitude !== null;

  return {
    id: Number(raw.id),
    title: String(raw.title || "Untitled event"),
    description: String(raw.description || ""),
    short_description: typeof raw.short_description === "string" ? raw.short_description : null,
    category: String(category.name ?? raw.category ?? "other").toLowerCase(),
    category_id: Number.isFinite(Number(category.id)) ? Number(category.id) : null,
    venue: String(venue.name || (typeof raw.venue === "string" ? raw.venue : "Venue not listed")),
    address: typeof venue.address === "string" ? venue.address : null,
    city: typeof city.name === "string" ? city.name : null,
    latitude: hasCoordinatePair ? latitude : null,
    longitude: hasCoordinatePair ? longitude : null,
    start_time: String(raw.start_time || new Date().toISOString()),
    end_time: typeof raw.end_time === "string" ? raw.end_time : null,
    price_min: raw.price_min == null ? null : Number(raw.price_min),
    price_max: raw.price_max == null ? null : Number(raw.price_max),
    currency: typeof raw.currency === "string" ? raw.currency : null,
    source_name: typeof raw.source_name === "string" ? raw.source_name : null,
    source_url: typeof raw.source_url === "string" ? safeUrl(raw.source_url, "") || null : null,
    image_url: typeof raw.image_url === "string" ? safeUrl(raw.image_url, "") || null : null,
    age_restriction: raw.age_restriction == null ? null : Number(raw.age_restriction),
    ...extra,
  };
}

export function hasCoordinates(event: EventItem): event is EventItem & { latitude: number; longitude: number } {
  return event.latitude !== null && event.longitude !== null &&
    Number.isFinite(event.latitude) && Number.isFinite(event.longitude);
}

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat("en", { weekday: "short", month: "short", day: "numeric" }).format(new Date(value));
}

export function formatEventTime(value: string): string {
  return new Intl.DateTimeFormat("en", { hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

export function eventPrice(event: EventItem): string {
  if (event.price_min == null) return "Price not listed";
  if (event.price_min === 0) return "Free";
  const upper = event.price_max != null && event.price_max !== event.price_min ? `–${event.price_max}` : "";
  return `${event.price_min}${upper} ${event.currency || ""}`.trim();
}
