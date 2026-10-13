# Changes made during the audit

> **Superseded in part by `ROUND_2_ADDENDUM.md`** (same day): STRATA is now level with the conventional table on speed, the suggested probe limit is 512, and the novelty score is 6.0/10. Read that file first; the text below is the first round as written.

2026-10-13. Base: commit `cd3b4cc`. **Nothing was committed or pushed**; all changes are in the
working tree for the authors to review. No existing file was deleted. The default behaviour
of the library (hash values, layout, results) is unchanged; the table object is 24-32 bytes
larger.

## 1. Bug fixes

| File | Change | Reason |
|---|---|---|
| `benchmarks/budget_main.cpp` | repetition count clamped to at least 1 | `--reps 0` indexed an empty vector (undefined behaviour) |
| `scripts/fetch_third_party.sh` | verifies that parallel-hashmap v1.4.1 is commit `22a7f6c`, fails otherwise | a tag can be moved |

## 2. Research modification (changes the scientific content; needs the authors' decision)

| File | Change |
|---|---|
| `include/strata/strata.hpp` | New `Options` fields `keyed`, `key[2]`, `index_slots`, `max_probe`; new status `kProbeLimit`; new constructor `Table(buffer, bytes, options)`; HalfSipHash-1-3 (`detail::halfsiphash13`); bounded `find`; `probe_fits`; static-index branch in `ensure`; `Stats::longest_probe`; `check_invariants` also checks the probe limit. +89 / -11 lines |

Rationale: `docs/LIMITATIONS.md` already named the missing protection against adversarial
keys and the unbounded rebuild step. The audit demonstrated the first concretely (section 3)
and added opt-in defences so that the weakness can be closed and its cost measured. The
method (interning, undo stack, LIFO removal) is not replaced. Whether the paper should
present this mode is for the authors to decide; the paper was not touched.

## 3. New files

| File | Purpose |
|---|---|
| `benchmarks/hardening_main.cpp` | colliding-identifier generator, flooding measurement, bounded mode on traces |
| `tests/fuzz_strata.cpp` | differential fuzzer (libFuzzer or standalone replay) |
| `tests/exhaustive_small.cpp` | bounded exhaustive check |
| `tests/halfsiphash_conformance.cpp` | keyed hash against the reference implementation |
| `tools/embedded/bounded.sh` | bounded mode on the emulated Cortex-M3 |
| `scripts/audit/phase2_launch.sh`, `fuzz.sh`, `exhaustive.sh`, `static_analysis.sh`, `cli_tests.sh`, `halfsiphash_check.sh`, `hardening.sh`, `repro.sh`, `final_verify.sh` | the audit's runnable checks |
| `scripts/audit/mutation_check.py`, `compare_runs.py`, `kill_prefix.py` | mutation check, run comparison, prefix-sharing simulation |
| `results/hardening/` | `flood.csv`, `traces.csv`, `environment.txt`, `flood_verification.txt` |
| `results/raw/20261013-120345-audit/` | re-measurement of the 8 TinyCC traces |
| `results/embedded/qemu_cortex_m3_bounded.txt` | emulator log, bounded mode |
| `reports/` | six reports, phase logs, artifacts |

## 4. Modified tests, tools and scripts

| File | Change |
|---|---|
| `tests/test_strata.cpp` | added `test_keyed_hash` and `test_bounded_mode` (checks 1 856 579 -> 2 706 587) |
| `scripts/test.sh` | also builds and runs the exhaustive check at depth 7 |
| `scripts/build.sh` | also builds `build/hardening` |
| `benchmarks/baselines/tables.hpp`, `benchmarks/bench_main.cpp` | new benchmark variant `strata_keyed` (a 13th table in each round) |
| `tools/embedded/main.cpp` | `-DTABLE_BOUNDED` variant |
| `results/embedded/qemu_cortex_m3.txt` | **regenerated** by re-running `tools/embedded/run.sh` on 5 traces with the changed header (stack 792 -> 504 bytes, code 2 557 -> 2 739 bytes); the previous log is in git history |

## 5. Documentation

| File | Change |
|---|---|
| `README.md` | section "Bounded mode and hash flooding"; novelty and Cortex-M3 rows updated; new commands and layout rows |
| `docs/CORRECTNESS.md` | section 7, argument for the bounded mode and keyed hash |
| `docs/LIMITATIONS.md` | adversarial-key and rebuild items rewritten to match the code; section "Added by the audit" |
| `docs/RELATED_WORK.md` | rows 16-22; the old self-assessment marked as superseded, text kept |

Not changed: `paper/`, `docs/RESULTS.md`, `paper/generated.tex`, `docs/METHODOLOGY.md`,
`docs/REPRODUCIBILITY.md`, stored runs under `results/raw/2026101*` and `results/summary/`.

## 6. Dependencies

No new dependency for the library or the existing pipeline. The audit's optional checks use
tools already on the machine: clang 21 with libFuzzer (fuzzing, mutation check, static
analysis), `curl` (downloads the reference HalfSipHash source into `build/`, not into the
repository).

## 7. Outside the repository

Scratch data under `/opt/strata_fuzz` (fuzz corpus, about 8 000 small files) and
`/opt/strata_clean` (clean copy used for the final verification) in the WSL filesystem. Both
can be deleted.
