# cdesproject — STRATA

**Topic:** The Memory-Constrained Compressed Symbol Table for Embedded Compilers.

STRATA is a scoped symbol table for C-like languages that keeps everything — the name
interner, the declarations and the scope bookkeeping — in **one contiguous buffer** that
the caller can supply. It never throws, it can run without an allocator, and when the buffer
is full it says so and changes nothing.

It is the successor of METIS-X ([adhyan-jain/Metis](https://github.com/adhyan-jain/Metis)).
It was rebuilt, not repaired; `docs/ARCHITECTURE_DECISION.md` explains why. METIS-X's code
is not in this repository: it is fetched at a pinned commit and used as a baseline.

> Status: research artifact and paper draft. Not peer reviewed, not submitted, not integrated
> into a compiler, not run on a microcontroller. See `docs/LIMITATIONS.md`.

## What was measured

Ten tables replayed the symbol-table calls that an instrumented Tiny C Compiler makes while
compiling eight open-source projects (cJSON, littlefs, zlib, Lua, FreeRTOS-Kernel, Mbed TLS,
TinyCC, SQLite). Run `20261011-161306-final`; all numbers below are in `docs/RESULTS.md`
with their source files.

| | STRATA against METIS-X, across the 8 traces |
|---|---|
| Correctness | both agree with the reference model on all 8 |
| Peak heap | 23% to 76% lower (median 58%) |
| Allocator calls | 98.7% to 99.9% fewer |
| Whole-trace replay time | 6% to 49% lower (median 21%); intervals overlap on 3 traces |
| Declare latency (p95) | 20% to 63% lower |
| Lookup latency (p95) | not improved (from 20% lower to 44% higher) |
| Scope-exit latency (p95) | 13% to 58% **higher** |

Fixed-buffer mode: a whole project replays from a buffer of 15.8 KiB (zlib) to 156.5 KiB
(TinyCC), 27 to 36 bytes per live declaration.

What did **not** work out:

* The 85% reduction target was met for allocator calls only. For memory it was reached only
  against one baseline (an interning Swiss-table map), in fixed-buffer mode, on 2 of 8 traces.
* That interning map is faster than STRATA on 7 of 8 traces (median 16%); STRATA's peak heap
  is 44–83% lower than its.
* On a synthetic trace with a 10 000-declaration scope entered 20 times STRATA is 30% slower
  than METIS-X unless shrinking is turned off.
* Timings on the development laptop move by 10–20% between runs.
* The algorithm is the textbook undo-stack symbol table. Our own novelty assessment is
  4.5/10 (`docs/RELATED_WORK.md`), not the 8/10 the project aimed for.

One finding about the old code: METIS-X refuses declarations when a single name is shadowed
about 250 levels deep (149 of 400 refused in our test). STRATA and all other baselines do not.

## How it works

```
 word 0                                                              end of buffer
 | index (linear probing) | identifier records ->   free   <- undo stack |
```

* **Identifier record** — one per distinct visible name: value, type tag, scope depth, and the
  name packed five characters per 32-bit word. It holds the innermost declaration.
* **Undo stack** — one word per declaration; three when it shadows (the hidden declaration is
  saved there). A scope mark is two words.
* **Scope exit** pops the undo stack and empties the index slots of names first seen in that
  scope. They are the newest keys, so no tombstones and no shifting are needed.
* **Fixed mode** `Table(buffer, bytes)`: no allocation, `kNoMemory` when full.
  **Growable mode** `Table(options)`: grows through `realloc`, optional `max_bytes`, shrinks
  when mostly empty.

```cpp
#include "strata/strata.hpp"

static uint32_t buffer[4096];                    // 16 KiB, no heap
strata::Table t(buffer, sizeof buffer);

t.declare_cstr("count", 1);                      // kOk
t.enter_scope();
t.declare_cstr("count", 2);                      // shadows
int32_t v;
t.resolve_cstr("count", &v);                     // v == 2
t.exit_scope();
t.resolve_cstr("count", &v);                     // v == 1
```

Limits: names 1–255 bytes, scope depth 16 383, buffer 64 MiB, 32-bit value, 8-bit type tag.

## Layout of the repository

| Path | Contents |
|---|---|
| `include/strata/strata.hpp` | the table (C++14, header only, no dependencies) |
| `tests/` | correctness tests and the independent reference model |
| `benchmarks/` | harness, fixed-buffer tool, baseline adapters |
| `tools/tcc-trace/` | patch and scripts that make Tiny C Compiler log its symbol-table calls |
| `workloads/traces/` | the eight compiler traces (gzip) and their manifest |
| `scripts/` | `test.sh`, `fetch_third_party.sh`, `build.sh`, `run_all.sh`, `analyze.py`, `make_report.py`, `gen_synthetic.py` |
| `results/raw/` | raw CSVs of two complete runs, with environment files |
| `results/summary/` | tables and figures generated from them |
| `docs/` | audit, decision, design space, related work, methodology, results, limitations, reproducibility, contributions, execution log |
| `paper/` | `main.tex`, `references.bib`, `generated.tex` (numbers), `main.pdf` |

## Build, test, reproduce

Linux x86-64, `g++` (C++14), `python3`, `git`.

```bash
bash scripts/test.sh                 # tests at -O2 and under ASan + UBSan
bash scripts/fetch_third_party.sh    # METIS @ 7b3dacf and parallel-hashmap v1.4.1 (baselines)
bash scripts/run_all.sh mylabel      # all experiments -> results/raw/<timestamp>-mylabel/
python3 scripts/analyze.py results/raw/<run>      # needs pandas, tabulate, matplotlib
python3 scripts/make_report.py <run>              # docs/RESULTS.md + paper/generated.tex
```

Details and expected variation: `docs/REPRODUCIBILITY.md`.

Test status at the reported commit: 1 177 892 checks, 0 failed, in both builds.

## Relationship to METIS-X

| | METIS-X | STRATA |
|---|---|---|
| Key | one slot per declaration | one record per name |
| Names | in the slot up to 12 bytes, else a heap block | in the buffer, packed |
| Shadowing | all declarations of a name in one probe cluster | hidden declarations on an undo stack |
| Scope exit | backward shift per entry | pop two stacks, empty the newest slots |
| Memory | grows, never shrinks, many allocations | one buffer; fixed or growable with a budget |
| Failure | can throw; refuses past 250 equal-hash keys | status codes; state unchanged on failure |
| Traces | regular expressions over source text | calls logged by a real compiler |

The four traces of the METIS-X manuscript are still run, as a labelled supplement.

## Authors and how this was produced

Shubhi Singh and Adhyan Jain (VIT Vellore). This repository was produced in one session by
an AI coding assistant working in Shubhi Singh's environment; Adhyan Jain has not yet
reviewed it. See `docs/CONTRIBUTIONS.md` before citing or submitting anything.

## Licence

MIT (`LICENSE`). The compiler traces are lists of identifiers produced by compiling the
projects named in `workloads/traces/MANIFEST.tsv`; those projects keep their own licences.
