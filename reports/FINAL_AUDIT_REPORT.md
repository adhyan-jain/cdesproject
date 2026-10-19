# Final audit report

> **Superseded in part by `ROUND_2_ADDENDUM.md`** (same day): STRATA is now level with the conventional table on speed, the suggested probe limit is 512, and the novelty score is 6.0/10. Read that file first; the text below is the first round as written.

Project: `cdesproject` (STRATA, a bounded-memory scoped symbol table). Audit date: 2026-10-13.
Start state: commit `cd3b4cc`, clean. End state: the same commit plus uncommitted changes
listed in `CHANGELOG_AUDIT.md`. Nothing was committed or pushed.

## 1. Executive summary

- The project is a C++ header library with benchmark tools and a paper draft. It has no web application, so the brief's browser phases do not apply; no browser was opened.
- Everything documented builds and runs. The existing test suite passed as found (1 856 579 checks, also under ASan + UBSan).
- The stored performance claims were re-measured and hold, including the unfavourable one: STRATA is slower than the conventional single-buffer table on all 8 compiler traces (11-34%) while needing 16-18% less memory.
- New testing found **no defect in the table itself**: 9.8 million fuzzing runs of the code as found, 2.2 million of the final code, and 80.6 million exhaustively enumerated operation sequences, all without a failure. A mutation check shows the fuzzer detects injected defects (6 of 6).
- One real defect was found in a tool (`budget --reps 0`, undefined behaviour) and fixed.
- One security weakness, already named in the project's limitations, was demonstrated concretely: valid C identifiers that collide in the default hash for every seed make declarations 223 times slower at 32 768 names. Two opt-in defences were added and measured.
- **Novelty: 5.5/10 on the brief's weighted rubric (4.9 before the audit). 8/10 is not justified** (`NOVELTY_ASSESSMENT.md`).

## 2. Repository and architecture

| Part | Path | Role |
|---|---|---|
| Library | `include/strata/strata.hpp` | one buffer of 32-bit words: index (linear probing with 8-bit fingerprints), identifier records growing up, undo stack growing down; fixed, growable and (new) bounded modes |
| Baseline | `benchmarks/baselines/arena_chain.hpp` | conventional chained table in one buffer |
| Other baselines | `benchmarks/baselines/tables.hpp` | adapters for 11 further tables, some fetched from third parties |
| Harness | `benchmarks/bench_main.cpp`, `budget_main.cpp`, (new) `hardening_main.cpp` | trace replay, fixed-buffer bisection, flooding experiments |
| Tests | `tests/` | unit and randomized tests, reference model, (new) fuzzer, exhaustive checker, hash conformance |
| Workloads | `workloads/traces/` | 15 gzip traces from instrumented TinyCC and chibicc |
| Embedded | `tools/embedded/` | bare-metal Cortex-M3 image for QEMU |
| Results | `results/` | raw CSVs of five runs, generated summaries, (new) `hardening/` |
| Paper | `paper/` | 5-page IEEE-style draft; **not updated by the audit** |

## 3. Setup and execution

Linux x86-64 or WSL 2, g++ with C++14, python3, git. Optional: clang with libFuzzer for the
fuzzer, `arm-none-eabi-g++` and `qemu-system-arm` for the emulated target.

```
bash scripts/test.sh                  # 12 s here
bash scripts/fetch_third_party.sh     # baselines at pinned commits
bash scripts/build.sh
bash scripts/audit/final_verify.sh    # all audit checks from a clean copy, about 5 minutes
```

Launch result: every step above succeeded on the first attempt. No configuration problem had
to be worked around. One environment note: when commands are passed to `wsl.exe` inline, the
outer shell expands `$` and `|`; the audit therefore runs script files only.

## 4. Browser testing

Not applicable and not performed. See `TEST_RESULTS.md` section 5.

## 5. Functional correctness

| Check | Result |
|---|---|
| Existing tests as found | pass |
| All 13 tables against the reference model on 8 traces | 104 pairs, 0 disagreements |
| Fuzzing, exhaustive enumeration, mutation check | no failure; 6 of 6 mutants detected |
| All-or-nothing guarantee on refusal | holds in every test, including the new `kProbeLimit` refusal |
| Emulated Cortex-M3 | 5 of 5 traces pass in fixed mode and in bounded mode |

Details and commands: `TEST_RESULTS.md`.

## 6. Performance

Stored claims reproduced on 7 of 8 traces for each paired comparison, with the remaining
trace differing only in whether a small difference is statistically established. Raw times
were 36% lower in this session than in the stored run, so only within-run ratios are
compared. Details: `PERFORMANCE_REPORT.md`.

## 7. Security and reliability findings

| ID | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| SEC-1 | P2 | **Hash flooding.** The default hash is an unkeyed Murmur-style mixer. Identifiers made only of `[A-Za-z0-9_]` that collide for every seed can be generated (so a secret seed alone would not help). 32 768 of them: declare 1.93 s against 8.6 ms, lookup 1.06 s. Matters only when the table is fed untrusted source. | `results/hardening/flood.csv`, `flood_verification.txt` | mitigated by opt-in keyed hash and probe limit; default unchanged |
| SEC-2 | P2 | **Unbounded step inside an operation.** Index rebuilds are O(live names) inside `declare`/`exit_scope`. | code reading; `docs/LIMITATIONS.md` | mitigated by the bounded mode (static index); default unchanged |
| REL-1 | P2 | `budget --reps 0` indexes an empty vector (undefined behaviour, reported by UBSan). | `artifacts/cli_tests.log`, first run | fixed, regression test C30 |
| SUP-1 | P3 | `parallel-hashmap` was fetched by tag; a tag can be moved. | `scripts/fetch_third_party.sh` | fixed: commit `22a7f6c` is verified |
| SUP-2 | P3 | Project sources for trace regeneration are fetched by tag or URL without checksums. | `tools/tcc-trace/make_traces.sh` | open; the stored traces are what results use |
| SEC-3 | P3 | The baseline `arena_chain` has the same unkeyed hash and no defence. | code reading | open (it is a baseline) |
| INF-1 | info | No secrets, tokens or machine paths in tracked files. The committer e-mail address is in the git history, as in any repository. | `git grep`, `git log` | none needed |
| INF-2 | info | The fixed constructor requires a buffer aligned for `uint32_t`; a misaligned buffer is undefined behaviour. Documented in the header, not checked at run time. | `strata.hpp` constructor comment | open; a run-time check would be cheap |
| INF-3 | info | The table is not thread-safe and says so; the character-code table is lazily initialised without synchronisation. | header comment | open by design |
| INF-4 | info | Heap peaks are reproducible to 0.22%, not to the byte. | `artifacts/repro_comparison.md` | documented here |

Checked without finding a problem: integer overflow in size computations (64-bit
intermediates are used; sanitizers with integer checks pass), out-of-bounds access (ASan on
tests, fuzzing and tools), behaviour with invalid or absent buffers, behaviour when the
allocator fails, names with embedded NUL or non-ASCII bytes, names past the length limit,
nesting past the depth limit, shell scripts (no use of untrusted input in commands).

Not applicable: authentication, authorization, sessions, uploads, databases, network
services. The project has none.

## 8. Bugs found and fixes made

| # | Problem | Fix | Regression test |
|---|---|---|---|
| 1 | REL-1 above | repetition count clamped to at least 1 | CLI cases C30, C30b |
| 2 | SUP-1 above | fetch script verifies the commit | `final_verify.sh` step V02 |
| 3 | Two compiler warnings in the audit's own fuzz harness | fixed | `static_analysis.sh` (0 warnings) |
| 4 | One wrong expectation in a test written during the audit (not a code defect; it failed in 4 of 12 configurations): a memory refusal was expected where the probe limit refuses first | expectation narrowed | `test_bounded_mode` |

Research modification (kept separate from bug fixes): the bounded mode and keyed hash,
`CHANGELOG_AUDIT.md` section 2.

## 9. Remaining issues

- SUP-2, SEC-3, INF-2 above.
- `docs/RESULTS.md`, `paper/generated.tex` and the paper describe run `20261011-165103-v3` and do not mention the bounded mode.
- The co-authors have not reviewed the repository, the paper or this audit.
- Everything in `TEST_RESULTS.md` section 4 (blocked and not tested).

## 10. Reproducibility

Good. Deterministic results reproduce exactly (minimum buffers, bytes used, correctness) or to
0.22% (heap peaks). Timing verdicts reproduce on 7 of 8 traces per comparison. A copy of the
tree without build products passes all 12 verification steps. What a third party cannot
reproduce without extra work: the traces themselves (they depend on the host's C headers and
on unpinned source downloads) and absolute times.
