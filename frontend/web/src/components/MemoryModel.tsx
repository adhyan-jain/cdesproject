// The signature visual: STRATA's one buffer, index | records → | free | ← undo, playing the
// story of one scope. It is a schematic (widths are proportional, not byte-exact); the Live lab
// shows the real buffer decoded from the C++ table.
import { useEffect, useState } from "react";
import { reducedMotion } from "../lib/motion";

type Rec = { id: string; name: string; scope: 0 | 1 };
type Undo = { id: string; kind: "mark" | "shadow" | "new"; label: string };
export interface Frame {
  key: string;
  title: string;          // the story headline, e.g. "SCOPE ENTERS."
  call: string;           // the call a compiler makes at this moment
  text: string;           // one sentence of explanation
  records: Rec[];
  undo: Undo[];
  visible: { name: string; from: "global" | "scope"; hidden?: boolean }[];
}

const G_COUNT: Rec = { id: "g-count", name: "count", scope: 0 };
const G_TOTAL: Rec = { id: "g-total", name: "total", scope: 0 };
const S_COUNT: Rec = { id: "s-count", name: "count", scope: 1 };
const S_RATE: Rec = { id: "s-rate", name: "rate", scope: 1 };
const MARK: Undo = { id: "u-mark", kind: "mark", label: "mark" };
const SHADOW: Undo = { id: "u-shadow", kind: "shadow", label: "count" };
const NEW: Undo = { id: "u-new", kind: "new", label: "rate" };
const GLOBALS = [{ name: "count", from: "global" as const }, { name: "total", from: "global" as const }];

export const FRAMES: Frame[] = [
  { key: "one", title: "ONE BUFFER.", call: "Table t(buffer, size);", text: "The caller hands STRATA one block of memory. Nothing is allocated after this, ever.", records: [], undo: [], visible: [] },
  { key: "four", title: "FOUR REGIONS.", call: "declare(\"count\"); declare(\"total\");", text: "A hash index at the front, one record per name growing right, the undo stack growing left, free space between.", records: [G_COUNT, G_TOTAL], undo: [], visible: GLOBALS },
  { key: "enter", title: "SCOPE ENTERS.", call: "enter_scope();", text: "Opening a block pushes a mark on the undo stack. It costs a few bytes and no allocation.", records: [G_COUNT, G_TOTAL], undo: [MARK], visible: GLOBALS },
  { key: "grow", title: "RECORDS GROW.", call: "declare(\"count\"); declare(\"rate\");", text: "The inner count hides the outer one: its old binding is saved on the undo stack. Lookups now find the inner count.", records: [G_COUNT, G_TOTAL, S_COUNT, S_RATE], undo: [MARK, SHADOW, NEW], visible: [{ name: "count", from: "global", hidden: true }, { name: "total", from: "global" }, { name: "count", from: "scope" }, { name: "rate", from: "scope" }] },
  { key: "exit", title: "SCOPE EXITS.", call: "exit_scope();", text: "Leaving the block pops the undo stack back to its mark, newest entry first, and frees the scope's records.", records: [G_COUNT, G_TOTAL], undo: [MARK], visible: GLOBALS },
  { key: "undo", title: "UNDO RESTORES.", call: "lookup(\"count\");  // the outer count again", text: "The table is exactly what it was before the scope opened. When the buffer is full, a call is refused and changes nothing.", records: [G_COUNT, G_TOTAL], undo: [], visible: GLOBALS },
];

const SLOT_OF = [2, 5, 0, 6];  // the index slot each record's name hashes to (illustrative)
const INDEX_W = 14;          // % of the bar
const REC_W = 11;
const UNDO_W: Record<Undo["kind"], number> = { mark: 6, shadow: 9, new: 7 };
const REGION_INFO: Record<string, string> = {
  index: "Index · open-addressing hash slots. Fixed size; it never moves.",
  records: "Records · one packed record per name, appended to the right.",
  free: "Free · whatever is left. When a request does not fit, STRATA refuses it cleanly.",
  undo: "Undo · scope marks and saved bindings, growing to the left. Popped on scope exit.",
};

export function MemoryModel({ frame, size = "large", interactive = true }: { frame: number; size?: "large" | "compact"; interactive?: boolean }) {
  const f = FRAMES[Math.max(0, Math.min(FRAMES.length - 1, frame))];
  const [hover, setHover] = useState<string | null>(null);
  const recW = f.records.length * REC_W;
  const undoW = f.undo.reduce((s, u) => s + UNDO_W[u.kind], 0);
  const freeW = 100 - INDEX_W - recW - undoW;
  const regions = interactive ? { onPointerLeave: () => setHover(null) } : {};
  const hov = (k: string) => (interactive ? { onPointerEnter: () => setHover(k), onFocus: () => setHover(k), onBlur: () => setHover(null), tabIndex: 0 } : {});
  const dim = (k: string) => (hover && hover !== k ? " dim" : "");

  return (
    <figure className={`mm mm-${size}`} aria-label={`Memory model: ${f.title} ${f.text}`}>
      <div className="mm-meta mono"><span>MEMORY MODEL / 01</span><span>BUFFER / FIXED</span><span>ALLOCATOR / NONE</span></div>
      <div className="mm-arrows mono" aria-hidden="true">
        <span style={{ left: `${INDEX_W}%` }}>records →</span>
        <span className="r">← undo</span>
      </div>
      <div className="mm-bar" {...regions}>
        <div className={`mm-region mm-index${dim("index")}`} style={{ width: `${INDEX_W}%` }} {...hov("index")}>
          <div className="mm-slots" aria-hidden="true">{Array.from({ length: 8 }, (_, i) => <i key={i} className={SLOT_OF.slice(0, f.records.length).includes(i) ? "on" : ""} />)}</div>
          <span className="mm-name">index</span>
        </div>
        <div className={`mm-region mm-records${dim("records")}`} style={{ width: `${recW}%` }} {...hov("records")}>
          {f.records.map((r) => <span key={r.id} className={`mm-rec s${r.scope}`}><b>{r.name}</b></span>)}
        </div>
        <div className={`mm-region mm-free${dim("free")}`} style={{ width: `${freeW}%` }} {...hov("free")}>
          <span className="mm-name">free</span>
        </div>
        <div className={`mm-region mm-undo${dim("undo")}`} style={{ width: `${undoW}%` }} {...hov("undo")}>
          {[...f.undo].reverse().map((u) => <span key={u.id} className={`mm-u ${u.kind}`} title={u.label}>{size === "large" ? u.label : ""}</span>)}
        </div>
      </div>
      <div className="mm-caption">
        <code className="mm-call">{f.call}</code>
        <span className="mm-hint">{hover ? REGION_INFO[hover] : f.visible.length ? "Visible names" : "Empty: index slots only"}</span>
      </div>
      {!hover && f.visible.length > 0 && (
        <ul className="mm-names" aria-label="Names a lookup can see">
          {f.visible.map((v, i) => (
            <li key={v.name + v.from + i} className={`${v.from}${v.hidden ? " hidden" : ""}`}>
              <span className="mono">{v.name}</span><small>{v.hidden ? "hidden" : v.from}</small>
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}

/** Plays frames 1–5 in a loop (the hero). Pauses while hovered; static with reduced motion. */
export function MemoryModelLoop() {
  const [frame, setFrame] = useState(3);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    if (reducedMotion() || paused) return;
    const t = setTimeout(() => setFrame((f) => (f >= FRAMES.length - 1 ? 1 : f + 1)), frame === 3 ? 3200 : 2200);
    return () => clearTimeout(t);
  }, [frame, paused]);
  return (
    <div className="mm-loop" onPointerEnter={() => setPaused(true)} onPointerLeave={() => setPaused(false)}>
      <div className="mm-steps mono" aria-hidden="true">
        {FRAMES.slice(1).map((f, i) => (
          <button key={f.key} className={frame === i + 1 ? "on" : ""} onClick={() => setFrame(i + 1)} tabIndex={-1}>{String(i + 1).padStart(2, "0")}</button>
        ))}
        <span className="mm-step-title">{FRAMES[frame].title}</span>
      </div>
      <MemoryModel frame={frame} />
    </div>
  );
}
