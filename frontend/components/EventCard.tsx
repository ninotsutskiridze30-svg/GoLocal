"use client";

import Link from "next/link";
import { Photo } from "@/components/Photo";
import { Tilt } from "@/components/Tilt";
import { eventPrice, formatEventDate, formatEventTime } from "@/lib/event-utils";
import type { EventItem } from "@/types/event";

interface EventCardProps {
  event: EventItem;
  saved: boolean;
  onToggleSave: (event: EventItem) => void;
  index?: number;
}

const categoryColor: Record<string, string> = {
  music: "bg-rose text-night",
  nightlife: "bg-violet text-night",
  exhibition: "bg-gold text-night",
  theatre: "bg-amber text-night",
  workshop: "bg-amber text-night",
  technology: "bg-teal text-night",
  market: "bg-gold text-night",
  film: "bg-violet text-night",
  festival: "bg-rose text-night",
  family: "bg-teal text-night",
  talk: "bg-teal text-night",
  social: "bg-gold text-night",
  sports: "bg-teal text-night",
  food: "bg-amber text-night",
};

export function EventCard({ event, saved, onToggleSave, index = 0 }: EventCardProps) {
  const match = typeof event.score === "number" ? Math.round(event.score * 100) : null;

  return <div className="animate-rise h-full" style={{ animationDelay: `${Math.min(index, 8) * 70}ms` }}>
    <Tilt strength={8} className="h-full">
      <article className="group glass relative flex h-full flex-col overflow-hidden rounded-3xl transition-shadow duration-500 hover:shadow-[0_30px_70px_rgba(155,123,255,0.22)]">
        <Link href={`/events/${event.id}`} className="relative block h-52 overflow-hidden" aria-label={`Open ${event.title}`}>
          <Photo src={event.image_url} alt="" className="size-full object-cover transition-transform duration-700 group-hover:scale-110" />
          <div className="absolute inset-0 bg-gradient-to-t from-night/90 via-night/10 to-transparent" />
          <span className={`absolute top-3 left-3 rounded-full px-2.5 py-1 font-mono text-[10px] font-bold tracking-widest uppercase ${categoryColor[event.category] ?? "bg-paper text-night"}`}>{event.category}</span>
          {event.demo && <span className="absolute top-3 right-3 rounded-full border border-rose/50 bg-night/70 px-2.5 py-1 font-mono text-[10px] tracking-widest text-rose uppercase">Demo</span>}
          <span className="absolute bottom-3 left-4 font-mono text-xs text-paper/90">{formatEventDate(event.start_time)} · {formatEventTime(event.start_time)}</span>
        </Link>

        <div className="flex flex-1 flex-col gap-2 p-5">
          <h3 className="font-display text-xl leading-tight font-semibold">
            <Link href={`/events/${event.id}`} className="transition-colors hover:text-gold">{event.title}</Link>
          </h3>
          <p className="text-sm text-muted">{event.venue}{event.city ? ` · ${event.city}` : ""}</p>
          {event.explanation && <p className="line-clamp-2 text-sm text-paper/80"><span className="text-gold">Why · </span>{event.explanation}</p>}

          <div className="mt-auto flex items-center gap-2 pt-4">
            <span className="font-semibold">{eventPrice(event)}</span>
            {match !== null && <span className="ml-auto rounded-full bg-gold/15 px-2.5 py-1 font-mono text-[11px] font-bold text-gold">{match}%</span>}
            <button type="button" onClick={() => onToggleSave(event)} aria-pressed={saved} aria-label={saved ? `Remove ${event.title} from saved` : `Save ${event.title}`}
              className={`grid size-10 place-items-center rounded-full border text-lg transition-all duration-300 hover:scale-110 active:scale-95 ${saved ? "border-rose bg-rose/20 text-rose" : "border-line bg-panel text-muted hover:border-rose/60 hover:text-rose"}`}>
              <span className={saved ? "animate-pulse-soft" : ""}>{saved ? "♥" : "♡"}</span>
            </button>
          </div>
        </div>
      </article>
    </Tilt>
  </div>;
}
