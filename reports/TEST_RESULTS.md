# Test results

Audit of 2026-10-13. Every result below comes from a command that was run; the log file is
named in the last column. Host: WSL 2 (Ubuntu 22.04) on an Intel Core Ultra 7 258V, g++ 11.4,
clang 21.1.8 (`reports/artifacts/environment.txt`).

## Summary

| Status | Count | What |
|---|---|---|
| PASS | 20 test groups | listed in section 1 |
| FAIL (final state) | 0 | |
| FAIL found and fixed | 1 | CLI case C30, `budget --reps 0` (section 3) |
| BLOCKED | 2 | 32-bit host build of the unit tests; run on a physical microcontroller |
| NOT TESTED | 6 | section 4 |
| NOT APPLICABLE | all browser tests | the project has no web interface (section 5) |

Final clean-copy verification: 12 of 12 steps passed (`artifacts/final_verification.log`).

## 1. Inventory and results

| ID | Test | Command | Result | Evidence |
|---|---|---|---|---|
| U1 | Unit and randomized differential tests, `-O2` | `bash scripts/test.sh` | PASS: 2 706 587 checks, 0 failed (1 856 579 before the audit added two test functions) | `artifacts/p2_test.log`, `final_verification.log` |
| U2 | The same under ASan + UBSan (g++) | `bash scripts/test.sh` | PASS: 2 706 587 checks, 0 failed, no sanitizer report | same |
| U3 | The same under ASan + UBSan + integer checks (clang 21) | `bash scripts/audit/static_analysis.sh` | PASS | `artifacts/static_analysis.log` |
| X1 | Bounded exhaustive check, depth 7 | part of `scripts/test.sh` | PASS: 2 239 488 sequences, 0 failures | `final_verification.log` |
| X2 | Bounded exhaustive check, depth 9 | `bash scripts/audit/exhaustive.sh 9` | PASS: 80 621 568 sequences, 725 594 112 operations, 130 361 632 refused operations (75 575 944 no-memory, 54 785 688 probe-limit), 0 failures, 1 min 54 s | `artifacts/exhaustive_small.log` |
| F1 | Differential fuzzing of the code **as found** (before any change) | `bash scripts/audit/fuzz.sh 600 3` | PASS: 9 773 374 executions, no failure, no sanitizer report | `artifacts/fuzz_strata_before_changes.log` |
| F2 | Differential fuzzing of the final code, all modes | `bash scripts/audit/fuzz.sh 600 3` | PASS: 2 239 433 executions, no failure | `artifacts/fuzz_strata.log` |
| M1 | Does the fuzzer catch bugs? Six injected defects | `python3 scripts/audit/mutation_check.py 60` | PASS: 6 of 6 detected, each within 0.2 s | `artifacts/mutation_check.log` |
| S1 | Strict warnings: g++ and clang `-Weverything`, C++14/17/20 | `static_analysis.sh` | PASS: 0 warnings (2 found in the new fuzz harness and fixed) | `artifacts/static_analysis.log` |
| S2 | Path-sensitive analyzers: clang static analyzer, `g++ -fanalyzer` | `static_analysis.sh` | PASS: no report | same |
| S3 | Header alone with `-fno-exceptions -fno-rtti -Werror`, host and `arm-none-eabi-g++ -mcpu=cortex-m3` | `static_analysis.sh` | PASS | same |
| H1 | Keyed hash against the reference HalfSipHash source | `bash scripts/audit/halfsiphash_check.sh` | PASS: 200 000 random inputs, 0 mismatches (reference file SHA-256 `096b33b6...8301c`) | `artifacts/halfsiphash_conformance.log` |
| E1 | Bare-metal Cortex-M3 under QEMU, fixed mode, 5 traces | `bash tools/embedded/run.sh zlib littlefs cjson lua freertos` | PASS: 5 of 5, checksums equal to the host | `artifacts/embedded_qemu.log`, `results/embedded/qemu_cortex_m3.txt` |
| E2 | The same in bounded mode (static index, probe limit 64, keyed hash) | `bash tools/embedded/bounded.sh` | PASS: 5 of 5, 0 refused, checksums equal to the ordinary fixed-mode host run | `results/embedded/qemu_cortex_m3_bounded.txt` |
| B1 | All 13 tables against the reference model on the 8 TinyCC traces | `bash scripts/audit/repro.sh audit` | PASS: 104 table/trace pairs, 0 wrong lookups, 0 wrong declaration results, 0 refused | `results/raw/20261013-120345-audit/`, `artifacts/repro_comparison.md` |
| B2 | Minimum fixed buffer reproduces | same | PASS: 32 of 32 values identical to the stored run | `artifacts/repro_comparison.md` |
| D1 | Flooding experiment: generated names collide; every configuration answers correctly | `bash scripts/audit/hardening.sh 5` | PASS: 32 768 names verified to collide under 9 seeds; 48 of 48 rows correct | `results/hardening/flood.csv`, `flood_verification.txt` |
| D2 | Bounded mode on 15 compiler traces, 7 probe limits, 2 hashes | same | PASS: 210 rows, 0 wrong lookups, 0 rebuilds | `results/hardening/traces.csv` |
| C | 41 command-line robustness cases under sanitizers | `bash scripts/audit/cli_tests.sh` | PASS: 41 of 41 (first run: 39 of 40) | `artifacts/cli_tests.log` |
| V | Everything above again from a clean copy of the tree | `bash scripts/audit/final_verify.sh` | PASS: 12 of 12 steps | `artifacts/final_verification.log` |

## 2. What the new tests check

- **Differential fuzzer** (`tests/fuzz_strata.cpp`). Input bytes select a configuration (fixed or growable, buffer size, packed or raw names, dense or sparse index, all keys in one cluster, failing allocator, keyed hash, static index, probe limit, an invalid configuration) and up to 4096 operations with names from a colliding pool or arbitrary bytes of length 0 to 455. After every operation the table must agree with the reference model; after every refusal the state digest must be unchanged; invariants are re-checked every 16 operations; at the end the table is unwound and leaks through the supplied allocator are checked. Coverage counter reported by libFuzzer: 529 edges before the new modes, 595 after.
- **Bounded exhaustive check** (`tests/exhaustive_small.cpp`). Every sequence of exactly *d* operations over {enter, exit, declare a, b, c, d} from an empty table, in 8 configurations chosen so that each kind of refusal occurs. This covers all shorter sequences as prefixes. It is exhaustive only within that scope.
- **Mutation check.** Six one-line defects (slot not emptied on scope exit, stale pointer after a buffer move, hidden type not restored, probe limit not enforced, raw-name length dropped, refused declaration that still writes). All six are detected.

## 3. Command-line robustness (Phase 3 equivalent)

`scripts/audit/cli_tests.sh` builds `bench`, `budget` and `hardening` with ASan + UBSan and runs
41 cases: missing, empty, blank, random-byte and CRLF files; unknown tags; names of 255, 256
and 300 bytes; non-ASCII, NUL, tab and `::` in names; 20 000 nested scopes; a 5 MB line;
consecutive unit separators; unknown options; an option without a value; zero, negative and
non-numeric repetition counts; an unwritable output path; invalid generator parameters.

| Case | Purpose | Expected | First run | After fix |
|---|---|---|---|---|
| C30 | `budget --mode budget --reps 0` | exit 0 | **FAIL**: UBSan "applying non-zero offset to null pointer" (median of an empty vector) | PASS |
| other 40 | see `artifacts/cli_tests.log` | defined exit status, no sanitizer report | PASS | PASS |

## 4. Not tested, and blocked

| Item | Status | Why |
|---|---|---|
| Unit tests built for a 32-bit host (`g++ -m32`) | BLOCKED | multilib not installed; not installed during the audit to avoid changing the system toolchain. The 32-bit evidence is the Cortex-M3 replay. |
| Physical microcontroller | BLOCKED | no device available |
| Full pipeline `scripts/run_all.sh` (synthetic traces, legacy traces, chibicc trace timing, worst-case clustering) | NOT TESTED | only the 8 TinyCC traces were re-measured; about 45 minutes for the rest |
| `scripts/analyze.py`, `scripts/make_report.py`, `scripts/extra_report.py` | NOT TESTED | `docs/RESULTS.md` and `paper/generated.tex` were not regenerated and still describe run `20261011-165103-v3` |
| Trace regeneration (`tools/tcc-trace/`, `tools/chibicc/`) and the chibicc end-to-end integration | NOT TESTED | stored traces were used |
| Paper build (`paper/main.tex`) | NOT TESTED | paper not changed |
| Big-endian target | NOT TESTED | no such target available; the keyed hash reads words in host order |
| valgrind, cppcheck | NOT RUN | not installed; sanitizers and two static analyzers were used instead |

## 5. Browser workflow coverage

None, and none claimed. The repository contains a header library, command-line tools, scripts
and a LaTeX paper. There is no page, form, login, upload, API endpoint or database to open in
a browser, so the brief's browser, UI, responsiveness and accessibility tests do not apply.
No screenshots exist for the same reason; the artifacts are logs and CSV files.

## 6. Known gaps in coverage

- Tests exercise `value` and `type` round-trips but not every `Stats` field.
- The fuzzer's operation cap (4096) and buffer cap (16 KiB fixed, about 4 KiB initial growable) leave very large tables to the randomized unit tests and trace replays.
- The failing-allocator path is fuzzed with `alloc`/`free` hooks only, not with a custom `realloc` hook.
- `arena_chain` (the baseline) is checked against the reference model on traces but was not fuzzed.
