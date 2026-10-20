import type { EventItem } from "@/types/event";
import { PHOTOS } from "@/lib/demo-events";

export const BUDGET_ANY = 200;

export type MoodId = "relaxed" | "tech" | "nightlife" | "culture";
export type SortKey = "date" | "price" | "match";

export interface Mood {
  id: MoodId;
  title: string;
  subtitle: string;
  image: string;
  categories: string[];
}

export const MOODS: Mood[] = [
  { id: "relaxed", title: "Relaxed", subtitle: "Slow pace, warm light, no rush", image: PHOTOS.cafe, categories: ["market", "film", "workshop", "exhibition"] },
  { id: "tech", title: "Tech & Innovation", subtitle: "Makers, builders and big ideas", image: PHOTOS.tech, categories: ["technology", "talk", "workshop"] },
  { id: "nightlife", title: "Nightlife", subtitle: "Late sets, dancefloors, rooftops", image: PHOTOS.nightlife, categories: ["nightlife", "music"] },
  { id: "culture", title: "Art & Culture", subtitle: "Galleries, stages and screens", image: PHOTOS.museum, categories: ["exhibition", "theatre", "film"] },
];

export const CATEGORIES = ["music", "nightlife", "exhibition", "theatre", "workshop", "technology", "sports", "festival", "market", "family", "talk", "film", "food", "social", "other"];

export interface FilterState {
  mood: MoodId | null;
  budget: number;
  category: string;
  from: string;
  to: string;
  freeOnly: boolean;
  savedOnly: boolean;
  sort: SortKey;
}

export const DEFAULT_FILTERS: FilterState = {
  mood: null,
  budget: BUDGET_ANY,
  category: "all",
  from: "",
  to: "",
  freeOnly: false,
  savedOnly: false,
  sort: "date",
};

/**
 * Applies every filter to a list of events. The mood only narrows the list when no AI search is
 * active, so an explicit search is never hidden by a mood choice.
 */
export function applyFilters(events: EventItem[], filters: FilterState, searchActive: boolean): EventItem[] {
  const mood = filters.mood && !searchActive ? MOODS.find((item) => item.id === filters.mood) : undefined;

  const matched = events.filter((event) => {
    if (mood && !mood.categories.includes(event.category)) return false;
    if (filters.category !== "all" && event.category !== filters.category) return false;
    if (filters.budget < BUDGET_ANY && (event.price_min == null || event.price_min > filters.budget)) return false;
    if (filters.freeOnly && event.price_min !== 0) return false;
    const day = event.start_time.slice(0, 10);
    if (filters.from && day < filters.from) return false;
    if (filters.to && day > filters.to) return false;
    return true;
  });

  return [...matched].sort((a, b) => {
    if (filters.sort === "price") return (a.price_min ?? Infinity) - (b.price_min ?? Infinity);
    if (filters.sort === "match") return (b.score ?? -1) - (a.score ?? -1);
    return Date.parse(a.start_time) - Date.parse(b.start_time);
  });
}
