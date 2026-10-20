"use client";

import { useState, type FormEvent } from "react";
import { HeroOrb } from "@/components/HeroOrb";
import type { EventSearchStatus } from "@/types/event";

const examples = ["Jazz under 40 GEL", "Free this weekend", "Tech meetup tonight", "Something quiet and artsy"];

interface HeroProps {
  activeQuery: string;
  loading: boolean;
  status: EventSearchStatus;
  message: string;
  resultCount: number;
  onSearch: (query: string) => void | Promise<void>;
}

/** Top of the page: a 3D orb, the headline and the AI search, which comes first. */
export function Hero({ activeQuery, loading, status, message, resultCount, onSearch }: HeroProps) {
  const [draft, setDraft] = useState("");

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (draft.trim()) void onSearch(draft.trim());
  };

  const statusLabel = loading ? "Searching…" : status === "live" ? "Live events" : status === "error" ? "Service offline" : "Preview listings";
  const statusColor = status === "live" ? "bg-teal" : status === "error" ? "bg-rose" : "bg-gold";

  return <section id="search" className="relative mx-auto grid w-full max-w-6xl items-center gap-8 px-5 pt-10 pb-16 md:grid-cols-[1.1fr_0.9fr] md:pt-16">
    <div>
      <p className="animate-rise mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1.5 font-mono text-[11px] tracking-[0.18em] text-gold uppercase">
        <span className="size-1.5 animate-pulse-soft rounded-full bg-gold" /> AI event discovery · Tbilisi
      </p>
      <h1 className="animate-rise font-display text-5xl leading-[0.98] font-semibold tracking-tight [animation-delay:120ms] md:text-7xl">
        Find something <span className="text-gradient italic">worth</span> your night.
      </h1>
      <p className="animate-rise mt-5 max-w-xl text-lg leading-relaxed text-muted [animation-delay:220ms]">
        Say what you feel like in your own words. We search local events, match them to your mood and budget, and explain why each one fits.
      </p>

      <form onSubmit={submit} role="search" className="animate-rise glass relative mt-9 flex flex-col gap-2 rounded-3xl p-2 shadow-[0_20px_60px_rgba(0,0,0,0.35)] transition-shadow duration-500 [animation-delay:320ms] focus-within:shadow-[0_0_0_4px_rgba(242,196,109,0.18),0_20px_60px_rgba(0,0,0,0.35)] sm:flex-row sm:items-center sm:rounded-full">
        <label htmlFor="ai-query" className="sr-only">Describe the event you are looking for</label>
        <span aria-hidden="true" className="hidden pl-4 text-xl text-gold sm:block">✦</span>
        <input
          id="ai-query"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="A cosy evening under 30 GEL, or jazz this Friday…"
          maxLength={2000}
          className="h-12 min-w-0 flex-1 bg-transparent px-3 text-[17px] outline-none placeholder:text-muted/70"
        />
        <div className="flex gap-2">
          {draft && <button type="button" onClick={() => setDraft("")} className="h-11 rounded-full px-4 text-sm text-muted hover:text-paper">Clear</button>}
          <button type="submit" disabled={loading || !draft.trim()} className="group relative h-12 flex-1 overflow-hidden rounded-full bg-gradient-to-r from-gold via-amber to-rose px-7 font-semibold text-night shadow-[0_10px_30px_rgba(242,196,109,0.35)] transition-all hover:-translate-y-0.5 hover:shadow-[0_16px_40px_rgba(255,93,143,0.4)] disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none">
            <span className="relative z-10">{loading ? "Searching…" : "Search"}</span>
            <span aria-hidden="true" className="shine absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100" />
          </button>
        </div>
      </form>

      <div className="animate-rise mt-4 flex flex-wrap gap-2 [animation-delay:420ms]" aria-label="Example searches">
        {examples.map((item) => <button key={item} type="button" onClick={() => { setDraft(item); void onSearch(item); }} className="rounded-full border border-line bg-panel px-3.5 py-1.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-gold/60 hover:text-paper">
          {item}
        </button>)}
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-2 text-sm text-muted" role="status" aria-live="polite">
        <span className={`size-2 rounded-full ${statusColor}`} aria-hidden="true" />
        <span>{statusLabel}</span>
        {activeQuery && <span>· Results for <b className="text-paper">“{activeQuery}”</b> ({resultCount})</span>}
        {message && <span className="text-rose">· {message}</span>}
      </div>
    </div>
    <div className="animate-rise relative hidden md:block [animation-delay:200ms]">
      <HeroOrb />
      <div className="glass absolute bottom-4 left-0 rounded-2xl px-4 py-3 text-sm shadow-xl">
        <p className="font-mono text-[11px] tracking-widest text-gold uppercase">Match explained</p>
        <p className="mt-1 text-paper">“Free, live and close to the centre.”</p>
      </div>
    </div>
  </section>;
}
