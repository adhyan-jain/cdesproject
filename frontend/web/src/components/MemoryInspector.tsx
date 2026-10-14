import type { EngineState, UndoView } from "../lib/engine";
import { formatValue, scopeName, typeName } from "../lib/values";

const fmt = (b: number) => (b >= 1024 && b % 1024 === 0 ? `${b / 1024} KiB` : `${b} B`);

type Cell = { region: "index" | "index-on" | "reserved" | "record" | "free" | "undo" | "undo-mark"; title: string };

// One cell per 4-byte word of the buffer the table lives in, read back after the last operation.
function cells(s: EngineState): Cell[] {
  const cap = s.stats.capacity / 4, idx = s.stats.index / 4, itop = s.stats.records / 4, undo = s.stats.undo / 4;
  const out: Cell[] = [];
  const occupied = new Map(s.index.map((x) => [x.slot, x]));
  for (let i = 0; i < idx; i++) {
    const o = occupied.get(i);
    out.push(o ? { region: "index-on", title: `index slot ${i}: ${o.name} (fingerprint ${o.fp}, home slot ${o.home}, probe ${o.probe})` } : { region: "index", title: `index slot ${i}: empty` });
  }
  const owner = new Map<number, string>();
  for (const r of s.records) for (let k = 0; k < r.words; k++) owner.set(r.ref + k, `${r.name} (record word ${k + 1} of ${r.words})`);
  for (let i = 0; i < itop; i++) out.push(i === 0 ? { region: "reserved", title: "reference 0, reserved for “none”" } : { region: "record", title: `identifier record: ${owner.get(i) ?? "?"}` });
  for (let i = idx + itop; i < cap - undo; i++) out.push({ region: "free", title: "free" });
  const undoCells: Cell[] = [];
  for (const u of s.undo) for (let k = 0; k < u.words; k++)
    undoCells.push({ region: u.kind === "mark" ? "undo-mark" : "undo", title: u.kind === "mark" ? "undo stack: scope mark" : `undo stack: ${u.kind} ${u.name}` });
  return out.concat(undoCells);
}

function undoLabel(u: UndoView, markDepth: number) {
  if (u.kind === "mark") return { tag: "mark", text: `${scopeName(markDepth)} begins`, words: u.words };
  if (u.kind === "new") return { tag: "new", text: `${u.name} · empty index slot ${u.slot} on exit`, words: u.words };
  return { tag: "shadow", text: `${u.name} · saved ${typeName(u.type)} ${formatValue(u.type, u.value)} (${scopeName(u.depth)})`, words: u.words };
}

export function MemoryInspector({ state }: { state: EngineState }) {
  const s = state.stats;
  const pct = (b: number) => `${(100 * b) / s.capacity}%`;
  const util = s.used / s.capacity;
  // Full: a call was refused for lack of memory and nothing has been freed since.
  const refusal = [...state.ops].reverse().find((o) => o.status === "kNoMemory");
  const full = !!refusal && s.used >= refusal.usedBytes;
  const label = full ? "Full" : util >= 0.8 ? "Near capacity" : "Available";
  const tone = full ? "error" : util >= 0.8 ? "warn" : "ok";
  const grid = cells(state);
  let markDepth = s.depth;

  return (
    <section className="card memory" aria-labelledby="memory-title">
      <div className="card-head">
        <h2 id="memory-title">Memory buffer</h2>
        <span className="card-hint">one fixed {fmt(s.capacity)} block · no heap allocation</span>
        <span className={`chip chip-${tone} push`}>{label}</span>
      </div>

      <div className="segbar" role="img" aria-label={`index ${s.index} bytes, records ${s.records} bytes, free ${s.free} bytes, undo stack ${s.undo} bytes`}>
        <div className="seg seg-index" style={{ width: pct(s.index) }} />
        <div className="seg seg-record" style={{ width: pct(s.records) }} />
        <div className="seg seg-free" style={{ width: pct(s.free) }} />
        <div className="seg seg-undo" style={{ width: pct(s.undo) }} />
      </div>
      <div className="seg-legend">
        <span><i className="sw sw-index" />Hash index <b className="mono">{s.index} B</b></span>
        <span><i className="sw sw-record" />Identifier records <b className="mono">{s.records} B</b> <em>→</em></span>
        <span><i className="sw sw-free" />Free <b className="mono">{s.free} B</b></span>
        <span><em>←</em> Undo stack <b className="mono">{s.undo} B</b><i className="sw sw-undo" /></span>
      </div>

      <div className="mem-body">
        <div className="words" style={{ gridTemplateColumns: `repeat(${Math.min(32, s.capacity / 4)}, 1fr)` }} aria-label="Buffer words">
          {grid.map((c, i) => (
            <span key={i} className={`w w-${c.region}`} title={`word ${i} · ${c.title}`} />
          ))}
        </div>
        <div className="undo-list">
          <div className="label">Undo stack · newest first</div>
          {state.undo.length === 0 && <p className="muted small">Empty. Declarations and scope marks are pushed here.</p>}
          <ol>
            {state.undo.slice(0, 9).map((u, i) => {
              const l = undoLabel(u, markDepth);
              if (u.kind === "mark") markDepth--;
              return (
                <li key={`${u.pos}-${i}`} className={`undo-item undo-${l.tag}`}>
                  <span className="undo-tag">{l.tag}</span>
                  <span className="undo-text mono">{l.text}</span>
                  <span className="undo-words mono">{l.words * 4} B</span>
                </li>
              );
            })}
          </ol>
          {state.undo.length > 9 && <p className="muted small">+ {state.undo.length - 9} older entries</p>}
        </div>
      </div>

      <div className="mem-stats">
        <div><span className="label">Capacity</span><b className="mono">{fmt(s.capacity)}</b></div>
        <div><span className="label">Used</span><b className="mono">{s.used} B</b></div>
        <div><span className="label">Free</span><b className="mono">{s.free} B</b></div>
        <div><span className="label">Peak used</span><b className="mono">{s.peak} B</b></div>
        <div className="util">
          <span className="label">Utilisation {(util * 100).toFixed(0)}%</span>
          <div className={`util-bar util-${tone}`}><div style={{ width: `${Math.min(100, util * 100)}%` }} /></div>
        </div>
      </div>
      <p className="footnote">
        Measured, not estimated: byte counts come from <code>strata::Table::stats()</code>; the layout is read back from the table's own buffer after every
        operation. Each cell is one 4-byte word. {s.indexSlots} index slots · table self-check {state.checks.invariants ? "passed" : "FAILED"}.
      </p>
    </section>
  );
}
