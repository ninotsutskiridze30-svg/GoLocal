import type { EventItem } from "@/types/event";

/**
 * Fictional preview listings, used when the FastAPI service is unavailable.
 * Every item is marked demo: true, links to no real source, and uses a generic photo
 * chosen to match its event type (Unsplash). Coordinates are approximate test points in Tbilisi.
 */
const photo = (id: string) => `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=1000&q=80`;

export const PHOTOS = {
  jazz: photo("1415201364774-f6f0bb35f28f"),
  liveBand: photo("1459749411175-04bf5292ceea"),
  gallery: photo("1606819717115-9159c900370b"),
  museum: photo("1518998053901-5348d3961a04"),
  workshop: photo("1595351298020-038700609878"),
  comedy: photo("1762421028563-d001864e41c7"),
  tech: photo("1496181133206-80ce9b88a853"),
  nightlife: photo("1545128485-c400e7702796"),
  market: photo("1526399743290-f73cb4022f48"),
  film: photo("1517604931442-7e0c8ed2963c"),
  cafe: photo("1564327367919-cb377ea6a88f"),
  festival: photo("1576646619495-4106b262ebbd"),
  food: photo("1567306295427-94503f8300d7"),
  family: photo("1561049527-9743861dce35"),
  talk: photo("1540575467063-178a50c2df87"),
  sports: photo("1489944440615-453fc2b6a9a9"),
};

type Seed = Omit<EventItem, "demo" | "source_name" | "source_url" | "currency"> & { price_min: number | null; price_max: number | null };

const seeds: Seed[] = [
  { id: 1, title: "Afterglow Jazz Session", description: "A late set of modern jazz and warm candlelight in an intimate listening room, with vinyl selections between sets.", short_description: "Late modern jazz in a candlelit room.", category: "music", venue: "Sample Listening Room", address: "Sololaki", city: "Tbilisi", latitude: 41.6938, longitude: 44.8128, start_time: "2026-10-23T20:00:00+04:00", end_time: "2026-10-23T22:00:00+04:00", price_min: 25, price_max: 35, image_url: PHOTOS.jazz, age_restriction: null, score: 0.96, explanation: "Matches your interest in live music and fits a 40 GEL budget." },
  { id: 2, title: "Gallery After Hours", description: "A small contemporary show after closing time, with a curator-led walk and a quiet wine bar.", category: "exhibition", venue: "Sample Art House", address: "Old Town", city: "Tbilisi", latitude: 41.6912, longitude: 44.8013, start_time: "2026-10-24T18:30:00+04:00", end_time: "2026-10-24T20:30:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.gallery, age_restriction: null, score: 0.91, explanation: "Free entry and a relaxed evening, a good fit for an art-focused mood." },
  { id: 3, title: "Clay, Coffee & Company", description: "A beginner-friendly ceramics session with coffee and time to make something by hand.", category: "workshop", venue: "Sample Makers Studio", address: "Marjanishvili", city: "Tbilisi", latitude: 41.7070, longitude: 44.7880, start_time: "2026-10-25T14:00:00+04:00", end_time: "2026-10-25T16:30:00+04:00", price_min: 45, price_max: 45, image_url: PHOTOS.workshop, age_restriction: null, score: 0.88, explanation: "A calm, hands-on afternoon that suits a relaxed plan." },
  { id: 4, title: "Small Stage Comedy Night", description: "Short-form comedy and local performers in an intimate room.", category: "theatre", venue: "Sample Stage", address: "Old Town", city: "Tbilisi", latitude: 41.6915, longitude: 44.8025, start_time: "2026-10-25T20:00:00+04:00", end_time: "2026-10-25T22:00:00+04:00", price_min: 20, price_max: 30, image_url: PHOTOS.comedy, age_restriction: 16, score: 0.82, explanation: "Lively and social, and it is within budget." },
  { id: 5, title: "Future Makers Meetup", description: "An evening to meet people working across design, technology and creative business.", category: "technology", venue: "Sample Foundry", address: "Fabrika", city: "Tbilisi", latitude: 41.6983, longitude: 44.8255, start_time: "2026-10-26T18:00:00+04:00", end_time: "2026-10-26T20:00:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.tech, age_restriction: null, score: 0.9, explanation: "A free meetup for builders, matching your tech interest." },
  { id: 6, title: "Rooftop Rhythm Social", description: "A feel-good dance session with a sunset view, open decks and a friendly crowd.", category: "nightlife", venue: "Sample Skyline Room", address: "Mtatsminda", city: "Tbilisi", latitude: 41.6900, longitude: 44.7800, start_time: "2026-10-27T21:00:00+04:00", end_time: "2026-10-27T23:30:00+04:00", price_min: 30, price_max: 50, image_url: PHOTOS.nightlife, age_restriction: 18, score: 0.87, explanation: "High energy and a late start, ideal for a night out." },
  { id: 7, title: "Sunday Market & Sound", description: "Local makers, seasonal food and small live sets at an open-air neighbourhood market.", category: "market", venue: "Sample Riverside Yard", address: "Riverside", city: "Tbilisi", latitude: 41.7060, longitude: 44.8035, start_time: "2026-10-28T11:00:00+04:00", end_time: "2026-10-28T16:00:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.market, age_restriction: null, score: 0.8, explanation: "Free to browse, with food and music for a slow Sunday." },
  { id: 8, title: "The Midnight Film Club", description: "A classic film, a short introduction and an informal conversation afterwards.", category: "film", venue: "Sample Picture House", address: "Sololaki", city: "Tbilisi", latitude: 41.6945, longitude: 44.8140, start_time: "2026-10-29T20:00:00+04:00", end_time: "2026-10-29T22:00:00+04:00", price_min: 15, price_max: 15, image_url: PHOTOS.film, age_restriction: null, score: 0.84, explanation: "Quiet and cinematic, and cheap." },
  { id: 9, title: "Basement Live: Indie Night", description: "Three local bands in a basement club with craft beer and a small merch table.", category: "music", venue: "Sample Basement", address: "Vera", city: "Tbilisi", latitude: 41.7180, longitude: 44.7930, start_time: "2026-10-30T19:30:00+04:00", end_time: "2026-10-30T23:00:00+04:00", price_min: 12, price_max: 12, image_url: PHOTOS.liveBand, age_restriction: 18, score: 0.9, explanation: "Live music at a low price, close to the centre." },
  { id: 10, title: "Street Food & Festival Lights", description: "A weekend food festival with stalls from twelve kitchens and a light installation after dark.", category: "festival", venue: "Sample Riverside Square", address: "Riverside", city: "Tbilisi", latitude: 41.7050, longitude: 44.8050, start_time: "2026-10-31T16:00:00+04:00", end_time: "2026-10-31T23:00:00+04:00", price_min: 0, price_max: 10, image_url: PHOTOS.festival, age_restriction: null, score: 0.86, explanation: "A festival with food and lights, a good social option." },
  { id: 11, title: "Family Picnic Day", description: "Games, a storytelling tent and a long picnic lawn for families and children.", category: "family", venue: "Sample Botanical Park", address: "Vake", city: "Tbilisi", latitude: 41.7110, longitude: 44.7800, start_time: "2026-11-01T11:00:00+04:00", end_time: "2026-11-01T17:00:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.family, age_restriction: null, score: 0.7, explanation: "Free and suitable for all ages." },
  { id: 12, title: "Startup Talks: Building Local", description: "Four short talks from founders on building products for a small city, followed by questions.", category: "talk", venue: "Sample Coworking Hall", address: "Fabrika", city: "Tbilisi", latitude: 41.6985, longitude: 44.8250, start_time: "2026-11-02T18:00:00+04:00", end_time: "2026-11-02T20:30:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.talk, age_restriction: null, score: 0.85, explanation: "Free talks on technology and business." },
  { id: 13, title: "Open Mic at the Corner Cafe", description: "Poets, comedians and singers sign up on the night. Coffee and pastries all evening.", category: "social", venue: "Sample Corner Cafe", address: "Old Town", city: "Tbilisi", latitude: 41.6920, longitude: 44.8000, start_time: "2026-11-03T19:00:00+04:00", end_time: "2026-11-03T21:30:00+04:00", price_min: 0, price_max: 0, image_url: PHOTOS.cafe, age_restriction: null, score: 0.78, explanation: "A cosy, free evening that fits a relaxed mood." },
  { id: 14, title: "Five-a-side Sunday", description: "Friendly pick-up football for all levels, with boots and a ball provided.", category: "sports", venue: "Sample Stadium Annex", address: "Dighomi", city: "Tbilisi", latitude: 41.7650, longitude: 44.9030, start_time: "2026-11-04T10:00:00+04:00", end_time: "2026-11-04T12:00:00+04:00", price_min: 8, price_max: 8, image_url: PHOTOS.sports, age_restriction: null, score: 0.65, explanation: "An active morning at a low price." },
];

export const demoEvents: EventItem[] = seeds.map((seed) => ({
  ...seed,
  end_time: seed.end_time,
  currency: "GEL",
  source_name: null,
  source_url: null,
  demo: true,
}));
