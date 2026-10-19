import { runTheory, type TheoryRequest, type TheoryResult } from "./theoryJobs";

let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, { ok: (r: TheoryResult) => void; fail: (e: Error) => void }>();

function getWorker(): Worker | null {
  if (worker) return worker;
  if (typeof Worker === "undefined") return null;
  try {
    worker = new Worker(new URL("./theory.worker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (e: MessageEvent<{ id: number; result?: TheoryResult; error?: string }>) => {
      const p = pending.get(e.data.id);
      if (!p) return;
      pending.delete(e.data.id);
      if (e.data.error) p.fail(new Error(e.data.error)); else p.ok(e.data.result as TheoryResult);
    };
    worker.onerror = () => { worker = null; };
    return worker;
  } catch {
    return null;
  }
}

/** Run a calculation off the main thread; falls back to running it here when workers are not available. */
export function compute(req: TheoryRequest): Promise<TheoryResult> {
  const w = getWorker();
  if (!w) return new Promise((ok, fail) => { setTimeout(() => { try { ok(runTheory(req)); } catch (e) { fail(e as Error); } }, 0); });
  const id = nextId++;
  return new Promise((ok, fail) => { pending.set(id, { ok, fail }); w.postMessage({ id, req }); });
}
