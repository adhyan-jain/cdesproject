// The lab's instrument panel: engine status, operation count, memory, scope depth, allocator,
// and the last few calls written as the calls a compiler makes. Every value comes from the
// engine's latest response; nothing here is simulated.
import type { EngineState, OpResult } from "../lib/engine";
import type { EngineHealth } from "./Header";

function call(r: OpResult): { text: string; note: string; tone: "ok" | "warn" | "bad" | "plain" } {
  if (r.effect === "refused") return { text: `declare("${r.name}")`, note: `refused · ${r.status}`, tone: "bad" };
  switch (r.op) {
    case "D": return { text: `declare("${r.name}")`, note: r.effect === "shadow" ? "shadows outer" : "record +1", tone: r.effect === "shadow" ? "warn" : "ok" };
    case "V": return { text: `declare("${r.name}", ${r.src})`, note: r.effect === "shadow" ? "shadows outer" : "record +1", tone: "ok" };
    case "L": return { text: `lookup("${r.name}")`, note: r.found ? `found · depth ${r.depth}` : "not found", tone: r.found ? "plain" : "bad" };
    case "E": return { text: "scope.enter()", note: `mark · depth ${r.depthAfter}`, tone: "plain" };
    case "X": return { text: "scope.exit()", note: `undo ${r.removed?.length ?? 0}${r.restored?.length ? ` · restored ${r.restored.length}` : ""}`, tone: "warn" };
  }
}

export function EngineStrip({ health, state, lines }: { health: EngineHealth; state: EngineState | null; lines: (number | undefined)[] }) {
  const s = state?.stats;
  const recent = state ? state.ops.slice(-5) : [];
  const first = state ? state.ops.length - recent.length : 0;
  return (
    <section className="estrip" aria-label="Engine status">
      <dl className="estrip-cells mono">
        <div><dt>ENGINE</dt><dd className={health.state}>{health.state === "ready" ? "READY" : health.state === "down" ? "OFFLINE" : "…"}</dd></div>
        <div><dt>TRACE</dt><dd>{state ? `${state.ops.length} ops` : "—"}{state && state.ops.length > 0 ? <span className="estrip-live">ACTIVE</span> : null}</dd></div>
        <div><dt>MEMORY</dt><dd>{s ? `${s.used} / ${s.capacity} B` : "—"}</dd></div>
        <div><dt>SCOPE</dt><dd>{s ? `depth ${s.depth}` : "—"}</dd></div>
        <div><dt>ALLOCATOR</dt><dd>NONE · fixed mode</dd></div>
      </dl>
      <ol className="estrip-trace mono" aria-label="Last calls">
        {recent.length === 0 && <li className="plain"><span>waiting for the first call…</span></li>}
        {recent.map((r, i) => {
          const c = call(r);
          const ln = lines[first + i];
          return (
            <li key={first + i} className={c.tone}>
              <span className="estrip-n">{String(first + i + 1).padStart(3, "0")}</span>
              <span>{c.text}</span>
              <small>{c.note}{ln !== undefined ? ` · line ${ln}` : ""}</small>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
