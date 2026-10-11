# cdesproject — bounded-memory scoped symbol tables (STRATA)

**Topic:** The Memory-Constrained Compressed Symbol Table for Embedded Compilers.

This repository studies symbol tables that live in **one fixed buffer**: no allocator, a
defined "out of memory" result, nothing half-done. It contains two such tables, compares
them with eight others on events logged by a real C compiler, and reports what was gained
and what was not.

* **STRATA** (`include/strata/strata.hpp`): each visible name stored once, packed; hidden
  declarations on an undo stack.
* **arena_chain** (`benchmarks/baselines/arena_chain.hpp`): the conventional design, a chained
  hash table over an entry arena. Written as a strong baseline.

It is the successor of METIS-X ([adhyan-jain/Metis](https://github.com/adhyan-jain/Metis)),
rebuilt rather than repaired (`docs/ARCHITECTURE_DECISION.md`). METIS-X's code is fetched at
a pinned commit and is not stored here.

> Status: research artifact and paper draft. Not peer reviewed, not submitted, not integrated
> into a compiler, run on an emulated microcontroller only. See `docs/LIMITATIONS.md`.

## Results at a glance

Run `20261011-165103-v3`: 31 paired rounds, 12 tables, 8 compiler traces (cJSON, littlefs,
zlib, Lua, FreeRTOS-Kernel, Mbed TLS, TinyCC, SQLite as compiled by an instrumented Tiny C
Compiler). Every number is in `docs/RESULTS.md` with its source file.

### STRATA against the previous table (METIS-X)

| Metric | Result across the 8 traces |
|---|---|
| Correctness | both agree with the reference model on all 8 |
| Peak heap | 23% to 76% lower (median 58%) |
| Allocator calls | 98.7% to 99.9% fewer |
| Replay time | faster on 7 traces, slower on 1 (cJSON, 6%); median 11% faster |
| Declare latency (p95) | 44% to 64% lower |
| Scope-exit latency (p95) | 67% to 88% lower |
| Lookup latency (p95) | not improved (lower on 3 of 8) |

### STRATA against a conventional allocator-free table (arena_chain)

| Metric | Result |
|---|---|
| Smallest fixed buffer | STRATA 16% to 18% smaller on every trace |
| Replay time, compiler traces | STRATA **slower** on 7 of 8 (median 30%) |
| Replay time, synthetic traces | STRATA faster on 5 of 9 (shadowing, scope churn, short names), slower on 3 |

### What this means

| Question | Answer from the data |
|---|---|
| Where does the gain over METIS-X come from? | Mostly from keeping everything in one allocation-free arena. The conventional table alone is 55–77% below METIS-X's peak heap and 11–36% faster. |
| What does STRATA's own design add? | About one sixth less memory, lookups whose cost does not grow with shadowing, and wins on shadow-heavy workloads; it costs time on ordinary C code. |
| How much memory does a project need? | 15.8 KiB (zlib) to 156.5 KiB (TinyCC): 27–36 bytes per live declaration. |
| Does it run on a small 32-bit target? | Under emulation: 5 traces on a bare-metal Cortex-M3 (QEMU) with 64 KiB RAM, no heap, 792 bytes of stack, about 2.6 KB of code, same results as the PC. Not on hardware. |
| Was the 85% target met? | For allocator calls, yes, on every trace. Scope-exit latency reaches it on 1 of 8 traces (range 67–88%). For memory against METIS-X, no (best 76% heap, 81% fixed buffer). |
| Is it novel? | Not as an algorithm. Our own assessment is about 4.5/10 (`docs/RELATED_WORK.md`). |

One finding about the old code: METIS-X refuses declarations when one name is shadowed about
250 levels deep (149 of 400 refused in our test). No other table does.

### What changed after review

| Review point | What was done | Outcome |
|---|---|---|
| Scope exit 13–58% slower than METIS-X | Undo entries record the index slot; exit empties it directly | now 67–88% faster than METIS-X |
| 30% slowdown on a large repeated scope | Shrinking waits for 64 calm scope exits | now about 2x faster than METIS-X there |
| Timing confidence | 31 interleaved rounds, paired differences, bootstrap intervals | all 8 comparisons with METIS-X are now established (7 faster, 1 slower) |
| No allocator-free baseline | `arena_chain` added | showed that most of the gain is not specific to STRATA |
| No embedded validation | bare-metal Cortex-M3 under QEMU | passes; still an emulator |
| Guarantees not verified | state digest before/after every refused operation, 30 configurations, adversarial collisions | `docs/CORRECTNESS.md`, 1 856 579 checks pass |

## How STRATA works

```
 word 0                                                              end of buffer
 | index (linear probing) | identifier records ->   free   <- undo stack |
```

* **Identifier record** — one per distinct visible name: value, type tag, scope depth, and the
  name packed five characters per 32-bit word. It holds the innermost declaration.
* **Undo stack** — one word per declaration (the name's index slot); three when it shadows
  (the hidden declaration is saved there). A scope mark is two words.
* **Scope exit** pops the undo stack and empties the recorded slots. Those keys are the
  newest in the index, so no tombstones and no shifting are needed (`docs/CORRECTNESS.md`).
* **Fixed mode** `Table(buffer, bytes)`: no allocation, `kNoMemory` when full, state unchanged.
  **Growable mode** `Table(options)`: `realloc` growth, optional `max_bytes`, delayed shrinking.

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

## Repository layout

| Path | Contents |
|---|---|
| `include/strata/strata.hpp` | STRATA (C++14, header only, no dependencies) |
| `benchmarks/baselines/` | `arena_chain.hpp` and the adapters for all compared tables |
| `benchmarks/` | replay harness, fixed-buffer tool |
| `tests/` | correctness tests and the independent reference model |
| `tools/tcc-trace/` | patch and scripts that make Tiny C Compiler log its symbol-table calls |
| `tools/embedded/` | bare-metal Cortex-M3 build and QEMU runner |
| `workloads/traces/` | the eight compiler traces (gzip) and their manifest |
| `scripts/` | `test.sh`, `fetch_third_party.sh`, `build.sh`, `run_all.sh`, `analyze.py`, `make_report.py`, `gen_synthetic.py` |
| `results/raw/`, `results/summary/` | raw CSVs of four complete runs; generated tables and figures |
| `results/embedded/` | log of the emulated Cortex-M3 run |
| `docs/` | audit, decision, design space, related work, methodology, correctness, results, limitations, reproducibility, contributions, execution log |
| `paper/` | `main.tex`, `references.bib`, `generated.tex` (numbers), `main.pdf` |

## Build, test, reproduce

Linux x86-64, `g++` (C++14), `python3`, `git`.

```bash
bash scripts/test.sh                 # tests at -O2 and under ASan + UBSan
bash scripts/fetch_third_party.sh    # METIS @ 7b3dacf and parallel-hashmap v1.4.1 (baselines)
bash scripts/run_all.sh mylabel      # all experiments -> results/raw/<timestamp>-mylabel/
python3 scripts/analyze.py results/raw/<run>      # needs pandas, tabulate, matplotlib
python3 scripts/make_report.py <run>              # docs/RESULTS.md + paper/generated.tex
bash tools/embedded/run.sh           # optional: needs arm-none-eabi-g++ and qemu-system-arm
```

Details and expected variation: `docs/REPRODUCIBILITY.md`.

## Authors and how this was produced

Shubhi Singh and Adhyan Jain (VIT Vellore). This repository was produced by an AI coding
assistant working in Shubhi Singh's environment; Adhyan Jain has not yet reviewed it. See
`docs/CONTRIBUTIONS.md` before citing or submitting anything.

## Licence

MIT (`LICENSE`). The compiler traces are lists of identifiers produced by compiling the
projects named in `workloads/traces/MANIFEST.tsv`; those projects keep their own licences.
