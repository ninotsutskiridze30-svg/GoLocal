export interface EventItem {
  id: number;
  title: string;
  description: string;
  short_description?: string | null;
  category: string;
  category_id?: number | null;
  venue: string;
  address?: string | null;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  start_time: string;
  end_time: string | null;
  price_min: number | null;
  price_max: number | null;
  currency: string | null;
  source_name: string | null;
  source_url: string | null;
  image_url: string | null;
  age_restriction?: number | null;
  score?: number;
  explanation?: string;
  demo?: boolean;
}

export interface EventSearchHit {
  event?: unknown;
  score?: number;
  explanation?: string;
}

export interface EventSearchResponse {
  results?: EventSearchHit[];
  mode?: string;
}

export type EventSearchStatus = "loading" | "live" | "demo" | "error";
