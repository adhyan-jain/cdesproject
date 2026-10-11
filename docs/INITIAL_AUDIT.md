# Initial Audit of the Existing Work

Audited on 11 October 2026 before any new code was written.

## 1. What was inspected

| Item | Where | State |
|---|---|---|
| Authenticated account | `gh auth status` | `shubhisingh1510` |
| METIS repository | https://github.com/adhyan-jain/Metis | public, no `LICENSE` file (the README shows an MIT badge that links to a missing file), 0 issues, 0 pull requests |
| Branch `main` | commit `7b3dacf` (10 Oct 2026) "Archive Phase 1-9 METIS research artifacts and project closure" | audited |
| Branch `research/metis-x` | commit `0b43440` | an ancestor of `main`; nothing extra |
| Branch `research/zephyr-symbol-compression` | commit `9d9db2b` | one commit ahead of `main` (a separate Zephyr runtime-symbol study; not part of METIS-X) |
| Tags | `phase1-final`, `metis-x-final` | noted |
| History | 87 commits, 1 Sep - 10 Oct 2026 | 77 by `adhyan-jain`, 10 by `shubhisingh1510` |
| Second author's repositories | `gh repo list shubhisingh1510` (14 repositories) | **none contains symbol-table work**. Her contributions to this topic are the 10 commits inside `adhyan-jain/Metis` (BUDGET-SYM prototype, Robin Hood/trie comparison, LRU lookup-cache fix, dashboard). There is no separate repository to audit. |

Read in full: `include/metis_x.hpp`, the three baselines in `include/historical/`, the
benchmark drivers in `src/`, `scripts/extract_corpus_events.py`, the tests in `tests/`, the
result CSVs in `results/`, the research notes in `research/l3/` (phases 1-9, closure note),
`paper/Metis.tex`, and the patent-disclosure package in `docs/patent/`.

Two things outside the code matter for this project:

* **Licence.** With no licence file, the METIS code cannot be copied into another repository.
  This project does not vendor it; `scripts/fetch_third_party.sh` fetches the audited commit
  at benchmark time.
* **Patent advisory.** `docs/METIS_X_FINAL_VALIDATION_REPORT.md` section 9 warns against
  publishing before a provisional patent filing. The METIS repository is nevertheless public.
  See `ARCHITECTURE_DECISION.md` for how this affected the visibility of the new repository.

## 2. Defects and limitations, each checked against the current code

Severity: **C** correctness, **M** memory, **L** latency, **V** research validity.

### D1. Declarations are refused once one name is shadowed about 250 deep (C) - reproduced

* **Where:** `include/metis_x.hpp`, `kMaxProbeDist = 250` (line 58), `dryRunCanInsert` (336-354), `insert` (239-245).
* **Problem:** all declarations of one name have the same hash, so they form one Robin Hood cluster. The 8-bit probe distance is capped at 250; the next insert returns -1.
* **Effect:** a legal program with deep shadowing loses declarations, and later lookups return the wrong (outer) declaration.
* **Evidence:** synthetic trace `deep_shadow_400` (one identifier declared in 400 nested scopes): METIS-X refused 149 of 400 declarations and returned 298 wrong lookup results; every other table, including the old baselines, had none. See `docs/RESULTS.md`, section C.
* **Fix in the new design:** a name is stored once; shadowing pushes a 12-byte undo entry. Depth is limited only by memory and a documented 16 383 scope limit.
* **Verified by:** `tests/test_strata.cpp::test_deep_shadowing` (5 000 nested declarations of one name).

### D2. Lookup cost grows with shadowing depth (L) - confirmed

* **Where:** `resolve` (252-278): the loop does not stop at the first match; it compares every entry with the same name and keeps the deepest scope.
* **Effect:** O(s) name comparisons for a name with s live declarations.
* **Evidence:** on the `shadow_heavy` trace METIS-X's lookup p95 and p99 are several times those of the tables that keep one entry per name (`docs/RESULTS.md`, section C).
* **Fix:** the identifier record holds the innermost declaration; a lookup never looks at shadowed ones.

### D3. Rehash is not exception-safe and leaks (C, M) - confirmed by reading

* **Where:** `rehash` (455-466): `old.swap(slots_); slots_.resize(newCap);`.
* **Problem:** if `resize` throws, `slots_` is empty while `capacity_` still holds the old value, so the next probe indexes an empty vector (undefined behaviour); heap name pointers held in `old` are never freed because `MetisXSlot` has no destructor. Also `insertSlotInternal` (358-359) pushes onto the scope frame after the heap copy of the name was made; if that `push_back` throws, the name leaks.
* **Evidence:** code inspection only. It was not triggered experimentally, because the header cannot be given a failing allocator without modifying it.
* **Fix:** the new table never throws. Growth uses `realloc`; a failed allocation returns `kNoMemory` with the table untouched.
* **Verified by:** `test_allocation_failure` (allocator that fails after 1..10 calls; contents compared with the reference model; no leaked block).

### D4. Every name longer than 12 bytes costs a heap allocation (M, L) - confirmed

* **Where:** `MetisXSlot::setName` (91-107), `new char[len]`.
* **Evidence:** on the compiler traces METIS-X makes tens of thousands of allocator calls per trace, the new table a few hundred at most (`docs/RESULTS.md`, allocator-call table).
* **Related false statement:** the header comment (line 17) says a 12-byte buffer "covers 93.4% of Zephyr names verbatim". Measured from the repository's own Zephyr trace, 49.7% of declarations and 22.7% of distinct names are at most 12 bytes.
* **Fix:** names live in the table's own buffer, packed five characters per 32-bit word.

### D5. The slot array never shrinks (M) - confirmed

* **Where:** `exitScope` (165-191) clears slots; nothing reduces `slots_`. `rehash` is only called to grow.
* **Effect:** after a large scope closes, the footprint stays at the high-water mark (the METIS-X manuscript measured 89% of the final Zephyr footprint as empty slots).
* **Fix:** growable mode halves the buffer when less than a quarter is in use; fixed mode never needed it.
* **Verified by:** `test_reclamation`.

### D6. Scope exit shifts clusters (L) - confirmed, modest in practice

* **Where:** `backwardShift` (417-431), called once per removed entry.
* **Effect:** O(k x cluster length) per scope exit.
* **Evidence:** measured exit latency in `docs/RESULTS.md`. On these workloads the cost is similar to the new table's, so this is a worst-case concern more than an average-case one.
* **Fix:** names first seen in the closing scope are the newest index entries; their slots are simply emptied. Nothing is shifted.

### D7. One heap vector per scope, contrary to the header comment (M) - confirmed

* **Where:** `scopeFrames_` is a `std::vector<std::vector<uint32_t>>` (line 491); the comment at line 24 says "no vector-of-vectors scope index".
* **Effect:** each scope that declares something allocates and later frees a vector.
* **Fix:** a scope mark is two words on the undo stack.

### D8. Silent `continue` in scope exit can hide corruption (C) - noted

* **Where:** `exitScope` lines 177-179 skip a frame entry whose slot is out of range, empty, or belongs to another scope.
* **Effect:** an inconsistency would be skipped without adjusting `liveCount_` instead of being detected. No such inconsistency was observed in our runs.
* **Fix:** the new table has `check_invariants()`, which the tests call throughout.

### D9. Alignment claim (V) - confirmed

* **Where:** comment "Cache-Conscious"; `MetisXSlot` is 32 bytes with `alignof` 4 and no `alignas`.
* **Effect:** a slot can straddle two cache lines; no hardware counters were ever collected. The claim is unsupported. (The new project makes no cache claim either.)

### D10. Traces come from regular expressions, not a compiler (V) - confirmed

* **Where:** `scripts/extract_corpus_events.py` (`TOKEN_RE`, `strip_comments_and_strings`, type-token heuristics).
* **Effect:** no preprocessing, no parsing; scope entries and exits are not even balanced.
* **Fix:** this project instruments Tiny C Compiler itself and records its real symbol-table calls while it compiles eight pinned projects (`tools/tcc-trace/`).

### D11. Heap figures of the main benchmark include harness data (V) - confirmed

* **Where:** `src/metis_x_bench_main.cpp` lines 170-180: a `std::unordered_set<std::string>` of all names is built inside the `heap::Scope` measurement window.
* **Effect:** about 20 MB (Zephyr) and 21 MB (ESP-IDF) are added to every table's reported heap.
* **Fix:** the new harness opens its accounting window after the trace is loaded and allocates nothing else inside it.

### D12. Per-call timing with a clock as expensive as the operation (V) - confirmed

* **Where:** `src/metis_x_bench_main.cpp` lines 216-226, `timer.now()` around every call.
* **Effect:** latency reductions varied from 19% to 59% between the repository's own result files.
* **Fix:** the primary time metric is now the whole-trace replay time (one timer per replay, 15 repetitions, bootstrap interval). Per-call latency is kept as a secondary metric, taken with the TSC and with the measured timer cost subtracted.

### D13. Weak and home-made baselines (V) - confirmed

* **Where:** `include/historical/embedded_conventional_symbol_table.hpp`: `insert` (79-...) calls `findInScope`, a linear scan over the scope's entries, and appends names to `arena_`, which `exitScope` (51-77) never truncates.
* **Effect:** the main baseline of the earlier paper wastes memory and time by construction.
* **Fix:** this project adds a map-per-scope stack, the undo-log algorithm of LLVM's `ScopedHashTable` over `std::unordered_map` and over a Swiss-table node map, and an interning Swiss flat map; the old tables are kept as additional baselines, unmodified.

### D14. The "ablation" is not an ablation (V) - confirmed

* **Where:** `src/metis_x_ablation_main.cpp`: `TableA1` and `TableA2` have empty `enterScope`/`exitScope`.
* **Effect:** two of the levels never delete anything, so the published "89% reduction" does not isolate inline storage.
* **Fix:** the new ablations change exactly one option of the same class (`pack_names`, `shrink`).

### D15. No integration and no use case (V) - confirmed, and only partly addressed here

* **Where:** `research/l3/phase8`, `project_closure.md`.
* **Finding:** Tiny C Compiler interns identifiers to integer tokens and resolves scopes through per-token pointers; a string-keyed scoped table has no place in that path.
* **What this project does about it:** it changes the question. The new table is itself an interner plus a scope mechanism, i.e. it covers the job that TCC's `table_ident` hash, `TokenSym` records and `Sym` stacks do together, and it is evaluated on the events that TCC really generates. It is still **not** integrated into TCC, and no end-to-end compile time is reported. See `LIMITATIONS.md`.

## 3. Things the earlier work did well and that were kept

* Differential testing against other tables: extended to a separate reference model and randomised sequences.
* Measuring heap with `malloc_usable_size` through an allocator hook.
* Recording negative results. The undo-log alternative that METIS phase 2 rejected for a Robin Hood table is, in a different form (undo entries that save shadowed declarations), the basis of the new design; `DESIGN_SPACE.md` explains why the earlier rejection does not transfer.
* The observation in `research/l3/phase2` that deleting a scope's entries in reverse order restores the previous table layout. The new table relies on the same stack discipline, with linear probing instead of Robin Hood.
