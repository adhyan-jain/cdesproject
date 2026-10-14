// End-to-end checks of the demo engine: request validation -> strata_engine -> strata::Table.
// Run with `npm test` in frontend/web.
import { test } from "node:test";
import assert from "node:assert/strict";
import { runEngine, toScript } from "../server/api.mjs";

const run = (ops, capacity = 256) => runEngine(toScript({ capacity, ops }));
const D = (name, value, type = 0) => ({ op: "declare", name, type, value });
const L = (name) => ({ op: "lookup", name });
const E = { op: "enter" }, X = { op: "exit" };
const visible = (s) => Object.fromEntries(s.records.map((r) => [r.name, [r.value, r.depth]]));
const checksPass = (s) => assert.deepEqual(s.checks, { invariants: true, resolveAgrees: true, modelAgrees: true });

test("declaring stores the name in the current scope", async () => {
  const s = await run([D("count", 1)]);
  assert.equal(s.ops[0].status, "kOk");
  assert.equal(s.ops[0].effect, "new");
  assert.deepEqual(visible(s), { count: [1, 0] });
  assert.equal(s.stats.liveDeclarations, 1);
  checksPass(s);
});

test("lookup returns the innermost visible declaration", async () => {
  const s = await run([D("count", 1), E, D("count", 2), L("count"), L("missing")]);
  assert.equal(s.ops[3].found, true);
  assert.equal(s.ops[3].value, 2);
  assert.equal(s.ops[3].depth, 1);
  assert.equal(s.ops[4].found, false);
  assert.equal(s.ops[3].changed, false, "a lookup must not change the table");
  checksPass(s);
});

test("shadowing saves the hidden declaration on the undo stack", async () => {
  const s = await run([D("count", 1), E, D("count", 2)]);
  assert.equal(s.ops[2].effect, "shadow");
  assert.deepEqual(s.ops[2].hidden, { value: 1, type: 0, depth: 0 });
  const shadow = s.undo.find((u) => u.kind === "shadow");
  assert.equal(shadow.name, "count");
  assert.equal(shadow.value, 1);
  checksPass(s);
});

test("exiting a scope restores the outer declaration and removes new names", async () => {
  const s = await run([D("count", 1), E, D("count", 2), D("tmp", 7), X, L("count"), L("tmp")]);
  const exit = s.ops[4];
  assert.equal(exit.effect, "exited");
  assert.deepEqual(exit.removed.map((r) => r.name), ["tmp"]);
  assert.equal(exit.restored[0].restored.value, 1);
  assert.equal(s.ops[5].value, 1);
  assert.equal(s.ops[6].found, false);
  assert.deepEqual(visible(s), { count: [1, 0] });
  checksPass(s);
});

test("nested scopes unwind one level at a time", async () => {
  const s = await run([D("x", 0), E, D("x", 1), E, D("x", 2), L("x"), X, L("x"), X, L("x")]);
  assert.deepEqual([s.ops[5].value, s.ops[7].value, s.ops[9].value], [2, 1, 0]);
  assert.equal(s.stats.depth, 0);
  checksPass(s);
});

test("a full buffer refuses with kNoMemory and leaves the table unchanged", async () => {
  const ops = [D("count", 1)];
  for (let i = 0; i < 12; i++) ops.push(D(`symbol_filler_${String(i).padStart(2, "0")}`, i));
  ops.push(L("count"));
  const s = await run(ops);
  const refused = s.ops.filter((o) => o.status === "kNoMemory");
  assert.ok(refused.length > 0, "the 256-byte buffer must fill up");
  for (const o of refused) {
    assert.equal(o.changed, false);
    assert.equal(o.digestBefore, o.digestAfter);
  }
  assert.equal(s.ops[s.ops.length - 1].value, 1, "earlier declarations are intact");
  assert.ok(s.stats.used <= s.stats.capacity);
  checksPass(s);
});

test("exit at the outermost scope is refused with kNoScope", async () => {
  const s = await run([X]);
  assert.equal(s.ops[0].status, "kNoScope");
  assert.equal(s.ops[0].changed, false);
});

test("redeclaring in the same scope replaces the value", async () => {
  const s = await run([D("a", 1), D("a", 5)]);
  assert.equal(s.ops[1].status, "kRedeclared");
  assert.deepEqual(visible(s), { a: [5, 0] });
  checksPass(s);
});

test("the same script always gives the same table (reset and replay are deterministic)", async () => {
  const ops = [D("count", 1), E, D("count", 2), X, D("n", 3)];
  const [a, b] = await Promise.all([run(ops), run(ops)]);
  assert.equal(a.digest, b.digest);
  const empty = await run([]);
  assert.equal(empty.stats.liveDeclarations, 0);
  assert.equal(empty.records.length, 0);
});

test("byte counts add up and match the decoded layout", async () => {
  const s = await run([D("count", 1), E, D("count", 2), D("tmp", 7)], 512);
  const st = s.stats;
  assert.equal(st.index + st.records + st.undo + st.free, st.capacity);
  assert.equal(st.index, st.indexSlots * 4);
  assert.equal(s.undo.reduce((n, u) => n + u.words, 0) * 4, st.undo);
  assert.equal((1 + s.records.reduce((n, r) => n + r.words, 0)) * 4, st.records);
});

test("invalid requests are rejected before reaching the engine", () => {
  assert.throws(() => toScript({ capacity: 256, ops: [D("2bad", 1)] }), /invalid name/);
  assert.throws(() => toScript({ capacity: 256, ops: [D("a b", 1)] }), /invalid name/);
  assert.throws(() => toScript({ capacity: 256, ops: [D("ok", 2 ** 31)] }), /32-bit/);
  assert.throws(() => toScript({ capacity: 100, ops: [] }), /capacity/);
  assert.throws(() => toScript({ capacity: 256, ops: [{ op: "rm" }] }), /unknown operation/);
});

test("the engine itself rejects malformed scripts", async () => {
  const bad = await runEngine("CAP 256\nD 9x 0 1\n");
  assert.equal(bad.ok, false);
  const nocap = await runEngine("D a 0 1\n");
  assert.equal(nocap.ok, false);
});
