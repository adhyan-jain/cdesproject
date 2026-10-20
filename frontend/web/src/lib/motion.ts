// Motion helpers for the redesigned pages. Every effect is skipped when the visitor asks for
// reduced motion, and none of them changes a value: numbers count up to the recorded figure.
import { useEffect, useRef, useState } from "react";

export const reducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Adds the class "in" to every .reveal element the first time it scrolls into view. */
export function useRevealAll(dep: unknown) {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".reveal:not(.in)"));
    if (reducedMotion() || !("IntersectionObserver" in window)) { els.forEach((e) => e.classList.add("in")); return; }
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    // Elements that appear later (tab switches, loaded reports) are picked up too.
    const mo = new MutationObserver(() => {
      document.querySelectorAll<HTMLElement>(".reveal:not(.in):not([data-watched])").forEach((e) => { e.dataset.watched = "1"; io.observe(e); });
    });
    mo.observe(document.body, { childList: true, subtree: true });
    return () => { io.disconnect(); mo.disconnect(); };
  }, [dep]);
}

/** Primary buttons lean a few pixels towards the pointer (fine pointers only). */
export function useMagnetic() {
  useEffect(() => {
    if (reducedMotion() || !window.matchMedia("(pointer: fine)").matches) return;
    let cur: HTMLElement | null = null;
    const move = (e: PointerEvent) => {
      const t = (e.target as HTMLElement).closest<HTMLElement>(".btn-primary, .magnetic");
      if (cur && cur !== t) { cur.style.transform = ""; cur = null; }
      if (!t || (t as HTMLButtonElement).disabled) return;
      const r = t.getBoundingClientRect();
      const dx = (e.clientX - (r.left + r.width / 2)) / r.width, dy = (e.clientY - (r.top + r.height / 2)) / r.height;
      t.style.transform = `translate(${(dx * 4).toFixed(2)}px, ${(dy * 3).toFixed(2)}px)`;
      cur = t;
    };
    const leave = () => { if (cur) cur.style.transform = ""; cur = null; };
    window.addEventListener("pointermove", move, { passive: true });
    document.addEventListener("pointerleave", leave);
    return () => { window.removeEventListener("pointermove", move); document.removeEventListener("pointerleave", leave); };
  }, []);
}

/** True once the element has been on screen. */
export function useSeen<T extends HTMLElement>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    if (reducedMotion() || !("IntersectionObserver" in window)) { setSeen(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } }, { threshold: 0.3 });
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  return [ref, seen];
}

/** Counts from 0 to `to` once `go` is true; ends exactly on `to`. */
export function useCountUp(to: number, go: boolean, ms = 1100) {
  const [v, setV] = useState(reducedMotion() ? to : 0);
  useEffect(() => {
    if (!go) return;
    if (reducedMotion()) { setV(to); return; }
    let raf = 0;
    const t0 = performance.now();
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / ms);
      setV(to * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(tick); else setV(to);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, go, ms]);
  return v;
}
