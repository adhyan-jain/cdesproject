import { useRef } from "react";
import { EXAMPLES } from "../lib/minic";
import { CAPACITIES } from "./Controls";

interface Props {
  code: string;
  onCode: (code: string) => void;
  capacity: number;
  onCapacity: (bytes: number) => void;
  disabled: boolean;
  total: number | null;     // operations in the compiled program, null when not compiled
  done: number;             // operations executed so far
  currentLine: number | null;
  errorLine: number | null;
  stale: boolean;           // code edited since it was compiled
  onRun: () => void;
  onStep: () => void;
  onRestart: () => void;
}

export function CodeEditor(p: Props) {
  const gutter = useRef<HTMLDivElement>(null);
  const lines = p.code.split("\n").length;
  const finished = p.total !== null && p.done >= p.total && !p.stale;

  return (
    <section className="card code-card" aria-labelledby="code-title">
      <div className="card-head">
        <h2 id="code-title">Write code</h2>
        <label className="push example-pick">
          <span className="sr-only">Load an example</span>
          <select
            className="select"
            value=""
            disabled={p.disabled}
            onChange={(e) => { const ex = EXAMPLES[Number(e.target.value)]; if (ex) p.onCode(ex.code); }}
          >
            <option value="" disabled>Examples…</option>
            {EXAMPLES.map((ex, i) => <option key={ex.title} value={i}>{ex.title}</option>)}
          </select>
        </label>
      </div>
      <div className="editor">
        <div className="gutter mono" ref={gutter} aria-hidden="true">
          {Array.from({ length: lines }, (_, i) => (
            <div key={i} className={i + 1 === p.errorLine ? "g-err" : i + 1 === p.currentLine ? "g-cur" : ""}>{i + 1}</div>
          ))}
        </div>
        <textarea
          className="code mono"
          value={p.code}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          aria-label="C code"
          wrap="off"
          onChange={(e) => p.onCode(e.target.value)}
          onScroll={(e) => { if (gutter.current) gutter.current.scrollTop = e.currentTarget.scrollTop; }}
          onKeyDown={(e) => {
            if (e.key === "Tab") {
              e.preventDefault();
              const t = e.currentTarget, s = t.selectionStart;
              p.onCode(p.code.slice(0, s) + "    " + p.code.slice(t.selectionEnd));
              requestAnimationFrame(() => { t.selectionStart = t.selectionEnd = s + 4; });
            }
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); p.onRun(); }
          }}
        />
      </div>
      <div className="code-actions">
        <button className="btn btn-primary" onClick={p.onRun} disabled={p.disabled}>
          <svg viewBox="0 0 16 16" aria-hidden="true" className="ico"><path d="M5 3.5v9l7-4.5-7-4.5z" fill="currentColor" /></svg>
          Run
        </button>
        <button className="btn" onClick={p.onStep} disabled={p.disabled || finished}>Step</button>
        <button className="btn btn-ghost" onClick={p.onRestart} disabled={p.disabled || p.total === null}>Restart</button>
        <span className="code-progress mono">
          {p.stale ? "edited · press Run" : p.total === null ? "Ctrl+Enter runs" : `${p.done} / ${p.total} ops${p.currentLine ? ` · line ${p.currentLine}` : ""}`}
        </span>
      </div>
      <div className="controls-foot">
        <label className="field inline">
          <span className="label">Buffer</span>
          <select className="select mono" value={p.capacity} onChange={(e) => p.onCapacity(Number(e.target.value))} disabled={p.disabled}>
            {CAPACITIES.map((c) => <option key={c} value={c}>{c >= 1024 ? `${c / 1024} KiB` : `${c} B`}</option>)}
          </select>
        </label>
        <span className="card-hint">int float char bool · {"{ }"} · functions · if while for</span>
      </div>
    </section>
  );
}
