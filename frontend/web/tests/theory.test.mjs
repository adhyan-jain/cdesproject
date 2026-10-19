// Checks of the Theory page (src/lib/theory.ts): every formula against the Python reference values
// (theory/verify/make_frontend_reference.py), and the model's claims against brute force.
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSync } from "esbuild";
import { mkdtempSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));
const out = buildSync({ entryPoints: [join(here, "..", "src", "lib", "theory.ts")], bundle: true, format: "esm", write: false, platform: "neutral" });
const file = join(mkdtempSync(join(tmpdir(), "theory-")), "theory.mjs");
writeFileSync(file, out.outputFiles[0].text);
const T = await import(pathToFileURL(file).href);
const ref = JSON.parse(readFileSync(join(here, "theory_reference.json"), "utf8"));

const close = (a, b, rel, abs = 1e-12) => Math.abs(a - b) <= Math.max(abs, rel * Math.abs(b));

test("refusal law (Theorem 7) matches the Python implementation", () => {
  for (const r of ref.refusal) assert.ok(close(T.refusalProbability(r.m, r.n, r.L), r.value, 1e-9), JSON.stringify(r));
});
test("unlimited-run probability (Proposition 11) matches the Python implementation", () => {
  for (const r of ref.unlimited) assert.ok(close(T.unlimitedRunProbability(r.m, r.n, r.L), r.value, 1e-6, 1e-9), JSON.stringify(r));
});
test("churn bound D_s (Proposition 12) matches the Python implementation", () => {
  for (const r of ref.churn) assert.ok(close(T.churnBound(r.m, r.n, r.s, r.L), r.value, 1e-6, 1e-9), JSON.stringify(r));
});
test("design values reproduce the paper's tables", () => {
  const n = 3072;
  assert.equal(T.smallestL((L) => T.refusalProbability(4096, n, L), 1e-2), 59);        // Table sustain, one push
  assert.equal(T.smallestL((L) => T.unlimitedRunProbability(4096, n, L), 1e-2), 161);  // unlimited run
  assert.equal(T.smallestL((L) => T.churnBound(4096, n, 8, L), 1e-6, 300, 600), 410);  // Table band, s = 8
  assert.equal(T.smallestL((L) => T.unlimitedRunProbability(1024, 768, L), 1e-6), 259);  // unlimited run at 1e-6
});

const randomRing = (m, n, seed) => {
  const rnd = T.mulberry32(seed), r = T.emptyRing(m);
  for (let i = 0; i < n; i++) T.ringInsert(r, i, Math.floor(rnd() * m));
  return { r, rnd };
};

test("Theorem 2: after any push/pop sequence the table is the insertion of the live keys", () => {
  for (let seed = 1; seed <= 300; seed++) {
    const m = 20, rnd = T.mulberry32(seed), r = T.emptyRing(m);
    let id = 0;
    for (let step = 0; step < 120; step++) {
      if (r.keys.length > 0 && (rnd() < 0.45 || r.keys.length >= m - 1)) T.ringClear(r, r.keys[r.keys.length - 1].id);   // pop newest
      else T.ringInsert(r, id++, Math.floor(rnd() * m));
      assert.ok(T.sameCells(r, T.rebuild(r)), `seed ${seed} step ${step}`);
    }
  }
});

const safeOrder = (r0, order) => {
  const r = T.cloneRing(r0);
  for (const id of order) {
    T.ringClear(r, id);
    if (!r.keys.every((k) => T.findable(r, k))) return false;
  }
  return true;
};
const shuffle = (a, rnd) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

test("Theorem 4: a deletion order is safe iff it lists every key before the keys it depends on; reverse insertion order is always safe", () => {
  let safe = 0, unsafe = 0;
  for (let seed = 1; seed <= 200; seed++) {
    const { r, rnd } = randomRing(16, 11, seed);
    // reverse insertion order (stack order) is safe for every table
    assert.ok(safeOrder(r, r.keys.map((k) => k.id).reverse()), `LIFO seed ${seed}`);
    const dep = new Map(r.keys.map((k) => [k.id, new Set(T.dependents(r, k))]));   // dep.get(x) = keys that depend on x
    for (let t = 0; t < 12; t++) {
      const order = shuffle(r.keys.map((k) => k.id), rnd);
      const pos = new Map(order.map((id, i) => [id, i]));
      const extension = order.every((x) => [...dep.get(x)].every((y) => pos.get(y) < pos.get(x)));   // dependents go first
      assert.equal(safeOrder(r, order), extension, `seed ${seed} order ${order}`);
      extension ? safe++ : unsafe++;
    }
  }
  assert.ok(safe > 0 && unsafe > 0, "the test should see both safe and unsafe orders");
});

test("Proposition 5: mean number of dependents is close to alpha / (2 (1 - alpha))", () => {
  const { r } = randomRing(4000, 2000, 7);
  const mean = r.keys.reduce((s, k) => s + T.dependents(r, k).length, 0) / r.keys.length;
  assert.ok(Math.abs(mean - T.orphanMean(0.5)) < 0.05, `${mean} vs ${T.orphanMean(0.5)}`);
  const none = r.keys.filter((k) => T.dependents(r, k).length === 0).length / r.keys.length;
  assert.ok(Math.abs(none - T.noDependentsFraction(0.5)) < 0.03, `${none} vs ${T.noDependentsFraction(0.5)}`);
});

test("Proposition 12: the constructed chain of at most s pushes is refused exactly when a dense window exists", () => {
  const rnd = T.mulberry32(5);
  let found = 0, absent = 0;
  for (let t = 0; t < 400; t++) {
    const m = 60, n = 42, L = 12, s = 2;
    const occ = T.randomTrunk(m, n, rnd);
    const chain = T.attackChain(occ, L, s);
    const w = T.windowEmpties(occ, L);
    assert.equal(chain !== null, Math.min(...w) <= s - 1);
    if (chain) {
      found++;
      assert.ok(chain.fills.length + 1 <= s);
      const steps = T.replayChain(occ, L, chain);
      assert.equal(steps[steps.length - 1].result, -1, "the final push is refused");
      assert.ok(steps.slice(0, -1).every((x) => x.result >= 0), "the earlier pushes succeed");
    } else absent++;
  }
  assert.ok(found > 0 && absent > 0);
});

test("Proposition 12: simulated vulnerability never exceeds the closed-form bound", () => {
  for (const [m, n, L, s] of [[256, 192, 60, 1], [256, 192, 60, 2], [256, 192, 60, 4], [128, 96, 40, 3]]) {
    const trials = 3000, mc = T.vulnerabilityMonteCarlo(m, n, L, s, trials, 11);
    const d = T.churnBound(m, n, s, L), se = Math.sqrt(Math.max(mc * (1 - mc), 1e-4) / trials);
    assert.ok(mc <= d + 3 * se, `m=${m} L=${L} s=${s}: simulated ${mc} > bound ${d}`);
  }
});
