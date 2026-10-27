# STRATA — a bounded-memory scoped symbol table

STRATA keeps a compiler's scoped symbol table in **one caller-supplied buffer**: no allocator, a
defined "out of memory" result, and a refusal that leaves the table exactly as it was. This repository
holds the library, its tests, the benchmarks and compiler traces, the verification programs of the
analysis, an interactive demo, and the IEEE Access manuscript.

> Status: research artifact. Not peer reviewed, not integrated into a production compiler, run on an
> emulated microcontroller only. STRATA is **smaller but not faster** than a conventional single-buffer
> table. Read `docs/LIMITATIONS.md` before relying on any claim.

## What is claimed, and where it is checked

| Claim | Where |
|---|---|
| Single buffer; every refused call leaves the buffer byte-for-byte unchanged | `tests/`, `docs/CORRECTNESS.md`, `docs/EVIDENCE.md` part 6 |
| Popping the newest key is an exact undo (index cells), so the index equals the insertion-only index of the live names; for linear probing LIFO is the only deletion order safe for every table | article Section V, `theory/verify/` |
| Exact refusal probability of a probe limit in the ideal-hash model (first capped query), with proved bounds for the refusal-filtered process | article Section VI and appendix, `theory/verify/` |
| About one sixth smaller fixed buffer than a conventional single-buffer table that stores a hash word (16.4-17.9%), but 5.3-9.0% against one that does not; almost all of the latter is name packing | article Section IX, `docs/EVIDENCE.md` parts 7-8, `results/review/` |
| **Slower** than the conventional table with a stored hash on all 8 traces (5-18% in five timing sessions on the final code) and than the one without on 6 of 8 (4-13%); 31-41% more instructions executed; faster than its heap-based predecessor METIS-X | article Section IX, `docs/EVIDENCE.md` parts 8 and 10 |
| No end-to-end speedup in a hosted compiler (chibicc); emulated Cortex-M3 runs only, no physical-device timing | article Sections IX-J, K |

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

strata::Key k;                                   // optional: pack and hash a name once,
b.make_key("count", 5, k);                       // then declare(k, ...) / resolve(k, ...)
```

Limits: names 1-255 bytes, scope depth 16 383, buffer at most 2^24−1 words (64 MiB − 4 bytes), 32-bit
value, 8-bit type tag. Bit-level layout: `docs/EVIDENCE.md`, part 4. Bounded mode bounds the index slots
examined by `declare`/`resolve`; scope exit is proportional to the scope, and default mode rebuilds the
index on growth.

## Repository layout

| Path | Contents |
|---|---|
| `include/strata/strata.hpp` | the library (C++14, header only) |
| `tests/` | unit and differential tests, independent reference model, exhaustive enumeration, fuzzer, `test_review.cpp` |
| `benchmarks/` | replay harness, fixed-buffer search, hardening (flooding), instruction counts; `baselines/` has the conventional arena tables |
| `workloads/traces/` | compiler traces (TinyCC and chibicc); checksums in `docs/trace_checksums*.sha256` |
| `tools/` | trace recorders (`tcc-trace/`), chibicc integration (`chibicc/`), Cortex-M3 build (`embedded/`), review helpers (`review/`) |
| `scripts/` | build, test, full pipeline (`run_all.sh`), analysis, report generators, `audit/` verification scripts |
| `results/` | raw CSVs and summaries of the paper run, hardening, chibicc, embedded and review experiments |
| `reports/artifacts/` | logs of the verification runs (tests, fuzzing, mutation, exhaustive enumeration) |
| `theory/` | theory manuscript sources (`paper/`), verification programs (`verify/`), figure templates (`template/`) |
| `manuscript/ieee_access/` | the IEEE Access article (LaTeX); `tables/` and `generated_numbers.tex` are generated; `manuscript/final/` is the course-template version |
| `paper/` | the earlier empirical paper and the generated numbers it shares |
| `frontend/` | interactive demo (React plus a C++ engine linked to the unmodified header); see `frontend/README.md` |

## Documents

| File | Contents |
|---|---|
| `docs/CORRECTNESS.md` | the correctness argument and the test strategy |
| `docs/LIMITATIONS.md` | what the evidence does not cover, and where STRATA is worse |
| `docs/EVIDENCE.md` | trace semantics, embedded and chibicc experiments, flooding, encodings, exhaustive harness, added tests (parts 1-6); the command-to-result manifest (7); the stronger baseline, monotonicity scan and timing sessions (8); rerunning from a clean checkout (9); instruction counts and the speed experiments (10) |
| `docs/AI_USE_DISCLOSURE.md` | account of AI assistance |
| `frontend/README.md` | the interactive demo |

Earlier runs, drafts, audit reports and process logs were removed from the working tree. They remain in git
under the tag `pre-cleanup` (`git show pre-cleanup:<path>`). `docs/RESULTS.md` is generated by
`scripts/make_report.py` and is not tracked.

## Build, test, reproduce

Linux x86-64, `g++` (C++14), `python3`, `git`; optional `clang++` (sanitizer and fuzzing runs),
`arm-none-eabi-g++` and `qemu-system-arm` (embedded), `pdflatex` and `bibtex` (manuscripts), Node (demo).

```bash
bash scripts/test.sh                 # tests at -O2 and under ASan + UBSan, bounded exhaustive check, review tests
CXX=clang++ bash scripts/test.sh     # the same with clang
bash scripts/audit/exhaustive.sh 9   # 80 621 568 operation sequences, a few minutes
bash scripts/audit/fuzz.sh 240 4     # libFuzzer (FUZZ_CXX=clang++ FUZZ_DIR=/some/dir), then scripts/audit/mutation_check.py
bash scripts/fetch_third_party.sh    # METIS @ 7b3dacf and parallel-hashmap v1.4.1 @ 22a7f6c (baselines)
bash scripts/run_all.sh mylabel      # all experiments -> results/raw/<timestamp>-mylabel/
python3 scripts/analyze.py results/raw/<run>      # needs pandas, tabulate, matplotlib
python3 scripts/make_report.py <run>              # docs/RESULTS.md + paper/generated.tex
bash theory/verify/run_all.sh        # exact law, proofs, design tables; builds the theory PDF (about 9 minutes;
                                     # needs pdflatex, latexmk, pgfplots; no network)
bash tools/embedded/run.sh           # optional: arm-none-eabi-g++ and qemu-system-arm

# instruction counts (needs perf_event_paranoid <= 2): see docs/EVIDENCE.md part 10
g++ -std=c++14 -O2 -o build/instr_count benchmarks/instr_count.cpp

cd manuscript/ieee_access && pdflatex main && bibtex main && pdflatex main && pdflatex main
cd frontend/web && npm install && npm test && npm start
```

Details, expected run times and the expected run-to-run variation: `docs/EVIDENCE.md` parts 7 and 9.

**The manuscript** (`manuscript/ieee_access/`, pdfLaTeX, BibTeX with `IEEEtran.bst`, official IEEE Access template):
`main.tex`, `abstract.tex` and `body.tex` are edited by hand; `generated_numbers.tex` and `tables/tab_*.tex` come from
`manuscript/tools/make_numbers.py`, `tab_sessions` and `tab_c1` from `make_sessions_tables.py`, `tab_instr` from
`make_instr_table.py`, `tables/th_*.tex` from `theory/verify/run_all.sh`; `python3 manuscript/tools/crosscheck.py`
checks that the generators agree. Zip the directory for Overleaf (`zip -r strata.zip .`).

**The theory** (`theory/paper/main.tex`, `theory/verify/`) proves the exact undo (every non-reordering rule), the safe
deletion orders and their orphan law, the exact finite-size refusal law (the classical tail of the unsuccessful-search
cost, with an explicit sum), the whole-fill probability, and the key-lifetime results; every theorem has a program
under `theory/verify/` that checks it by enumeration in exact arithmetic.

## Authors and provenance

Authors of the IEEE Access manuscript: Adhyan Jain, Shubhi Singh and Prof. Bhuvaneswari M. (corresponding author),
Vellore Institute of Technology. AI coding assistants were used at the authors' direction for planning, writing code,
help with the literature review, and drafting and editing text; `docs/AI_USE_DISCLOSURE.md` records what was done and how
it was checked.

## Licence

MIT (`LICENSE`). The compiler traces are lists of identifiers produced by compiling the projects named in
`workloads/traces/MANIFEST.tsv`; those projects keep their own licences.
