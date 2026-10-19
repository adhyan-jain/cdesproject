import { useState } from "react";
import recorded from "../data/recorded.json";
import { BarList, ChartCard, ForestPlot, PairedColumns } from "../components/charts";
import { LiveCheck } from "../components/LiveCheck";
import { compact, nf, TRACE_BLURB, traceLabel } from "../lib/format";

type Trace = (typeof recorded.perTrace)[number];

export function Benchmarks({ ready }: { ready: boolean }) {
  const [sel, setSel] = useState("sqlite");
  const t = recorded.perTrace.find((p) => p.trace === sel)! as Trace;
  const rows = (pick: (r: Trace["tables"][number]) => number) =>
    [...t.tables].sort((a, b) => pick(a) - pick(b)).map((r) => ({ key: r.impl, label: r.short, value: pick(r), highlight: r.impl === "strata", detail: r.label }));
  const fullTable = (
    <table className="results-table">
      <thead><tr><th>Table</th><th className="num">Peak heap</th><th className="num">Allocator calls</th><th className="num">Replay (median)</th><th className="num">Lookup p95</th><th className="num">Declare p95</th><th className="num">Wrong</th></tr></thead>
      <tbody>
        {t.tables.map((r) => (
          <tr key={r.impl} className={r.impl === "strata" ? "row-hl" : ""}>
            <td>{r.label}</td>
            <td className="num mono">{r.peakKiB} KiB</td>
            <td className="num mono">{nf.format(r.allocs)}</td>
            <td className="num mono">{r.replayMs} ms<span className="sub">{r.replayMinMs}–{r.replayMaxMs}</span></td>
            <td className="num mono">{r.lookupP95} ns</td>
            <td className="num mono">{r.declareP95} ns</td>
            <td className="num mono">{r.wrong}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div className="stack">
      <header className="page-head">
        <h1>Benchmarks</h1>
        <p>
          Recorded run <code>{recorded.run}</code>: {parseInt(recorded.rounds)} paired, interleaved rounds per trace on {recorded.cpu.replace(/\(R\)|\(TM\)/g, "")}, {recorded.compiler.replace(/ \(.*\)/, "")},
          WSL 2. Every figure on this page is read from <code>results/</code> by <code>frontend/web/scripts/make-results.mjs</code>; none is typed in.
        </p>
      </header>

      <section aria-labelledby="per-trace">
        <div className="filter-row" role="tablist" aria-label="Compiler trace">
          {recorded.perTrace.map((p) => (
            <button key={p.trace} role="tab" aria-selected={p.trace === sel} className={`trace-chip ${p.trace === sel ? "on" : ""}`} onClick={() => setSel(p.trace)}>
              {traceLabel(p.trace)}
            </button>
          ))}
        </div>

        <div className="trace-strip card">
          <div>
            <h2 id="per-trace">{traceLabel(t.trace)} <span className="muted">· {TRACE_BLURB[t.trace]}</span></h2>
            <p className="muted small">Symbol-table calls the Tiny C Compiler made while compiling {t.units} source file{t.units > 1 ? "s" : ""} of this project.</p>
          </div>
          <dl className="facts">
            <div><dt>Operations</dt><dd>{nf.format(t.ops)}</dd></div>
            <div><dt>Declarations</dt><dd>{nf.format(t.declares)}</dd></div>
            <div><dt>Lookups</dt><dd>{nf.format(t.lookups)}</dd></div>
            <div><dt>Scopes opened</dt><dd>{nf.format(t.scopes)}</dd></div>
            <div><dt>Distinct names</dt><dd>{nf.format(t.distinctNames)}</dd></div>
            <div><dt>Max depth</dt><dd>{t.maxDepth}</dd></div>
            <div><dt>Wrong answers</dt><dd className={t.wrong === 0 ? "ok-text" : ""}>{t.wrong}</dd></div>
          </dl>
        </div>

        <div className="grid-3">
          <ChartCard title="Peak memory" sub="Most heap held at any moment while replaying the trace. Lower is better." table={fullTable}>
            <BarList rows={rows((r) => r.peakKiB)} format={(v) => `${v.toFixed(1)} KiB`} axisLabel="KiB" />
          </ChartCard>
          <ChartCard title="Allocator calls" sub="malloc/new calls during the replay. Lower is better; note the log scale." table={fullTable}>
            <BarList rows={rows((r) => r.allocs)} format={(v) => compact(v)} log axisLabel="calls" />
          </ChartCard>
          <ChartCard title="Replay time" sub={`Median of ${t.reps} rounds for the whole trace. Lower is better.`} table={fullTable}>
            <BarList rows={rows((r) => r.replayMs)} format={(v) => `${v.toFixed(2)} ms`} axisLabel="ms" />
          </ChartCard>
        </div>
      </section>

      <section aria-labelledby="fair-title">
        <h2 id="fair-title" className="section-title">Against the fair baseline</h2>
        <p className="section-lede">
          Most of the saving over std::unordered_map comes from using one buffer at all. The fair comparison is therefore a conventional
          allocator-free single-buffer table (hash chains in an arena), given the smallest buffer each one needs.
        </p>
        <div className="grid-2">
          <ChartCard
            title="Smallest fixed buffer that holds the trace"
            sub={`Found by search for each table. STRATA needs ${Math.round(Math.min(...recorded.perTrace.map((p) => p.bufferReductionPct)))}–${Math.round(Math.max(...recorded.perTrace.map((p) => p.bufferReductionPct)))}% less on every trace.`}
            table={
              <table className="results-table">
                <thead><tr><th>Trace</th><th className="num">STRATA</th><th className="num">Single-buffer</th><th className="num">Smaller by</th></tr></thead>
                <tbody>{recorded.perTrace.map((p) => (
                  <tr key={p.trace}><td>{traceLabel(p.trace)}</td><td className="num mono">{p.strataBufferKiB} KiB</td><td className="num mono">{p.arenaBufferKiB} KiB</td><td className="num mono">{p.bufferReductionPct}%</td></tr>
                ))}</tbody>
              </table>
            }
          >
            <PairedColumns
              categories={recorded.perTrace.map((p) => ({ key: p.trace, label: traceLabel(p.trace) }))}
              series={[
                { label: "STRATA", values: recorded.perTrace.map((p) => p.strataBufferKiB) },
                { label: "Conventional single-buffer", values: recorded.perTrace.map((p) => p.arenaBufferKiB) },
              ]}
              format={(v) => `${v.toFixed(1)} KiB`}
              axisLabel="KiB"
            />
          </ChartCard>
          <ChartCard
            title="Replay time against the single-buffer table"
            sub="Median paired difference with its 95% interval. An interval that crosses zero means no established difference."
            table={
              <table className="results-table">
                <thead><tr><th>Trace</th><th className="num">Difference</th><th className="num">95% interval</th><th className="num">STRATA</th><th className="num">Single-buffer</th></tr></thead>
                <tbody>{recorded.perTrace.map((p) => (
                  <tr key={p.trace}><td>{traceLabel(p.trace)}</td><td className="num mono">{p.timeVsArenaPct > 0 ? "+" : ""}{p.timeVsArenaPct}%</td><td className="num mono">{p.ciLow} to {p.ciHigh}%</td><td className="num mono">{p.strataMs} ms</td><td className="num mono">{p.arenaMs} ms</td></tr>
                ))}</tbody>
              </table>
            }
            footer="Positive = STRATA faster. Interval from the paired rounds of the recorded run."
          >
            <ForestPlot
              rows={recorded.perTrace.map((p) => ({ key: p.trace, label: traceLabel(p.trace), value: p.timeVsArenaPct, low: p.ciLow, high: p.ciHigh, detail: `${p.strataMs} vs ${p.arenaMs} ms` }))}
              negLabel="slower" posLabel="faster"
            />
          </ChartCard>
        </div>
      </section>

      <section aria-labelledby="live-title">
        <h2 id="live-title" className="section-title">Check it live</h2>
        <LiveCheck ready={ready} />
      </section>
    </div>
  );
}
