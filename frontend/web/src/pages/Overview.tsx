import { useEffect, useRef, useState } from "react";
import recorded from "../data/recorded.json";
import { BarList, ChartCard } from "../components/charts";
import { FRAMES, MemoryModel, MemoryModelLoop } from "../components/MemoryModel";
import { nf, compact } from "../lib/format";
import { reducedMotion, useCountUp, useSeen } from "../lib/motion";
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
const zlib = recorded.perTrace.find((t) => t.trace === "zlib")!;

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
    <div className="home">
      {/* ---------------------------------------------------------------- hero */}
      <section className="hero2">
        <div className="hero2-text reveal">
          <p className="meta mono">COMPILER DESIGN PROJECT · VIT VELLORE · TRACE / 08</p>
          <h1>A compiler's symbol table in one fixed block of memory.</h1>
          <p className="lede">
            STRATA keeps every name a compiler sees, its nested scopes and the undo information for leaving a scope in a single buffer that the caller
            provides. It never calls the allocator after start-up, and when the buffer is full it refuses cleanly instead of crashing. We measured it
            on {nf.format(totalOps)} real symbol-table operations recorded from a C compiler building 8 open-source projects.
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={() => go("analyse")}>Analyse your code</button>
            <button className="btn btn-lg" onClick={() => go("lab")}>Open the live lab</button>
            <button className="btn btn-ghost btn-lg" onClick={() => go("benchmarks")}>See the benchmarks →</button>
          </div>
        </div>
        <div className="hero2-visual reveal">
          <MemoryModelLoop />
        </div>
      </section>

      {/* ---------------------------------------------------------------- story */}
      <Story />

      {/* ---------------------------------------------------------------- results */}
      <section className="band" aria-labelledby="kpi-title">
        <div className="band-head reveal">
          <p className="meta mono">THE RESULT · RUN / {recorded.run}</p>
          <h2 id="kpi-title" className="display">What it bought.</h2>
        </div>
        <div className="figures">
          <Figure value={strata.wrong === 0 ? 100 : NaN} suffix="%" label="Correct answers"
            sub={`${nf.format(strata.wrong)} wrong of ${nf.format(strata.checked)} lookups and declarations, 8 compiler traces`} />
          <Figure value={Math.round(std.heapMedian)} suffix="%" small="less" label="Peak memory vs std::unordered_map + undo log"
            sub={`median; range ${Math.round(std.heapMin)}–${Math.round(std.heapMax)}%, lower on ${std.traces} of ${std.traces} traces`} />
          <Figure value={Math.floor(Math.min(...allocCut) * 10) / 10} decimals={1} suffix="%" small="fewer, at least" label="Allocator calls vs std::unordered_map + undo log"
            sub={`up to ${Math.floor(Math.max(...allocCut) * 10) / 10}%; zlib: ${zlib.strataAllocs} calls vs ${compact(zlib.stdAllocs)}`} />
          <Figure value={Math.round(Math.min(...bufCut))} to={Math.round(Math.max(...bufCut))} suffix="%" small="smaller" label="Fixed buffer vs a conventional single-buffer table"
            sub={`speed: ${verdict(arena)} (slower on ${arena.slower}, faster on ${arena.faster} of ${arena.traces}). The theory addendum traces the saving to a stored hash word plus name packing.`} />
        </div>
      </section>

      <section className="band split">
        <div className="reveal">
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
            footer={<>The conventional single-buffer table is compared separately, by smallest fixed buffer: it is the fair baseline.</>}
          >
            <BarList rows={memRows.map((r, i) => ({ ...r, highlight: i === 0 }))} format={(v) => `${v.toFixed(0)}%`} axisLabel="peak memory saved, %" />
          </ChartCard>
        </div>

        <article className="verdicts2 reveal">
          <h3>Where STRATA stands</h3>
          <p className="viz-sub">Replay time over the same traces, 31 paired rounds each.</p>
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
          <p className="honest">
            The honest summary: STRATA is not faster than a well-built allocator-free table. Its contribution is predictable memory, far fewer
            allocations, a {Math.round(Math.min(...bufCut))}–{Math.round(Math.max(...bufCut))}% smaller fixed buffer, and clean refusal when full.
            {fitTraces.length > 0 && <> On an emulated 64 KiB Cortex-M3, STRATA fit {fitTraces.length} workloads that the conventional table could not.</>}
          </p>
        </article>
      </section>

      {/* ---------------------------------------------------------------- theory */}
      <section className="band" aria-labelledby="theory-strip">
        <div className="band-head reveal">
          <p className="meta mono">THEORY · ADDED 2026-10-18</p>
          <h2 id="theory-strip" className="display">And what was proved.</h2>
          <p className="band-lede">The theory manuscript Adhyan Jain added on 18 October asks what the last-in-first-out order of scopes gives a table like this. Three results matter for the design.</p>
        </div>
        <ol className="facts reveal">
          <li><span className="mono">THEOREM 2</span><b>Popping the newest name is an exact undo.</b><p>For every open-addressing scheme that never moves a key, clearing the newest key's cell returns exactly the table you would get by inserting the remaining keys. So scope exit cannot leave the index damaged.</p></li>
          <li><span className="mono">THEOREM 7</span><b>Probe limit 258, not 455.</b><p>At load 3/4, keeping a refusal at most one in a million per declaration needs a probe limit of 258 for large indexes; the bound used before asked for 455.</p></li>
          <li><span className="mono">PROPOSITION 16</span><b>Where the 16–18% comes from.</b><p>Not storing a hash word saves 9.2–12.2%, packing names a further 5.3–9.0%; interning by itself is space-neutral on these traces.</p></li>
        </ol>
        <button className="btn reveal" onClick={() => go("theory")}>Explore the theory →</button>
      </section>

      {/* ---------------------------------------------------------------- method + ways in */}
      <section className="band" aria-labelledby="how-title">
        <div className="band-head reveal">
          <p className="meta mono">METHOD / 04 STEPS</p>
          <h2 id="how-title" className="display">How the evidence was produced.</h2>
        </div>
        <ol className="steps4 reveal">
          <li><span className="mono">01</span><b>Record</b><p>A patched Tiny C Compiler logs every declare, lookup and scope change while it compiles 8 real C projects.</p></li>
          <li><span className="mono">02</span><b>Replay</b><p>Each log is replayed through STRATA and five other tables; every answer is checked against a reference model.</p></li>
          <li><span className="mono">03</span><b>Measure</b><p>Peak heap, allocator calls and replay time, {parseInt(recorded.rounds)} paired rounds per trace on {recorded.cpu.replace(/\(R\)|\(TM\)/g, "")}.</p></li>
          <li><span className="mono">04</span><b>Stress</b><p>Bare-metal Cortex-M3 runs in QEMU, a second compiler (chibicc), hash-flooding inputs, fuzzing and exhaustive checks.</p></li>
        </ol>
      </section>

      <section className="ways reveal" aria-label="Where to go next">
        <button onClick={() => go("analyse")}><span className="mono">TRY IT / 01</span><b>Analyse your code</b><p>Paste a C program; see every name, its scope, its uses and the buffer it needs.</p><i aria-hidden="true">→</i></button>
        <button onClick={() => go("benchmarks")}><span className="mono">RESULTS / 02</span><b>See the measurements</b><p>Eight compiler traces, six tables, the fair baseline and the stress tests.</p><i aria-hidden="true">→</i></button>
        <button onClick={() => go("theory")}><span className="mono">THEORY / 03</span><b>Read the proofs</b><p>Exact undo, refusal probabilities and probe limits, with interactive models.</p><i aria-hidden="true">→</i></button>
      </section>
    </div>
  );
}

// One big number that counts up when it scrolls into view. NaN shows a dash.
function Figure({ value, to, decimals = 0, suffix, small, label, sub }: {
  value: number; to?: number; decimals?: number; suffix: string; small?: string; label: string; sub: string;
}) {
  const [ref, seen] = useSeen<HTMLDivElement>();
  const a = useCountUp(Number.isFinite(value) ? value : 0, seen);
  const b = useCountUp(to ?? 0, seen);
  const fmt = (v: number) => v.toFixed(decimals);
  return (
    <div className="figure reveal" ref={ref}>
      <span className="figure-label mono">{label}</span>
      <b className="figure-num">
        {Number.isFinite(value) ? fmt(a) : "—"}{to !== undefined && <>–{fmt(b)}</>}<span className="figure-unit">{suffix}</span>
      </b>
      {small && <span className="figure-small">{small}</span>}
      <p>{sub}</p>
    </div>
  );
}

// The memory story: a sticky memory block on the left, one step per screen on the right.
function Story() {
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLDivElement | null)[]>([]);
  useEffect(() => {
    if (!("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.i));
    }, { rootMargin: "-45% 0px -45% 0px" });
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, []);
  const still = reducedMotion();
  return (
    <section className="story" aria-label="How STRATA uses its buffer, step by step">
      <div className="story-sticky" aria-hidden="true">
        <div className="story-frame">
          <MemoryModel frame={active} />
          <div className="story-progress">{FRAMES.map((f, i) => <i key={f.key} className={i <= active ? "on" : ""} />)}</div>
        </div>
      </div>
      <div className="story-steps">
        {FRAMES.map((f, i) => (
          <div key={f.key} className={`story-step${active === i ? " on" : ""}`} data-i={i} ref={(el) => { refs.current[i] = el; }}>
            <span className="meta mono">STEP / {String(i + 1).padStart(2, "0")}</span>
            <h2 className="story-title">{f.title}</h2>
            <p>{f.text}</p>
            <code className="story-call">{f.call}</code>
            <div className="story-inline"><MemoryModel frame={i} size="compact" interactive={false} /></div>
            {i < FRAMES.length - 1 && !still && <span className="story-down" aria-hidden="true">↓</span>}
          </div>
        ))}
      </div>
    </section>
  );
}
