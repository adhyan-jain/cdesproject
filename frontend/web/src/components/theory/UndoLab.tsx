// Theorems 2 and 4 and Proposition 5, played on a small ring of cells: pop the newest key and the table is exactly
// what inserting the live keys would give; clear any other key and the keys that probed past it are lost.
import { useMemo, useRef, useState } from "react";
import { cloneRing, dependents, emptyRing, findable, mulberry32, orphanMean, rebuild, ringClear, ringInsert, sameCells, type Ring } from "../../lib/theory";

const M = 24;
const SIZE = 380, C = SIZE / 2, RAD = 148, CELL = 15;
const pos = (c: number, r = RAD) => {
  const a = (2 * Math.PI * c) / M - Math.PI / 2;
  return { x: C + r * Math.cos(a), y: C + r * Math.sin(a) };
};
const hue = (id: number) => (id * 47) % 360;

interface State { ring: Ring; next: number; note: string; tone: "info" | "ok" | "bad" }
const START = "Push some keys, then try the two ways of removing one.";

export function UndoLab() {
  const rnd = useRef(mulberry32(3));
  const [st, setSt] = useState<State>({ ring: emptyRing(M), next: 1, note: START, tone: "info" });
  const [sel, setSel] = useState<number | null>(null);
  const [homeInput, setHomeInput] = useState("");

  const { ring } = st;
  const info = useMemo(() => {
    const lost = ring.keys.filter((k) => !findable(ring, k)).map((k) => k.id);
    const dep = new Map(ring.keys.map((k) => [k.id, dependents(ring, k)]));
    const mean = ring.keys.length ? [...dep.values()].reduce((s, d) => s + d.length, 0) / ring.keys.length : 0;
    return { lost, dep, mean, same: sameCells(ring, rebuild(ring)) };
  }, [ring]);
  const alpha = ring.keys.length / M;

  const push = (home?: number) => {
    if (ring.keys.length >= M - 1) return setSt({ ...st, note: "The ring keeps one cell empty so that lookups end; clear a key first.", tone: "info" });
    const r = cloneRing(ring);
    const h = home ?? Math.floor(rnd.current() * M);
    const res = ringInsert(r, st.next, h);
    setSt({ ring: r, next: st.next + 1, note: `Pushed k${st.next}: home ${h}, stored in cell ${res.cell}${res.probes ? ` (probed ${res.probes} occupied cell${res.probes > 1 ? "s" : ""})` : ""}.`, tone: "info" });
  };
  const fill = () => {
    const r = cloneRing(ring); let id = st.next;
    while (r.keys.length < Math.round(0.7 * M)) ringInsert(r, id++, Math.floor(rnd.current() * M));
    setSt({ ring: r, next: id, note: "Filled to about 70% load with random homes.", tone: "info" });
  };
  const remove = (which: "newest" | "oldest" | "random") => {
    if (!ring.keys.length) return;
    const idx = which === "newest" ? ring.keys.length - 1 : which === "oldest" ? 0 : Math.floor(rnd.current() * ring.keys.length);
    const victim = ring.keys[idx];
    const r = cloneRing(ring);
    ringClear(r, victim.id);
    const lost = r.keys.filter((k) => !findable(r, k));
    const same = sameCells(r, rebuild(r));
    if (which === "newest") {
      setSt({ ring: r, next: st.next, tone: "ok", note: `Popped k${victim.id}, the newest key. Theorem 2: the table is exactly what inserting the remaining ${r.keys.length} keys gives (${same ? "checked ✓" : "MISMATCH"}).` });
    } else if (lost.length) {
      setSt({ ring: r, next: st.next, tone: "bad", note: `Cleared k${victim.id}, not the newest key. ${lost.length} key${lost.length > 1 ? "s" : ""} (${lost.map((k) => "k" + k.id).join(", ")}) can no longer be found: their lookups stop at the hole it left.` });
    } else {
      setSt({ ring: r, next: st.next, tone: "info", note: `Cleared k${victim.id}, not the newest key. No live key depended on it, so this time nothing broke${same ? "" : " (but the table no longer equals the insertion of the live keys)"}.` });
    }
    setSel(null);
  };
  const reset = () => { rnd.current = mulberry32(3); setSel(null); setSt({ ring: emptyRing(M), next: 1, note: START, tone: "info" }); };

  const selKey = ring.keys.find((k) => k.id === sel) ?? null;
  const selDeps = new Set(selKey ? info.dep.get(selKey.id) : []);
  const lostSet = new Set(info.lost);

  return (
    <div className="th-lab">
      <div className="th-lab-main">
        <div className="card th-ringcard">
          <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="th-ring" role="img" aria-label="Ring of 24 cells with the live keys">
            {Array.from({ length: M }, (_, c) => {
              const p = pos(c), id = ring.cells[c], key = ring.keys.find((k) => k.id === id);
              const q = pos(c, RAD + 26);
              return (
                <g key={c}>
                  <circle cx={p.x} cy={p.y} r={CELL} fill={id === -1 ? "var(--c-free)" : `hsl(${hue(id)} 55% 78%)`}
                    stroke={lostSet.has(id) ? "var(--error)" : selDeps.has(id) ? "var(--c-undo)" : id === sel ? "var(--accent)" : "var(--border-strong)"}
                    strokeWidth={lostSet.has(id) || selDeps.has(id) || id === sel ? 3 : 1} />
                  {key && <text x={p.x} y={p.y + 4} textAnchor="middle" className="th-cell-label">{key.id}</text>}
                  <text x={q.x} y={q.y + 3} textAnchor="middle" className="th-cell-index">{c}</text>
                </g>
              );
            })}
            {selKey && (() => {
              const a = pos(selKey.home, RAD - 30), b = pos(selKey.cell, RAD - 30);
              const span = (selKey.cell - selKey.home + M) % M;
              return (
                <g>
                  <path d={`M ${a.x} ${a.y} A ${RAD - 30} ${RAD - 30} 0 ${span > M / 2 ? 1 : 0} 1 ${b.x} ${b.y}`} fill="none" stroke="var(--accent)" strokeWidth="2" strokeDasharray="4 3" />
                  <circle cx={a.x} cy={a.y} r="4" fill="var(--accent)" />
                  <text x={C} y={C - 4} textAnchor="middle" className="th-center">k{selKey.id}</text>
                  <text x={C} y={C + 14} textAnchor="middle" className="th-center-sub">home {selKey.home} → cell {selKey.cell}</text>
                </g>
              );
            })()}
            {!selKey && <text x={C} y={C + 4} textAnchor="middle" className="th-center-sub">{ring.keys.length} keys · load {alpha.toFixed(2)}</text>}
          </svg>
          <div className="th-legend">
            <span><i style={{ background: "hsl(210 55% 78%)" }} />live key</span>
            <span><i className="th-ring-bad" />lost (lookup fails)</span>
            <span><i className="th-ring-dep" />depends on the selected key</span>
          </div>
        </div>
      </div>

      <div className="th-lab-side">
        <div className="card th-controls">
          <div className="th-row">
            <button className="btn btn-primary small" onClick={() => push()}>Push random key</button>
            <input className="th-num" aria-label="Home cell" inputMode="numeric" placeholder="home" value={homeInput} onChange={(e) => setHomeInput(e.target.value.replace(/\D/g, "").slice(0, 2))} />
            <button className="btn small" onClick={() => { const h = Number(homeInput); if (homeInput !== "" && h < M) push(h); }} disabled={homeInput === "" || Number(homeInput) >= M}>Push at home</button>
            <button className="btn small" onClick={fill}>Fill to 70%</button>
          </div>
          <div className="th-row">
            <button className="btn small" onClick={() => remove("newest")} disabled={!ring.keys.length}>Pop newest (stack order)</button>
            <button className="btn small" onClick={() => remove("oldest")} disabled={!ring.keys.length}>Clear oldest</button>
            <button className="btn small" onClick={() => remove("random")} disabled={!ring.keys.length}>Clear a random key</button>
            <button className="btn btn-ghost small" onClick={reset}>Reset</button>
          </div>
          <p className={`th-note th-note-${st.tone}`} role="status">{st.note}</p>
        </div>

        <div className="th-stats">
          <div className="th-stat"><span>Table equals the insertion of the live keys</span><b className={info.same ? "ok" : "bad"}>{info.same ? "yes ✓" : "no ✗"}</b></div>
          <div className="th-stat"><span>Live keys no longer found</span><b className={info.lost.length ? "bad" : "ok"}>{info.lost.length}</b></div>
          <div className="th-stat"><span>Mean keys that depend on a key</span><b>{info.mean.toFixed(2)}<small> · limit law at this load {alpha > 0 && alpha < 1 ? orphanMean(alpha).toFixed(2) : "–"}</small></b></div>
        </div>

        <div className="card th-table-card">
          <table className="th-table">
            <thead><tr><th>key</th><th>home</th><th>cell</th><th>probed</th><th>depend on it</th></tr></thead>
            <tbody>
              {ring.keys.length === 0 && <tr><td colSpan={5} className="th-empty">No keys yet.</td></tr>}
              {ring.keys.map((k) => (
                <tr key={k.id} className={k.id === sel ? "on" : lostSet.has(k.id) ? "lost" : ""} onClick={() => setSel(k.id === sel ? null : k.id)}>
                  <td><i className="th-dot" style={{ background: `hsl(${hue(k.id)} 55% 78%)` }} />k{k.id}</td>
                  <td className="mono">{k.home}</td>
                  <td className="mono">{k.cell}</td>
                  <td className="mono">{(k.cell - k.home + M) % M}</td>
                  <td className="mono">{info.dep.get(k.id)?.length ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="th-foot">
          Click a key to see its probe path. A key is <b>safe to clear first</b> only if nothing depends on it (Theorem 4a); the <b>newest</b> key never
          has dependents, which is why stack order is exact (Theorem 2) and the only order that is safe for every table (Theorem 4b). Table of {M} cells, linear probing; this is a model of the scheme in the paper, not the C++ engine.
        </p>
      </div>
    </div>
  );
}
