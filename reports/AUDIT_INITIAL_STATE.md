# Audit: initial state

Date: 2026-10-13. Repository `cdesproject` at commit `cd3b4cc` (clean working tree, in sync with
`origin/main`, private GitHub repository `shubhisingh1510/cdesproject`). Everything below
describes the project **before** the audit changed anything.

## 1. What the project is

A research artifact on scoped symbol tables for compilers that must run in a fixed amount of
memory. Topic line: "The Memory-Constrained Compressed Symbol Table for Embedded Compilers".

| Item | State found |
|---|---|
| Kind of software | A C++14 header-only library, command-line benchmark tools, shell and Python scripts, a LaTeX paper. **There is no server, no web page and no user interface.** |
| Proposed table | STRATA, `include/strata/strata.hpp` (586 lines): interned names, an undo stack and scope marks in one caller-supplied buffer; fixed and growable modes |
| Strong baseline | `benchmarks/baselines/arena_chain.hpp`: a conventional chained table in one buffer |
| Other baselines | per-scope `std::unordered_map`, undo log over `std::unordered_map`, the same over parallel-hashmap, an interning Swiss map, and three tables of the earlier project METIS (fetched at a pinned commit, not stored) |
| Workloads | symbol-table calls logged by a patched Tiny C Compiler on 8 pinned C projects (`workloads/traces/`), 7 traces from a patched chibicc, synthetic stress traces, 4 regex-extracted traces of the earlier work |
| Reported run | `results/raw/20261011-165103-v3` (31 interleaved paired rounds) |
| Paper | `paper/main.tex`, 5 pages, "When Does a Compact Scoped Symbol Table Pay Off?" |

## 2. Research claims found (to be verified)

From `README.md`, `docs/RESULTS.md` and the paper:

1. STRATA and all baselines agree with an independent reference model on every trace.
2. Against METIS-X on the 8 compiler traces: peak heap 23-76% lower, allocator calls about 99% fewer, replay faster on 7 and slower on 1.
3. Against the conventional arena table: the smallest fixed buffer is 16-18% smaller on every trace; replay is **slower** on 7 of 8 traces (median 30%).
4. A refused operation (`kNoMemory`, `kTooDeep`, invalid name) leaves the table bit-for-bit unchanged.
5. It runs on a bare-metal Cortex-M3 under QEMU with 64 KiB of RAM and no heap, with host-identical results.
6. Self-assessed novelty about 4.5/10; the 8/10 goal is stated as **not** reached.

The documents are unusually candid: negative results, an unprotected worst case and missing
experiments are listed in `docs/LIMITATIONS.md`.

## 3. How to build and run (as documented, Linux x86-64)

```
bash scripts/test.sh                 # tests at -O2 and under ASan + UBSan
bash scripts/fetch_third_party.sh    # METIS @ 7b3dacf, parallel-hashmap v1.4.1
bash scripts/run_all.sh <label>      # all experiments -> results/raw/<timestamp>-<label>/
python3 scripts/analyze.py results/raw/<run>
python3 scripts/make_report.py <run>
bash tools/embedded/run.sh           # arm-none-eabi-g++ and qemu-system-arm
```

Environment available for the audit: Windows 11 with WSL 2 (Ubuntu 22.04), g++ 11.4, clang 21.1.8
with libFuzzer and the sanitizer runtimes, arm-none-eabi-g++ 10.3.1, QEMU 6.2, Python 3.10 in
WSL and Python with pandas/matplotlib on Windows. Not available: cppcheck, valgrind, a 32-bit
host multilib, any physical microcontroller.

## 4. Issues known or suspected before testing

Taken from the project's own documents and from reading the source:

| # | Issue | Source |
|---|---|---|
| K1 | The hash is unkeyed; with every key in one cluster a lookup scans the cluster. "A compiler that reads untrusted source and needs a bound would need a seeded hash or a probe limit." | `docs/LIMITATIONS.md` |
| K2 | An index rebuild is O(live names) and happens inside `declare` or `exit_scope`: no constant bound on the latency of those calls. | `docs/LIMITATIONS.md` |
| K3 | No fuzzing; correctness rests on hand-written and randomized tests. | reading `tests/` |
| K4 | The correctness argument is informal; nothing is machine-checked or exhaustively enumerated. | `docs/CORRECTNESS.md` |
| K5 | `parallel-hashmap` is fetched by tag, not by commit. | `scripts/fetch_third_party.sh` |
| K6 | Project sources for trace regeneration are fetched by tag or URL without checksums. | `tools/tcc-trace/make_traces.sh` |
| K7 | Not integrated into a compiler as a replacement; no hardware run; C only; one machine. | `docs/LIMITATIONS.md` |
| K8 | Co-authors have not reviewed the repository or the paper. | `docs/CONTRIBUTIONS.md` |

Checked and **not** found: placeholder functions, hardcoded outputs, mock data (`git grep` for
TODO/FIXME/placeholder/mock in tracked sources: no hits); secrets, tokens or machine paths in
tracked files; an empty `src/` directory exists and is unused.

## 5. Testing tools available

| Need | Tool | Used |
|---|---|---|
| Unit and randomized tests | `tests/test_strata.cpp` (existing) | yes |
| Memory and undefined-behaviour errors | ASan, UBSan (g++ and clang) | yes |
| Fuzzing | libFuzzer in clang 21 | yes (written during the audit) |
| Static analysis | clang static analyzer, `g++ -fanalyzer`, `-Weverything` | yes |
| Embedded target | arm-none-eabi-g++, QEMU mps2-an385 | yes |
| Browser automation | a Chrome automation integration is installed on this machine | **not applicable**: the project has nothing to open in a browser |

## 6. Phases of the brief that do not apply

The brief's Phase 2 (start backend/frontend, open in a browser) and Phase 3 (browser testing of
pages, forms, authentication, uploads, responsiveness, accessibility) assume a web application.
This project has none. Those items are recorded as NOT APPLICABLE in `TEST_RESULTS.md`; no
browser was opened and none is claimed. The equivalent work done instead: building and running
every documented command, and testing the command-line tools with valid, invalid, empty and
boundary inputs.
