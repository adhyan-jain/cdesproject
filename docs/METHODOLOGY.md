# Methodology

## 1. Hypotheses

* **H1 (memory).** On compiler-generated traces STRATA holds less memory at its peak than
  METIS-X and than each conventional baseline.
* **H2 (time).** STRATA's whole-trace replay time is not higher than METIS-X's.
* **H3 (fixed memory).** STRATA replays each trace from one caller-supplied buffer without
  calling an allocator, and the required buffer size can be stated per project.

Each can fail: H1 and H2 per trace and per baseline, H3 by a refused operation.
The brief's engineering target of an 85% reduction is tested as stated, with the formula
`(baseline - new) / baseline x 100`, per metric and per baseline.

## 2. Tables compared

| Id | What it is | Source |
|---|---|---|
| `strata` | this project, default options | `include/strata/strata.hpp` |
| `strata_raw` | ablation: names stored as raw bytes | same, `pack_names = false` |
| `strata_noshrink` | ablation: buffer never given back | same, `shrink = false` |
| `metis_x` | previous implementation, unmodified | METIS `include/metis_x.hpp` @ `7b3dacf` |
| `metis_arena_lp` | previous arena baseline, unmodified | METIS `include/historical/embedded_conventional_symbol_table.hpp` |
| `metis_scope_maps` | previous map-per-scope baseline, unmodified | METIS `include/historical/conventional_symbol_table.hpp` |
| `scope_map_stack` | `std::unordered_map` per open scope | `benchmarks/baselines/tables.hpp` |
| `std_undo_log` | `std::unordered_map` name -> innermost binding, undo log (LLVM `ScopedHashTable` algorithm); names erased when their last binding dies | same |
| `swiss_undo_log` | the same on `phmap::node_hash_map` (Swiss-table port) | same; parallel-hashmap v1.4.1 |
| `swiss_interned` | `phmap::flat_hash_map` name -> id (never erased within a unit), dense heads, undo log | same |

All tables implement the same four operations with the same semantics:
innermost declaration wins; a declaration of a name already declared in the current scope
replaces it; leaving the outermost scope is a no-op. Names are passed as existing
`std::string` objects, so no table pays for constructing a string. The baselines written
for this project were written to be good, not weak: `std_undo_log` and `swiss_undo_log`
reclaim names, `swiss_interned` is the fastest design we know for this interface.

## 3. Workloads

### A. Compiler traces (primary)

`tools/tcc-trace/apply_patch.py` adds logging to Tiny C Compiler (commit `43c7708`) at the
points where it really touches its symbol tables:

| Event | TCC site |
|---|---|
| `L name` lookup | `sym_find` |
| `D name` declaration | `sym_link` (ordinary identifiers) and file-scope `global_identifier_push` |
| `E` / `X` scope | every `++local_scope` / `--local_scope` (blocks, statement scopes, prototype parameter scopes) and the parameter scope of `gen_function` |
| `U` unit | start of `tccgen_compile` |

The patched compiler then compiles eight projects (`tools/tcc-trace/make_traces.sh`,
versions in `workloads/traces/MANIFEST.tsv`): cJSON 1.7.18, littlefs 2.9.3, zlib 1.3.1,
Lua 5.4.7, FreeRTOS-Kernel 11.1.0 (POSIX port, our minimal config), Mbed TLS 3.6.2
(3 of 108 files do not compile with TCC and are skipped), TinyCC itself, SQLite 3.46.0
amalgamation. A translation unit is one compilation; the table is destroyed and rebuilt at
each `U`.

What these traces are: the exact sequence of symbol-table calls a real C compiler made,
including system headers and the compiler's built-in declarations. What they are not: struct
tags, members, labels and macros (TCC keeps those elsewhere); events of other compilers; and
"G" events (a file-scope identifier pushed from inside a local scope, e.g. an implicit
function declaration), which are logged but ignored by the replay.

### B. Synthetic stress traces

`scripts/gen_synthetic.py`, fixed seeds: short names (1-3 bytes), long names (40-80),
nesting to depth 200, heavy shadowing of 24 names, lookup-heavy, 50 000 live names, scope
churn, a 10 000-declaration scope entered 20 times, and one name declared in 400 nested
scopes.

### C. Regex-extracted traces (supplemental)

The four traces used in the METIS-X manuscript (FreeRTOS, Arduino, Zephyr, ESP-IDF), read
from the METIS repository. They come from a lexical heuristic and are reported separately.
The old arena table is omitted on the two large ones because one replay takes minutes.

## 4. Measurements

Each (trace, table) pair gets four passes (`benchmarks/bench_main.cpp`):

1. **Check.** Every lookup result and every declaration status is compared with
   `tests/reference_model.hpp` (a `std::map` of vectors that shares no code with any table).
2. **Memory.** The trace is replayed inside a heap-accounting window opened after the trace
   is loaded. All `operator new` calls and STRATA's allocator calls go through a counter that
   uses `malloc_usable_size`. Reported: peak bytes, final bytes, allocator calls.
   A `realloc` that returns a different address is charged as if old and new block coexisted.
3. **Replay time (primary time metric).** 2 warm-up + 15 measured replays of the whole
   trace, one `steady_clock` interval per replay, including table construction and
   destruction at unit boundaries. Reported: median, min, max, and a 95% percentile-bootstrap
   interval of the median (2 000 resamples).
4. **Per-operation latency (secondary).** Three replays with a TSC read (`rdtscp`) before and
   after every operation; the median cost of an empty interval is measured at start-up and
   subtracted; p50/p95/p99 and mean per operation kind; the median of the three replays is
   kept. These numbers are near the timer's resolution and are used to compare tables, not
   as absolute costs.

Fixed-buffer experiment (`benchmarks/budget_main.cpp`): bisection to 64 bytes for the
smallest buffer with which the whole trace replays without a refused operation, for packed
and raw names; then 9 timed replays at 1x, 1.25x, 2x and 4x that size.

Worst case: every key forced into one probe cluster (test hook), sizes 16 to 4 096.

## 5. Derived quantities

* `bytes per live declaration` = peak heap / largest number of simultaneously live declarations in a unit.
* `ns per operation` = median replay time / number of trace operations.
* `reduction %` = (baseline - new) / baseline x 100. Negative = worse.

## 6. Environment

Written to `results/raw/<run>/environment.txt` by `scripts/run_all.sh`: compiler and flags
(`g++ -std=c++14 -O2`), kernel, CPU model, libc, pinning (`taskset -c 2`), repetitions,
commits of this repository and of the two fetched baselines.

## 7. Correctness tests

`tests/test_strata.cpp`, built at `-O2` and with `-fsanitize=address,undefined`:
scoping and shadowing, redeclaration policy, name rules (empty, 255, 256 bytes, embedded NUL,
non-identifier bytes), record layout, all keys in one cluster, invalid scope operations and
the depth limit, six randomised runs of 100 000-300 000 operations against the reference
model with invariants checked along the way, reclamation and shrinking, fixed-buffer
exhaustion, an allocator that fails after *k* calls for k = 1..10, a growable budget, and
5 000-deep shadowing.

## 8. What the methodology cannot show

See `LIMITATIONS.md`. In short: replay is not compilation; one machine; hosted x86-64, not a
microcontroller.
