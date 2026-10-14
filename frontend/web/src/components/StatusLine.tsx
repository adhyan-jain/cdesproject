import type { OpResult } from "../lib/engine";
import { describe, type Tone } from "../lib/describe";

export type StatusSource =
  | { kind: "op"; result: OpResult; seq: number }
  | { kind: "invalid"; message: string; seq: number }
  | { kind: "error"; message: string; seq: number }
  | { kind: "idle" };

function Icon({ tone }: { tone: Tone }) {
  if (tone === "ok")
    return <svg viewBox="0 0 16 16" className="ico" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>;
  if (tone === "info")
    return <svg viewBox="0 0 16 16" className="ico" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" /><path d="M8 7v4M8 4.8v.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>;
  return <svg viewBox="0 0 16 16" className="ico" aria-hidden="true"><path d="M8 2.5l6 11H2l6-11z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><path d="M8 7v3M8 11.8v.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>;
}

export function StatusLine({ source }: { source: StatusSource }) {
  let tone: Tone = "info", title = "Ready", detail = "Declare a variable, open a scope, or run the guided demo.", code: string | undefined, foot: string | undefined;
  if (source.kind === "op") {
    const d = describe(source.result);
    ({ tone, title, detail, code } = d);
    foot = source.result.changed
      ? `state digest ${source.result.digestBefore.slice(0, 8)} → ${source.result.digestAfter.slice(0, 8)}`
      : `table unchanged · digest ${source.result.digestAfter.slice(0, 8)}`;
  } else if (source.kind === "invalid") {
    tone = "warn"; title = /^Line \d+:/.test(source.message) ? "Code error · not run" : "Invalid input · not sent"; detail = source.message;
  } else if (source.kind === "error") {
    tone = "error"; title = "Engine error"; detail = source.message;
  }
  return (
    <section className={`card status status-${tone}`} aria-live="polite" key={"seq" in source ? source.seq : 0}>
      <div className="status-icon"><Icon tone={tone} /></div>
      <div className="status-text">
        <div className="status-title">
          {title}
          {code && <code className="code-chip">{code}</code>}
        </div>
        <p>{detail}</p>
        {foot && <p className="status-foot mono">{foot}</p>}
      </div>
    </section>
  );
}
