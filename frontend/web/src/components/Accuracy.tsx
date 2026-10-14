import { useState } from "react";
import recorded from "../data/recorded.json";

// Live check: POST /api/trace replays a stored TinyCC trace through STRATA and the conventional
// single-buffer table in the C++ engine, checking every answer against the reference model.
interface Side { wrongLookups: number; wrongDeclares: number; refused: number; peakBytes: number; invariants: boolean; medianUs: number }
interface TraceRun {
  ok: true; trace: string; label: string; compiler: string; ops: number; declares: number; lookups: number; units: number; rounds: number;
  strata: Side; arena: Side; timeDiffMedianPct: number; timeDiffMinPct: number; timeDiffMaxPct: number;
}

const TRACE_ORDER: [string, string][] = [
  ["cjson", "cJSON"], ["littlefs", "littlefs"], ["zlib", "zlib"], ["freertos", "FreeRTOS"],
  ["lua", "Lua"], ["tinycc", "TinyCC"], ["sqlite", "SQLite"], ["mbedtls", "Mbed TLS"],
];
const nf = new Intl.NumberFormat("en-US");
const kib = (b: number) => `${(b / 1024).toFixed(1)} KiB`;
const pct = (x: number) => `${x > 0 ? "" : ""}${x.toFixed(1)}%`;
const range = (a: number, b: number) => `${Math.round(a)}–${Math.round(b)}%`;

async function runTrace(trace: string): Promise<TraceRun> {
  let res: Response;
  try {
    res = await fetch("/api/trace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ trace }) });
  } catch {
    throw new Error("Cannot reach the local demo server.");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok || !body?.ok) throw new Error(body?.error ?? `HTTP ${res.status}`);
  return body as TraceRun;
}

export function Accuracy({ ready }: { ready: boolean }) {
  const [runs, setRuns] = useState<Record<string, TraceRun>>({});
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (traces: string[]) => {
    setError(null);
    try {
      for (const t of traces) {
        setRunning(t);
        const r = await runTrace(t);
        setRuns((prev) => ({ ...prev, [t]: r }));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(null);
    }
  };

  const done = TRACE_ORDER.filter(([t]) => runs[t]).map(([t]) => runs[t]);
  const checked = done.reduce((n, r) => n + r.lookups + r.declares, 0);
  const wrong = done.reduce((n, r) => n + r.strata.wrongLookups + r.strata.wrongDeclares, 0);

  // Recorded (paper run) headline figures.
  const strataCorrect = recorded.correctness.find((c) => c.impl === "strata")!;
  const allCorrect = recorded.correctness.every((c) => c.wrong === 0);
  const std = recorded.vsAll.find((v) => v.impl === "std_undo_log")!;
  const arena = recorded.vsAll.find((v) => v.impl === "arena_chain")!;
  const allocCut = recorded.perTrace.map((t) => 100 * (1 - t.strataAllocs / t.stdAllocs));
  const bufCut = recorded.perTrace.map((t) => t.bufferReductionPct);

  return (
    <section className="accuracy" aria-labelledby="acc-title">
      <h2 id="acc-title" className="section-title">Accuracy &amp; performance</h2>

      <div className="kpis">
        <div className="card kpi">
          <span className="label">Correctness</span>
          <b className="kpi-num">{strataCorrect.wrong === 0 ? "100%" : `${(100 * (1 - strataCorrect.wrong / strataCorrect.checked)).toFixed(3)}%`}</b>
          <span className="kpi-sub">{nf.format(strataCorrect.wrong)} wrong of {nf.format(strataCorrect.checked)} answers on 8 compiler traces</span>
        </div>
        <div className="card kpi">
          <span className="label">Peak memory vs std::unordered_map + undo log</span>
          <b className="kpi-num">{range(std.heapMin, std.heapMax)} <small>less</small></b>
          <span className="kpi-sub">median {Math.round(std.heapMedian)}% · lower on {std.traces} of {std.traces} traces</span>
        </div>
        <div className="card kpi">
          <span className="label">Allocator calls vs std::unordered_map + undo log</span>
          <b className="kpi-num">{Math.floor(Math.min(...allocCut) * 10) / 10}–{Math.floor(Math.max(...allocCut) * 10) / 10}% <small>fewer</small></b>
          <span className="kpi-sub">e.g. zlib: {recorded.perTrace.find((t) => t.trace === "zlib")!.strataAllocs} vs {nf.format(recorded.perTrace.find((t) => t.trace === "zlib")!.stdAllocs)}</span>
        </div>
        <div className="card kpi">
          <span className="label">Replay time vs std::unordered_map + undo log</span>
          <b className="kpi-num">{range(std.timeMin, std.timeMax)} <small>faster</small></b>
          <span className="kpi-sub">median {Math.round(std.timeMedian)}% · faster on {std.faster} of {std.traces} (established)</span>
        </div>
        <div className="card kpi kpi-plain">
          <span className="label">vs conventional single-buffer table</span>
          <b className="kpi-num">{Math.round(Math.min(...bufCut))}–{Math.round(Math.max(...bufCut))}% <small>smaller buffer</small></b>
          <span className="kpi-sub">speed: no reliable difference (slower on {arena.slower} of {arena.traces}, faster on {arena.faster})</span>
        </div>
      </div>
      <p className="acc-note">
        “Accuracy” for a symbol table means every lookup returns the right declaration. It is a requirement, not an advantage:
        {allCorrect ? " every table measured was also 100% correct." : " not every table measured was correct."} STRATA's gains are memory and allocations;
        its speed depends on what it is compared with.
      </p>

      <div className="acc-grid">
        <article className="card acc-live">
          <div className="card-head">
            <h3>Live check on this laptop</h3>
            <span className="card-hint">real compiler traces → C++ engine</span>
          </div>
          <p className="muted small pad-x">
            Replays every symbol-table call the Tiny C Compiler made while compiling a real project. Each answer of STRATA is checked against the
            independent reference model; then STRATA and the conventional single-buffer table are timed in 11 alternating rounds.
          </p>
          <div className="acc-buttons">
            {TRACE_ORDER.map(([t, label]) => (
              <button key={t} className={`btn small ${runs[t] ? "btn-done" : ""}`} disabled={!ready || running !== null} onClick={() => void run([t])}>
                {running === t ? <span className="spinner" aria-label="running" /> : null}
                {label}
              </button>
            ))}
            <button className="btn btn-primary small" disabled={!ready || running !== null} onClick={() => void run(TRACE_ORDER.map(([t]) => t))}>
              Run all 8
            </button>
          </div>
          {error && <p className="acc-error" role="alert">{error}</p>}
          {done.length > 0 && (
            <>
              <div className="table-wrap">
                <table className="results-table live-table">
                  <thead>
                    <tr>
                      <th>Trace</th><th className="num">Answers checked</th><th className="num">Wrong</th><th className="num">Accuracy</th>
                      <th className="num">Peak memory</th><th className="num">Saved vs conv.</th><th className="num">Time vs conv.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {done.map((r) => {
                      const w = r.strata.wrongLookups + r.strata.wrongDeclares;
                      const n = r.lookups + r.declares;
                      const saved = 100 * (1 - r.strata.peakBytes / r.arena.peakBytes);
                      return (
                        <tr key={r.trace}>
                          <td>{r.label}<span className="sub">{nf.format(r.ops)} operations · {r.units} file{r.units > 1 ? "s" : ""}</span></td>
                          <td className="num mono">{nf.format(n)}</td>
                          <td className="num mono">{w}</td>
                          <td className="num mono strong">{w === 0 ? "100%" : `${(100 * (1 - w / n)).toFixed(3)}%`}</td>
                          <td className="num mono">{kib(r.strata.peakBytes)}<span className="sub">conv. {kib(r.arena.peakBytes)}</span></td>
                          <td className="num mono">{pct(saved)}</td>
                          <td className="num mono">
                            {r.timeDiffMedianPct >= 0 ? `${r.timeDiffMedianPct.toFixed(1)}% faster` : `${(-r.timeDiffMedianPct).toFixed(1)}% slower`}
                            <span className="sub">{(r.strata.medianUs / 1000).toFixed(2)} vs {(r.arena.medianUs / 1000).toFixed(2)} ms</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="footnote">
                {nf.format(wrong)} wrong of {nf.format(checked)} answers checked on {done.length} trace{done.length > 1 ? "s" : ""}; table self-check{" "}
                {done.every((r) => r.strata.invariants) ? "passed" : "FAILED"}. Times: this machine, Windows, g++ {done[0].compiler}, median of 11 rounds; they
                vary from run to run, so only differences of more than about 10% mean anything. The reported timing is the 31-round run on the right.
              </p>
            </>
          )}
        </article>

        <article className="card acc-recorded">
          <div className="card-head">
            <h3>Recorded results</h3>
            <span className="card-hint">paper run {recorded.run}</span>
          </div>
          <p className="muted small pad-x">
            31 paired rounds per trace, {recorded.cpu}, {recorded.compiler.replace(/ \(.*\)/, "")}, WSL 2. Read from <code>results/</code> by{" "}
            <code>frontend/web/scripts/make-results.mjs</code>.
          </p>
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr><th>STRATA compared with</th><th className="num">Peak memory</th><th className="num">Replay time</th></tr>
              </thead>
              <tbody>
                {recorded.vsAll.map((v) => (
                  <tr key={v.impl}>
                    <td>{v.label}</td>
                    <td className="num mono">
                      {v.impl === "arena_chain" ? `${Math.round(Math.min(...bufCut))}–${Math.round(Math.max(...bufCut))}% smaller` : `${range(v.heapMin, v.heapMax)} less`}
                      <span className="sub">{v.impl === "arena_chain" ? "smallest fixed buffer" : `median ${Math.round(v.heapMedian)}%`}</span>
                    </td>
                    <td className="num mono">
                      {v.faster === v.traces ? `${range(v.timeMin, v.timeMax)} faster` : v.slower === v.traces ? `${range(-v.timeMax, -v.timeMin)} slower` : v.faster === 0 && v.slower <= 2 ? "no reliable difference" : `mixed · median ${Math.abs(v.timeMedian).toFixed(1)}% ${v.timeMedian < 0 ? "slower" : "faster"}`}
                      <span className="sub">faster on {v.faster}, slower on {v.slower} of {v.traces}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr><th>Trace</th><th className="num">Answers</th><th className="num">Wrong</th><th className="num">Peak heap</th><th className="num">Allocations</th><th className="num">Replay</th></tr>
              </thead>
              <tbody>
                {recorded.perTrace.map((t) => (
                  <tr key={t.trace}>
                    <td>{TRACE_ORDER.find(([k]) => k === t.trace)?.[1]}</td>
                    <td className="num mono">{nf.format(t.checked)}</td>
                    <td className="num mono">{t.wrong}</td>
                    <td className="num mono">{t.strataHeapKiB} KiB<span className="sub">std: {t.stdHeapKiB}</span></td>
                    <td className="num mono">{nf.format(t.strataAllocs)}<span className="sub">std: {nf.format(t.stdAllocs)}</span></td>
                    <td className="num mono">{t.strataMs} ms<span className="sub">std: {t.stdMs}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="footnote">“std” = std::unordered_map + undo log (the algorithm of LLVM's ScopedHashTable).</p>
        </article>
      </div>
    </section>
  );
}
