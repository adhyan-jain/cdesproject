// Checks of the code window's C subset (src/lib/minic.ts) and of the live trace check.
// minic.ts is bundled with esbuild (installed with Vite) so that Node can import it.
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSync } from "esbuild";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
import { runEngine, toScript, traceScript } from "../server/api.mjs";

const here = fileURLToPath(new URL(".", import.meta.url));
const out = buildSync({ entryPoints: [join(here, "..", "src", "lib", "minic.ts")], bundle: true, format: "esm", write: false, platform: "neutral" });
const file = join(mkdtempSync(join(tmpdir(), "minic-")), "minic.mjs");
writeFileSync(file, out.outputFiles[0].text);
const { compile, CodeError, EXAMPLES } = await import(pathToFileURL(file).href);

const short = (ops) => ops.map((o) =>
  o.op === "declare" ? `D ${o.name}=${o.value}` : o.op === "declareFrom" ? `V ${o.name}<-${o.src}` : o.op === "lookup" ? `L ${o.name}` : o.op === "enter" ? "E" : "X");
const run = (src, capacity = 512) => {
  const { ops } = compile(src);
  return runEngine(toScript({ capacity, ops: ops.map(({ line, ...o }) => o) }));
};
const example = (title) => EXAMPLES.find((e) => e.title === title).code;

test("shadowing example becomes declare / scope / lookup calls", () => {
  assert.deepEqual(short(compile(example("Shadowing")).ops), ["D x=1", "E", "D x=2", "L x", "X", "L x"]);
});

test("functions open one scope for parameters and body", () => {
  assert.deepEqual(short(compile("int f(int a, int b) { int c = a; return c + b; }").ops),
    ["D f=0", "E", "D a=0", "D b=0", "V c<-a", "L c", "L b", "X"]);
});

test("a for loop variable lives in its own scope", () => {
  assert.deepEqual(short(compile("for (int i = 0; i < 3; i++) { i; }").ops), ["E", "D i=0", "L i", "L i", "E", "L i", "X", "X"]);
});

test("library calls and string literals are not looked up", () => {
  assert.deepEqual(short(compile('int x = 1; printf("%d %s", x, "y");').ops), ["D x=1", "L x"]);
});

test("every operation carries its source line", () => {
  const { ops } = compile("int a = 1;\n{\n  a;\n}\n");
  assert.deepEqual(ops.map((o) => o.line), [1, 2, 3, 4]);
});

test("errors name the line", () => {
  const cases = [["int x = 1;\n{\n  int y = 2;\n", 2, /never closed/], ["double d = 1.0;", 1, /not supported/], ["int x = 1\nint y = 2;", 1, /Missing ';'/], ["x = 5\ny = 6;", 1, /Missing ';'/], ["}", 1, /no matching/]];
  for (const [src, line, re] of cases) {
    assert.throws(() => compile(src), (e) => e instanceof CodeError && e.line === line && re.test(e.message), src);
  }
});

test("every example runs on the real table and agrees with the reference model", async () => {
  for (const ex of EXAMPLES) {
    const s = await run(ex.code, ex.title.includes("256") ? 256 : 512);
    assert.deepEqual(s.checks, { invariants: true, resolveAgrees: true, modelAgrees: true }, ex.title);
  }
});

test("shadowing example: inner lookup 2, outer lookup 1", async () => {
  const s = await run(example("Shadowing"));
  const looks = s.ops.filter((o) => o.op === "L").map((o) => o.value);
  assert.deepEqual(looks, [2, 1]);
});

test("undeclared example: the out-of-scope name is reported, nothing is declared", async () => {
  const s = await run(example("Undeclared name"));
  const v = s.ops.find((o) => o.op === "V" && o.src === "b");
  assert.equal(v.effect, "undeclared");
  assert.equal(v.changed, false);
  assert.ok(!s.records.some((r) => r.name === "c"));
});

test("declaring from a float converts like C", async () => {
  const s = await run("float r = 2.5;\nint n = r;\nn;");
  assert.equal(s.ops[2].value, 2);
});

test("fill example refuses with kNoMemory in a 256-byte buffer", async () => {
  const s = await run(example("Fill a 256-byte buffer"), 256);
  const refused = s.ops.filter((o) => o.status === "kNoMemory");
  assert.equal(refused.length, 1);
  assert.equal(refused[0].changed, false);
  assert.equal(s.ops[s.ops.length - 1].value, 1);
});

test("live trace check: zlib replays with no wrong answer and less memory than the conventional table", async () => {
  const r = await runEngine(traceScript("zlib"), 120000);
  assert.equal(r.ok, true);
  assert.equal(r.ops, 58058);
  assert.equal(r.strata.wrongLookups + r.strata.wrongDeclares + r.strata.refused, 0);
  assert.equal(r.arena.wrongLookups + r.arena.wrongDeclares + r.arena.refused, 0);
  assert.ok(r.strata.invariants);
  assert.ok(r.strata.peakBytes < r.arena.peakBytes);
  assert.throws(() => traceScript("../../etc/passwd"), /unknown trace/);
});

// ---- relaxed mode (Analyse your code): the wider C people paste ----------------------------
const relaxed = (src) => compile(src, { relaxed: true }).ops;

test("relaxed: qualifiers, long/unsigned/double, pointers and arrays are understood", () => {
  const ops = relaxed("static const unsigned long m = 0x1F;\ndouble f(const int *p, int n[]) { long s = 0; return s; }\nint a[3] = {1, m, 2};\nchar *s = \"x\";");
  assert.deepEqual(short(ops), ["D m=31", "D f=0", "E", "D p=0", "D n=0", "D s=0", "L s", "X", "L m", "D a=0", "D s=0"]);
  assert.deepEqual(ops.filter((o) => o.ctype).map((o) => o.ctype), ["static const unsigned long", "double", "const int *", "int[]", "long", "int[]", "char *"]);
  assert.deepEqual(ops.filter((o) => o.kind).map((o) => o.kind), ["var", "function", "param", "param", "var", "var", "var"]);
});

test("relaxed: do, switch, case and casts", () => {
  assert.deepEqual(short(relaxed("int x = 1;\ndo { x++; } while (x < 3);\nswitch (x) { case 1: x = (unsigned long) x; break; default: break; }")),
    ["D x=1", "E", "L x", "X", "L x", "L x", "E", "L x", "L x", "X"]);
});

test("relaxed: still reports real mistakes, and struct is named as unsupported", () => {
  assert.throws(() => relaxed("int x = 1\nint y;"), (e) => e instanceof CodeError && e.line === 1 && /Missing ';'/.test(e.message));
  assert.throws(() => relaxed("struct p { int x; };"), (e) => e instanceof CodeError && /not analysed yet/.test(e.message));
});

test("relaxed: a pasted program runs on the real table and every check passes", async () => {
  const ops = relaxed("long total = 0;\nint main(void) {\n  int total = 5;\n  double avg = total;\n  return (int) avg;\n}\n");
  const r = await runEngine(toScript({ capacity: 512, ops: ops.map(({ line, ctype, kind, ...o }) => o) }));
  assert.equal(r.ok, true);
  assert.deepEqual([r.checks.invariants, r.checks.resolveAgrees, r.checks.modelAgrees], [true, true, true]);
  assert.equal(r.ops.find((o) => o.name === "total" && o.op === "D" && o.depthAfter === 1).effect, "shadow");
});
