// Copies the recorded results into src/data/recorded.json, so the page shows numbers read from
// the result files rather than typed in by hand. Run: npm run results
//   results/raw/<RUN>/compiler_summary.csv            correctness, peak heap, allocations, replay time per table
//   results/summary/<RUN>/compiler_strata_vs_all.csv   STRATA against each table
//   results/summary/<RUN>/decomposition.csv            smallest fixed buffers, paired time with 95% CI
//   results/summary/<RUN>/sweep.csv + raw sweep_minbuf  shadowing / name-length sweep
//   results/summary/<RUN>/chibicc_end_to_end.csv       second compiler, end to end
//   results/chibicc/units.csv                          identical assembly per unit
//   results/embedded/*.txt                             bare-metal Cortex-M3 runs under QEMU
//   results/hardening/flood.csv                        hash-flooding experiment
// Test counts that exist only in reports are listed in TESTS with the file they come from.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { repoRoot, webRoot } from "../server/paths.mjs";

const RUN = "20261013-143828-paper";
const TRACES = ["cjson", "littlefs", "zlib", "freertos", "lua", "tinycc", "sqlite", "mbedtls"];
// Tables compared in the demo. The METIS tables are left out of the demo on purpose.
const IMPLS = { strata: "STRATA", arena_chain: "Conventional single-buffer table", std_undo_log: "std::unordered_map + undo log",
  swiss_undo_log: "Swiss map + undo log", scope_map_stack: "One hash map per scope", swiss_interned: "Interned Swiss flat map" };
const SHORT = { strata: "STRATA", arena_chain: "Single-buffer (arena)", std_undo_log: "std map + undo log",
  swiss_undo_log: "Swiss map + undo log", scope_map_stack: "Map per scope", swiss_interned: "Interned Swiss map" };
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
const r2 = (x) => Math.round(Number(x) * 100) / 100;
const ms = (ns) => Math.round(Number(ns) / 1e4) / 100;
const kv = (text) => Object.fromEntries(text.split(/\r?\n/).filter((l) => l.includes(":")).map((l) => [l.split(":")[0].trim(), l.slice(l.indexOf(":") + 1).trim()]));

const results = join(repoRoot, "results");
const raw = join(results, "raw", RUN), sum = join(results, "summary", RUN);
const summary = csv(join(raw, "compiler_summary.csv")).filter((r) => TRACES.includes(r.trace));
const env = kv(readFileSync(join(raw, "environment.txt"), "utf8"));

// ---- correctness ---------------------------------------------------------------------------
const correctness = Object.entries(IMPLS).map(([impl, label]) => {
  const rows = summary.filter((r) => r.impl === impl);
  const checked = rows.reduce((n, r) => n + Number(r.lookups) + Number(r.declares), 0);
  const wrong = rows.reduce((n, r) => n + Number(r.wrong_lookups) + Number(r.wrong_declares), 0);
  const refused = rows.reduce((n, r) => n + Number(r.refused_declares), 0);
  return { impl, label, traces: rows.length, checked, wrong, refused };
});

// ---- STRATA against each table (min/median/max over the 8 traces) ---------------------------
// This file repeats the column name "median" (heap, then time), so it is read by position:
// baseline, traces, faster, slower, heap min, heap median, heap max, time min, time median, time max
const vsAll = readFileSync(join(sum, "compiler_strata_vs_all.csv"), "utf8").trim().split(/\r?\n/).slice(1).map(parseLine)
  .filter((c) => BASELINE_ROWS[c[0]])
  .map((c) => ({
    impl: BASELINE_ROWS[c[0]], label: IMPLS[BASELINE_ROWS[c[0]]], short: SHORT[BASELINE_ROWS[c[0]]], traces: Number(c[1]), faster: Number(c[2]), slower: Number(c[3]),
    heapMin: r1(c[4]), heapMedian: r1(c[5]), heapMax: r1(c[6]), timeMin: r1(c[7]), timeMedian: r1(c[8]), timeMax: r1(c[9]),
  }));

// ---- smallest fixed buffers and paired time against the conventional table -------------------
const decomposition = Object.fromEntries(csv(join(sum, "decomposition.csv")).map((r) => [r.trace, {
  strataBufferKiB: r1(r["STRATA fixed buffer KiB"]), arenaBufferKiB: r1(r["arena+chains fixed buffer KiB"]),
  bufferReductionPct: r1(r["memory: STRATA vs arena+chains, red. %"]),
  timeVsArenaPct: r1(r["time: STRATA vs arena+chains, red. %"]), ciLow: r1(r["CI low"]), ciHigh: r1(r["CI high"]),
}]));

// ---- per trace: workload shape and every table's figures -------------------------------------
const perTrace = TRACES.map((t) => {
  const get = (impl) => summary.find((r) => r.trace === t && r.impl === impl);
  const s = get("strata"), a = get("arena_chain"), u = get("std_undo_log");
  const tables = Object.keys(IMPLS).map((impl) => {
    const r = get(impl);
    return {
      impl, label: IMPLS[impl], short: SHORT[impl],
      peakKiB: r1(Number(r.peak_bytes) / 1024), allocs: Number(r.allocs),
      replayMs: ms(r.replay_ns_median), replayMinMs: ms(r.replay_ns_min), replayMaxMs: ms(r.replay_ns_max),
      lookupP95: r1(r.lookup_p95_ns), declareP95: r1(r.declare_p95_ns),
      wrong: Number(r.wrong_lookups) + Number(r.wrong_declares),
    };
  });
  return {
    trace: t, ops: Number(s.ops), declares: Number(s.declares), lookups: Number(s.lookups), scopes: Number(s.enters),
    units: Number(s.units), distinctNames: Number(s.distinct_names), peakLive: Number(s.peak_live_decls), maxDepth: Number(s.max_depth),
    reps: Number(s.reps),
    checked: Number(s.lookups) + Number(s.declares), wrong: Number(s.wrong_lookups) + Number(s.wrong_declares),
    strataHeapKiB: r1(Number(s.peak_bytes) / 1024), stdHeapKiB: r1(Number(u.peak_bytes) / 1024),
    strataAllocs: Number(s.allocs), stdAllocs: Number(u.allocs),
    strataMs: ms(s.replay_ns_median), stdMs: ms(u.replay_ns_median), arenaMs: ms(a.replay_ns_median),
    tables,
    ...decomposition[t],
  };
});

// ---- shadowing / name-length sweep -----------------------------------------------------------
const SIGMA = { s10: 1, s12: 1.2, s15: 1.5, s20: 2, s30: 3, s40: 4, s80: 8 };
const minbuf = csv(join(raw, "sweep_minbuf.csv"));
const sweepTime = csv(join(sum, "sweep.csv"));
const sweep = minbuf.map((r) => {
  const [s, l] = r.trace.split("_");
  const sigma = SIGMA[s], L = Number(l.slice(1));
  const t = sweepTime.find((x) => Number(x.sigma) === sigma && Number(x.L) === L);
  return {
    sigma, L, strataKiB: r1(Number(r.strata_min_bytes) / 1024), arenaKiB: r1(Number(r.arena_chain_min_bytes) / 1024),
    savingPct: r1(100 * (1 - Number(r.strata_min_bytes) / Number(r.arena_chain_min_bytes))),
    timePct: t ? r1(t["time red. %"]) : null, ciLow: t ? r1(t["CI low"]) : null, ciHigh: t ? r1(t["CI high"]) : null,
    faster: t ? t["STRATA faster"] : null,
  };
}).sort((a, b) => a.L - b.L || a.sigma - b.sigma);

// ---- second compiler (chibicc) ---------------------------------------------------------------
const chUnits = csv(join(results, "chibicc", "units.csv"));
const chEnv = kv(readFileSync(join(results, "chibicc", "environment.txt"), "utf8"));
const parseCI = (s) => (s || "").replace(/[[\]\s]/g, "").split(",").map(Number);
const chibiccProjects = readFileSync(join(sum, "chibicc_end_to_end.csv"), "utf8").trim().split(/\r?\n/).slice(1).map(parseLine).map((c) => {
  const [sl, sh] = parseCI(c[6]), [al, ah] = parseCI(c[8]);
  return { project: c[0], units: Number(c[1]), originalS: r2(c[2] * 1000) / 1000, strataPct: r1(c[5]), strataCiLow: sl, strataCiHigh: sh,
    arenaPct: r1(c[7]), arenaCiLow: al, arenaCiHigh: ah, rssMB: r1(c[9]) };
});
const chibicc = {
  commit: chEnv.chibicc, rounds: chEnv.rounds,
  units: chUnits.length,
  compiled: chUnits.filter((u) => u.original_compiles === "1").length,
  strataIdentical: chUnits.filter((u) => u.original_compiles === "1" && u.strata_identical_asm === "1").length,
  arenaIdentical: chUnits.filter((u) => u.original_compiles === "1" && u.arena_identical_asm === "1").length,
  projects: chibiccProjects,
};

// ---- bare-metal Cortex-M3 under QEMU ---------------------------------------------------------
function blocks(text) {
  return text.split(/\n(?===\s)/).filter((b) => b.startsWith("==")).map((b) => ({ head: b.split("\n")[0], body: b }));
}
const field = (body, name) => { const m = body.match(new RegExp(`^${name}\\s+(\\S+)`, "m")); return m ? m[1] : null; };
const fitText = readFileSync(join(results, "embedded", "fit_cortex_m3.txt"), "utf8");
const embeddedFit = blocks(fitText).map(({ head, body }) => {
  const m = head.match(/==\s+(\S+)\s+buffer\s+(\d+)\s+bytes\s+table\s+(\S+)/);
  return { trace: m[1], bufferKiB: Number(m[2]) / 1024, table: m[3] === "ARENA" ? "Single-buffer (arena)" : "STRATA",
    refused: Number(field(body, "refused operations")), peakUsed: Number(field(body, "peak used bytes")),
    fits: /RESULT:\s+PASS/.test(body) };
});
const boundedText = readFileSync(join(results, "embedded", "qemu_cortex_m3_bounded.txt"), "utf8");
const embeddedBounded = blocks(boundedText).map(({ head, body }) => ({
  trace: head.match(/==\s+(\S+)/)[1], ops: Number(field(body, "operations")), refused: Number(field(body, "refused operations")),
  bufferBytes: Number(field(body, "buffer bytes")), peakUsed: Number(field(body, "peak used bytes")),
  stackBytes: Number(field(body, "stack bytes used")), staticRam: Number(field(body, "static RAM bytes")),
  checksumMatches: field(body, "checksum") === field(body, "expected \\(host run\\)"), pass: /RESULT:\s+PASS/.test(body),
  codeBytes: Number((body.match(/object file, bytes\):\s*\n\s*(\d+)/) || [])[1]),
}));
const embeddedEnv = kv(fitText.split("\n==")[0]);

// ---- hash flooding ---------------------------------------------------------------------------
const flood = csv(join(results, "hardening", "flood.csv")).map((r) => ({
  names: Number(r.names), input: r.input, config: r.config, declareMs: ms(r.declare_ns_median), lookupMs: ms(r.lookup_ns_median),
  refused: Number(r.refused), longestProbe: Number(r.longest_probe), correct: r.correct === "1",
}));

// ---- test counts that live in the reports (with their sources) ------------------------------
const TESTS = [
  { label: "Unit and differential test checks", value: 2732358, note: "0 failed", source: "NOVELTY_GATE.md" },
  { label: "Exhaustively enumerated operation sequences", value: 80.6e6, note: "no failure", source: "reports/FINAL_AUDIT_REPORT.md" },
  { label: "Fuzzing runs over the audit", value: 14.5e6, note: "no failure", source: "reports/ROUND_2_ADDENDUM.md" },
  { label: "Injected defects caught by the fuzzer", value: 6, of: 6, note: "each within 0.2 s", source: "reports/TEST_RESULTS.md" },
];
// Fail loudly if a cited figure is no longer in its source file.
const needles = { "NOVELTY_GATE.md": "2 732 358", "reports/FINAL_AUDIT_REPORT.md": "80.6 million", "reports/ROUND_2_ADDENDUM.md": "14.5 million", "reports/TEST_RESULTS.md": "6 of 6" };
for (const [file, needle] of Object.entries(needles)) {
  if (!readFileSync(join(repoRoot, file), "utf8").includes(needle)) throw new Error(`${file} no longer contains "${needle}"`);
}

const out = {
  run: RUN, cpu: env.cpu, compiler: env.compiler, kernel: env.kernel, rounds: env.rounds,
  correctness, vsAll, perTrace, sweep, chibicc, embeddedFit, embeddedBounded, embeddedEnv, flood, tests: TESTS,
};
mkdirSync(join(webRoot, "src", "data"), { recursive: true });
writeFileSync(join(webRoot, "src", "data", "recorded.json"), JSON.stringify(out, null, 2) + "\n");
console.log(`wrote src/data/recorded.json from ${RUN}: ${perTrace.length} traces, ${sweep.length} sweep points, ${embeddedFit.length} fit runs, ${embeddedBounded.length} bounded runs, ${flood.length} flood rows, chibicc ${chibicc.strataIdentical}/${chibicc.compiled} identical`);
