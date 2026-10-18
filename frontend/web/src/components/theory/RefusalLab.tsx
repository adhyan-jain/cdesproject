// Theorem 7, Proposition 11 and Proposition 12 as calculators: the exact refusal probability of one push, the chance that a
// table can ever refuse a fresh name, and the schedule-free bound for a persistent set of names with bounded churn above it.
import { useEffect, useRef, useState } from "react";
import { compute } from "../../lib/theoryClient";
import type { TheoryResult } from "../../lib/theoryJobs";
import tables from "../../data/paper-tables.json";

const SIZES = [256, 1024, 4096];
const EPS = [1e-2, 1e-4, 1e-6];
const fmt = (p: number) => (p === 0 ? "0" : p >= 0.001 ? p.toFixed(p >= 0.1 ? 3 : 4) : p.toExponential(2));
const SUP: Record<string, string> = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
const fmtEps = (e: number) => "10" + String(Math.round(Math.log10(e))).replace(/./g, (c) => SUP[c]);

type Point = Extract<TheoryResult, { kind: "point" }>;
type Design = Extract<TheoryResult, { kind: "design" }>;

export function RefusalLab() {
  const [m, setM] = useState(1024);
  const [alpha, setAlpha] = useState(0.75);
  const [L, setL] = useState(130);
  const [s, setS] = useState(2);
  const [eps, setEps] = useState(1e-4);
  const [point, setPoint] = useState<Point | null>(null);
  const [design, setDesign] = useState<Design | null>(null);
  const [busy, setBusy] = useState<"point" | "design" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ticket = useRef(0);
  const n = Math.floor(alpha * m);

  useEffect(() => {
    const my = ++ticket.current;
    setBusy("point"); setError(null);
    const t = setTimeout(() => {
      compute({ kind: "point", m, n, L, s })
        .then((r) => { if (my === ticket.current && r.kind === "point") setPoint(r); })
        .catch((e: Error) => { if (my === ticket.current) setError(e.message); })
        .finally(() => { if (my === ticket.current) setBusy(null); });
    }, 120);
    return () => clearTimeout(t);
  }, [m, n, L, s]);

  const findL = () => {
    setBusy("design"); setError(null);
    compute({ kind: "design", m, n, s, eps })
      .then((r) => { if (r.kind === "design") setDesign(r); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(null));
  };

  return (
    <div className="th-calc">
      <div className="card th-inputs">
        <div className="th-grid-inputs">
          <label className="field"><span className="th-label">Index slots m</span>
            <select value={m} onChange={(e) => { setM(+e.target.value); setDesign(null); }}>{SIZES.map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="field"><span className="th-label">Load α = {alpha.toFixed(2)} <small>(n = {n} keys)</small></span>
            <input type="range" min={0.3} max={0.9} step={0.05} value={alpha} onChange={(e) => { setAlpha(+e.target.value); setDesign(null); }} /></label>
          <label className="field"><span className="th-label">Probe limit L = {L}</span>
            <input type="range" min={10} max={Math.min(m, 400)} step={1} value={L} onChange={(e) => setL(+e.target.value)} /></label>
          <label className="field"><span className="th-label">Churn depth s = {s} <small>(live names above the persistent ones)</small></span>
            <input type="range" min={1} max={8} step={1} value={s} onChange={(e) => { setS(+e.target.value); setDesign(null); }} /></label>
        </div>
      </div>

      {error && <div className="card offline" role="alert">{error}</div>}

      <div className="th-metrics" aria-busy={busy === "point"}>
        <div className="card th-metric">
          <h3>One fresh name is refused</h3>
          <div className="th-big">{point ? fmt(point.refusal) : "…"}</div>
          <p>Theorem 7: the exact probability that the <i>L</i> cells from a new name&rsquo;s home are all occupied. A classical quantity; the exact finite-size form and its use as a design rule are the paper&rsquo;s.</p>
        </div>
        <div className="card th-metric">
          <h3>Some fresh name <i>can</i> be refused</h3>
          <div className="th-big">{point ? fmt(point.unlimited) : "…"}</div>
          <p>Proposition 11: the probability that the table holds a block longer than <i>L</i>. If it does, enough push/pop pairs will eventually hit it, so this is the failure chance of an unlimited run at this occupancy.</p>
        </div>
        <div className="card th-metric accent">
          <h3>Refusal anywhere, with churn depth {s}</h3>
          <div className="th-big">≤ {point ? fmt(point.churn) : "…"}</div>
          <p>Proposition 12: for <b>every</b> schedule that keeps at most {s} names live above these {n}, however long it runs. It is the supremum over schedules, reached as the schedule repeats fresh chains.</p>
        </div>
      </div>
      <p className="th-foot">Ordering check: one push &le; can-ever-refuse &le; churn bound (for s=1 the last two coincide up to the bound&rsquo;s slack). Computed in your browser from the paper&rsquo;s formulas{busy === "point" ? " …" : ""}; the same code is compared with the Python reference in <code>npm test</code>.</p>

      <div className="card th-design">
        <div className="th-design-head">
          <h3>Smallest probe limit for a target</h3>
          <label className="field inline"><span className="th-label">failure probability</span>
            <select value={eps} onChange={(e) => { setEps(+e.target.value); setDesign(null); }}>{EPS.map((x) => <option key={x} value={x}>{fmtEps(x)}</option>)}</select></label>
          <button className="btn btn-primary small" onClick={findL} disabled={busy === "design"}>{busy === "design" ? "Searching…" : `Find L for m=${m}, α=${alpha.toFixed(2)}, s=${s}`}</button>
        </div>
        {design && (
          <div className="th-design-out">
            <div><span>one push</span><b>{design.onePush}</b></div>
            <div><span>unlimited run</span><b>{design.unlimited}</b><small>+{design.unlimited - design.onePush}</small></div>
            <div><span>churn depth {s}</span><b>{design.churn}</b><small>+{design.churn - design.unlimited}</small></div>
          </div>
        )}
      </div>

      <div className="th-tables">
        <div className="card">
          <h3 className="th-tt">Paper table: probe limit at load 3/4</h3>
          <table className="th-table">
            <thead><tr><th>m</th><th>ε</th><th>one push</th><th>unlimited run</th><th>extra</th></tr></thead>
            <tbody>{tables.sustain.map((r) => <tr key={`${r.m}-${r.eps}`}><td className="mono">{r.m}</td><td className="mono">{fmtEps(r.eps)}</td><td className="mono">{r.onePush}</td><td className="mono">{r.unlimited}</td><td className="mono">+{r.extra}</td></tr>)}</tbody>
          </table>
        </div>
        <div className="card">
          <h3 className="th-tt">Paper table: price of churn depth s</h3>
          <table className="th-table">
            <thead><tr><th>m</th><th>ε</th>{tables.band.s.map((x) => <th key={x}>s={x}</th>)}</tr></thead>
            <tbody>{tables.band.rows.map((r) => <tr key={`${r.m}-${r.eps}`}><td className="mono">{r.m}</td><td className="mono">{fmtEps(r.eps)}</td>{r.L.map((v, i) => <td key={i} className="mono">{v}</td>)}</tr>)}</tbody>
          </table>
        </div>
      </div>
      <p className="th-foot">Both tables are generated from the manuscript&rsquo;s table files by <code>npm run theory-data</code>; the buttons above recompute any other point. For m=4096 the search takes a few seconds.</p>
    </div>
  );
}
