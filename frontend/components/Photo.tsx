/* Plain <img> keeps remote image hosts out of next.config; these URLs come from the API and demo data. */
/* eslint-disable @next/next/no-img-element */

interface PhotoProps {
  src: string | null | undefined;
  alt: string;
  className?: string;
}

/** Event or mood photo. Falls back to a warm gradient when no image is available. */
export function Photo({ src, alt, className }: PhotoProps) {
  if (!src) return <div className={`bg-gradient-to-br from-gold/25 via-rose/20 to-violet/30 ${className ?? ""}`} role="img" aria-label={alt} />;
  return <img src={src} alt={alt} loading="lazy" className={className} />;
}
