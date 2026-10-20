"use client";

import { useState } from "react";
import { EventCard } from "@/components/EventCard";
import { DateField } from "@/components/DateField";
import { MapView } from "@/components/MapView";
import { Select } from "@/components/Select";
import { Photo } from "@/components/Photo";
import { Reveal } from "@/components/Reveal";
import { Tilt } from "@/components/Tilt";
import { BUDGET_ANY, CATEGORIES, DEFAULT_FILTERS, MOODS, type FilterState, type MoodId, type SortKey } from "@/lib/filters";
import type { EventItem } from "@/types/event";

interface DiscoverProps {
  filters: FilterState;
  onFiltersChange: (next: FilterState) => void;
  events: EventItem[];
  totalCount: number;
  searchActive: boolean;
  savedIds: ReadonlySet<number>;
  onToggleSave: (event: EventItem) => void;
  onReset: () => void;
}

const sortLabels: Record<SortKey, string> = { date: "Soonest", price: "Lowest price", match: "Best match" };
const CategoryIcon = () => <svg viewBox="0 0 20 20" aria-hidden="true" className="size-4"><path d="M3 5.5h14M3 10h14M3 14.5h9" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>;
const moodGlow: Record<MoodId, string> = { relaxed: "from-gold/40", tech: "from-teal/40", nightlife: "from-rose/40", culture: "from-violet/40" };

export function Discover({ filters, onFiltersChange, events, totalCount, searchActive, savedIds, onToggleSave, onReset }: DiscoverProps) {
  const [view, setView] = useState<"grid" | "map">("grid");
  const set = (patch: Partial<FilterState>) => onFiltersChange({ ...filters, ...patch });
  const isFiltered = JSON.stringify(filters) !== JSON.stringify(DEFAULT_FILTERS);

  return <>
    <section id="moods" className="relative mx-auto max-w-6xl px-5 py-20">
      <Reveal>
        <p className="font-mono text-xs tracking-[0.2em] text-gold uppercase">01 · Mood</p>
        <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight md:text-5xl">How do you want to <span className="italic text-gradient">feel</span> tonight?</h2>
      </Reveal>
      <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
        {MOODS.map((mood, index) => {
          const active = filters.mood === mood.id;
          return <Reveal key={mood.id} delay={index * 90}>
            <Tilt strength={12} className="h-full">
              <button type="button" aria-pressed={active} onClick={() => set({ mood: active ? null : mood.id })}
                className={`group relative h-72 w-full overflow-hidden rounded-3xl border-2 text-left transition-all duration-500 ${active ? "border-gold shadow-[0_0_50px_rgba(242,196,109,0.35)]" : "border-transparent hover:border-line"}`}>
                <Photo src={mood.image} alt="" className="absolute inset-0 size-full object-cover transition-transform duration-700 group-hover:scale-110" />
                <div className={`absolute inset-0 bg-gradient-to-t from-night via-night/40 to-transparent`} />
                <div className={`absolute -inset-10 bg-gradient-to-br ${moodGlow[mood.id]} to-transparent opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100`} />
                <div className="absolute inset-x-0 bottom-0 p-5">
                  <span className={`mb-2 grid size-9 place-items-center rounded-full text-base transition-colors ${active ? "bg-gold text-night" : "bg-paper/15 text-paper"}`}>{active ? "✓" : mood.title[0]}</span>
                  <p className="font-display text-2xl leading-tight font-semibold">{mood.title}</p>
                  <p className="mt-1 text-xs text-paper/70">{mood.subtitle}</p>
                </div>
              </button>
            </Tilt>
          </Reveal>;
        })}
      </div>

      <Reveal delay={150} className="glass mt-8 flex flex-col gap-4 rounded-3xl p-6 sm:flex-row sm:items-center">
        <label htmlFor="budget" className="min-w-40 font-semibold">Budget <span className="ml-2 font-mono text-sm text-gold">{filters.budget >= BUDGET_ANY ? "any" : `≤ ${filters.budget} GEL`}</span></label>
        <input id="budget" type="range" min={0} max={BUDGET_ANY} step={5} value={filters.budget} onChange={(event) => set({ budget: Number(event.target.value) })}
          className="h-2 w-full cursor-pointer appearance-none rounded-full bg-gradient-to-r from-teal via-gold to-rose accent-gold" />
      </Reveal>
    </section>

    <section id="events" className="relative mx-auto max-w-6xl px-5 pb-10">
      <Reveal className="relative z-40 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="font-mono text-xs tracking-[0.2em] text-gold uppercase">02 · {searchActive ? "Search results" : filters.savedOnly ? "Saved" : "Events"}</p>
          <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight md:text-5xl">
            {events.length} {events.length === 1 ? "night" : "nights"} <span className="text-muted text-2xl">{totalCount !== events.length ? `of ${totalCount}` : ""}</span>
          </h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="glass flex rounded-full p-1" role="group" aria-label="View">
            {(["grid", "map"] as const).map((mode) => <button key={mode} type="button" onClick={() => setView(mode)} aria-pressed={view === mode}
              className={`rounded-full px-4 py-2 text-sm font-semibold capitalize transition-all ${view === mode ? "bg-paper text-night" : "text-muted hover:text-paper"}`}>{mode}</button>)}
          </div>
          <Select
            label="Sort"
            value={filters.sort}
            onChange={(sort) => set({ sort: sort as SortKey })}
            options={(Object.keys(sortLabels) as SortKey[]).map((key) => ({ value: key, label: sortLabels[key] }))}
            className="w-64"
          />
        </div>
      </Reveal>

      <Reveal delay={80} className="relative z-30 mt-6 flex flex-wrap items-center gap-3">
        <Select
          label="Category"
          value={filters.category}
          onChange={(category) => set({ category })}
          icon={<CategoryIcon />}
          options={[{ value: "all", label: "All categories" }, ...CATEGORIES.map((item) => ({ value: item, label: item }))]}
          className="w-72"
        />
        <DateField label="From" value={filters.from} max={filters.to || undefined} onChange={(from) => set({ from })} />
        <DateField label="Until" value={filters.to} min={filters.from || undefined} onChange={(to) => set({ to })} />
        <button type="button" onClick={() => set({ freeOnly: !filters.freeOnly })} aria-pressed={filters.freeOnly} className={`h-11 rounded-full border px-4 text-sm font-semibold transition-all ${filters.freeOnly ? "border-teal bg-teal/15 text-teal" : "border-line bg-panel text-muted hover:text-paper"}`}>Free only</button>
        <button type="button" onClick={() => set({ savedOnly: !filters.savedOnly })} aria-pressed={filters.savedOnly} className={`h-11 rounded-full border px-4 text-sm font-semibold transition-all ${filters.savedOnly ? "border-rose bg-rose/15 text-rose" : "border-line bg-panel text-muted hover:text-paper"}`}>♥ Saved only</button>
        {isFiltered && <button type="button" onClick={onReset} className="h-11 px-3 text-sm font-semibold text-gold underline-offset-4 hover:underline">Reset all</button>}
      </Reveal>

      <div className="mt-10">
        {view === "map" ? <MapView events={events} savedIds={savedIds} onToggleSave={onToggleSave} /> : events.length > 0 ? <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {events.map((event, index) => <EventCard key={event.id} event={event} index={index} saved={savedIds.has(event.id)} onToggleSave={onToggleSave} />)}
        </div> : <Reveal className="glass rounded-3xl p-12 text-center">
          <p className="font-display text-3xl font-semibold">{filters.savedOnly ? "No saved nights yet." : "Nothing matches these filters."}</p>
          <p className="mt-3 text-muted">{filters.savedOnly ? "Tap ♡ on any event to keep it here." : "Try another mood, raise the budget or widen the dates."}</p>
          <button type="button" onClick={onReset} className="mt-6 rounded-full bg-paper px-5 py-2.5 font-semibold text-night transition-transform hover:-translate-y-0.5">Reset filters</button>
        </Reveal>}
      </div>
    </section>
  </>;
}
