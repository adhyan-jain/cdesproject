import type { EngineState } from "../lib/engine";
import { describe } from "../lib/describe";

export function Timeline({ state, lines }: { state: EngineState; lines?: (number | undefined)[] }) {
  const items = state.ops.map((r, i) => ({ n: i + 1, r, d: describe(r) })).reverse().slice(0, 60);
  return (
    <section className="card timeline" aria-labelledby="timeline-title">
      <div className="card-head">
        <h2 id="timeline-title">Event history</h2>
        <span className="card-hint">{state.ops.length} operations</span>
      </div>
      {items.length === 0 ? (
        <p className="muted small pad">No operations yet.</p>
      ) : (
        <ol className="events">
          {items.map(({ n, d }) => (
            <li key={n} className={`event event-${d.tone}`}>
              <span className="event-n mono">{String(n).padStart(2, "0")}</span>
              <span className="event-dot" aria-hidden="true" />
              <div className="event-body">
                <div className="event-title">
                  {d.title}
                  {d.code && d.code !== "kOk" && <code className="code-chip">{d.code}</code>}
                  {lines?.[n - 1] !== undefined && <span className="line-chip mono">line {lines[n - 1]}</span>}
                </div>
                <div className="event-detail">{d.detail}</div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
