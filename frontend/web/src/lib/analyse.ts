// "Analyse your code": a pasted C program becomes the calls a compiler makes on its symbol table
// (lib/minic.ts, relaxed mode), the real strata::Table runs them (server/api.mjs -> engine), and
// this file turns the two into a plain report: every name, where it is declared and used, what it
// hides, and the smallest fixed buffer that holds the whole program.
import { runOps, type EngineState, type Op, type OpResult } from "./engine";
import { compile, type LineOp } from "./minic";

const BUFFER_STEPS = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536];

export interface NameInfo {
  id: number;
  name: string;
  ctype: string;
  kind: "var" | "param" | "function";
  line: number;
  depth: number;            // 0 = global
  uses: number[];           // source lines of the lookups that found this declaration
  shadows?: { line: number; depth: number };   // the outer declaration it hides
  shadowedBy: number[];     // lines of inner declarations that hide it
  redeclared?: boolean;     // refused: same name already declared in this scope
}

export interface Problem { line: number; kind: "undeclared" | "redeclared" | "unused" | "refused"; text: string }

export interface Report {
  lines: number;
  ops: number;
  declarations: number;
  lookups: number;
  scopes: number;
  maxDepth: number;
  names: NameInfo[];
  problems: Problem[];
  buffer: { bytes: number; state: EngineState } | null;   // smallest buffer with no refusal
  tooSmall: { bytes: number; refusedAt: number } | null;   // the step below it, where the table refused
  checksOk: boolean;
}

const refused = (r: OpResult) => r.effect === "refused" && r.status !== "kRedeclared";

/** Smallest buffer from BUFFER_STEPS on which the engine refuses no operation for lack of room. */
async function smallestBuffer(ops: Op[]) {
  let below: Report["tooSmall"] = null;
  for (const bytes of BUFFER_STEPS) {
    const state = await runOps(bytes, ops);
    const i = state.ops.findIndex(refused);
    if (i < 0) return { buffer: { bytes, state }, tooSmall: below };
    below = { bytes, refusedAt: i };
  }
  return { buffer: null, tooSmall: below };
}

export async function analyse(src: string): Promise<Report> {
  const { ops } = compile(src, { relaxed: true });
  const plain: Op[] = ops.map(({ line: _l, ctype: _c, kind: _k, ...op }) => op as Op);
  const { buffer, tooSmall } = await smallestBuffer(plain);
  // With no fitting buffer, report from the largest run (its later operations were refused).
  const state = buffer?.state ?? (await runOps(BUFFER_STEPS[BUFFER_STEPS.length - 1], plain));
  return build(src, ops, state, buffer, tooSmall);
}

function build(src: string, ops: LineOp[], state: EngineState, buffer: Report["buffer"], tooSmall: Report["tooSmall"]): Report {
  // Replay the scope structure next to the engine's answers to attribute each use to a declaration.
  const names: NameInfo[] = [];
  const scopes: Map<string, number>[] = [new Map()];
  const problems: Problem[] = [];
  let maxDepth = 0, scopeCount = 0, lookups = 0, decls = 0;
  const resolve = (name: string) => {
    for (let d = scopes.length - 1; d >= 0; d--) { const id = scopes[d].get(name); if (id !== undefined) return id; }
    return undefined;
  };
  const use = (name: string, line: number, found: boolean | undefined) => {
    lookups++;
    const id = resolve(name);
    if (id !== undefined && found !== false) names[id].uses.push(line);
    else problems.push({ line, kind: "undeclared", text: `"${name}" is used but never declared (or declared later).` });
  };

  ops.forEach((op, i) => {
    const r = state.ops[i];
    if (!r) return;
    switch (op.op) {
      case "enter": scopes.push(new Map()); scopeCount++; maxDepth = Math.max(maxDepth, scopes.length - 1); break;
      case "exit": if (scopes.length > 1) scopes.pop(); break;
      case "lookup": use(op.name, op.line, r.found); break;
      case "declare":
      case "declareFrom": {
        if (op.op === "declareFrom") use(op.src, op.line, r.srcFound);
        decls++;
        if (r.effect === "refused") {
          if (r.status === "kRedeclared") problems.push({ line: op.line, kind: "redeclared", text: `"${op.name}" is declared twice in the same scope.` });
          else problems.push({ line: op.line, kind: "refused", text: `The table ran out of room at "${op.name}" (${r.status}).` });
          break;
        }
        const outer = resolve(op.name);
        const info: NameInfo = {
          id: names.length, name: op.name, ctype: op.ctype ?? "int", kind: op.kind ?? "var", line: op.line,
          depth: scopes.length - 1, uses: [], shadowedBy: [],
        };
        if (outer !== undefined) {
          info.shadows = { line: names[outer].line, depth: names[outer].depth };
          names[outer].shadowedBy.push(op.line);
        }
        names.push(info);
        scopes[scopes.length - 1].set(op.name, info.id);
        break;
      }
    }
  });
  for (const n of names)
    if (n.uses.length === 0 && n.kind !== "function")
      problems.push({ line: n.line, kind: "unused", text: `${n.kind === "param" ? "Parameter" : "Variable"} "${n.name}" is declared but never used.` });
  problems.sort((a, b) => a.line - b.line);

  return {
    lines: src.split("\n").length,
    ops: ops.length,
    declarations: decls,
    lookups,
    scopes: scopeCount,
    maxDepth,
    names,
    problems,
    buffer,
    tooSmall,
    checksOk: state.checks.invariants && state.checks.resolveAgrees && state.checks.modelAgrees,
  };
}

export const SAMPLE = `#include <stdio.h>

static const int LIMIT = 100;
int total = 0;

double average(const int *values, int n) {
    long sum = 0;
    for (int i = 0; i < n; i++) {
        sum += values[i];
    }
    return (double) sum / n;
}

int main(void) {
    int data[5] = {4, 8, 15, 16, 23};
    int total = 5;              /* hides the global total */
    unsigned int count = 0;
    while (count < 3) {
        int step = 2;
        count += step;
    }
    double avg = average(data, total);
    char unused = 'x';
    printf("%f %d %d\\n", avg, count, LIMIT);
    return 0;
}
`;
