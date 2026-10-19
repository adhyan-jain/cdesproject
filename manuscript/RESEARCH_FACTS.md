# Research facts for the manuscript

Prepared 2026-10-13 from the repository at commit `36f9f6c` and a full re-run of the
experiments on that code (`results/raw/20261013-143828-paper`). Every number in the manuscript must
trace to a row of this file. Nothing here is taken from memory of earlier drafts.

## 1. The ten questions

| # | Question | Answer |
|---|---|---|
| 1 | Research problem | A scoped symbol table for a compiler that has a hard memory budget (one caller-supplied buffer, no allocator), must fail in a defined way at the budget, and may be given source text its operator does not trust. |
| 2 | Research gap | Published and deployed scoped tables (Appel's undo-stack scheme, LLVM `ScopedHashTable`, TinyCC's symbol stacks) rely on an allocator, have no defined behaviour at a memory bound and no bound on work per call. We found no measurement that separates what a compact single-buffer design gains from what it costs, on events produced by real compilers. *This is the result of a limited search (about twenty web queries), not of a systematic review.* |
| 3 | Proposed solution | STRATA: index, interned names with the innermost declaration, and an undo stack in one buffer; a refusal that changes nothing; an optional bounded mode (static index, probe limit, keyed hash). |
| 4 | What is new | Not the algorithm (hash table plus undo stack is textbook). New here: (a) the combination under a hard budget with a tested all-or-nothing refusal; (b) the canonical-state property and its use to carry an insertion-only probe bound over to a table with deletions; (c) a rebuild that hashes each name once with no scratch memory; (d) the measured decomposition against a conventional single-buffer table; (e) seed-independent colliding identifiers for a packed-identifier hash, with defences measured. |
| 5 | Contributions | Section 3 below. |
| 6 | Comparison with existing methods | 12 other tables behind one interface on the same traces; the decisive comparison is with `arena_chain`, a conventional chained table in one buffer written as a strong baseline. |
| 7 | Evidence | Section 4 below, each item with its file. |
| 8 | Experiments conducted | Trace replay (8 TinyCC traces, 7 chibicc traces, 9 synthetic, 4 legacy); minimum fixed buffer by bisection; per-translation-unit fit; shadowing and name-length sweep; hash flooding; probe-length distribution; emulated Cortex-M3; chibicc end-to-end integration (earlier code version only). |
| 9 | Reproducible | Everything in section 4 marked R was re-run for this manuscript. Items marked S are stored results of an earlier code version. |
| 10 | Limitations | Section 6 below. |

## 2. Verified facts about the implementation

| Fact | Source |
|---|---|
| C++14, header only, 676 lines, no dependencies beyond `<cstdint>`, `<cstdlib>`, `<cstring>` | `include/strata/strata.hpp` |
| One buffer of 32-bit words: index at the start, identifier records growing up, undo stack growing down | header comment and code |
| Index slot: 8-bit fingerprint, 24-bit record reference; linear probing; maximum load 3/4 (1/2 with `sparse_index`) | `slot_word`, `ensure` |
| Record: value word, meta word (name words, raw flag, tail length, 8-bit type, 14-bit depth), name words | `declare`, enum of masks |
| Names of `[A-Za-z0-9_]` packed 5 characters per word; other names stored as raw bytes | `make_key` |
| Undo entry: 1 word for a first declaration (its index slot), 3 words for a shadowing declaration, 2 words for a scope mark | `declare`, `enter_scope` |
| Limits: names 1-255 bytes, depth 16 383, buffer 64 MiB, 32-bit value, 8-bit type tag | header |
| Statuses: `kOk`, `kRedeclared`, `kNoMemory`, `kNameTooLong`, `kEmptyName`, `kNoScope`, `kTooDeep`, `kProbeLimit` | header |
| Default hash: MurmurHash3-style 32-bit mixer over packed words; keyed option: HalfSipHash-1-3 | `detail::hash_words`, `detail::halfsiphash13` |
| Rebuild only when the index size changes; one hash per name; no scratch memory | `relocate`, `stash_undo`, `reindex` |
| Baseline `arena_chain`: bucket heads, entry stack (next, hash, value, length and depth, name bytes), scope marks, in one buffer | `benchmarks/baselines/arena_chain.hpp` |

## 3. Contributions the evidence supports

1. A single-buffer scoped symbol table with a strong failure guarantee: a refused operation leaves the state bit-for-bit unchanged.
2. A canonical-state property: with a static index, the state after any operation sequence equals that of a fresh table holding the live declarations. Proved (informally) and tested.
3. A bounded mode with a per-call probe limit, and a bound on the probability that the limit refuses a legitimate name, validated by measurement.
4. A measured decomposition of the gain over the predecessor table into "one allocation-free buffer" and "the compact design", on compiler-generated workloads, including the diagnosis of a rebuild artefact that made the compact design look 11-34% slower than it is.
5. Colliding identifiers for a Murmur-style hash restricted to an identifier alphabet, valid for every seed, with the slowdown and two defences measured.
6. An evaluation method: symbol-table events logged by two instrumented C compilers; differential fuzzing, bounded exhaustive enumeration and a mutation check as evidence for the guarantees.

## 4. Results directly supported by experimental evidence

Run directory for timing: `results/raw/20261013-143828-paper` (full pipeline on the final code; R = re-run).
`G` marks values that are regenerated into `manuscript/overleaf/generated_numbers.tex` by
`manuscript/tools/make_numbers.py`; the manuscript uses those macros, never typed numbers.

| ID | Result | Status | Source file |
|---|---|---|---|
| E1 | All 13 tables agree with the reference model on the 8 TinyCC traces (104 pairs, 0 wrong) | R, G | `compiler_summary.csv` |
| E2 | Minimum fixed buffer: STRATA 15.75-156.5 KiB, 16.4-17.9% below `arena_chain` on every trace | R, G | `budget.csv` |
| E3 | Bytes per live declaration, STRATA | R, G | `budget.csv`, `compiler_summary.csv` |
| E4 | Peak heap, STRATA against METIS-X and the other tables | R, G | `compiler_summary.csv` |
| E5 | Allocator calls against METIS-X | R, G | `compiler_summary.csv` |
| E6 | Replay time, paired ratios with bootstrap intervals: STRATA vs `arena_chain`, vs METIS-X, `arena_chain` vs METIS-X | R, G | `compiler_replays.csv` |
| E6a | Per-trace verdicts of E6 differ between two runs of the same code (final run: faster on 2, slower on 3; paper run: faster on 0, slower on 2, not established on 6). Both runs: within about 10% | R | `20261013-125704-final`, `20261013-143828-paper` |
| E7 | Per-operation latency p95 (lookup, declare, scope exit) | R, G | `compiler_summary.csv` |
| E8 | Effect of the rebuild changes: before/after with identical deterministic outputs | R | `results/raw/20261013-120345-audit` vs `20261013-125704-final`, `reports/artifacts/speed_comparison.md` |
| E9 | Ablations: raw names (packing off), sparse index, no shrinking | R, G | `compiler_replays.csv`, `budget.csv` |
| E10 | Synthetic stress traces (9) and METIS-X refusing declarations under deep shadowing | R, G | `synthetic_summary.csv` |
| E11 | Shadowing and name-length sweep, memory model | R, G | `sweep_minbuf.csv`, `sweep_summary.csv` |
| E12 | Per-translation-unit fit at fixed budgets | R, G | `units.csv` |
| E13 | Hash flooding: 32 768 colliding identifiers, four configurations | R, G | `results/hardening/flood.csv`, `flood_verification.txt` |
| E14 | Bounded mode on 15 compiler traces, probe limits 4-128, two hashes | R, G | `results/hardening/traces.csv` |
| E15 | Probe-length distribution against the bound, 24 configurations, 10 million samples each | R, G | `results/hardening/probes.csv` |
| E16 | Keyed hash cost on replay time | R, G | `compiler_replays.csv` |
| E17 | Emulated Cortex-M3, fixed and bounded modes, 5 traces, code size and stack | R | `results/embedded/*.txt` |
| E18 | Verification: unit checks, exhaustive sequences, fuzz executions, mutants | R | `reports/artifacts/*.log`, `reports/ROUND_2_ADDENDUM.md` |
| E19 | chibicc end-to-end integration (assembly identical on 158 units; no compile-time gain) | **S**: measured with the code of 2026-10-11, before the rebuild changes; not re-run | `results/chibicc/*.csv` |

## 5. Claims supported by published literature (not by our experiments)

| Claim | Source | Checked how |
|---|---|---|
| Hash table plus undo stack is the standard scoped-table scheme | Appel 1998, ch. 5 | book cited from knowledge of its content; DOI of the book verified |
| LLVM `ScopedHashTable` implements that scheme with per-key and per-scope chains | LLVM documentation | page read |
| Crafted keys degrade hash tables (algorithmic complexity attacks) | Crosby and Wallach 2003 | USENIX page read in part |
| MurmurHash2/3 multicollisions hold for any seed; SipHash as remedy | Aumasson and Bernstein 2012; slides | slides read (slide 37), paper DOI verified |
| HalfSipHash-1-3 is used for hash-table flooding resistance on 32-bit machines | Linux kernel documentation | page read |
| Expected probes of insertion-only linear probing: (1 + 1/(1-a)^2)/2 | Knuth vol. 3, sec. 6.4 | book, not re-read; our measurement reproduces the value |
| Deletions with tombstones change the behaviour of linear probing | Bender, Kuszmaul, Kuszmaul 2021 | DOI verified, abstract level |
| Constant-independence analyses of linear probing | Pagh, Pagh, Ruzic 2007; Thorup 2015 notes | DOI and arXiv id verified, not read in full |
| History-independent hashing | Naor and Teague 2001; Blelloch and Golovin 2007 | DOIs verified, abstract level |

## 6. Limitations that must be disclosed

- Replay of logged events, not a compiler running on the table (except the partial chibicc integration, E19, on an earlier version).
- One machine (a laptop under WSL 2); emulated microcontroller only; no hardware.
- C only; two small compilers; traces depend on host headers.
- The probe bound assumes an ideal hash; HalfSipHash-1-3 is modelled as one.
- The collision construction is a known technique applied to a new alphabet.
- STRATA is not faster than the conventional table; it is level, with a smaller buffer.
- Baselines other than METIS and parallel-hashmap were written for this project.
- The literature search was limited; several sources were checked at abstract level only.
- The work was produced with an AI coding assistant (see section 8).

## 7. Hypotheses that need further work (not to be stated as results)

- That refusals at a limit of 512 are negligible for real programs (supported by the bound under the ideal-hash assumption and by simulation, not by program text at scale).
- That the remaining 5-10% lookup-latency difference is due to index load.
- That the design carries over to C++ or scripting-language front ends.
- That results would hold on a physical Cortex-M device.

## 8. Missing information that only the authors can supply

Listed in `AUTHOR_DETAILS_REQUIRED.md`: affiliations, e-mail addresses, corresponding author,
ORCID of the submitting author, biographies and photographs, funding statement, conflict of
interest statement, the decision on how AI assistance is disclosed, and whether the guide is an
author.

## 9. Inconsistencies found and how they were resolved

| Inconsistency | Resolution |
|---|---|
| `docs/RESULTS.md`, `paper/` and the README's first tables report STRATA 11-34% slower than `arena_chain` (run of 2026-10-11); later runs show the two level | The earlier figure was an implementation artefact (rebuild on every buffer growth). The manuscript reports the final code and describes the artefact as a finding (E8). |
| "No refusal at a probe limit of 64" (15 traces) against 0.77% refusals at full load in simulation | Both are true. The manuscript reports both and recommends the limit from the bound. |
| Heap peaks differ by up to 0.22% between runs of unchanged tables | `malloc_usable_size` rounding depends on allocation history; stated as measurement resolution. |
| Author name spelled "Venkataramana" in the repository and "Venkatataramana" in the manuscript instructions | The manuscript uses the spelling given in the instructions and flags it for confirmation. |
| Guide's name spelled "Bhuvaneshwari M" in the repository and "Bhuvaneswari M." in the instructions | Same: instruction spelling used, flagged. |
| Author order: repository draft lists Adhyan Jain first | The instructions' order (Shubhi Singh first) is used. |
