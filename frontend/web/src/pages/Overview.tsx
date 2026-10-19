import recorded from "../data/recorded.json";
import { BarList, ChartCard } from "../components/charts";
import { nf, compact } from "../lib/format";
import type { Page } from "../components/Header";

const strata = recorded.correctness.find((c) => c.impl === "strata")!;
const std = recorded.vsAll.find((v) => v.impl === "std_undo_log")!;
const arena = recorded.vsAll.find((v) => v.impl === "arena_chain")!;
const allocCut = recorded.perTrace.map((t) => 100 * (1 - t.strataAllocs / t.stdAllocs));
const bufCut = recorded.perTrace.map((t) => t.bufferReductionPct);
const totalOps = recorded.perTrace.reduce((n, t) => n + t.ops, 0);
const fits = recorded.embeddedFit;
const fitTraces = [...new Set(fits.filter((f) => f.table === "STRATA" && f.fits).map((f) => f.trace))]
  .filter((t) => fits.some((f) => f.trace === t && f.table !== "STRATA" && !f.fits && f.bufferKiB === fits.find((g) => g.trace === t && g.table === "STRATA")!.bufferKiB));

const verdict = (v: (typeof recorded.vsAll)[number]) =>
  v.faster === v.traces ? `${Math.round(v.timeMin)}–${Math.round(v.timeMax)}% faster` :
  v.slower === v.traces ? `${Math.round(-v.timeMax)}–${Math.round(-v.timeMin)}% slower` :
  v.faster === 0 && v.slower <= 2 ? "no reliable difference" : `mixed (median ${Math.abs(v.timeMedian).toFixed(1)}% ${v.timeMedian < 0 ? "slower" : "faster"})`;

export function Overview({ go }: { go: (p: Page) => void }) {
  const memRows = recorded.vsAll
    .filter((v) => v.impl !== "arena_chain")
    .map((v) => ({ key: v.impl, label: v.short, value: v.heapMedian, detail: `range ${Math.round(v.heapMin)}–${Math.round(v.heapMax)}% over 8 traces` }))
    .sort((a, b) => b.value - a.value);
  return (
    <div className="stack">
      <section className="hero">
        <div className="hero-text">
          <p className="eyebrow">Compiler design project · VIT Vellore</p>
          <h1>A compiler's symbol table in one fixed block of memory.</h1>
          <p className="lede">
            STRATA keeps every name a compiler sees, its nested scopes and the undo information for leaving a scope in a single buffer that the caller
            provides. It never calls the allocator after start-up, and when the buffer is full it refuses cleanly instead of crashing. We measured it
            on {nf.format(totalOps)} real symbol-table operations recorded from a C compiler building 8 open-source projects.
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={() => go("lab")}>Open the live lab</button>
            <button className="btn" onClick={() => go("benchmarks")}>See the benchmarks</button>
          </div>
        </div>
        <BufferDiagram />
      </section>

      <section aria-labelledby="kpi-title">
        <h2 id="kpi-title" className="section-title">Headline results</h2>
        <div className="kpis">
          <div className="card kpi">
            <span className="label">Correct answers</span>
            <b className="kpi-num">{strata.wrong === 0 ? "100%" : "—"}</b>
            <span className="kpi-sub">{nf.format(strata.wrong)} wrong of {nf.format(strata.checked)} lookups and declarations, 8 compiler traces</span>
          </div>
          <div className="card kpi">
            <span className="label">Peak memory vs std::unordered_map + undo log</span>
            <b className="kpi-num">{Math.round(std.heapMedian)}% <small>less (median)</small></b>
            <span className="kpi-sub">range {Math.round(std.heapMin)}–{Math.round(std.heapMax)}%, lower on {std.traces} of {std.traces} traces</span>
          </div>
          <div className="card kpi">
            <span className="label">Allocator calls vs std::unordered_map + undo log</span>
            <b className="kpi-num">{Math.floor(Math.min(...allocCut) * 10) / 10}% <small>fewer, at least</small></b>
            <span className="kpi-sub">up to {Math.floor(Math.max(...allocCut) * 10) / 10}%; zlib: {recorded.perTrace.find((t) => t.trace === "zlib")!.strataAllocs} calls vs {compact(recorded.perTrace.find((t) => t.trace === "zlib")!.stdAllocs)}</span>
          </div>
          <div className="card kpi">
            <span className="label">Fixed buffer vs a conventional single-buffer table</span>
            <b className="kpi-num">{Math.round(Math.min(...bufCut))}–{Math.round(Math.max(...bufCut))}% <small>smaller</small></b>
            <span className="kpi-sub">speed: {verdict(arena)} (slower on {arena.slower}, faster on {arena.faster} of {arena.traces})</span>
          </div>
        </div>
      </section>

      <div className="grid-2">
        <ChartCard
          title="Peak memory saved by STRATA"
          sub="Median reduction in peak heap over the 8 compiler traces, against each conventional design."
          table={
            <table className="results-table">
              <thead><tr><th>Compared with</th><th className="num">Median</th><th className="num">Range</th><th className="num">Replay time</th></tr></thead>
              <tbody>
                {recorded.vsAll.filter((v) => v.impl !== "arena_chain").map((v) => (
                  <tr key={v.impl}><td>{v.label}</td><td className="num mono">{v.heapMedian}%</td><td className="num mono">{v.heapMin}–{v.heapMax}%</td><td className="num mono">{verdict(v)}</td></tr>
                ))}
              </tbody>
            </table>
          }
          footer={<>The conventional single-buffer table is compared separately below, by smallest fixed buffer: it is the fair baseline.</>}
        >
          <BarList rows={memRows.map((r, i) => ({ ...r, highlight: i === 0 }))} format={(v) => `${v.toFixed(0)}%`} axisLabel="peak memory saved, %" />
        </ChartCard>

        <article className="card verdicts">
          <div className="viz-head"><div><h3>Where STRATA stands</h3><p className="viz-sub">Replay time over the same traces, 31 paired rounds each.</p></div></div>
          <ul className="verdict-list">
            {recorded.vsAll.map((v) => {
              const kind = v.faster === v.traces ? "good" : v.slower === v.traces ? "bad" : "neutral";
              return (
                <li key={v.impl}>
                  <span className={`badge ${kind}`}>{kind === "good" ? "Faster" : kind === "bad" ? "Slower" : "Level"}</span>
                  <div>
                    <b>{v.label}</b>
                    <span>{verdict(v)} · faster on {v.faster}, slower on {v.slower} of {v.traces}</span>
                  </div>
                </li>
              );
            })}
          </ul>
          <p className="viz-foot">
            The honest summary: STRATA is not faster than a well-built allocator-free table. Its contribution is predictable memory, far fewer
            allocations, a {Math.round(Math.min(...bufCut))}–{Math.round(Math.max(...bufCut))}% smaller fixed buffer, and clean refusal when full.
            {fitTraces.length > 0 && <> On an emulated 64 KiB Cortex-M3, STRATA fit {fitTraces.length} workloads that the conventional table could not.</>}
          </p>
        </article>
      </div>

      <section className="card pipeline" aria-labelledby="how-title">
        <h2 id="how-title">How the evidence was produced</h2>
        <ol>
          <li><b>Record</b><span>A patched Tiny C Compiler logs every declare, lookup and scope change while it compiles 8 real C projects.</span></li>
          <li><b>Replay</b><span>Each log is replayed through STRATA and five other tables; every answer is checked against a reference model.</span></li>
          <li><b>Measure</b><span>Peak heap, allocator calls and replay time, {parseInt(recorded.rounds)} paired rounds per trace on {recorded.cpu.replace(/\(R\)|\(TM\)/g, "")}.</span></li>
          <li><b>Stress</b><span>Bare-metal Cortex-M3 runs in QEMU, a second compiler (chibicc), hash-flooding inputs, fuzzing and exhaustive checks.</span></li>
        </ol>
      </section>
    </div>
  );
}

// The buffer layout drawn from the format documented in include/strata/strata.hpp.
function BufferDiagram() {
  return (
    <figure className="card buffer-figure" aria-label="Layout of the STRATA buffer">
      <figcaption>One buffer, four regions</figcaption>
      <svg viewBox="0 0 360 114" role="img" aria-label="Hash index, identifier records growing right, free space, undo stack growing left">
        <rect x="10" y="40" width="70" height="40" rx="5" fill="var(--c-index)" />
        <rect x="82" y="40" width="110" height="40" rx="5" fill="var(--c-record)" />
        <rect x="194" y="40" width="96" height="40" rx="5" fill="var(--c-free)" />
        <rect x="292" y="40" width="58" height="40" rx="5" fill="var(--c-undo)" />
        <text x="45" y="64" className="fig-in" textAnchor="middle">index</text>
        <text x="137" y="64" className="fig-in light" textAnchor="middle">records →</text>
        <text x="242" y="64" className="fig-in" textAnchor="middle">free</text>
        <text x="321" y="64" className="fig-in light" textAnchor="middle">← undo</text>
        <text x="45" y="104" className="fig-cap" textAnchor="middle">hash slots</text>
        <text x="137" y="104" className="fig-cap" textAnchor="middle">one per name</text>
        <text x="242" y="104" className="fig-cap" textAnchor="middle">refuse if gone</text>
        <text x="321" y="104" className="fig-cap" textAnchor="middle">scope exit</text>
        <line x1="10" x2="350" y1="22" y2="22" className="fig-rule" />
        <text x="180" y="16" className="fig-cap" textAnchor="middle">fixed size, chosen by the caller · no allocator calls</text>
      </svg>
      <p>Records grow from the left and the undo stack from the right. Leaving a scope pops the undo stack and restores hidden names, so the
        table always returns to exactly the state it had before the scope.</p>
    </figure>
  );
}
