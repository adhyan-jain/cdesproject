import { useState } from "react";
import { nf, traceLabel } from "../lib/format";

// Live check: POST /api/trace replays a stored TinyCC trace through STRATA and the conventional
// single-buffer table in the C++ engine, checking every answer against the reference model.
interface Side { wrongLookups: number; wrongDeclares: number; refused: number; peakBytes: number; invariants: boolean; medianUs: number }
interface TraceRun {
  ok: true; trace: string; label: string; compiler: string; ops: number; declares: number; lookups: number; units: number; rounds: number;
  strata: Side; arena: Side; timeDiffMedianPct: number; timeDiffMinPct: number; timeDiffMaxPct: number;
}

const TRACES = ["cjson", "littlefs", "zlib", "freertos", "lua", "tinycc", "sqlite", "mbedtls"];
const kib = (b: number) => `${(b / 1024).toFixed(1)} KiB`;

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

export function LiveCheck({ ready }: { ready: boolean }) {
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

  const done = TRACES.filter((t) => runs[t]).map((t) => runs[t]);
  const checked = done.reduce((n, r) => n + r.lookups + r.declares, 0);
  const wrong = done.reduce((n, r) => n + r.strata.wrongLookups + r.strata.wrongDeclares, 0);

  return (
    <article className="card live-card">
      <div className="viz-head">
        <div>
          <h3>Run it yourself</h3>
          <p className="viz-sub">
            Replays every symbol-table call the Tiny C Compiler made while compiling a real project, on this computer, through the C++ engine.
            Each answer of STRATA is checked against an independent reference model; then STRATA and the conventional single-buffer table are
            timed in 11 alternating rounds.
          </p>
        </div>
      </div>
      <div className="acc-buttons">
        {TRACES.map((t) => (
          <button key={t} className={`btn small ${runs[t] ? "btn-done" : ""}`} disabled={!ready || running !== null} onClick={() => void run([t])}>
            {running === t ? <span className="spinner" aria-label="running" /> : null}
            {traceLabel(t)}
          </button>
        ))}
        <button className="btn btn-primary small" disabled={!ready || running !== null} onClick={() => void run(TRACES)}>
          Run all 8
        </button>
        {!ready && <span className="muted small">Needs the local C++ engine (npm start).</span>}
      </div>
      {error && <p className="acc-error" role="alert">{error}</p>}
      {done.length > 0 && (
        <>
          <div className="table-wrap">
            <table className="results-table live-table">
              <thead>
                <tr>
                  <th>Trace</th><th className="num">Answers checked</th><th className="num">Wrong</th><th className="num">Accuracy</th>
                  <th className="num">Peak memory</th><th className="num">Saved vs single-buffer</th><th className="num">Time vs single-buffer</th>
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
                      <td className="num mono">{kib(r.strata.peakBytes)}<span className="sub">single-buffer {kib(r.arena.peakBytes)}</span></td>
                      <td className="num mono">{saved.toFixed(1)}%</td>
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
          <p className="footnote pad-x">
            {nf.format(wrong)} wrong of {nf.format(checked)} answers checked on {done.length} trace{done.length > 1 ? "s" : ""}; table self-check{" "}
            {done.every((r) => r.strata.invariants) ? "passed" : "FAILED"}. Times are from this machine (Windows, g++ {done[0].compiler}, median of 11
            rounds) and vary between runs, so only differences above about 10% mean anything. The reported timing is the 31-round recorded run.
          </p>
        </>
      )}
    </article>
  );
}
