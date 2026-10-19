// The paper's formulas and a small model of non-reordering open addressing, in plain TypeScript.
// No imports: tests bundle this file with esbuild and compare every formula with the Python reference
// (theory/verify). Conventions follow the manuscript: a ring of m cells holds n = m - k keys, linear probing, a key is
// refused iff the L cells from its home are all occupied.

// ---- numerics -------------------------------------------------------------------------------------------------
const LF: number[] = [0];
function logFact(n: number): number {
  while (LF.length <= n) LF.push(LF[LF.length - 1] + Math.log(LF.length));
  return LF[n];
}
const logQ = (j: number, s: number) => Math.log(j / s) + (s - j) * Math.log(s) - logFact(s - j);

function convTrunc(a: Float64Array, b: Float64Array, cap: number): Float64Array {
  const out = new Float64Array(cap + 1);
  for (let i = 0; i < a.length && i <= cap; i++) {
    const ai = a[i];
    if (ai === 0) continue;
    const lim = Math.min(b.length, cap + 1 - i);
    for (let j = 0; j < lim; j++) out[i + j] += ai * b[j];
  }
  return out;
}

const maxOf = (v: Float64Array) => v.reduce((x, y) => Math.max(x, y), 0);

/** w^(*p) truncated at degree cap, as (normalised vector, log scale): the true power is vec * exp(logScale). */
function powerScaled(w: Float64Array, p: number, cap: number): [Float64Array, number] {
  let res = new Float64Array(cap + 1); res[0] = 1;
  let lres = 0;
  let base = w.slice(0, cap + 1); let lbase = 0;
  while (p > 0) {
    if (p & 1) {
      res = convTrunc(res, base, cap);
      const sc = maxOf(res); for (let i = 0; i < res.length; i++) res[i] /= sc;
      lres += Math.log(sc) + lbase;
    }
    p = Math.floor(p / 2);
    if (p > 0) {
      base = convTrunc(base, base, cap);
      const sc = maxOf(base); for (let i = 0; i < base.length; i++) base[i] /= sc;
      lbase = 2 * lbase + Math.log(sc);
    }
  }
  return [res, lres];
}

// ---- Theorem 7: refusal probability of one fresh push -----------------------------------------------------------
/** R_m(n, L): probability that a fresh key's first L cells are all occupied (n keys, m cells, linear probing). */
export function refusalProbability(m: number, n: number, L: number): number {
  const k = m - n;
  if (k <= 0 || L <= 0) return 1;
  if (k === 1) return Math.max(m - L, 0) / m;
  const lq = logQ(k, m);
  let tot = 0;
  for (let g = L + 1; g <= n + 1; g++) {
    if (m - g < k - 1) break;
    tot += (g - L) * Math.exp((g - 1) * Math.log(g) - logFact(g) + logQ(k - 1, m - g) - lq);
  }
  return (k / m) * tot;
}

// ---- Proposition 11: can a fresh name ever be refused at this occupancy? -----------------------------------------
function blockWeights(m: number, cap: number): Float64Array {
  const b = new Float64Array(m + 1);
  for (let g = 1; g <= Math.min(cap, m); g++) b[g] = Math.exp((g - 1) * Math.log(g) - logFact(g) - g);
  return b;
}
/** P(W > 0): probability that some block (an empty cell and the run after it) has more than L cells. */
export function unlimitedRunProbability(m: number, n: number, L: number): number {
  const k = m - n;
  if (k <= 0) return 1;
  if (L >= m) return 0;
  const num = powerScaled(blockWeights(m, L), k, m);
  const den = powerScaled(blockWeights(m, m), k, m);
  return Math.max(0, 1 - (num[0][m] / den[0][m]) * Math.exp(num[1] - den[1]));
}

// ---- Proposition 12: bounded churn above a persistent trunk -------------------------------------------------------
function gapWeights(keys: number, x: number): Float64Array {
  const w = new Float64Array(keys + 1);
  for (let g = 0; g <= keys; g++) w[g] = Math.exp((g > 0 ? (g - 1) * Math.log(g + 1) - logFact(g) : 0) + g * Math.log(x));
  return w;
}
function tilt(keys: number, empties: number): number {
  let lo = 1e-9, hi = Math.exp(-1) * (1 - 1e-12);
  for (let it = 0; it < 100; it++) {
    const x = (lo + hi) / 2;
    const w = gapWeights(3000, x);
    let a = 0, c = 0;
    for (let g = 0; g < w.length; g++) { a += w[g]; c += g * w[g]; }
    if (c / a < keys / empties) lo = x; else hi = x;
  }
  return (lo + hi) / 2;
}
/** D_s: closed-form bound on the probability that the trunk of `keys` keys has a window of L cells with at most s-1 empty cells. */
export function churnBound(m: number, keys: number, s: number, L: number): number {
  const e = m - keys;
  const T = Math.max(L - s + 1, 0);
  if (e <= s || s * keys >= e * T) return 1;
  const w = gapWeights(keys, tilt(keys, e));
  const [X, lx] = powerScaled(w, s - 1, keys);
  const [R, lr] = powerScaled(w, e - s - 1, keys);
  const [Z, lz] = powerScaled(w, e, keys);
  let num = 0;
  for (let u = 0; u <= Math.min(keys, T - 1); u++) {
    if (X[u] === 0) continue;
    const tau = T - u, r = keys - u;
    const lo = w.subarray(0, Math.min(tau, r + 1)), hi = w.subarray(tau, r + 1);
    if (hi.length === 0) continue;
    const conv = convTrunc(lo, hi, r);
    for (let j = 0; j < conv.length; j++) {
      const rest = r - (j + tau);
      if (conv[j] !== 0 && rest >= 0) num += X[u] * conv[j] * R[rest];
    }
  }
  return Math.min(1, ((e * num) / Z[keys]) * Math.exp(lx + lr - lz));
}

/** Smallest L in [lo, hi] with f(L) <= eps, by bisection (f is decreasing in L). */
export function smallestL(f: (L: number) => number, eps: number, lo = 2, hi = 4096): number {
  let a = lo, b = hi;
  while (a < b) { const mid = (a + b) >> 1; if (f(mid) <= eps) b = mid; else a = mid + 1; }
  return a;
}

// ---- Proposition 5: orphans ----------------------------------------------------------------------------------------
/** Mean number of keys that depend on a key (limit law): alpha / (2 (1 - alpha)). */
export const orphanMean = (alpha: number) => alpha / (2 * (1 - alpha));
/** Fraction of keys with no dependents (removable out of order): (1 - alpha)(e^alpha - 1)/alpha. */
export const noDependentsFraction = (alpha: number) => ((1 - alpha) * (Math.exp(alpha) - 1)) / alpha;

// ---- a small model of non-reordering open addressing (for the interactive pages) -----------------------------------
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface RingKey { id: number; home: number; cell: number }
export interface Ring { m: number; keys: RingKey[]; cells: number[] }   // cells[c] = id of the key stored there, or -1

export const emptyRing = (m: number): Ring => ({ m, keys: [], cells: new Array(m).fill(-1) });
export const cloneRing = (r: Ring): Ring => ({ m: r.m, keys: r.keys.map((k) => ({ ...k })), cells: r.cells.slice() });

/** Insert a key with the given home by linear probing; refuses (and changes nothing) after `limit` occupied cells. */
export function ringInsert(r: Ring, id: number, home: number, limit = Infinity): { ok: boolean; cell: number; probes: number } {
  let c = home, probes = 0;
  while (r.cells[c] !== -1) {
    c = (c + 1) % r.m; probes++;
    if (probes >= limit || probes >= r.m) return { ok: false, cell: -1, probes };
  }
  r.cells[c] = id;
  r.keys.push({ id, home, cell: c });
  return { ok: true, cell: c, probes };
}

/** Clear a key's cell and forget it. (Nothing else moves: the scheme never reorders.) */
export function ringClear(r: Ring, id: number): void {
  const i = r.keys.findIndex((k) => k.id === id);
  if (i < 0) return;
  r.cells[r.keys[i].cell] = -1;
  r.keys.splice(i, 1);
}

/** The table that inserting the live keys in their insertion order would give (Theorem 2's right-hand side). */
export function rebuild(r: Ring): Ring {
  const out = emptyRing(r.m);
  for (const k of r.keys) ringInsert(out, k.id, k.home);
  return out;
}
export const sameCells = (a: Ring, b: Ring) => a.cells.every((v, i) => v === b.cells[i]);

/** A lookup starts at the home and stops at the first empty cell: is the key still found? */
export function findable(r: Ring, k: RingKey): boolean {
  let c = k.home;
  for (let step = 0; step < r.m; step++) {
    if (r.cells[c] === k.id) return true;
    if (r.cells[c] === -1) return false;
    c = (c + 1) % r.m;
  }
  return false;
}

/** Keys y whose probe path passes strictly through k's cell before reaching their own: clearing k first orphans them. */
export function dependents(r: Ring, k: RingKey): number[] {
  const out: number[] = [];
  for (const y of r.keys) {
    if (y.id === k.id) continue;
    for (let c = y.home; c !== y.cell; c = (c + 1) % r.m) if (c === k.cell) { out.push(y.id); break; }
  }
  return out;
}

// ---- Proposition 12 on a concrete table: windows with few empty cells ---------------------------------------------
/** Empty cells in the window of L cells that starts at each cell (cyclic). */
export function windowEmpties(occ: boolean[], L: number): number[] {
  const m = occ.length, out: number[] = new Array(m).fill(0);
  let cur = 0;
  for (let t = 0; t < Math.min(L, m); t++) if (!occ[t]) cur++;
  out[0] = cur;
  for (let i = 1; i < m; i++) {
    if (!occ[i - 1]) cur--;
    if (!occ[(i + L - 1) % m]) cur++;
    out[i] = cur;
  }
  return out;
}

/** Occupancy of n keys with uniform homes under unrestricted linear probing on a ring of m cells. */
export function randomTrunk(m: number, n: number, rnd: () => number): boolean[] {
  const occ = new Array<boolean>(m).fill(false);
  for (let i = 0; i < n; i++) {
    let c = Math.floor(rnd() * m);
    while (occ[c]) c = (c + 1) % m;
    occ[c] = true;
  }
  return occ;
}

/** Fraction of random trunks that are s-vulnerable (some window of L cells with at most s-1 empty cells). */
export function vulnerabilityMonteCarlo(m: number, n: number, L: number, s: number, trials: number, seed: number): number {
  const rnd = mulberry32(seed);
  let hit = 0;
  for (let t = 0; t < trials; t++) {
    const w = windowEmpties(randomTrunk(m, n, rnd), L);
    if (Math.min(...w) <= s - 1) hit++;
  }
  return hit / trials;
}

/** The chain of at most s pushes from the proof of Proposition 12(b): fill the empty cells of a dense window, then push at its start. */
export function attackChain(occ: boolean[], L: number, s: number): { start: number; fills: number[] } | null {
  const w = windowEmpties(occ, L);
  let best = 0;
  for (let i = 1; i < w.length; i++) if (w[i] < w[best]) best = i;
  if (w[best] > s - 1) return null;
  const fills: number[] = [];
  for (let t = 0; t < L; t++) if (!occ[(best + t) % occ.length]) fills.push((best + t) % occ.length);
  return { start: best, fills };
}

/** Replay a chain on a probe-limited table: returns, per push, the cell used or -1 if refused. */
export function replayChain(occ: boolean[], L: number, chain: { start: number; fills: number[] }): { home: number; result: number }[] {
  const cells = occ.slice(), m = cells.length, steps: { home: number; result: number }[] = [];
  const push = (home: number) => {
    let c = home, probes = 0;
    while (cells[c]) { c = (c + 1) % m; probes++; if (probes >= L) { steps.push({ home, result: -1 }); return; } }
    cells[c] = true; steps.push({ home, result: c });
  };
  for (const f of chain.fills) push(f);
  push(chain.start);
  return steps;
}
