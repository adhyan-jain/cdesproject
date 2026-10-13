# Novelty gate

2026-10-13, branch `research/strata-paper-completion`. This document decides whether the
paper's claims are defensible against the prior work that was reviewed, with the final
implementation and fresh measurements. It is one assessor's judgment with a limited
literature search; it does not predict a review outcome.

**Verdict: PASS, for the narrowed claims of section 1 and for a venue that accepts incremental
empirical systems work (work-in-progress, student research, short paper).** The verdict does
not say the contribution is large. It would be FAIL for the claims an earlier draft made
(a new or faster symbol table), and for a venue that requires algorithmic novelty.

Human approvals are a separate matter and are **not** covered by this gate
(`SUBMISSION_READINESS.md`, section 10).

## 1. Final contribution statement

> For scoped symbol tables confined to one fixed buffer, we (a) measure what a compact
> interning design saves and costs against a conventional single-buffer table on events
> logged by real compilers, including the diagnosis of an implementation artifact that
> made the compact design look up to a third slower than it is; (b) show that removing
> declarations in reverse order of creation keeps the table in the state of a freshly built
> one, and use that to bound how often a per-call probe limit refuses an honest name; and
> (c) measure a known hash-collision attack restricted to identifier characters and the
> cost of two defences.

What is **not** claimed: a new hashing scheme or scoped-table algorithm; that the compact
table is faster than the conventional one; that the collision attack is new; any result on
hardware; any benefit in a hosted compiler; security beyond the stated assumption.

## 2. Closest prior work

Verification level: DOI = bibliographic record confirmed through Crossref on 2026-10-13;
PAGE = page or file opened; CODE = fetched and built; BOOK = textbook, not re-read.
Full list: `manuscript/REFERENCE_AUDIT.md`.

| Work | Level | What it does | Overlap with the claims |
|---|---|---|---|
| Appel, *Modern Compiler Implementation in C*, 1998, ch. 5 | BOOK (DOI of the book confirmed) | hash table + undo stack for scopes | **the algorithm used**; claim (a)'s subject, not its contribution |
| LLVM `ScopedHashTable` | PAGE | the same scheme over an allocator-backed map | same semantics; no budget, refusal guarantee or probe bound |
| Tiny C Compiler symbol stacks | CODE | token table and symbol stacks | the workload source; malloc-based |
| MicroPython interned strings (`qstr`) | PAGE | interned identifier pools in little RAM | overlaps the interning motivation; no scopes or failure semantics |
| Graham, Joy, Roubine, 1979 | DOI | hashed symbol tables with explicit scope control | historical; content known from an annotated bibliography only |
| Pagh and Rodler, "Cuckoo hashing", 2004 | DOI | worst-case constant lookups by moving keys | a bounded-probe dictionary exists; it moves keys and rehashes |
| Herlihy, Shavit, Tzafrir, "Hopscotch hashing", 2008 | DOI | keys kept within a fixed neighbourhood by displacement | same; resizes when an insertion cannot be placed |
| Bender, Kuszmaul, Kuszmaul, FOCS 2021 | DOI (abstract) | deletions and tombstones in linear probing | background for (b): general deletions degrade a table |
| Naor and Teague 2001; Blelloch and Golovin 2007 | DOI (abstract) | history-independent data structures and hashing | **closest to (b)**: a stronger property (layout independent of insertion order) obtained differently |
| Knuth vol. 3; Pagh, Pagh, Ruzic 2007; Thorup 2015 notes | BOOK / DOI / PAGE (not read in full) | analysis of linear probing; interval counting | **the technique of the bound in (b)** |
| Crosby and Wallach 2003 | PAGE | algorithmic complexity attacks on hash tables | the threat of (c) |
| Aumasson and Bernstein 2012 (paper DOI; slides read) | DOI / PAGE | Murmur multicollisions for any seed; SipHash | **the attack of (c)** |
| Linux kernel SipHash documentation; reference code | PAGE / CODE | HalfSipHash-1-3 for hash tables | the defence of (c), used as designed |
| rustc-hash README | PAGE (quotation confirmed) | deliberately unkeyed hash in a hosted compiler | the opposite design choice, reasonably argued |

Searches that found nothing relevant (which shows only that these queries found nothing): a
published scoped symbol table with a hard memory budget and a stated failure guarantee; a
published measurement of compact against conventional single-buffer scoped tables on
compiler-generated events; a hash-flooding attack on a C compiler's identifier table; a
probe-limit-with-refusal table analysed for refusal probability.

## 3. What is established and what is different

| Element | Established by | What is specific here | Strength |
|---|---|---|---|
| Scoped table with undo stack | Appel; LLVM | nothing | none |
| Single buffer, write-after-reserve refusal | arena allocation (Hanson 1990) is the idea | the tested all-or-nothing property across every refusal kind | engineering |
| Removing the newest key from linear probing by emptying its slot | follows from the insertion rule (Knuth) | stated and used for scope exit | observation, not claimed as new |
| Canonical state (Proposition 1) | weaker than history independence | the statement for a scoped table, its induction, a direct test | small, table-specific |
| Probe bound (Proposition 2) | interval counting plus Chernoff | applicability to a table with deletions via Proposition 1; validation; the finding that 64 is too small | small; standard technique |
| Probe limit by refusal instead of displacement | cuckoo, hopscotch bound probes by moving keys | the variant compatible with last-in-first-out removal and a fixed buffer | design choice, argued |
| Collision attack | Aumasson and Bernstein | restriction to packed identifier words; measurement | application of a known technique |
| Measured decomposition and the rebuild artifact | none found | the central empirical result | **the main contribution** |

## 4. Implementation changes on this branch and why

The library `include/strata/strata.hpp`, the tests and the baselines are **byte-identical**
to commit `36f9f6c` (`git diff 36f9f6c -- include tests benchmarks/baselines` is empty). No
algorithmic change was made on this branch: the literature review found no deficiency that a
new component would fix, and the brief asks for none without one.

| Change | Deficiency | Effect |
|---|---|---|
| `tools/embedded/bounded.sh`: probe limit from the environment, default 512 (was a fixed 64) | the script contradicted the documented recommendation | emulator run repeated at 512: 5 of 5 pass, no refusal |
| `benchmarks/hardening_main.cpp`: trace experiment also runs limits 256 and 512 | the recommended limit was not among those measured on real traces | 0 refusals at 64, 128, 256, 512 on 15 traces, both hashes |
| `scripts/analyze.py`, `scripts/make_report.py`: know the `strata_keyed` variant; keep chibicc traces out of the "compiler" sections | the project's own report generator crashed on runs made after 2026-10-13 | `docs/RESULTS.md` and `paper/generated.tex` regenerated from the new run |
| `scripts/run_all.sh`: skip chibicc traces in the compiler loop | they were measured twice and mixed into the TinyCC files | future runs only |

Earlier changes of 2026-10-13 that the paper's claims rest on (rebuild only when the index
size changes, one hash per name, one probe walk; bounded mode; keyed hash) are in `36f9f6c`
and are described in `reports/ROUND_2_ADDENDUM.md` with their before/after measurements.

## 5. Experiments after the implementation was frozen

All on the header of `36f9f6c`, on 2026-10-13, WSL 2 / Ubuntu 22.04, g++ 11.4, Intel Core
Ultra 7 258V, one pinned core.

| Experiment | Command | Output |
|---|---|---|
| Full pipeline: 8 TinyCC + 7 chibicc traces, 13 tables, 31 rounds; 9 synthetic; 4 legacy; budgets; worst case | `bash scripts/run_all.sh paper` | `results/raw/20261013-143828-paper/` |
| Sweep, per-unit budgets, chibicc trace timing | `bash scripts/run_extra.sh results/raw/20261013-143828-paper all` | same directory |
| chibicc end to end, 3 builds, 21 rounds | `bash tools/chibicc/build.sh && python3 tools/chibicc/evaluate.py` | `results/chibicc/` (old: `results/chibicc-20261011/`) |
| Flooding, bounded mode on traces (limits 4-512), probe distribution (240 million samples) | `PROBE_TRIALS=500 bash scripts/audit/hardening.sh 5` | `results/hardening/` |
| Emulated Cortex-M3, fixed and bounded (limit 512, keyed) | `bash tools/embedded/run.sh ...`, `bash tools/embedded/bounded.sh` | `results/embedded/` |
| Reports | `python scripts/analyze.py results/raw/20261013-143828-paper`; `python scripts/make_report.py 20261013-143828-paper`; `python manuscript/tools/make_numbers.py` | `docs/RESULTS.md`, `paper/generated*.tex`, `paper/tables/` |

## 6. Correctness and regression results

| Check | Result | Log |
|---|---|---|
| Clean-copy verification, 12 steps (unit tests at `-O2` and under ASan + UBSan, exhaustive depth 7, fetch, build, 41 CLI cases, static analysis, hash conformance, fuzzing, mutation check, hardening, both emulator runs, short benchmark) | 12 passed, 0 failed, on the branch state | `reports/artifacts/final_verification.log` |
| Unit and randomized differential tests | 2 732 358 checks, 0 failed | same |
| Exhaustive enumeration, depth 9 | 80 621 568 sequences, 0 failures | `reports/artifacts/exhaustive_small.log` |
| Fuzzing of the final library code | 2 476 136 executions (3 workers x 600 s), no failure | `reports/artifacts/fuzz_strata.log` |
| Mutation check | 9 of 9 injected defects detected | `reports/artifacts/mutation_check.log` |
| All tables against the reference model, 15 traces | 195 pairs, 0 wrong | `compiler_summary.csv` |
| Two independent number generators | 49 shared quantities, 0 disagreements | `python manuscript/tools/crosscheck.py` |
| Paper builds, checks | `paper/main.pdf` 14 pages, `paper/short.pdf` 3 pages; all mechanical checks pass | `python manuscript/tools/check_manuscript.py paper main` / `short` |

Not run: unit tests on a 32-bit host (no multilib), anything on hardware, valgrind.

## 7. Evidence for each central claim

| Claim | Evidence | Raw data |
|---|---|---|
| Fixed buffer 16.4% to 17.9% smaller than the conventional table on every trace | bisection to 64 bytes, 8 traces; identical in three runs | `budget.csv` |
| Replay time within about 10% of the conventional table, not faster | paired ratios, 31 rounds: slower on 2 (7.2%, 10.7%), not established on 6; a second run of the same code: faster on 2, slower on 3 (-10.7% to +7.0%) | `compiler_replays.csv` of `20261013-143828-paper` and `20261013-125704-final` |
| Most of the gain over METIS-X comes from the single allocation-free buffer | conventional table 14.6% to 34.8% faster than METIS-X; STRATA 15.9% to 36.7%; heap peaks of the two single-buffer tables equal on 6 of 8 traces | `compiler_summary.csv`, `compiler_replays.csv` |
| The earlier 11% to 34% penalty was a rebuild artifact | before/after runs with every deterministic output identical (1 248 values) | `20261013-120345-audit` vs `20261013-125704-final`; `reports/artifacts/speed_comparison.md` |
| A refused operation changes nothing | state digest before and after every refusal in unit tests, enumeration and fuzzing; mutant M6 detected | test logs |
| Canonical state | induction in the paper; `test_canonical_state` (360 comparisons by digest and `memcmp`); the measured mean probe count equals Knuth's insertion-only value at four loads | `tests/test_strata.cpp`, `probes.csv` |
| Probe bound | proof in the paper; never exceeded in 168 configuration/limit cells, 10 million samples each | `results/hardening/probes.csv` |
| A limit of 64 is not safe in general; 512 is supported | 0.77% of fresh names exceed 64 at load 3/4; none of 10 million exceed 512; bound 1.1e-7 | same |
| Colliding identifiers exist for every seed and slow the table quadratically | 32 768 names verified under 9 seeds; about 300-fold at 32 768 names, exponent about 2 | `flood.csv`, `flood_verification.txt` |
| Keyed hash removes it at 20% to 32% of replay time | ratio 1.1-1.2 colliding/ordinary; paired cost on 8 traces | `flood.csv`, `compiler_replays.csv` |
| No end-to-end benefit in a hosted compiler | chibicc, 158 of 158 units identical; -3.7% to +2.2% | `results/chibicc/` |

## 8. Limitations, competing explanations, negative results

- **Negative:** not faster than the conventional design; slower on 2 traces; no end-to-end gain; the keyed hash costs a quarter of replay time; the smaller buffer changes the outcome for at most 23 of 169 translation units.
- **Instability:** per-trace timing verdicts differ between two runs of the same code. Only "within about 10%" is claimed.
- **Competing explanation for the memory saving:** the conventional baseline stores a 4-byte hash and an unpacked name per declaration; a conventional table without the stored hash would narrow the gap. Not built. The claim is therefore "against this conventional design", and the paper describes the baseline's entry layout.
- **Competing explanation for "no refusal on traces":** small tables below their load limit, which is what the paper says.
- **Assumptions:** the bound holds for an ideal hash; HalfSipHash-1-3 is assumed to behave as one against an adversary without the key.
- **Scope of evidence:** one machine, replay, emulator, C only, self-written baselines, informal proofs, limited literature search.

## 9. What would weaken or overturn the claims

1. A published or open-source scoped table with a memory budget and a refusal guarantee (would reduce the differentiation of the design, not the measurements).
2. A conventional single-buffer table without a stored hash measured to within a few percent of STRATA's buffer (would shrink claim (a)).
3. A run on native Linux or hardware in which the two tables differ by much more than 10% (would change the timing claim).
4. A flaw in Proposition 1 for some operation sequence longer than those enumerated (the fuzzer and randomized tests have not found one).

## 10. Decision

| Gate condition | Status |
|---|---|
| Novelty reassessed after the implementation was final | done (this document) |
| Every central claim has identified support | yes (section 7) |
| Experiments rerun on the final implementation | yes (section 5); library unchanged since |
| Regression, correctness, hardening and reproducibility checks pass | yes (section 6) |
| Results from the correct code version match paper, tables, figures and raw data | yes: generated from the raw files; two generators agree on 49 quantities |
| Independent final review finds no blocker that invalidates the core contribution | none found; major weaknesses are disclosed in the paper (`manuscript/reports/MANUSCRIPT_REVIEW.md`) |

**PASS.** Remaining uncertainty: the literature search (about twenty-five web queries, several
sources at abstract level); the single machine; and whether reviewers consider an honest
incremental result sufficient. A PASS here permits a local merge. It does not authorise
submission, a push, or any statement on behalf of the authors.
