// Proposition 12 on a concrete table: a trunk of persistent names, a window of L cells with at most s-1 empty cells,
// and the short chain of pushes that gets a fresh name refused. Then the simulated probability against the bound.
import { useMemo, useState } from "react";
import { attackChain, churnBound, mulberry32, randomTrunk, replayChain, vulnerabilityMonteCarlo, windowEmpties } from "../../lib/theory";

const M = 96;
const MC_TRIALS = 5000;
const SIZE = 400, C = SIZE / 2, RAD = 150, R = 4.1;
const pos = (c: number, r = RAD) => {
  const a = (2 * Math.PI * c) / M - Math.PI / 2;
  return { x: C + r * Math.cos(a), y: C + r * Math.sin(a) };
};
const fmt = (p: number) => (p === 0 ? "0" : p >= 0.001 ? p.toFixed(3) : p.toExponential(2));

export function WindowLab() {
  const [alpha, setAlpha] = useState(0.75);
  const [L, setL] = useState(30);
  const [s, setS] = useState(2);
  const [seed, setSeed] = useState(4);
  const [replayed, setReplayed] = useState(false);
  const [mc, setMc] = useState<{ v: number; se: number; trials: number } | null>(null);
  const [searchNote, setSearchNote] = useState<string | null>(null);
  const n = Math.floor(alpha * M);

  const occ = useMemo(() => randomTrunk(M, n, mulberry32(seed)), [n, seed]);
  const view = useMemo(() => {
    const w = windowEmpties(occ, L);
    let best = 0;
    for (let i = 1; i < M; i++) if (w[i] < w[best]) best = i;
    const chain = attackChain(occ, L, s);
    return { best, empties: w[best], chain, steps: chain ? replayChain(occ, L, chain) : null };
  }, [occ, L, s]);
  const bound = useMemo(() => churnBound(M, n, s, L), [n, s, L]);

  const inWindow = new Set(Array.from({ length: L }, (_, t) => (view.best + t) % M));
  const filled = new Set(replayed && view.steps ? view.steps.filter((x) => x.result >= 0).map((x) => x.result) : []);
  const vulnerable = view.chain !== null;
  const refused = replayed && view.steps && view.steps[view.steps.length - 1].result === -1;

  const findVulnerable = () => {
    for (let k = 1; k <= 600; k++) {
      if (attackChain(randomTrunk(M, n, mulberry32(seed + k)), L, s)) { setSeed(seed + k); setReplayed(false); setMc(null); setSearchNote(null); return; }
    }
    setSearchNote("No vulnerable table among 600 draws at these settings: lower L or raise s.");
  };
  const touch = <T,>(f: (v: T) => void) => (v: T) => { f(v); setReplayed(false); setMc(null); setSearchNote(null); };

  return (
    <div className="th-lab">
      <div className="th-lab-main">
        <div className="card th-ringcard">
          <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="th-ring" role="img" aria-label="Ring of 96 cells; the densest window is highlighted">
            {Array.from({ length: M }, (_, c) => {
              const p = pos(c);
              const full = occ[c] || filled.has(c);
              return <circle key={c} cx={p.x} cy={p.y} r={R} fill={full ? (filled.has(c) && !occ[c] ? "var(--c-undo)" : "var(--c-record)") : "var(--c-free)"}
                stroke={inWindow.has(c) ? (vulnerable ? "var(--error)" : "var(--accent)") : "none"} strokeWidth={inWindow.has(c) ? 2.4 : 0} />;
            })}
            <text x={C} y={C - 8} textAnchor="middle" className="th-center">{view.empties} empty</text>
            <text x={C} y={C + 12} textAnchor="middle" className="th-center-sub">in the densest {L}-cell window</text>
            <text x={C} y={C + 30} textAnchor="middle" className="th-center-sub">starting at cell {view.best}</text>
          </svg>
          <div className="th-legend">
            <span><i style={{ background: "var(--c-record)" }} />occupied by a persistent name</span>
            <span><i style={{ background: "var(--c-undo)" }} />filled by the chain</span>
            <span><i className="th-ring-bad" />densest window</span>
          </div>
        </div>
      </div>

      <div className="th-lab-side">
        <div className="card th-controls">
          <div className="th-grid-inputs one">
            <label className="field"><span className="th-label">Load α = {alpha.toFixed(2)} <small>({n} persistent names in {M} cells)</small></span>
              <input type="range" min={0.4} max={0.9} step={0.05} value={alpha} onChange={(e) => touch(setAlpha)(+e.target.value)} /></label>
            <label className="field"><span className="th-label">Probe limit L = {L}</span>
              <input type="range" min={4} max={40} value={L} onChange={(e) => touch(setL)(+e.target.value)} /></label>
            <label className="field"><span className="th-label">Churn depth s = {s} <small>(at most s−1 = {s - 1} empty cells allowed in the window)</small></span>
              <input type="range" min={1} max={8} value={s} onChange={(e) => touch(setS)(+e.target.value)} /></label>
          </div>
          <div className="th-row">
            <button className="btn small" onClick={() => touch(setSeed)(seed + 1)}>New random table</button>
            <button className="btn small" onClick={findVulnerable}>Draw a vulnerable table</button>
            {searchNote && <span className="th-hint">{searchNote}</span>}
          </div>
        </div>

        <div className={`th-verdict ${vulnerable ? "bad" : "ok"}`}>
          {vulnerable
            ? <>This table is <b>{s}-vulnerable</b>: a window of {L} cells has only {view.empties} empty cell{view.empties === 1 ? "" : "s"}. A schedule of {view.chain!.fills.length + 1} push{view.chain!.fills.length ? "es" : ""} gets a fresh name refused.</>
            : <>This table is <b>not {s}-vulnerable</b>: every window of {L} cells has at least {s} empty cells, so no schedule that keeps at most {s} names live above it can be refused.</>}
        </div>

        <div className="card th-controls">
          <div className="th-row">
            <button className="btn btn-primary small" onClick={() => setReplayed(true)} disabled={!vulnerable}>Run the chain on a probe-limited table</button>
            {!vulnerable && <span className="th-hint">This table has no refusing chain. Lower L, raise s, or draw a vulnerable table.</span>}
            {replayed && <button className="btn btn-ghost small" onClick={() => setReplayed(false)}>Clear</button>}
          </div>
          {replayed && view.steps && (
            <ol className="th-steps">
              {view.steps.map((x, i) => (
                <li key={i} className={x.result < 0 ? "bad" : ""}>
                  push with home {x.home}: {x.result >= 0 ? `stored in cell ${x.result}` : <b>refused (all {L} cells from the home are occupied)</b>}
                </li>
              ))}
            </ol>
          )}
          {refused && <p className="th-note th-note-bad">The last push is refused, as Proposition 12(b) constructs: fill the empty cells of the window with names whose home is that cell, then push at the window&rsquo;s first cell.</p>}
        </div>

        <div className="card th-controls">
          <div className="th-row">
            <button className="btn small" onClick={() => { const v = vulnerabilityMonteCarlo(M, n, L, s, MC_TRIALS, seed * 7 + 1); setMc({ v, se: Math.sqrt(Math.max(v * (1 - v), 1e-6) / MC_TRIALS), trials: MC_TRIALS }); }}>Estimate over {MC_TRIALS} random tables</button>
          </div>
          <div className="th-stats flat">
            <div className="th-stat"><span>Simulated probability that a table is {s}-vulnerable</span><b>{mc ? <>{fmt(mc.v)}<small> ± {fmt(1.96 * mc.se)} (95%)</small></> : "–"}</b></div>
            <div className="th-stat"><span>Closed-form bound D<sub>{s}</sub> (Proposition 12c)</span><b>{fmt(bound)}</b></div>
          </div>
          <p className="th-foot">The bound is an upper bound on the exact vulnerability probability. The simulated value carries sampling error, so when the bound is tight the estimate can exceed it by up to the interval shown. This vulnerability probability is the supremum, over all schedules, of the chance of any refusal.</p>
        </div>
      </div>
    </div>
  );
}
