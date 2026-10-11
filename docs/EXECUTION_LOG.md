# Execution Log

One working session, 11 October 2026. Times are omitted; the order is exact.

| # | Step | Outcome |
|---|---|---|
| 1 | `gh auth status`, repository listing, commit search | Account `shubhisingh1510`. The symbol-table work of both authors is in `adhyan-jain/Metis`; no separate repository of the second author exists. |
| 2 | Fetched all branches and tags of METIS | `main` at `7b3dacf`; two research branches; no licence file; a patent advisory in the docs. |
| 3 | Read `metis_x.hpp`, baselines, drivers, extractor, notes | 15 audit items (`INITIAL_AUDIT.md`). |
| 4 | Profiled the old trace files | Names up to 137 bytes; C++ corpora contain `::`. Set the name limit to 255 bytes with a raw fallback. |
| 5 | Decision: rebuild (`ARCHITECTURE_DECISION.md`) | Identifier-keyed table in one buffer. |
| 6 | Instrumented Tiny C Compiler (`tools/tcc-trace/`) | First patch attempt failed to apply one edit (script error); fixed. Hooks in `sym_find`, `sym_link`, `global_identifier_push`, every scope change, `gen_function`. |
| 7 | Traced 8 projects | First attempt: FreeRTOS failed (config defined two tick-width macros) and TinyCC failed (generated header missing). Both fixed. Mbed TLS: 3 of 108 files do not compile with TCC and are skipped. |
| 8 | STRATA version 1: identifier records + 12-byte binding records | Tests written. A C-string overload made `declare("", 0, 1)` ambiguous: renamed to `declare_cstr`/`resolve_cstr`. Three test expectations were wrong (not the code) and were corrected. 953 842 checks pass, also under ASan + UBSan. |
| 9 | Harness and baselines; first trial on Lua | All tables agree with the reference model. STRATA's peak heap was barely below METIS-X: growth by doubling with a fresh allocation held two copies. |
| 10 | Growth changed to 1.5x through `realloc` | Peak heap fell. Accounting charges a moving `realloc` for both blocks. |
| 11 | Fixed-buffer tool: first run reported "does not fit in 64 MiB" | Bug: a 64 MiB buffer exceeded the 24-bit word limit and the table marked itself invalid. Now clamps. |
| 12 | Trial numbers: about 60% below METIS-X in memory, not 85% | Redesigned the records: innermost declaration inside the identifier record, hidden declarations on an undo stack (4 bytes per ordinary declaration instead of 12); index starts at 16 slots. `sqlite3.c` minimum buffer 177 728 -> 143 744 bytes. |
| 13 | Tests updated for the new layout | One test assumed that refused declarations form a suffix; wrong, corrected. 977 685 checks pass. |
| 14 | First full run `20261011-160113-full` (commit `8169bf5`) | Kept. 80/80 compiler pairs correct. METIS-X refuses 149 declarations on `deep_shadow_400`. STRATA slower than METIS-X on `lookup_heavy` and `big_scope_exit`. |
| 15 | Diagnosis of `lookup_heavy` | Tried triangular probing and a maximum index load of 1/2 in a scratch build. Triangular probing: no consistent gain, dropped. Load 1/2: faster on four traces, costs index memory. Repeating the same binary showed 20-40% run-to-run movement on this trace, so part of the first result was noise. |
| 16 | Added `sparse_index` as an option (default off) and a fourth STRATA variant in the benchmarks | 1 177 892 checks pass. |
| 17 | Second full run (`-final`, commit `3aee381`) | The run reported in `RESULTS.md`. |
| 18 | Related-work search | The undo-stack scheme is in Appel's textbook and LLVM; 6-bit packing has the RADIX-50 precedent; one intended citation (Cook and LeBlanc 1983) could not be confirmed and was dropped. Novelty self-assessment 4.5/10, not the 8/10 goal. |
| 19 | Documents and paper draft | `docs/RESULTS.md` and `paper/generated.tex` are generated from the CSVs by `scripts/make_report.py`. Paper: 4 pages, compiles with pdflatex + bibtex. |
| 20 | Clean-checkout check | Cloned the repository into an empty directory, ran `scripts/test.sh` (1 177 892 checks, 0 failed, both builds), `scripts/fetch_third_party.sh` and `REPS=2 scripts/run_all.sh`. The pipeline completed; correctness results were identical to the reported run (88/88 compiler pairs, 42/42 legacy pairs, and METIS-X on `deep_shadow_400` the only failing synthetic pair). That short run is not stored. |
| 21 | Repository created (private) and pushed; `adhyan-jain` invited with write access | Invitation pending at the time of writing. |
| 22 | Version 2 of the table | Slot recorded in the undo entry (scope exit without re-hashing), shrinking delayed by 64 calm scope exits, hash computed in the packing loop. Run `20261011-163944-v2` kept. |
| 23 | External review received (six points) | Addressed in steps 24-28; summary in `RESULTS.md`, section 2. |
| 24 | Conventional allocator-free baseline `arena_chain` | Agrees with the reference model on every trace. It turned out to be faster than STRATA on ordinary C traces and only 16-18% larger: most of the gain over METIS-X is not specific to STRATA. Reported as such. |
| 25 | Timing protocol changed | 31 rounds, tables interleaved in rotating order, paired differences with bootstrap intervals. |
| 26 | Guarantee tests and written argument | `state_digest()`; all-or-nothing checked in 30 configurations including adversarial collisions; `docs/CORRECTNESS.md`. 1 856 579 checks pass. |
| 27 | Emulated embedded target | First attempt to install the cross toolchain raced with another package installation and had to be repeated. Bare-metal Cortex-M3 under QEMU, 64 KiB RAM: five traces pass with host-identical results. |
| 28 | Final run `20261011-165103-v3` | Reported in `RESULTS.md` and the paper; the paper's claim was narrowed to the decomposition. |

## Things tried and not kept

* Separate binding records with a shadow chain (step 8): replaced in step 12.
* Initial index sized as a fraction of the buffer: replaced in step 12.
* Doubling growth with copy: replaced in step 10.
* Triangular probing: measured in step 15, no benefit.

## Decisions taken without asking

* Repository created **private** although the brief prefers public, because of the patent
  advisory and missing licence in METIS (`ARCHITECTURE_DECISION.md`).
* METIS code is fetched, never copied.
* Licence of this repository: MIT, copyright in both authors' names; to be confirmed by them.
* The 85% target was treated as a hypothesis and is reported as met or not met per metric.
