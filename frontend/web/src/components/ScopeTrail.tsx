import type { EngineState } from "../lib/engine";
import { scopeName } from "../lib/values";

// Global → Scope 1 → Scope 2, with how many declarations each scope currently owns
// (visible records plus declarations hidden on the undo stack).
export function ScopeTrail({ state }: { state: EngineState }) {
  const depth = state.stats.depth;
  const owned = Array.from({ length: depth + 1 }, () => 0);
  for (const r of state.records) owned[r.depth]++;
  for (const u of state.undo) if (u.kind === "shadow") owned[u.depth]++;
  return (
    <nav className="scope-trail" aria-label="Open scopes">
      {owned.map((n, d) => (
        <span className="crumb-wrap" key={d}>
          {d > 0 && (
            <svg className="crumb-arrow" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M6 3.5L10.5 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          <span className={`crumb ${d === depth ? "active" : ""}`} aria-current={d === depth ? "true" : undefined}>
            <span className="crumb-depth">{d}</span>
            {scopeName(d)}
            <span className="crumb-count">{n}</span>
          </span>
        </span>
      ))}
    </nav>
  );
}
