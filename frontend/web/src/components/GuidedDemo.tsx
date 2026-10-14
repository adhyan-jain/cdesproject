import type { Described } from "../lib/describe";

export interface DemoStep { title: string; caption: string; look: string }

export const DEMO_CAPACITY = 256;

export const DEMO_STEPS: DemoStep[] = [
  {
    title: "Declare an outer variable",
    caption: "STRATA stores the variable in the current scope.",
    look: "int count = 1 appears in Global. In the buffer: one identifier record (12 B) and a 4 B undo entry.",
  },
  {
    title: "Enter an inner scope",
    caption: "Nested scopes allow local declarations to temporarily hide outer declarations.",
    look: "The scope trail gains Scope 1; a 2-word scope mark is pushed on the undo stack.",
  },
  {
    title: "Shadow the variable",
    caption: "The inner declaration is now visible. The previous declaration is preserved for restoration.",
    look: "Lookup of count returns 2. The outer count = 1 is shown as hidden: it was saved on the undo stack.",
  },
  {
    title: "Exit the inner scope",
    caption: "STRATA uses its undo stack to restore the previous declaration when the scope ends.",
    look: "count is back to 1, read from the undo entry; lookup confirms it.",
  },
  {
    title: "Fill the buffer until it refuses",
    caption: "STRATA rejects the operation without partially modifying the existing table.",
    look: `This table lives in a ${DEMO_CAPACITY}-byte buffer. New names are declared until one does not fit: kNoMemory, digest unchanged, count still 1.`,
  },
];

interface Props {
  step: number;          // steps completed so far
  outcome?: Described;   // what the engine reported for the latest operation
  playing: boolean;
  busy: boolean;
  onNext: () => void;
  onTogglePlay: () => void;
  onRestart: () => void;
  onClose: () => void;
}

export function GuidedDemo({ step, outcome, playing, busy, onNext, onTogglePlay, onRestart, onClose }: Props) {
  const done = step >= DEMO_STEPS.length;
  const shown = DEMO_STEPS[Math.max(0, step - 1)];
  return (
    <section className="demo-bar" aria-label="Guided demo" aria-live="polite">
      <div className="demo-steps" aria-hidden="true">
        {DEMO_STEPS.map((s, i) => (
          <span key={s.title} className={`demo-dot ${i < step ? "done" : ""} ${i === step - 1 ? "current" : ""}`}>{i + 1}</span>
        ))}
      </div>
      <div className="demo-text">
        <div className="demo-kicker">
          Guided demo · step {Math.max(1, step)} of {DEMO_STEPS.length}
          {busy && <span className="spinner" aria-label="running" />}
        </div>
        {step === 0 ? (
          <div className="demo-title">Starting with an empty {DEMO_CAPACITY}-byte table…</div>
        ) : (
          <>
            <div className="demo-title">{shown.title}</div>
            <p className="demo-caption">“{shown.caption}”</p>
            <p className="demo-look">{shown.look}</p>
          </>
        )}
        {outcome && step > 0 && (
          <p className={`demo-outcome tone-${outcome.tone}`}>
            <span className="demo-outcome-label">Engine</span>
            <b>{outcome.title}</b>
            {outcome.code && <code className="code-chip">{outcome.code}</code>}
            <span className="demo-outcome-detail">{outcome.detail}</span>
          </p>
        )}
      </div>
      <div className="demo-actions">
        {!done && (
          <button className="btn small" onClick={onTogglePlay} disabled={busy && !playing}>
            {playing ? "Pause" : "Play"}
          </button>
        )}
        {!done && (
          <button className="btn btn-primary small" onClick={onNext} disabled={busy || playing}>
            Next step
          </button>
        )}
        <button className="btn small" onClick={onRestart} disabled={busy}>
          Restart demo
        </button>
        <button className="btn btn-ghost small" onClick={onClose} disabled={busy} aria-label="Close guided demo">
          Close
        </button>
      </div>
    </section>
  );
}
