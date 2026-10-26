# STRATA — a bounded-memory scoped symbol table

STRATA keeps a compiler's scoped symbol table in **one caller-supplied buffer**: no allocator, a
defined "out of memory" result, and a refusal that leaves the table exactly as it was. This repository
holds the library, its tests, the benchmarks and compiler traces, the verification programs of the
analysis, an interactive demo, and the IEEE Access manuscript.

> Status: research artifact. Not peer reviewed, not integrated into a production compiler, run on an
> emulated microcontroller only. Read `docs/LIMITATIONS.md` before relying on any claim.

## What is claimed, and where it is checked

| Claim | Where |
|---|---|
| Single buffer; every refused call leaves the buffer byte-for-byte unchanged | `tests/`, `docs/CORRECTNESS.md`, `docs/EVIDENCE.md` |
| Popping the newest key is an exact undo (index cells), so the index equals the insertion-only index of the live names; LIFO is the only deletion order safe for every table (linear probing) | article Section V, `theory/verify/` |
| Exact refusal probability of a probe limit in the ideal-hash model (first capped query), with bounds for the refusal-filtered process | article Section VI, `theory/verify/`, `docs/EVIDENCE.md` |
| About one sixth smaller fixed buffer than a conventional single-buffer table on eight C traces; most of it is a stored hash word and name packing | article Section IX, `docs/RESULTS.md`, `results/review/` |
| No end-to-end speedup in a hosted compiler (chibicc); emulated Cortex-M3 runs only | article Sections IX-J, K |

Numbers are produced by programs from the raw files in `results/`; the article's tables are generated, not typed.

## How STRATA works

```
 word 0                                                              end of buffer
 | index (linear probing) | identifier records ->   free   <- undo stack |
```

* **Identifier record**: one per distinct visible name: value, a meta word (type, scope depth, name
  length), and the name packed five characters per 32-bit word. It holds the innermost declaration.
* **Undo stack**: one word per first declaration (the name's index slot), three when it shadows (the
  hidden declaration is saved there); a scope mark is two words.
* **Scope exit** pops the undo stack and empties the recorded slots. Those keys are the newest in the
  index, so no tombstones and no shifting are needed.
* **Modes**: fixed `Table(buffer, bytes)` (never allocates, `kNoMemory` when full); growable
  `Table(options)`; **bounded** (static index, probe limit `L`, optional keyed HalfSipHash-1-3).

```cpp
#include "strata/strata.hpp"

static uint32_t buffer[4096];                    // 16 KiB, no heap
strata::Table t(buffer, sizeof buffer);
t.declare_cstr("count", 1);                      // kOk
t.enter_scope();
t.declare_cstr("count", 2);                      // shadows
t.exit_scope();                                  // "count" is 1 again

strata::Options o;                               // bounded mode
o.index_slots = 2048; o.max_probe = 512;
o.keyed = true; o.key[0] = k0; o.key[1] = k1;    // key from the device, a fresh one per table
strata::Table b(buffer, sizeof buffer, o);
```

Limits: names 1–255 bytes, scope depth 16 383, buffer at most 2^24−1 words (64 MiB − 4 bytes), 32-bit
value, 8-bit type tag. Bit-level layout: `docs/EVIDENCE.md`, part 4. Bounded mode bounds the index slots
examined by `declare`/`resolve`; scope exit is proportional to the scope, and default mode rebuilds the
index on growth.

## Repository layout

| Path | Contents |
|---|---|
| `include/strata/strata.hpp` | the library (C++14, header only) |
| `tests/` | unit and differential tests, independent reference model, exhaustive enumeration, fuzzer, `test_review.cpp` |
| `benchmarks/` | replay harness, fixed-buffer search, hardening (flooding) experiments; `baselines/` has the conventional arena tables |
| `workloads/traces/` | compiler traces (TinyCC and chibicc); checksums in `docs/trace_checksums*.sha256` |
| `tools/` | trace recorders (`tcc-trace/`), chibicc integration (`chibicc/`), Cortex-M3 build (`embedded/`), review helpers (`review/`) |
| `scripts/` | build, test, full pipeline (`run_all.sh`), analysis, report generators, `audit/` verification scripts |
| `results/` | raw CSVs and summaries of the paper run, hardening, chibicc, embedded and review experiments |
| `reports/artifacts/` | logs of the verification runs (tests, fuzzing, mutation, exhaustive enumeration) |
| `theory/` | theory manuscript sources (`paper/`), verification programs (`verify/`), figure templates (`template/`) |
| `manuscript/ieee_access/` | the IEEE Access article (LaTeX) with generated tables and figures; `final/` is the course-template version; `tools/` and `figures/source/` regenerate numbers and plots |
| `paper/` | the earlier empirical paper and the generated numbers it shares |
| `frontend/` | interactive demo (React plus a C++ engine linked to the unmodified header) |
| `docs/` | the documents below |

## Documents

| File | Contents |
|---|---|
| `docs/CORRECTNESS.md` | the correctness argument and the test strategy |
| `docs/LIMITATIONS.md` | what the evidence does not cover |
| `docs/RESULTS.md` | generated results of run `20261013-143828-paper` |
| `docs/REPRODUCIBILITY.md` | environment and how to rerun |
| `docs/REVIEW_MANIFEST.md` | every table, figure and number of the article mapped to the command that produces it, with run times |
| `docs/EVIDENCE.md` | trace semantics, embedded and chibicc experiments, flooding, encodings, exhaustive harness, added tests |
| `docs/REVIEW_EXPERIMENTS_BENCH.md` | the stronger baseline without a stored hash, the monotonicity scan, the five timing sessions, timer and machine details |
| `docs/AI_USE_DISCLOSURE.md` | account of AI assistance |
| `theory/README.md`, `frontend/README.md`, `manuscript/ieee_access/README.md` | how to build the theory paper, the demo and the article |

Earlier runs, drafts, audit reports and process logs were removed from the working tree. They remain in git
under the tag `pre-cleanup` (`git show pre-cleanup:<path>`).

## Build, test, reproduce

Linux x86-64, `g++` (C++14), `python3`, `git`.

```bash
bash scripts/test.sh                 # tests at -O2 and under ASan + UBSan, bounded exhaustive check, review tests
bash scripts/audit/exhaustive.sh 9   # 80 621 568 operation sequences, a few minutes
bash scripts/fetch_third_party.sh    # METIS @ 7b3dacf and parallel-hashmap v1.4.1 @ 22a7f6c (baselines)
bash scripts/run_all.sh mylabel      # all experiments -> results/raw/<timestamp>-mylabel/
python3 scripts/analyze.py results/raw/<run>      # needs pandas, tabulate, matplotlib
python3 scripts/make_report.py <run>              # docs/RESULTS.md + paper/generated.tex
bash theory/verify/run_all.sh        # exact law, proofs, design tables; builds the theory PDF
bash tools/embedded/run.sh           # optional: arm-none-eabi-g++ and qemu-system-arm

cd manuscript/ieee_access && pdflatex main && bibtex main && pdflatex main && pdflatex main
cd frontend/web && npm install && npm test && npm start
```

Details and the expected run-to-run variation: `docs/REPRODUCIBILITY.md`.

## Authors and provenance

Authors of the IEEE Access manuscript: Adhyan Jain and Shubhi Singh (Vellore Institute of Technology), under the
guidance of Prof. Bhuvaneshwari M. The implementation, experiments, proofs and text were produced with AI coding
assistants working at the authors' direction; `docs/AI_USE_DISCLOSURE.md` records what was done and how it was checked.

## Licence

MIT (`LICENSE`). The compiler traces are lists of identifiers produced by compiling the projects named in
`workloads/traces/MANIFEST.tsv`; those projects keep their own licences.
