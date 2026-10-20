"use client";

import { useRef, type CSSProperties, type ReactNode } from "react";

/**
 * 3D tilt with a light spotlight that follows the pointer. The transform is applied straight to the
 * DOM node, so hover stays smooth without re-rendering React.
 */
export function Tilt({ children, className = "", strength = 10 }: { children: ReactNode; className?: string; strength?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  const onMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const node = ref.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    node.style.transform = `perspective(900px) rotateX(${(0.5 - y) * strength}deg) rotateY(${(x - 0.5) * strength}deg) translateZ(0)`;
    node.style.setProperty("--spot-x", `${x * 100}%`);
    node.style.setProperty("--spot-y", `${y * 100}%`);
    node.style.setProperty("--spot-o", "1");
  };

  const onLeave = () => {
    const node = ref.current;
    if (!node) return;
    node.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
    node.style.setProperty("--spot-o", "0");
  };

  return <div
    ref={ref}
    onPointerMove={onMove}
    onPointerLeave={onLeave}
    className={`relative transition-transform duration-300 ease-out will-change-transform ${className}`}
    style={{ transformStyle: "preserve-3d", "--spot-x": "50%", "--spot-y": "50%", "--spot-o": "0" } as CSSProperties}
  >
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-10 rounded-[inherit] transition-opacity duration-300"
      style={{ opacity: "var(--spot-o)", background: "radial-gradient(420px circle at var(--spot-x) var(--spot-y), rgba(255,255,255,0.14), transparent 45%)" }}
    />
    {children}
  </div>;
}
