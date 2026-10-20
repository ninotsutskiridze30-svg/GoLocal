import Link from "next/link";

/** GoLocal AI mark: a gradient location pin with a spark, built from SVG so it stays crisp at any size. */
export function LogoMark({ className = "size-9" }: { className?: string }) {
  return <svg viewBox="0 0 48 48" className={className} aria-hidden="true">
    <defs>
      <linearGradient id="logo-grad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#f2c46d" />
        <stop offset="0.5" stopColor="#ff5d8f" />
        <stop offset="1" stopColor="#9b7bff" />
      </linearGradient>
      <linearGradient id="logo-glow" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#fff" stopOpacity="0.35" />
        <stop offset="1" stopColor="#fff" stopOpacity="0" />
      </linearGradient>
    </defs>
    <path d="M24 3c-9.4 0-17 7.4-17 16.7C7 33.5 24 45 24 45s17-11.5 17-25.3C41 10.4 33.4 3 24 3z" fill="url(#logo-grad)" />
    <path d="M24 3c-9.4 0-17 7.4-17 16.7 0 3.4.9 6.3 2.6 9.1C13.9 14.9 18.3 11 24 11s10.1 3.9 14.4 17.8c1.7-2.8 2.6-5.7 2.6-9.1C41 10.4 33.4 3 24 3z" fill="url(#logo-glow)" />
    <circle cx="24" cy="20" r="8.2" fill="#0a0812" />
    <path d="M24 14.2l1.6 4.2 4.2 1.6-4.2 1.6-1.6 4.2-1.6-4.2-4.2-1.6 4.2-1.6z" fill="#f6eee2" />
  </svg>;
}

export function Logo() {
  return <Link href="/" className="group inline-flex items-center gap-3" aria-label="GoLocal AI home">
    <span className="relative grid place-items-center transition-transform duration-500 group-hover:-rotate-6 group-hover:scale-105">
      <span className="absolute inset-0 -z-10 rounded-full bg-rose/30 blur-md transition-opacity duration-500 group-hover:opacity-100" />
      <LogoMark />
    </span>
    <span className="font-display text-[22px] leading-none tracking-tight">
      <span className="font-semibold italic">GoLocal</span>
      <span className="ml-1.5 rounded-md border border-line bg-panel px-1.5 py-0.5 font-mono text-[11px] font-medium tracking-widest text-gold not-italic">AI</span>
    </span>
  </Link>;
}
