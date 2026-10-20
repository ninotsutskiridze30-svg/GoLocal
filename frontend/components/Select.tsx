"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  icon?: ReactNode;
  className?: string;
}

/**
 * Custom dropdown with a glass popover, keyboard support (arrows, Enter, Escape, Home, End),
 * click-outside closing and an animated check on the selected option.
 */
export function Select({ label, value, options, onChange, icon, className = "" }: SelectProps) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const listId = useId();

  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  const selected = options[selectedIndex];

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  const openList = () => {
    setActive(selectedIndex);
    setOpen(true);
  };

  const choose = (index: number) => {
    onChange(options[index].value);
    setOpen(false);
    trigger.current?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
        event.preventDefault();
        openList();
      }
      return;
    }
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setActive((index) => Math.min(options.length - 1, index + 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        setActive((index) => Math.max(0, index - 1));
        break;
      case "Home":
        event.preventDefault();
        setActive(0);
        break;
      case "End":
        event.preventDefault();
        setActive(options.length - 1);
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        choose(active);
        break;
      case "Escape":
      case "Tab":
        setOpen(false);
        break;
    }
  };

  return <div ref={root} className={`relative ${className}`}>
    <button
      ref={trigger}
      type="button"
      aria-label={label}
      aria-haspopup="listbox"
      aria-expanded={open}
      aria-controls={open ? listId : undefined}
      onClick={() => (open ? setOpen(false) : openList())}
      onKeyDown={onKeyDown}
      className={`group flex h-11 w-full min-w-44 cursor-pointer items-center gap-3 rounded-full border bg-panel pr-4 pl-4 text-left text-sm font-semibold backdrop-blur-xl transition-all duration-300 hover:border-gold/50 hover:bg-paper/[0.07] focus-visible:border-gold ${open ? "border-gold/60 shadow-[0_0_0_4px_rgba(242,196,109,0.12)]" : "border-line"}`}
    >
      {icon && <span className="text-gold" aria-hidden="true">{icon}</span>}
      <span className="flex-1 truncate capitalize">
        <span className="mr-2 font-mono text-[10px] tracking-widest text-muted uppercase">{label}</span>
        {selected?.label}
      </span>
      <svg viewBox="0 0 20 20" aria-hidden="true" className={`size-4 text-muted transition-transform duration-300 ${open ? "rotate-180 text-gold" : "group-hover:text-paper"}`}>
        <path d="M5 7.5l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>

    {open && <ul
      id={listId}
      role="listbox"
      aria-label={label}
      aria-activedescendant={`${listId}-${active}`}
      tabIndex={-1}
      className="glass-strong absolute top-full right-0 left-0 z-50 mt-2 max-h-80 min-w-full origin-top animate-pop overflow-auto rounded-2xl p-1.5 shadow-[0_24px_60px_rgba(0,0,0,0.55)] outline-none [scrollbar-color:rgba(242,196,109,0.35)_transparent] [scrollbar-width:thin]"
      onKeyDown={onKeyDown}
    >
      {options.map((option, index) => {
        const isSelected = option.value === value;
        const isActive = index === active;
        return <li
          key={option.value}
          id={`${listId}-${index}`}
          role="option"
          aria-selected={isSelected}
          onMouseEnter={() => setActive(index)}
          onClick={() => choose(index)}
          className={`relative flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm capitalize transition-colors duration-150 ${isActive ? "bg-paper/[0.08] text-paper" : "text-paper/80"} ${isSelected ? "font-semibold text-gold" : ""}`}
        >
          <span className={`size-1.5 shrink-0 rounded-full transition-all duration-300 ${isSelected ? "scale-100 bg-gold" : "scale-0 bg-transparent"}`} aria-hidden="true" />
          <span className="flex-1 truncate">{option.label}</span>
          {isSelected && <svg viewBox="0 0 20 20" aria-hidden="true" className="size-4 animate-pop text-gold"><path d="M4.5 10.5l3.5 3.5 7.5-8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
        </li>;
      })}
    </ul>}
  </div>;
}
