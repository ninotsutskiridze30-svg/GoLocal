"use client";

import Link from "next/link";
import { useState } from "react";
import { eventPrice, formatEventDate, formatEventTime } from "@/lib/event-utils";
import type { EventItem } from "@/types/event";

const WIDTH = 900;
const HEIGHT = 560;
const BOUNDS = { minLat: 41.66, maxLat: 41.79, minLon: 44.77, maxLon: 44.93 };

/** Maps a latitude and longitude to the schematic canvas. */
function project(latitude: number, longitude: number): [number, number] {
  const x = ((longitude - BOUNDS.minLon) / (BOUNDS.maxLon - BOUNDS.minLon)) * WIDTH;
  const y = ((BOUNDS.maxLat - latitude) / (BOUNDS.maxLat - BOUNDS.minLat)) * HEIGHT;
  return [Math.min(WIDTH - 30, Math.max(30, x)), Math.min(HEIGHT - 30, Math.max(30, y))];
}

const districts = [
  { name: "Old Town", lat: 41.6915, lon: 44.8000 },
  { name: "Sololaki", lat: 41.6950, lon: 44.8140 },
  { name: "Fabrika", lat: 41.6990, lon: 44.8265 },
  { name: "Riverside", lat: 41.7070, lon: 44.8010 },
  { name: "Marjanishvili", lat: 41.7080, lon: 44.7870 },
  { name: "Vake", lat: 41.7120, lon: 44.7790 },
  { name: "Mtatsminda", lat: 41.6890, lon: 44.7790 },
  { name: "Vera", lat: 41.7190, lon: 44.7920 },
  { name: "Dighomi", lat: 41.7660, lon: 44.9010 },
];

interface MapViewProps {
  events: EventItem[];
  savedIds: ReadonlySet<number>;
  onToggleSave: (event: EventItem) => void;
}

/** Schematic map of event venues. Pins use real coordinates; the background is not to scale. */
export function MapView({ events, savedIds, onToggleSave }: MapViewProps) {
  const located = events.filter((event) => event.latitude != null && event.longitude != null);
  const [selectedId, setSelectedId] = useState<number | null>(located[0]?.id ?? null);
  const selected = located.find((event) => event.id === selectedId) ?? located[0] ?? null;
  const river = "M 40 330 C 180 300, 220 380, 330 350 S 520 270, 620 300 S 800 360, 880 320";

  return <div id="map" className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
    <div className="glass relative overflow-hidden rounded-3xl">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="aspect-[9/5.6] w-full" role="img" aria-label="Schematic map of event venues in Tbilisi">
        <defs>
          <radialGradient id="map-glow" cx="50%" cy="50%" r="60%">
            <stop offset="0" stopColor="#9b7bff" stopOpacity="0.25" />
            <stop offset="1" stopColor="#0a0812" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="river" x1="0" x2="1">
            <stop offset="0" stopColor="#3fd6c6" stopOpacity="0.1" />
            <stop offset="0.5" stopColor="#3fd6c6" stopOpacity="0.6" />
            <stop offset="1" stopColor="#3fd6c6" stopOpacity="0.1" />
          </linearGradient>
        </defs>
        <rect width={WIDTH} height={HEIGHT} fill="url(#map-glow)" />
        {Array.from({ length: 13 }).map((_, i) => <line key={`v${i}`} x1={i * 75} y1="0" x2={i * 75} y2={HEIGHT} stroke="rgba(255,236,210,0.05)" />)}
        {Array.from({ length: 8 }).map((_, i) => <line key={`h${i}`} x1="0" y1={i * 80} x2={WIDTH} y2={i * 80} stroke="rgba(255,236,210,0.05)" />)}
        <path d={river} fill="none" stroke="url(#river)" strokeWidth="18" strokeLinecap="round" />
        <path d={river} fill="none" stroke="#3fd6c6" strokeOpacity="0.5" strokeWidth="1.5" strokeDasharray="4 8" />
        {districts.map((district) => {
          const [x, y] = project(district.lat, district.lon);
          return <text key={district.name} x={x} y={y} fill="rgba(246,238,226,0.3)" fontSize="13" textAnchor="middle" className="font-mono tracking-widest uppercase">{district.name}</text>;
        })}
        {located.map((event) => {
          const [x, y] = project(event.latitude as number, event.longitude as number);
          const active = event.id === selected?.id;
          return <g key={event.id} transform={`translate(${x} ${y})`} className="cursor-pointer" onClick={() => setSelectedId(event.id)} role="button" tabIndex={0} aria-label={`Show ${event.title} on the map`}
            onKeyDown={(key) => { if (key.key === "Enter") setSelectedId(event.id); }}>
            {active && <circle r="26" fill="#ff5d8f" opacity="0.25"><animate attributeName="r" values="14;30;14" dur="2.2s" repeatCount="indefinite" /><animate attributeName="opacity" values="0.5;0;0.5" dur="2.2s" repeatCount="indefinite" /></circle>}
            <circle r={active ? 13 : 9} fill={active ? "#ff5d8f" : "#f2c46d"} stroke="#0a0812" strokeWidth="3" className="transition-all duration-300" />
          </g>;
        })}
      </svg>
      <p className="absolute bottom-3 left-4 font-mono text-[11px] tracking-widest text-muted uppercase">Schematic · not to scale</p>
    </div>

    <div className="flex flex-col gap-3">
      {located.length === 0 && <p className="glass rounded-3xl p-6 text-muted">No events with coordinates match these filters.</p>}
      {located.map((event) => <button key={event.id} type="button" onClick={() => setSelectedId(event.id)} aria-pressed={event.id === selected?.id}
        className={`glass flex items-center justify-between gap-3 rounded-2xl p-4 text-left transition-all hover:-translate-y-0.5 ${event.id === selected?.id ? "border-rose/60 bg-rose/10" : ""}`}>
        <span>
          <span className="block font-semibold">{event.title}</span>
          <span className="block font-mono text-xs text-muted">{formatEventDate(event.start_time)} · {formatEventTime(event.start_time)} · {event.venue}</span>
        </span>
        <span className="font-mono text-xs text-gold">{eventPrice(event)}</span>
      </button>)}
      {selected && <div className="glass animate-rise rounded-3xl p-5">
        <p className="font-mono text-[11px] tracking-widest text-gold uppercase">Selected</p>
        <p className="mt-2 font-display text-2xl font-semibold">{selected.title}</p>
        <p className="mt-1 text-sm text-muted">{selected.address}, {selected.city}</p>
        <div className="mt-5 flex flex-wrap gap-2">
          <Link href={`/events/${selected.id}`} className="rounded-full bg-paper px-4 py-2 text-sm font-semibold text-night transition-transform hover:-translate-y-0.5">Open details</Link>
          <button type="button" onClick={() => onToggleSave(selected)} className="rounded-full border border-line px-4 py-2 text-sm font-semibold transition-colors hover:border-rose hover:text-rose">{savedIds.has(selected.id) ? "♥ Saved" : "♡ Save"}</button>
        </div>
      </div>}
    </div>
  </div>;
}
