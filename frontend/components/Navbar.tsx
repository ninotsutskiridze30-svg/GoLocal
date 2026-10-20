"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";
import { useSavedEvents } from "@/lib/saved";

const links = [
  { href: "/#search", label: "Ask AI" },
  { href: "/#moods", label: "Moods" },
  { href: "/#events", label: "Events" },
  { href: "/#map", label: "Map" },
];

export function Navbar() {
  const pathname = usePathname();
  const { saved } = useSavedEvents();
  const savedActive = pathname === "/saved";

  return <header className="sticky top-0 z-50 px-4 pt-4">
    <nav className="glass mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full py-2.5 pr-2.5 pl-5 shadow-[0_10px_40px_rgba(0,0,0,0.35)]" aria-label="Main">
      <Logo />
      <ul className="hidden items-center gap-1 md:flex">
        {links.map((link) => <li key={link.href}>
          <Link href={link.href} className="group relative block rounded-full px-4 py-2 text-sm font-medium text-muted transition-colors hover:text-paper">
            {link.label}
            <span className="absolute inset-x-4 -bottom-0.5 h-px origin-left scale-x-0 bg-gradient-to-r from-gold to-rose transition-transform duration-300 group-hover:scale-x-100" />
          </Link>
        </li>)}
      </ul>
      <Link href="/saved" aria-current={savedActive ? "page" : undefined} className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-all hover:-translate-y-0.5 ${savedActive ? "border-rose/60 bg-rose/15 text-paper" : "border-line bg-panel text-paper hover:border-gold/50"}`}>
        <span aria-hidden="true" className="text-rose">♥</span> Saved
        <span className="grid min-w-6 place-items-center rounded-full bg-gold px-1.5 font-mono text-[11px] font-bold text-night">{saved.length}</span>
      </Link>
    </nav>
  </header>;
}
