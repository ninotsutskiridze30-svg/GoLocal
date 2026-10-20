"use client";

interface DateFieldProps {
  label: string;
  value: string;
  min?: string;
  max?: string;
  onChange: (value: string) => void;
}

/** Date input with a glass pill, a calendar glyph and a dark native picker. */
export function DateField({ label, value, min, max, onChange }: DateFieldProps) {
  return <label className={`group relative flex h-11 cursor-pointer items-center gap-3 rounded-full border bg-panel pr-4 pl-4 text-sm backdrop-blur-xl transition-all duration-300 hover:border-gold/50 focus-within:border-gold focus-within:shadow-[0_0_0_4px_rgba(242,196,109,0.12)] ${value ? "border-gold/40" : "border-line"}`}>
    <svg viewBox="0 0 20 20" aria-hidden="true" className={`size-4 shrink-0 transition-colors ${value ? "text-gold" : "text-muted group-hover:text-paper"}`}>
      <rect x="3" y="4.5" width="14" height="12.5" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M3 8.5h14M7 3v3M13 3v3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
    <span className="font-mono text-[10px] tracking-widest text-muted uppercase">{label}</span>
    <input
      type="date"
      value={value}
      min={min}
      max={max}
      onChange={(event) => onChange(event.target.value)}
      aria-label={label}
      className="min-w-0 flex-1 cursor-pointer bg-transparent text-paper outline-none [color-scheme:dark] [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-60 [&::-webkit-calendar-picker-indicator]:transition-opacity hover:[&::-webkit-calendar-picker-indicator]:opacity-100"
    />
    {value && <button type="button" onClick={(event) => { event.preventDefault(); onChange(""); }} aria-label={`Clear ${label}`} className="grid size-5 place-items-center rounded-full bg-paper/10 text-xs text-muted transition-colors hover:bg-rose/30 hover:text-paper">×</button>}
  </label>;
}
