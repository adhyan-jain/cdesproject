// Copies the recorded results of the paper run into src/data/recorded.json, so the page shows
// numbers read from the result files rather than typed in by hand. Run: npm run results
//   results/raw/20261013-143828-paper/compiler_summary.csv          correctness, peak heap, allocations
//   results/summary/20261013-143828-paper/compiler_strata_vs_all.csv STRATA against each table
//   results/summary/20261013-143828-paper/decomposition.csv         smallest fixed buffers, paired time
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { repoRoot, webRoot } from "../server/paths.mjs";

const RUN = "20261013-143828-paper";
const TRACES = ["cjson", "littlefs", "zlib", "freertos", "lua", "tinycc", "sqlite", "mbedtls"];
// Tables compared in the demo. The METIS tables are left out of the demo on purpose.
const IMPLS = { strata: "STRATA", arena_chain: "Conventional single-buffer table", std_undo_log: "std::unordered_map + undo log",
  swiss_undo_log: "Swiss map + undo log", scope_map_stack: "One hash map per scope", swiss_interned: "Interned Swiss flat map" };
const BASELINE_ROWS = { "arena + chains (allocator-free)": "arena_chain", "std map + undo log": "std_undo_log",
  "Swiss node map + undo log": "swiss_undo_log", "map per scope": "scope_map_stack", "Swiss flat map, interned": "swiss_interned" };

function csv(path) {
  const [head, ...rows] = readFileSync(path, "utf8").trim().split(/\r?\n/).map(parseLine);
  return rows.map((r) => Object.fromEntries(head.map((h, i) => [h.trim(), r[i]])));
}
function parseLine(line) {
  const out = []; let cur = "", q = false;
  for (const c of line) {
    if (c === '"') q = !q; else if (c === "," && !q) { out.push(cur); cur = ""; } else cur += c;
  }
  out.push(cur);
  return out;
}
const r1 = (x) => Math.round(Number(x) * 10) / 10;

const raw = join(repoRoot, "results", "raw", RUN), sum = join(repoRoot, "results", "summary", RUN);
const summary = csv(join(raw, "compiler_summary.csv")).filter((r) => TRACES.includes(r.trace));
const env = Object.fromEntries(readFileSync(join(raw, "environment.txt"), "utf8").split(/\r?\n/).filter(Boolean).map((l) => [l.split(":")[0], l.slice(l.indexOf(":") + 1).trim()]));

const correctness = Object.entries(IMPLS).map(([impl, label]) => {
  const rows = summary.filter((r) => r.impl === impl);
  const checked = rows.reduce((n, r) => n + Number(r.lookups) + Number(r.declares), 0);
  const wrong = rows.reduce((n, r) => n + Number(r.wrong_lookups) + Number(r.wrong_declares), 0);
  const refused = rows.reduce((n, r) => n + Number(r.refused_declares), 0);
  return { impl, label, traces: rows.length, checked, wrong, refused };
});

// This file repeats the column name "median" (heap, then time), so it is read by position:
// baseline, traces, faster, slower, heap min, heap median, heap max, time min, time median, time max
const vsAll = readFileSync(join(sum, "compiler_strata_vs_all.csv"), "utf8").trim().split(/\r?\n/).slice(1).map(parseLine)
  .filter((c) => BASELINE_ROWS[c[0]])
  .map((c) => ({
    impl: BASELINE_ROWS[c[0]], label: IMPLS[BASELINE_ROWS[c[0]]], traces: Number(c[1]), faster: Number(c[2]), slower: Number(c[3]),
    heapMin: r1(c[4]), heapMedian: r1(c[5]), heapMax: r1(c[6]), timeMin: r1(c[7]), timeMedian: r1(c[8]), timeMax: r1(c[9]),
  }));

const decomposition = Object.fromEntries(csv(join(sum, "decomposition.csv")).map((r) => [r.trace, {
  strataBufferKiB: r1(r["STRATA fixed buffer KiB"]), arenaBufferKiB: r1(r["arena+chains fixed buffer KiB"]),
  bufferReductionPct: r1(r["memory: STRATA vs arena+chains, red. %"]),
  timeVsArenaPct: r1(r["time: STRATA vs arena+chains, red. %"]), ciLow: r1(r["CI low"]), ciHigh: r1(r["CI high"]),
}]));

const perTrace = TRACES.map((t) => {
  const get = (impl) => summary.find((r) => r.trace === t && r.impl === impl);
  const s = get("strata"), a = get("arena_chain"), u = get("std_undo_log");
  return {
    trace: t, ops: Number(s.ops), checked: Number(s.lookups) + Number(s.declares), wrong: Number(s.wrong_lookups) + Number(s.wrong_declares),
    strataHeapKiB: r1(Number(s.peak_bytes) / 1024), stdHeapKiB: r1(Number(u.peak_bytes) / 1024),
    strataAllocs: Number(s.allocs), stdAllocs: Number(u.allocs),
    strataMs: Math.round(Number(s.replay_ns_median) / 1e4) / 100, stdMs: Math.round(Number(u.replay_ns_median) / 1e4) / 100,
    arenaMs: Math.round(Number(a.replay_ns_median) / 1e4) / 100,
    ...decomposition[t],
  };
});

const out = { run: RUN, cpu: env.cpu, compiler: env.compiler, kernel: env.kernel, rounds: env.rounds, correctness, vsAll, perTrace };
mkdirSync(join(webRoot, "src", "data"), { recursive: true });
writeFileSync(join(webRoot, "src", "data", "recorded.json"), JSON.stringify(out, null, 2) + "\n");
console.log(`wrote src/data/recorded.json from ${RUN}`);
