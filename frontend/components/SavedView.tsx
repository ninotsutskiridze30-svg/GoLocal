"use client";

import Link from "next/link";
import { EventCard } from "@/components/EventCard";
import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";
import { Reveal } from "@/components/Reveal";
import { useSavedEvents } from "@/lib/saved";

/** Every event the visitor has saved, sorted by start time. Stored in this browser. */
export function SavedView() {
  const { saved, ids, toggle } = useSavedEvents();
  const sorted = [...saved].sort((a, b) => Date.parse(a.start_time) - Date.parse(b.start_time));

  return <>
    <Navbar />
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-14">
      <Reveal>
        <p className="font-mono text-xs tracking-[0.2em] text-rose uppercase">Your list</p>
        <h1 className="mt-3 font-display text-5xl font-semibold tracking-tight md:text-6xl">Saved <span className="italic text-gradient">nights</span></h1>
        <p className="mt-4 text-muted">{sorted.length === 0 ? "Nothing saved yet." : `${sorted.length} saved · kept in this browser`}</p>
      </Reveal>

      {sorted.length > 0 ? <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {sorted.map((event, index) => <EventCard key={event.id} event={event} index={index} saved={ids.has(event.id)} onToggleSave={toggle} />)}
      </div> : <Reveal className="glass mt-12 rounded-3xl p-14 text-center">
        <p className="font-display text-3xl font-semibold">A quiet list, for now.</p>
        <p className="mt-3 text-muted">Tap ♡ on any night you like and it will wait for you here.</p>
        <Link href="/#events" className="mt-7 inline-block rounded-full bg-paper px-6 py-3 font-semibold text-night transition-transform hover:-translate-y-0.5">Discover events</Link>
      </Reveal>}
    </main>
    <Footer />
  </>;
}
