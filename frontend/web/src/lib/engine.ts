// Client for the local engine API (server/api.mjs -> frontend/engine/strata_engine.cpp).
// The UI keeps the list of operations; every change sends the whole list and the engine
// replays it on a fresh strata::Table, so the C++ table is always the source of truth.

export type Op =
  | { op: "declare"; name: string; type: number; value: number }
  | { op: "declareFrom"; name: string; type: number; src: string }
  | { op: "lookup"; name: string }
  | { op: "enter" }
  | { op: "exit" };

export type StatusName = "kOk" | "kRedeclared" | "kNoMemory" | "kNameTooLong" | "kEmptyName" | "kNoScope" | "kTooDeep" | "kProbeLimit";

export interface Decl { value: number; type: number; depth: number }
export interface ExitItem extends Decl { name: string; restored?: Decl }

export interface OpResult {
  op: "D" | "V" | "L" | "E" | "X";
  src?: string;
  srcFound?: boolean;
  srcValue?: number;
  srcType?: number;
  name?: string;
  type?: number;
  value?: number;
  status?: StatusName;
  code?: number;
  effect: "undeclared" | "new" | "shadow" | "redeclared" | "refused" | "found" | "missing" | "entered" | "exited";
  hidden?: Decl;
  removed?: ExitItem[];
  restored?: ExitItem[];
  found?: boolean;
  depth?: number;
  changed: boolean;
  digestBefore: string;
  digestAfter: string;
  usedBytes: number;
  depthAfter: number;
}

export interface RecordView { name: string; value: number; type: number; depth: number; ref: number; words: number }
export type UndoView =
  | { kind: "mark"; pos: number; words: number; itop: number }
  | { kind: "new"; pos: number; words: number; name: string; slot: number }
  | { kind: "shadow"; pos: number; words: number; name: string; value: number; type: number; depth: number };
export interface SlotView { slot: number; fp: number; ref: number; name: string; home: number; probe: number }

export interface EngineState {
  ok: true;
  engine: { source: string; header: string; compiler: string; mode: string };
  capacityBytes: number;
  stats: {
    capacity: number; used: number; peak: number; index: number; records: number; undo: number; free: number;
    liveDeclarations: number; liveIdentifiers: number; depth: number; indexSlots: number; rebuilds: number;
  };
  checks: { invariants: boolean; resolveAgrees: boolean; modelAgrees: boolean };
  digest: string;
  ops: OpResult[];
  records: RecordView[];
  undo: UndoView[];
  index: SlotView[];
}

export class EngineError extends Error {
  constructor(message: string, readonly unavailable: boolean) { super(message); }
}

export async function runOps(capacity: number, ops: Op[]): Promise<EngineState> {
  let res: Response;
  try {
    res = await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ capacity, ops }) });
  } catch {
    throw new EngineError("Cannot reach the local demo server. Is `npm start` still running?", true);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok || !body?.ok) throw new EngineError(body?.error ?? `engine error (HTTP ${res.status})`, res.status >= 500);
  return body as EngineState;
}

export async function health(): Promise<{ compiler: string } | null> {
  try {
    const res = await fetch("/api/health");
    const body = await res.json();
    return body.ok ? { compiler: body.engine.compiler } : null;
  } catch {
    return null;
  }
}
