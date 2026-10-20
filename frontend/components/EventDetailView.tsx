"use client";

import Link from "next/link";
import { Footer } from "@/components/Footer";
import { EventCard } from "@/components/EventCard";
import { Navbar } from "@/components/Navbar";
import { Photo } from "@/components/Photo";
import { Reveal } from "@/components/Reveal";
import { Tilt } from "@/components/Tilt";
import { useEventEngine } from "@/hooks/useEventEngine";
import { demoEvents } from "@/lib/demo-events";
import { eventPrice, formatEventDate, formatEventTime, safeUrl } from "@/lib/event-utils";
import { useSavedEvents } from "@/lib/saved";

export function EventDetailView({ id }: { id: number }) {
  const { events } = useEventEngine(demoEvents);
  const { ids: savedIds, toggle } = useSavedEvents();
  const event = events.find((item) => item.id === id) ?? demoEvents.find((item) => item.id === id) ?? null;

  if (!event) {
    return <>
      <Navbar />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-5 py-32 text-center">
        <p className="font-mono text-xs tracking-[0.2em] text-gold uppercase">Not found</p>
        <h1 className="mt-4 font-display text-5xl font-semibold">This night has moved on.</h1>
        <Link href="/#events" className="mt-8 rounded-full bg-paper px-6 py-3 font-semibold text-night transition-transform hover:-translate-y-0.5">Browse events</Link>
      </main>
      <Footer />
    </>;
  }

  const saved = savedIds.has(event.id);
  const match = typeof event.score === "number" ? Math.round(event.score * 100) : null;
  const sourceUrl = !event.demo && event.source_url ? safeUrl(event.source_url, "") : "";
  const place = [event.address, event.city].filter(Boolean).join(", ");
  const similar = events.filter((item) => item.id !== event.id && item.category === event.category).slice(0, 3);
  const fallback = similar.length ? similar : events.filter((item) => item.id !== event.id).slice(0, 3);

  return <>
    <Navbar />
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 pt-6 pb-10">
      <Link href="/#events" className="inline-flex items-center gap-2 text-sm text-muted transition-colors hover:text-gold">← Back to events</Link>

      <div className="mt-6 grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <Reveal>
          <Tilt strength={6} className="overflow-hidden rounded-[2rem] shadow-[0_40px_100px_rgba(0,0,0,0.5)]">
            <div className="relative aspect-[4/5] overflow-hidden">
              <Photo src={event.image_url} alt={event.title} className="size-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-night/80 via-transparent to-transparent" />
              <span className="absolute top-5 left-5 rounded-full bg-gold px-3 py-1 font-mono text-[11px] font-bold tracking-widest text-night uppercase">{event.category}</span>
            </div>
          </Tilt>
        </Reveal>

        <Reveal delay={120} className="space-y-6">
          <div>
            <p className="font-mono text-sm text-gold">{formatEventDate(event.start_time)} · {formatEventTime(event.start_time)}{event.end_time ? ` – ${formatEventTime(event.end_time)}` : ""}</p>
            <h1 className="mt-3 font-display text-5xl leading-[1.02] font-semibold tracking-tight md:text-6xl">{event.title}</h1>
            <p className="mt-4 text-lg text-muted">{event.venue}{place ? ` · ${place}` : ""}</p>
          </div>

          {event.description && <p className="leading-relaxed text-paper/85">{event.description}</p>}

          <dl className="glass grid grid-cols-2 gap-5 rounded-3xl p-6">
            <div><dt className="font-mono text-[11px] tracking-widest text-muted uppercase">Price</dt><dd className="mt-1 text-xl font-semibold">{eventPrice(event)}</dd></div>
            <div><dt className="font-mono text-[11px] tracking-widest text-muted uppercase">Age</dt><dd className="mt-1 text-xl font-semibold">{event.age_restriction != null ? `${event.age_restriction}+` : "All ages"}</dd></div>
            <div><dt className="font-mono text-[11px] tracking-widest text-muted uppercase">Source</dt><dd className="mt-1 font-semibold">{event.demo ? "Fictional demo listing" : event.source_name || "Not provided"}</dd></div>
            <div><dt className="font-mono text-[11px] tracking-widest text-muted uppercase">Category</dt><dd className="mt-1 font-semibold capitalize">{event.category}</dd></div>
          </dl>

          <div className="relative overflow-hidden rounded-3xl border border-gold/30 bg-gradient-to-br from-gold/15 via-rose/5 to-violet/10 p-6">
            <p className="font-mono text-[11px] tracking-widest text-gold uppercase">Why the AI suggests it</p>
            <p className="mt-3 font-display text-2xl leading-snug font-medium">{event.explanation || "No explanation was provided for this listing."}</p>
            {match !== null && <div className="mt-5">
              <div className="flex justify-between font-mono text-xs text-muted"><span>Match score</span><span className="text-gold">{match}%</span></div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-paper/10"><div className="h-full rounded-full bg-gradient-to-r from-teal via-gold to-rose transition-[width] duration-1000" style={{ width: `${match}%` }} /></div>
            </div>}
          </div>

          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => toggle(event)} aria-pressed={saved} className={`rounded-full px-6 py-3 font-semibold transition-all hover:-translate-y-0.5 ${saved ? "bg-rose text-night" : "bg-paper text-night"}`}>{saved ? "♥ Saved" : "♡ Save this night"}</button>
            {sourceUrl && <a href={sourceUrl} target="_blank" rel="noreferrer" className="rounded-full border border-line px-6 py-3 font-semibold transition-colors hover:border-gold hover:text-gold">Open source ↗</a>}
          </div>
        </Reveal>
      </div>

      {fallback.length > 0 && <section className="mt-24">
        <Reveal>
          <p className="font-mono text-xs tracking-[0.2em] text-gold uppercase">More like this</p>
          <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight">You might also like</h2>
        </Reveal>
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {fallback.map((item, index) => <EventCard key={item.id} event={item} index={index} saved={savedIds.has(item.id)} onToggleSave={toggle} />)}
        </div>
      </section>}
    </main>
    <Footer />
  </>;
}
