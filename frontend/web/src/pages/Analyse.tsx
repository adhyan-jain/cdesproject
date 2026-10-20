import { useRef, useState } from "react";
import { analyse, SAMPLE, type NameInfo, type Report } from "../lib/analyse";
import { CodeError } from "../lib/minic";
import { EngineError } from "../lib/engine";
import { nf } from "../lib/format";

const bytes = (n: number) => (n >= 1024 ? `${n / 1024} KiB` : `${n} B`);
const scopeName = (d: number) => (d === 0 ? "global" : `level ${d}`);
const KIND: Record<NameInfo["kind"], string> = { var: "variable", param: "parameter", function: "function" };
const PROBLEM_LABEL = { undeclared: "Not declared", redeclared: "Declared twice", unused: "Never used", refused: "Out of room" } as const;

export function Analyse({ ready, onOpenInLab }: { ready: boolean; onOpenInLab: (code: string) => void }) {
  const [code, setCode] = useState(SAMPLE);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<{ line?: number; message: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [analysed, setAnalysed] = useState<string | null>(null);
  const gutter = useRef<HTMLDivElement>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setReport(await analyse(code));
      setAnalysed(code);
    } catch (e) {
      setReport(null);
      if (e instanceof CodeError) setError({ line: e.line, message: e.message });
      else setError({ message: e instanceof EngineError ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  };

  const lines = code.split("\n").length;
  const stale = report && analysed !== code;

  return (
    <div className="stack">
      <header className="page-head">
        <h1>Analyse your code</h1>
        <p>
          Paste a C program and press <b>Analyse</b>. You get every name in it, where it is declared, where it is used, which names hide
          others, and how much memory STRATA needs to hold the program's symbol table. The program is not run: it is turned into the calls a
          compiler makes on its symbol table (declare, look up, open scope, close scope), and those calls run on the real C++ table.
        </p>
      </header>

      <div className="an-grid">
        <section className="card an-input" aria-labelledby="an-code">
          <div className="card-head">
            <h2 id="an-code">Your code</h2>
            <div className="an-head-actions">
              <button className="btn btn-ghost small" onClick={() => { setCode(""); setReport(null); setError(null); }}>Clear</button>
              <button className="btn btn-ghost small" onClick={() => setCode(SAMPLE)}>Sample</button>
            </div>
          </div>
          <div className="editor an-editor">
            <div className="gutter mono" ref={gutter} aria-hidden="true">
              {Array.from({ length: lines }, (_, i) => <div key={i} className={i + 1 === error?.line ? "g-err" : ""}>{i + 1}</div>)}
            </div>
            <textarea
              className="code mono"
              value={code}
              spellCheck={false}
              autoCapitalize="off"
              autoComplete="off"
              aria-label="C code to analyse"
              placeholder="Paste a C program here…"
              wrap="off"
              onChange={(e) => setCode(e.target.value)}
              onScroll={(e) => { if (gutter.current) gutter.current.scrollTop = e.currentTarget.scrollTop; }}
              onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void run(); } }}
            />
          </div>
          <div className="code-actions">
            <button className="btn btn-primary" onClick={() => void run()} disabled={!ready || busy || !code.trim()}>
              {busy ? "Analysing…" : "Analyse"}
            </button>
            <button className="btn" onClick={() => onOpenInLab(code)} disabled={!code.trim()}>Step through it in the Live lab</button>
            <span className="code-progress mono">{stale ? "edited · press Analyse" : "Ctrl+Enter"}</span>
          </div>
          <p className="an-support">
            <b>Understood:</b> int, char, float, double, bool, long, short, unsigned, const, static, pointers, arrays, functions, blocks, if,
            while, do, for, switch. <b>Not yet:</b> struct, union, enum, typedef. Programs up to 400 symbol-table calls.
          </p>
          {!ready && <p className="an-error" role="alert">The C++ engine is offline. Start it with <code>npm start</code> in <code>frontend/web</code>.</p>}
          {error && (
            <p className="an-error" role="alert">{error.line ? <b>Line {error.line}: </b> : null}{error.message}</p>
          )}
        </section>

        <div className="an-out">
          {report ? <ReportView r={report} /> : (
            <div className="card an-empty">
              <h3>What you will see</h3>
              <ol className="an-steps">
                <li><b>Summary.</b> How many names, uses and scopes, and how deep the scopes nest.</li>
                <li><b>Memory.</b> The smallest fixed buffer that holds the whole program, and how it is used.</li>
                <li><b>Every name.</b> Type, scope, line, every line that uses it, and what it hides.</li>
                <li><b>Things to check.</b> Names used before they are declared, declared twice, or never used.</li>
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ReportView({ r }: { r: Report }) {
  const shadowing = r.names.filter((n) => n.shadows);
  const st = r.buffer?.state.stats;
  return (
    <>
      <div className="kpis an-kpis">
        <Kpi label="Names declared" value={r.names.length} sub={`${r.names.filter((n) => n.kind === "function").length} functions · ${r.names.filter((n) => n.kind === "param").length} parameters`} />
        <Kpi label="Uses (look-ups)" value={r.lookups} sub="each time a name is read or written" />
        <Kpi label="Scopes opened" value={r.scopes} sub={`deepest nesting: ${r.maxDepth} level${r.maxDepth === 1 ? "" : "s"}`} />
        <Kpi label="Names that hide another" value={shadowing.length} sub={shadowing.length ? shadowing.map((n) => n.name).slice(0, 3).join(", ") : "no shadowing"} />
      </div>

      <section className="card an-mem" aria-labelledby="an-mem-title">
        <div className="card-head"><h2 id="an-mem-title">Memory STRATA needs</h2></div>
        {r.buffer && st ? (
          <div className="an-mem-body">
            <p className="an-big"><b>{bytes(r.buffer.bytes)}</b> is the smallest buffer (of 256 B, 512 B, 1 KiB, …) that holds this program's whole symbol table.</p>
            {r.tooSmall && <p className="muted">At {bytes(r.tooSmall.bytes)} the table ran out of room at call {r.tooSmall.refusedAt + 1} and refused it cleanly, without crashing or losing earlier names.</p>}
            <MemBar used={st.peak} cap={r.buffer.bytes} />
            <dl className="an-dl">
              <dt>Most memory in use at once</dt><dd>{nf.format(st.peak)} bytes</dd>
              <dt>Symbol-table calls</dt><dd>{nf.format(r.ops)} ({r.declarations} declarations, {r.lookups} look-ups, {r.scopes} scopes)</dd>
              <dt>Allocator calls</dt><dd>0, everything lives in the one buffer</dd>
              <dt>Engine checks</dt><dd>{r.checksOk ? "all answers agree with the reference model ✓" : "a check failed ✗"}</dd>
            </dl>
          </div>
        ) : (
          <p className="pad">Even 64 KiB is not enough for this program in the demo; {r.tooSmall ? `the table refused call ${r.tooSmall.refusedAt + 1}.` : ""}</p>
        )}
      </section>

      <section className="card" aria-labelledby="an-names-title">
        <div className="card-head"><h2 id="an-names-title">Every name</h2><span className="card-hint">in the order the compiler meets them</span></div>
        <div className="table-wrap">
          <table className="results-table an-table">
            <thead><tr><th>Name</th><th>Type</th><th>Kind</th><th>Scope</th><th className="num">Line</th><th>Used on lines</th><th>Notes</th></tr></thead>
            <tbody>
              {r.names.map((n) => (
                <tr key={n.id}>
                  <td className="mono"><b>{n.name}</b></td>
                  <td className="mono">{n.ctype}</td>
                  <td>{KIND[n.kind]}</td>
                  <td>{scopeName(n.depth)}</td>
                  <td className="num">{n.line}</td>
                  <td className="mono">{n.uses.length ? [...new Set(n.uses)].join(", ") : <span className="muted">none</span>}</td>
                  <td className="an-note">
                    {n.shadows && <>hides the {scopeName(n.shadows.depth)} <code>{n.name}</code> from line {n.shadows.line}. </>}
                    {n.shadowedBy.length > 0 && <>hidden on line{n.shadowedBy.length > 1 ? "s" : ""} {n.shadowedBy.join(", ")}. </>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card" aria-labelledby="an-prob-title">
        <div className="card-head"><h2 id="an-prob-title">Things to check</h2><span className="card-hint">{r.problems.length || "none"}</span></div>
        {r.problems.length === 0 ? <p className="pad muted">Nothing: every name is declared before use, once per scope, and used.</p> : (
          <ul className="an-problems">
            {r.problems.map((p, i) => (
              <li key={i}><span className={`badge ${p.kind === "unused" ? "neutral" : "bad"}`}>{PROBLEM_LABEL[p.kind]}</span><span className="mono">line {p.line}</span><span>{p.text}</span></li>
            ))}
          </ul>
        )}
        <p className="viz-foot">Library functions such as printf are not counted as names. Values are not evaluated; only names are tracked.</p>
      </section>
    </>
  );
}

function Kpi({ label, value, sub }: { label: string; value: number; sub: string }) {
  return (
    <div className="card kpi">
      <span className="label">{label}</span>
      <b className="kpi-num">{nf.format(value)}</b>
      <span className="kpi-sub">{sub}</span>
    </div>
  );
}

function MemBar({ used, cap }: { used: number; cap: number }) {
  const pct = Math.min(100, (100 * used) / cap);
  return (
    <div className="an-bar" role="img" aria-label={`${used} of ${cap} bytes used at the peak`}>
      <div className="an-bar-fill" style={{ width: `${pct}%` }} />
      <span className="an-bar-text mono">{nf.format(used)} / {nf.format(cap)} bytes at the peak ({pct.toFixed(0)}%)</span>
    </div>
  );
}
