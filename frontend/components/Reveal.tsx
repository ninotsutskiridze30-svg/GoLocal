"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/** Fades and lifts its children into view the first time they scroll into the viewport. */
export function Reveal({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.disconnect();
      }
    }, { threshold: 0.12 });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return <div
    ref={ref}
    className={`transition-all duration-700 ease-out ${visible ? "translate-y-0 opacity-100 blur-0" : "translate-y-8 opacity-0 blur-[3px]"} ${className}`}
    style={{ transitionDelay: `${delay}ms` }}
  >
    {children}
  </div>;
}
