import recorded from "../data/recorded.json";
import { ChartCard, ForestPlot, LineChart } from "../components/charts";
import { compact, nf, traceLabel } from "../lib/format";

const fit = recorded.embeddedFit;
const bounded = recorded.embeddedBounded;
const flood = recorded.flood;
const sweep = recorded.sweep;
const ch = recorded.chibicc;

const FLOOD_SERIES: [string, string, string][] = [
  ["ordinary", "default", "Ordinary names"],
  ["colliding", "default", "Colliding names, default hash"],
  ["colliding", "keyed", "Colliding names, keyed hash"],
  ["colliding", "bounded_keyed", "Colliding names, keyed + probe limit"],
];
const floodNames = [...new Set(flood.map((f) => f.names))].sort((a, b) => a - b);
const floodAt = (input: string, config: string, n: number) => flood.find((f) => f.input === input && f.config === config && f.names === n);
const worst = floodAt("colliding", "default", floodNames[floodNames.length - 1])!;
const base = floodAt("ordinary", "default", floodNames[floodNames.length - 1])!;
const keyedBase = floodAt("ordinary", "keyed", floodNames[floodNames.length - 1])!;
const boundedRefusals = flood.filter((f) => f.input === "colliding" && f.config === "bounded").reduce((n, f) => n + f.refused, 0);

const sigmas = [...new Set(sweep.map((s) => s.sigma))].sort((a, b) => a - b);
const lengths = [...new Set(sweep.map((s) => s.L))].sort((a, b) => a - b);
const sweepAt = (sigma: number, L: number) => sweep.find((s) => s.sigma === sigma && s.L === L)!;
const timeVerdicts = lengths.map((L) => {
  const pts = sweep.filter((s) => s.L === L);
  return { L, faster: pts.filter((p) => (p.ciLow ?? 0) > 0).length, slower: pts.filter((p) => (p.ciHigh ?? 0) < 0).length, n: pts.length };
});

const fitPairs = [...new Set(fit.map((f) => `${f.trace}|${f.bufferKiB}`))].map((k) => {
  const [trace, kb] = k.split("|");
  const s = fit.find((f) => f.trace === trace && f.bufferKiB === Number(kb) && f.table === "STRATA")!;
  const a = fit.find((f) => f.trace === trace && f.bufferKiB === Number(kb) && f.table !== "STRATA")!;
  return { trace, kb: Number(kb), s, a };
});

function Fit({ ok, refused }: { ok: boolean; refused: number }) {
  return ok
    ? <span className="badge good"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6.2 5 8.5l4.5-5" /></svg>Fits</span>
    : <span className="badge bad"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 3l6 6M9 3 3 9" /></svg>Does not fit · {nf.format(refused)} refused</span>;
}

export function Stress() {
  return (
    <div className="stack">
      <header className="page-head">
        <h1>Stress tests</h1>
        <p>What happens outside the comfortable case: a microcontroller with 64 KiB of RAM, a second compiler, inputs built to collide in the hash
          table, heavy shadowing, and automated testing for correctness.</p>
      </header>

      <section aria-labelledby="emb-title">
        <h2 id="emb-title" className="section-title">Bare-metal Cortex-M3</h2>
        <p className="section-lede">{recorded.embeddedEnv.machine}; built with {recorded.embeddedEnv.compiler?.split(" (")[0]}, run under {recorded.embeddedEnv.emulator?.split(" (")[0]}. Emulated, not real hardware.</p>
        <div className="kpis kpis-4">
          <div className="card kpi"><span className="label">Bare-metal runs passed</span><b className="kpi-num">{bounded.filter((b) => b.pass && b.checksumMatches).length} of {bounded.length}</b><span className="kpi-sub">checksum equal to the desktop run, 0 refused operations</span></div>
          <div className="card kpi"><span className="label">STRATA code size</span><b className="kpi-num">{nf.format(bounded[0].codeBytes)} <small>bytes</small></b><span className="kpi-sub">sum of the strata:: functions in the object file</span></div>
          <div className="card kpi"><span className="label">Stack used</span><b className="kpi-num">{Math.max(...bounded.map((b) => b.stackBytes))} <small>bytes</small></b><span className="kpi-sub">bounded-mode build; no heap, no operating system</span></div>
          <div className="card kpi"><span className="label">Workloads only STRATA fits</span><b className="kpi-num">{fitPairs.filter((p) => p.s.fits && !p.a.fits).length}</b><span className="kpi-sub">same buffer, conventional table refuses</span></div>
        </div>
        <div className="grid-2">
          <article className="card">
            <div className="viz-head"><div><h3>Same buffer, two tables</h3><p className="viz-sub">Each workload replayed on the device with a fixed buffer. A refusal means the table ran out of room.</p></div></div>
            <div className="table-wrap">
              <table className="results-table">
                <thead><tr><th>Workload</th><th className="num">Buffer</th><th>STRATA</th><th>Conventional single-buffer</th></tr></thead>
                <tbody>{fitPairs.map((p) => (
                  <tr key={`${p.trace}${p.kb}`}>
                    <td>{traceLabel(p.trace)}</td><td className="num mono">{p.kb} KiB</td>
                    <td><Fit ok={p.s.fits} refused={p.s.refused} /><span className="sub">peak {nf.format(p.s.peakUsed)} B</span></td>
                    <td><Fit ok={p.a.fits} refused={p.a.refused} /><span className="sub">peak {nf.format(p.a.peakUsed)} B</span></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </article>
          <article className="card">
            <div className="viz-head"><div><h3>Bounded mode on the device</h3><p className="viz-sub">Static index, probe limit and keyed hash; every answer checksum-compared with the desktop run.</p></div></div>
            <div className="table-wrap">
              <table className="results-table">
                <thead><tr><th>Workload</th><th className="num">Operations</th><th className="num">Buffer</th><th className="num">Peak used</th><th className="num">Static RAM</th><th>Result</th></tr></thead>
                <tbody>{bounded.map((b) => (
                  <tr key={b.trace}>
                    <td>{traceLabel(b.trace)}</td><td className="num mono">{nf.format(b.ops)}</td><td className="num mono">{nf.format(b.bufferBytes)} B</td>
                    <td className="num mono">{nf.format(b.peakUsed)} B</td><td className="num mono">{nf.format(b.staticRam)} B</td>
                    <td><Fit ok={b.pass && b.checksumMatches} refused={b.refused} /></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </article>
        </div>
      </section>

      <section aria-labelledby="flood-title">
        <h2 id="flood-title" className="section-title">Hash flooding</h2>
        <p className="section-lede">
          Identifiers crafted to share one hash value make every declaration walk a long chain. At {nf.format(worst.names)} such names the default
          table took {(worst.declareMs / base.declareMs).toFixed(0)}× as long to declare them as ordinary names. The opt-in keyed hash removes the
          attack, at a cost of {Math.round(100 * (keyedBase.declareMs / base.declareMs - 1))}% on ordinary input.
        </p>
        <ChartCard
          title="Time to declare all names"
          sub="Median of 5 runs, 150-character identifiers. Lower is better."
          table={
            <table className="results-table">
              <thead><tr><th className="num">Names</th>{FLOOD_SERIES.map(([, , l]) => <th key={l} className="num">{l}</th>)}</tr></thead>
              <tbody>{floodNames.map((n) => (
                <tr key={n}><td className="num mono">{nf.format(n)}</td>{FLOOD_SERIES.map(([i, c, l]) => <td key={l} className="num mono">{floodAt(i, c, n)!.declareMs} ms</td>)}</tr>
              ))}</tbody>
            </table>
          }
          footer={<>The probe limit without the key ("bounded") instead refuses colliding names: {nf.format(boundedRefusals)} refusals over the runs, every answer still correct.</>}
        >
          <LineChart xs={floodNames} xLabel="names declared" xFormat={(v) => compact(v)} logX logY
            series={FLOOD_SERIES.map(([i, c, l]) => ({ label: l, values: floodNames.map((n) => floodAt(i, c, n)!.declareMs) }))}
            yFormat={(v) => (v >= 1000 ? `${+(v / 1000).toPrecision(3)} s` : v >= 1 ? `${+v.toPrecision(3)} ms` : `${+(v * 1000).toPrecision(3)} µs`)} yLabel="declare time" />
        </ChartCard>
      </section>

      <section aria-labelledby="sweep-title">
        <h2 id="sweep-title" className="section-title">Shadowing and name length</h2>
        <p className="section-lede">
          Synthetic traces with 4,096 live declarations where each name is shadowed σ times on average, with names of fixed length L. The real
          compiler traces sit at σ = 1. STRATA's memory saving grows with shadowing; its speed follows name length, not shadowing:{" "}
          {timeVerdicts.map((v, i) => <span key={v.L}>{i > 0 && "; "}L = {v.L}: faster at {v.faster}, slower at {v.slower} of {v.n}</span>)}.
        </p>
        <ChartCard
          title="Fixed-buffer saving against the single-buffer table"
          sub="Reduction of the smallest buffer, by shadowing factor σ (log spacing)."
          table={
            <table className="results-table">
              <thead><tr><th className="num">σ</th>{lengths.map((L) => <th key={L} className="num">L = {L}</th>)}{lengths.map((L) => <th key={`t${L}`} className="num">time, L = {L}</th>)}</tr></thead>
              <tbody>{sigmas.map((s) => (
                <tr key={s}><td className="num mono">{s}</td>
                  {lengths.map((L) => <td key={L} className="num mono">{sweepAt(s, L).savingPct}%</td>)}
                  {lengths.map((L) => { const p = sweepAt(s, L); return <td key={`t${L}`} className="num mono">{p.timePct}%<span className="sub">{p.ciLow} to {p.ciHigh}</span></td>; })}
                </tr>
              ))}</tbody>
            </table>
          }
          footer="Time: positive = STRATA faster than the single-buffer table, with the 95% interval."
        >
          <LineChart xs={sigmas} xLabel="shadowing factor σ" xFormat={(v) => `${v}`} logX
            series={lengths.map((L) => ({ label: `names of ${L} characters`, values: sigmas.map((s) => sweepAt(s, L).savingPct) }))}
            yFormat={(v) => `${Math.round(v)}%`} yLabel="buffer saved" />
        </ChartCard>
      </section>

      <section aria-labelledby="ch-title">
        <h2 id="ch-title" className="section-title">Inside a second compiler</h2>
        <p className="section-lede">STRATA and the single-buffer table were built into chibicc, a small C11 compiler, and used to compile {ch.projects.length} projects end to end, {parseInt(ch.rounds)} paired rounds each.</p>
        <div className="grid-2">
          <div className="kpis kpis-col">
            <div className="card kpi"><span className="label">Identical assembly output</span><b className="kpi-num">{ch.strataIdentical} of {ch.compiled}</b><span className="kpi-sub">source files compiled with STRATA inside chibicc, byte-for-byte equal to the original</span></div>
            <div className="card kpi"><span className="label">End-to-end effect</span><b className="kpi-num">none <small>established</small></b><span className="kpi-sub">symbol-table work is a small part of compiling, so whole-compile time does not improve</span></div>
          </div>
          <ChartCard
            title="Whole-compile time, STRATA against original chibicc"
            sub="Median paired difference per project with its 95% interval."
            table={
              <table className="results-table">
                <thead><tr><th>Project</th><th className="num">Files</th><th className="num">STRATA</th><th className="num">95% interval</th><th className="num">Single-buffer</th></tr></thead>
                <tbody>{ch.projects.map((p) => (
                  <tr key={p.project}><td>{traceLabel(p.project)}</td><td className="num mono">{p.units}</td><td className="num mono">{p.strataPct}%</td><td className="num mono">{p.strataCiLow} to {p.strataCiHigh}%</td><td className="num mono">{p.arenaPct}%</td></tr>
                ))}</tbody>
              </table>
            }
          >
            <ForestPlot rows={ch.projects.map((p) => ({ key: p.project, label: traceLabel(p.project), value: p.strataPct, low: p.strataCiLow, high: p.strataCiHigh, detail: `${p.units} files` }))} negLabel="slower" posLabel="faster" />
          </ChartCard>
        </div>
      </section>

      <section aria-labelledby="tests-title">
        <h2 id="tests-title" className="section-title">Correctness testing</h2>
        <div className="kpis kpis-4">
          {recorded.tests.map((t) => (
            <div className="card kpi" key={t.label}>
              <span className="label">{t.label}</span>
              <b className="kpi-num">{"of" in t ? `${t.value} of ${t.of}` : t.value < 1e7 ? nf.format(t.value) : `${t.value / 1e6} million`}</b>
              <span className="kpi-sub">{t.note} · <code>{t.source}</code></span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
