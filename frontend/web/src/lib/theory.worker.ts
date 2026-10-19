import { runTheory, type TheoryRequest } from "./theoryJobs";

// The DOM typings are in use, so describe the worker global by hand.
const ctx = self as unknown as {
  onmessage: ((e: { data: { id: number; req: TheoryRequest } }) => void) | null;
  postMessage: (m: unknown) => void;
};
ctx.onmessage = (e) => {
  const { id, req } = e.data;
  try {
    ctx.postMessage({ id, result: runTheory(req) });
  } catch (err) {
    ctx.postMessage({ id, error: err instanceof Error ? err.message : String(err) });
  }
};
