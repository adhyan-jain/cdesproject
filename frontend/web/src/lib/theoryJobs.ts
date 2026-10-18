// The heavy calculations of the Theory page, as plain functions of a request. They run in a web worker
// (theory.worker.ts) so that the page stays responsive at m = 4096, and inline if workers are unavailable.
import { churnBound, refusalProbability, smallestL, unlimitedRunProbability } from "./theory";

export type TheoryRequest =
  | { kind: "point"; m: number; n: number; L: number; s: number }
  | { kind: "design"; m: number; n: number; s: number; eps: number };

export type TheoryResult =
  | { kind: "point"; refusal: number; unlimited: number; churn: number }
  | { kind: "design"; onePush: number; unlimited: number; churn: number };

export function runTheory(req: TheoryRequest): TheoryResult {
  if (req.kind === "point") {
    return {
      kind: "point",
      refusal: refusalProbability(req.m, req.n, req.L),
      unlimited: unlimitedRunProbability(req.m, req.n, req.L),
      churn: churnBound(req.m, req.n, req.s, req.L),
    };
  }
  const onePush = smallestL((L) => refusalProbability(req.m, req.n, L), req.eps, 2, req.m);
  const unlimited = smallestL((L) => unlimitedRunProbability(req.m, req.n, L), req.eps, 2, req.m);
  const churn = smallestL((L) => churnBound(req.m, req.n, req.s, L), req.eps, Math.max(2, unlimited), req.m);
  return { kind: "design", onePush, unlimited, churn };
}
