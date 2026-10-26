# Evidence behind the paper's claims

> **Removed sources.** Citations in this file to `docs/EXECUTION_LOG.md`, `docs/ADDENDUM_2026-10-17.md`, `docs/RELATED_WORK.md`, `reports/TEST_RESULTS.md`, `submission/REPRODUCE.md`, `theory/PROOF_AUDIT.md`, `SUBMISSION_READINESS.md` and similar process documents refer to files deleted in the repository cleanup. They are kept in the git tag `pre-cleanup` (`git show pre-cleanup:<path>`).

One document for the supporting facts that the article summarizes: how the traces are defined, the embedded and compiler experiments, the flooding experiments, the bit-level encodings, the exhaustive harness and the tests added after the reviewer report. Everything was read from the files and logs it names; "not recorded" means the repository does not say. The command-to-table map is in `REVIEW_MANIFEST.md`.


## 1. Compiler traces: schema, semantics, pinned sources

Everything below was read from the files named in it. "Not recorded" means that the repository
does not say. Commit of this document: `c5d8eb8ae9f313001181b73ef76c54f2376714c8` (branch
`reviewer-report-revision`; the working tree was not clean when this was written, see
`docs/REVIEW_MANIFEST.md`). The traces themselves were last changed in commit `2d8672b`
(2026-10-11) and have not changed since.

### 1. Trace file format

Files: `workloads/traces/<project>.trace.gz` (TinyCC, eight projects) and
`workloads/traces/chibicc_<project>.trace.gz` (chibicc, seven projects), plus `MANIFEST.tsv` and
`ENVIRONMENT.txt`. Plain text, one event per line, a tag and an optional single argument:

| Line | Meaning | Replayed as |
|---|---|---|
| `U` | a translation unit (one compiler process invocation in TinyCC, one compiler process in chibicc) starts | the table is destroyed and a new one created (`benchmarks/common.hpp: OP_UNIT`). The very first `U` is dropped ("the first unit needs no reset") |
| `E` | a lexical scope is entered | `enter_scope()` |
| `X` | a lexical scope is left | `exit_scope()` |
| `D name` | an ordinary identifier is entered in the compiler's symbol table | `declare(name, seq++)` |
| `L name` | the compiler looks an identifier up | `resolve(name)` |
| `G name` | (TinyCC only) a file-scope identifier pushed while a local scope is open, e.g. an implicit function declaration | **ignored** by every replay tool |

Loader: `benchmarks/common.hpp: load_trace()` (used by `bench`, `budget` and `hardening`); the
embedded images use `tools/embedded/gen_trace_header.py`. The loader also accepts the older
`ENTER_SCOPE/EXIT_SCOPE/DECLARE/USE` format of the predecessor repository; none of the stored
traces uses it.

Rules the loader applies (these decide what the paper's "Events" column counts):

* An unknown tag (this is where `G` goes) is counted in `Trace::ignored` and skipped.
* For `D`/`L`, anything after the first space of the argument is cut off; an **empty** name or a name
  longer than 255 bytes is counted as ignored and skipped. Only the chibicc traces contain empty
  names (see section 3).
* The paper's "Events" column (`tables/tab_workloads.tex`) is the number of replayed operations:
  the number of lines of the file minus the first `U`, minus `G` lines, minus skipped lines.
  Example: cJSON has 20 875 lines (`MANIFEST.tsv`) and 20 874 events.
* `gen_trace_header.py` (embedded) skips `G` but does **not** skip empty names (it would fail
  with an index error on one). It is only ever run on the eight TinyCC traces, which contain none.

`MANIFEST.tsv` columns: `project, version, source, units_ok, units_failed, events` where `events`
is the **line count** of the trace (so it includes `U` and `G`; it is larger than the paper's
Events column by one (the dropped first `U`) plus the number of `G` lines). Per-trace line
statistics computed by `tools/review/trace_stats.py` are in `docs/trace_stats.txt`.

### 2. How TinyCC events map to the one-namespace API

The API (`include/strata/strata.hpp`) has exactly one namespace: names of 1 to 255 bytes, a stack of
scopes, `declare` (new name -> `kOk`; the same name already declared **in the current scope** ->
`kRedeclared`, value and type replaced in place), `resolve` (innermost declaration wins),
`enter_scope`, `exit_scope`. This is the ordinary-identifier namespace of C (variables, functions,
typedef names, enumeration constants). The trace logs only that namespace.

`tools/tcc-trace/apply_patch.py` patches `tccgen.c` of TinyCC `43c7708b85681a2fd4451c8a541af4494a8919b2`
(every replacement must match exactly once or the script stops). The hooks, by the code each one
is attached to:

| Hook (anchor text in `tccgen.c`) | Event | Notes |
|---|---|---|
| `tccgen_compile` start / `tccgen_finish` start | `U` / closes the trace file | writes `X` for any scope still open when the file closes (unbalanced exits are impossible in the stored traces: `E` and `X` counts are equal in every file) |
| `sym_find` (the lookup of `table_ident[v]->sym_identifier`) | `L name` | one `L` per call, including calls for names that resolve to nothing |
| `sym_link` when `yes` and `!(s->v & SYM_STRUCT)` | `D name` | `SYM_STRUCT` symbols are struct/union/enum **tags**: excluded |
| `global_identifier_push` | `D name` when no logged scope is open, else `G name` | pushes at file scope while inside a function (implicit declarations) |
| the two block-scope open/close pairs (`++local_scope` / `--local_scope`, one pair for each of the two scope functions) | `E` / `X` | |
| the function-prototype parameter scope in the declarator code | `E` / `X` | every function declarator, with or without a body, opens one |
| `gen_function` ("push parameters" ... `sym_pop(&local_stack...)`) | `E` / `X` | parameters of a definition live in a scope that ends with the function |

What is **not** logged (stated in the docstring of `apply_patch.py`): struct/union/enum tags (a separate
namespace in C and in TinyCC: `sym_struct`), struct members (`SYM_FIELD`), labels (`label_stack`),
macros (preprocessor table). The library therefore models exactly one of C's namespaces; the other
namespaces are not modelled and are not claimed to be. No trace event distinguishes a typedef from a
variable or enumerator: all three are `D`.

Consequences, measured on the stored traces with `tools/review/trace_stats.py`
(`docs/trace_stats.txt`):

* **Same-scope replacement never occurs in the TinyCC traces.** The number of `D` events that name an
  identifier already declared in the same scope is 0 in all eight. Why (TinyCC rejecting or
  reusing a redeclared symbol before it reaches the hooked function) was not checked: the repository
  does not contain TinyCC's source. The `kRedeclared` path is exercised by the unit tests,
  the exhaustive enumeration, the fuzzer and by the chibicc traces (section 3), not by the TinyCC
  traces. The paper's correctness statement for the TinyCC traces (no wrong declaration result)
  is therefore a statement about new declarations only.
* A fraction of lookups is never satisfied: from 12.5 percent of the `L` events (SQLite: 21 578 of
  172 426) to 34 percent (cJSON: 3 099 of 9 194; zlib: 8 648 of 27 405 = 31.6 percent) resolve to nothing
  (the embedded log gives the same hit counts: zlib 18 757 hits of 27 405). Why TinyCC calls `sym_find` for identifiers that are not declared in
  the ordinary namespace is not recorded in the repository; the replay simply has them miss.
* Compiler-generated and built-in names appear as ordinary names: `__builtin_va_list`, `__va_arg`,
  `__builtin_memcpy`, and every other name TinyCC declares itself at the start of each unit (the first
  lines of `tinycc.trace.gz` are `L __builtin_va_list`, `D __builtin_va_list`, ...). Between 5.7 percent
  (SQLite) and 53 percent (cJSON) of the `D` events of the TinyCC traces start with `__` (the glibc
  headers are included; `docs/trace_stats.txt`, column `__names`). TinyCC's anonymous symbols (numbers above `SYM_FIRST_ANOM`, e.g. anonymous structs,
  string literals) have no name and are not logged.
* `G` events: freertos 1, littlefs 1, sqlite 4, tinycc 3, zlib 5, others 0; all ignored by the replay.
  A later `L` of such a name therefore misses in the replay although TinyCC found it.
* Headers are part of the trace: the compiler reads the C library headers, so events from `<stdio.h>`
  and friends are counted (no filtering by file). The headers were those of Ubuntu 22.04, glibc
  `2.35-0ubuntu3.15` (`workloads/traces/ENVIRONMENT.txt`); other headers change the counts
  (`docs/REPRODUCIBILITY.md`). The include path of TinyCC itself (its `include/` directory) is not
  recorded.
* A translation unit that TinyCC cannot compile is skipped and its partial trace discarded
  (`make_traces.sh`). The skipped files are printed to the console only and **are not recorded**;
  the counts are in `MANIFEST.tsv` (Mbed TLS: 105 compiled, 3 skipped, all others 0 skipped;
  `docs/EXECUTION_LOG.md` row 7 says "3 of 108").

### 3. How chibicc events map

`tools/chibicc/apply_patch.py` patches `parse.c` of chibicc commit
`90d1f7f199cc55b13c7fdb5839d1409806633fdb` (rui314/chibicc, MIT). Same file format. chibicc
resolves identifiers by string, with one hash map per open scope; the patch hooks its four scope
functions:

| chibicc function | Event |
|---|---|
| first call of the logger (once per compiler process) | `U` |
| `enter_scope` / `leave_scope` | `E` / `X` |
| `push_scope(name)` | `D name` |
| `find_var(tok)` | `L <token text>` |
| `find_func` (looks in the outermost scope only) | not logged (it only matters for the integration, below) |

Because chibicc keeps typedef names, enumeration constants, variables and functions in the same
`VarScope` map, they are all `D`, as for TinyCC. chibicc's tags (`push_tag_scope`, `find_tag`), goto
labels, macros and keywords use other structures and are not logged. Differences from TinyCC that
matter:

* chibicc is run **once per translation unit** (one process = one `U`); `evaluate.py` concatenates
  the traces of the units that the unmodified compiler accepts.
* Compiler-generated names are logged: `__func__`, `__FUNCTION__` and the unique labels `.L..N` that
  chibicc invents for string literals and compound literals (419 `D .L..N` lines in the cJSON
  trace). They are ordinary `D` events.
* **Empty names.** chibicc declares unnamed entities (for example unnamed parameters) under the empty
  string; the trace contains `D ` with no argument (136 in cJSON, 3 613 in SQLite; 9 324 in all seven
  traces). The replay tools skip them (empty names are not valid for the API), so the chibicc
  replays declare fewer names than the trace has `D` lines (cJSON: 3 496 declares against 3 632 `D`
  lines, which matches `results/hardening/traces.csv`). In the chibicc **integration** (section 6)
  they are not skipped: the empty name is stored as the single byte `0x01`.
* **Same-scope replacement does occur**: 2 (cJSON), 5 (FreeRTOS), 1 (littlefs), 4 (Lua), 122
  (Mbed TLS), 3 (SQLite), 13 (zlib) `D` events name an identifier already declared in the same
  scope (`docs/trace_stats.txt`).
* `G` events do not exist in chibicc traces.
* Trace file sizes and units (`units_ok`): chibicc accepts 158 of 170 units (`results/chibicc/units.csv`);
  failures: littlefs `lfs.c`; zlib `gzlib.c gzread.c gzwrite.c`; FreeRTOS `tasks.c`; Mbed TLS `aes.c
  aesni.c debug.c gcm.c psa_crypto_slot_management.c ssl_tls.c ssl_tls12_server.c`. Its FreeRTOS set
  has 8 files (no POSIX `port.c`), TinyCC's has 9.

### 4. Pinned sources

Sources are fetched by `tools/tcc-trace/make_traces.sh` (clone with `--depth 1 --branch <tag>`, or
download of an archive). They are pinned by **tag or URL, not by commit hash, and no archive checksum
is checked**; the commit hashes that the tags pointed to are **not recorded**.

| Project | Version | Source | Build flags passed to the compiler | Units (TinyCC) |
|---|---|---|---|---|
| cJSON | v1.7.18 | git `DaveGamble/cJSON` | none | `cJSON.c`, `cJSON_Utils.c` (2) |
| littlefs | v2.9.3 | git `littlefs-project/littlefs` | none | `lfs.c`, `lfs_util.c` (2) |
| zlib | v1.3.1 | git `madler/zlib` | `-I<zlib>` | all `*.c` in the root (15) |
| Lua | 5.4.7 | `https://www.lua.org/ftp/lua-5.4.7.tar.gz` | `-DLUA_USE_POSIX` | all `src/*.c` (34) |
| FreeRTOS-Kernel | V11.1.0 | git `FreeRTOS/FreeRTOS-Kernel` | `-I include -I portable/ThirdParty/GCC/Posix -I .../Posix/utils -I tools/tcc-trace/freertos-config` | `tasks queue list timers event_groups stream_buffer croutine`, `portable/MemMang/heap_4.c`, POSIX `port.c` (9) |
| Mbed TLS | v3.6.2 | git `Mbed-TLS/mbedtls` | `-I include -I library`, default configuration | all `library/*.c` (105 compiled, 3 skipped) |
| TinyCC | `43c7708` | git `repo.or.cz/tinycc` (GitHub mirror as fallback) | `-I<tinycc>`; generated `tccdefs_.h` | `tcc.c` (1) |
| SQLite | 3.46.0 | `https://www.sqlite.org/2024/sqlite-amalgamation-3460000.zip` | none | `sqlite3.c` (1) |

* FreeRTOS uses `tools/tcc-trace/freertos-config/FreeRTOSConfig.h`, "a minimal configuration written
  for cdesproject ... not taken from any FreeRTOS demo". The first attempt failed because a config
  defined two tick-width macros (`docs/EXECUTION_LOG.md` row 7).
* TinyCC itself is compiled with the patched TinyCC (self-hosting trace): `tcc version 0.9.28rc
  2026-10-03 HEAD@43c7708b*` (`workloads/traces/ENVIRONMENT.txt`; the `*` marks the patched tree).
* Headers: the host's C library headers, Ubuntu 22.04 / glibc 2.35-0ubuntu3.15; the trace date is
  2026-10-11T15:42:12Z. No other header set (musl, newlib, an embedded libc) was traced.
* chibicc traces: chibicc `90d1f7f` with its own `include/` copied next to the binary (`build.sh`),
  same project versions and flags (`tools/chibicc/evaluate.py: PROJECTS`), sources from `~/cdes/src`
  (the working directory of `make_traces.sh`), `-S` mode.
* Regeneration commands: `bash tools/tcc-trace/build_tcc.sh ~/cdes` then
  `bash tools/tcc-trace/make_traces.sh ~/cdes <outdir>`; `bash tools/chibicc/build.sh` then
  `python3 tools/chibicc/evaluate.py`. Runtime of the TinyCC steps is not recorded;
  `evaluate.py` takes about 12 minutes (`submission/REPRODUCE.md`).

### 5. Checksums of every trace file used by the paper

`bash tools/review/trace_checksums.sh` writes
`docs/trace_checksums.sha256` (SHA-256 of the 15 `*.trace.gz` files, `MANIFEST.tsv` and
`ENVIRONMENT.txt`, verify with `sha256sum -c docs/trace_checksums.sha256` from the repository root)
and `docs/trace_checksums_uncompressed.sha256` (SHA-256 of the decompressed trace text, so that a
different gzip implementation does not matter; verify with
`bash tools/review/trace_checksums.sh --check`). Both were generated and checked at the commit above.

The nine **synthetic** traces of the paper are not stored; `scripts/gen_synthetic.py` regenerates them with
fixed seeds. No checksum of them is recorded. The traces of the predecessor repository (METIS) are
fetched and are not part of the paper's main results.

### 6. The reference model (`tests/reference_model.hpp`)

* 59 lines, includes only `<cstdint> <map> <string> <utility> <vector>`; it does not include
  `strata.hpp`, `arena_chain.hpp` or any benchmark header and shares no code with them.
* State: `std::map<std::string, std::vector<Decl>> names_` (for every visible name, the stack of its
  declarations `{depth, value, type}`) and `std::vector<std::vector<std::string>> scopes_` (names declared
  in each open scope, in order).
* `declare(name, value, type)`: if the top declaration of that name has the current depth, replace its
  value and type and return 1 (this is `kRedeclared`); else push `{depth, value, type}`, record the name
  in the current scope and return 0. `exit()` pops one declaration for each name of the innermost scope
  and erases names whose stack becomes empty; it refuses (returns false) at depth 0. `resolve` returns the
  top declaration. `live()`, `distinct()` and `depth()` give the counters that the tests compare.
* It is independent of `strata.hpp` in the sense of an independent *implementation of the specification*:
  different data structure (ordered map of vectors, no hashing, no fixed buffer, no packing, no index),
  no shared helper. It is **not** independent in authorship (written by the same authors from the same
  specification), it does not model capacity, name-length limits (1 to 255 bytes), the depth limit (16 383),
  probe limits or refusals; callers apply a call to the model only when the table accepted it
  (`tests/exhaustive_small.cpp`: "a refused operation is not applied"; `benchmarks/hardening_main.cpp:
  mode_traces` likewise). Whether the table was right to refuse is checked separately (state digest
  unchanged after a refusal; refusal reasons enumerated in `exhaustive_small`).
* Users: `tests/test_strata.cpp`, `tests/fuzz_strata.cpp`, `tests/exhaustive_small.cpp`,
  `benchmarks/bench_main.cpp` (`reference_pass`: expected declare results and lookup results for the
  whole trace, compared with every one of the 13 tables), `benchmarks/hardening_main.cpp`, and
  `frontend/engine/strata_engine.cpp`.
* A table is "correct" on a trace when every lookup value equals the model's and every declare result
  (new / redeclared) equals the model's (`wrong_lookups`, `wrong_declares` in `compiler_summary.csv`).
  Because the TinyCC traces contain no same-scope redeclaration, "wrong declaration result = 0" on them can
  only mean that no declaration was wrongly reported as redeclared.

### 7. What stays unchanged in the chibicc integration

`tools/chibicc/apply_patch.py` (with `-DCDES_BACKEND`) replaces **only** the per-scope `vars` hash maps
of `parse.c`: `push_scope`, `find_var` and the lookup in `find_func` call `cdes_put`, `cdes_get` and
`cdes_get_global` of `tools/chibicc/cdes_backend.cpp`, and `enter_scope`/`leave_scope` call
`cdes_enter`/`cdes_leave`. Everything else in chibicc is unchanged: the `Scope` struct is still
allocated per scope (its `vars` map is simply never filled), the **tag** maps (`scope->tags`, struct/union/enum
tags), goto labels, the preprocessor's macro table, the keyword table, the include cache and the
`Obj`/`Type` structures. Typedef names, enumeration constants, variables and functions go through
`push_scope` and therefore through the replaced table.

Back-end details (`cdes_backend.cpp`):

* chibicc stores a pointer per declaration; the tables store a 32-bit value, so the pointers live in
  a side array `g_vals` (grown with `realloc`, never freed), and the table holds the index.
* `find_func` asks for the declaration in the **outermost** scope, which an innermost-first table
  cannot answer when a local name hides it, so declarations made at depth 0 are also kept in a second
  table instance of the same kind (`g_global`). Both the STRATA and the arena build do this, so
  their memory use includes two tables plus `g_vals`.
* Empty names are stored as the byte `0x01`.
* The STRATA back end uses growable mode (`strata::Table g_all, g_global;` default options); a refusal
  aborts the compiler (`fail`). The arena back end is `arena_chain::Table`, same call pattern.
* The keyed hash and bounded mode are **not** used in the integration.
* Build flags: `cc -std=c11 -O2 -fno-common -w` for chibicc, `g++ -std=c++14 -O2 -fno-exceptions -fno-rtti
  -DBACKEND_STRATA|-DBACKEND_ARENA` for the back end (`tools/chibicc/build.sh`).


## 2. Emulated Cortex-M3 and the chibicc end-to-end experiment

All facts below are read from `tools/embedded/`, `tools/chibicc/`, `results/embedded/`,
`results/chibicc/` and the manuscript generators. "Not recorded" = the repository does not say.
The ARM toolchain and QEMU are not installed on the machine on which this document was prepared, so
nothing in section A was re-run for this document; the numbers are those of the stored logs.

**Restatement, to be kept in the paper: every Cortex-M3 result is from an emulator (QEMU 6.2.0,
machine `mps2-an385`). No physical device was used, the emulator provides no timing, and no energy,
cache or flash-wait-state behaviour is measured.**

### A. Cortex-M3 under QEMU

#### A.1 Toolchain and commands

Recorded in `results/embedded/*.txt` (2026-10-13; the exact commit is not recorded in those files,
they were committed in `cddcb25`):

* `arm-none-eabi-g++ (15:10.3-2021.07-4) 10.3.1 20210621 (release)`
* `QEMU emulator version 6.2.0 (Debian 1:6.2+dfsg-2ubuntu6.31)`
* host reference build: `g++ (Ubuntu 11.4.0) -std=c++14 -O2`

Fixed-buffer images (`bash tools/embedded/run.sh zlib littlefs cjson lua freertos`; for each trace):

```
gunzip -c workloads/traces/$t.trace.gz > build/embedded/$t.trace
python3 tools/embedded/gen_trace_header.py build/embedded/$t.trace > build/embedded/trace_data.h
MIN=$(python3 tools/embedded/min_buffer.py $t)                     # buffer size, see A.4
g++ -std=c++14 -O2 -Ibuild/embedded -DBUFFER_BYTES=$MIN -o build/embedded/host tools/embedded/main.cpp
./build/embedded/host                                              # prints: checksum refused peak_used
ARMFLAGS="-mcpu=cortex-m3 -mthumb -Os -fno-exceptions -fno-rtti -fno-threadsafe-statics -ffunction-sections -fdata-sections"
arm-none-eabi-g++ -std=c++14 $ARMFLAGS -Ibuild/embedded -DBUFFER_BYTES=$MIN -DEXPECTED_CHECKSUM=${SUM}u -c tools/embedded/main.cpp -o build/embedded/main.o
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -Os -c tools/embedded/startup.c -o build/embedded/startup.o
arm-none-eabi-g++ -mcpu=cortex-m3 -mthumb -nostartfiles -T tools/embedded/link.ld -Wl,--gc-sections \
    --specs=nano.specs --specs=nosys.specs build/embedded/startup.o build/embedded/main.o -o build/embedded/$t.elf
qemu-system-arm -M mps2-an385 -cpu cortex-m3 -nographic -semihosting -kernel build/embedded/$t.elf     # under `timeout 120`
```

Other scripts: `tools/embedded/bounded.sh` (bounded mode, section A.6), `tools/embedded/fit.sh TRACE KiB ...`
(same trace and same buffer for STRATA and the arena table, section A.7). Run time on the development
machine: 10 s for the five fixed-mode images and 11 s for the five bounded images
(`reports/artifacts/final_verification.log`, steps V10 and V11, including compilation).

#### A.2 Linker script and memory layout (`tools/embedded/link.ld`)

| Region | Origin | Length | Holds |
|---|---|---|---|
| `FLASH` (rx) | `0x00000000` | 1024 KiB | vector table, `.text`, `.rodata` (including the whole trace, A.3), `.ARM.exidx`, the load image of `.data` |
| `RAM` (rwx) | `0x20000000` | **64 KiB** | `.data`, `.bss` (the table buffer and the table object), then free space, then the stack |

`_stack_bottom = end of .bss`; `_stack_top = 0x20000000 + 64 KiB = 0x20010000`; the stack grows down
from `_stack_top`. There is no heap. `main.cpp` defines `malloc`, `free` and `realloc` for ARM as stubs that
fail on purpose ("fixed-buffer mode must not need an allocator"). The 64 KiB limit is enforced **only by
the linker script**: the linker fails if `.data` + `.bss` exceed 64 KiB, but nothing checks the stack against
the end of `.bss`, and no QEMU option limits the machine's memory (the scripts pass none). "Restricted
to 64 KiB of memory" in the paper therefore means: static data fits in a 64 KiB region and the measured
stack high-water mark lies below `_stack_top`, with the measured sum (below) far under 64 KiB.

#### A.3 What is allocated where

| Item | Where | Size |
|---|---|---|
| table buffer `static uint32_t g_buffer[BUFFER_BYTES/4]` | `.bss` (RAM) | `BUFFER_BYTES` (= `MIN`, A.4) |
| table object `room[sizeof(Tab)]` (placement-new, recreated at every `U`) and other statics | `.bss` (RAM) | the "static RAM bytes" line minus the buffer: **364 B in every run** (e.g. zlib 16 748 - 16 384) |
| stack | RAM, top down from `0x20010000` | high-water mark 492 B (fixed mode) / 484 B (bounded mode) |
| heap | none | 0 |
| **trace input** `kKind[]` (1 B per operation), `kName[]` (2 B per operation), `kNames[]` pointers and the name strings | `static const` arrays, i.e. `.rodata` in **FLASH** | e.g. Lua 188 509 operations -> about 3 B per operation plus names |

**The trace input is not counted in the 64 KiB**: it is `const` data placed in flash by `link.ld`
(`*(.rodata*) > FLASH`); the size line of every image reports `data 0`, so nothing of it is copied to RAM.
The whole image (`text`, which "includes the embedded trace") is: zlib 191 212 B, littlefs 81 208 B,
cJSON 84 116 B, Lua 617 112 B, FreeRTOS 156 980 B (`results/embedded/qemu_cortex_m3.txt`), all below the
1 024 KiB flash region. On a real part the trace would not exist; a compiler's own input would arrive over
some other path whose buffers are not modelled here.

RAM actually used by the five images (static + measured stack): zlib 16 748 + 492; littlefs 20 844 + 492;
cJSON 31 084 + 492; Lua 37 228 + 492; FreeRTOS 45 420 + 492 bytes, i.e. at most 45 912 B of 65 536 B.
The three traces that do **not** fit are the ones whose smallest single buffer already exceeds 64 KiB
(`results/raw/20261013-143828-paper/budget.csv`, STRATA packed, factor 1.00): Mbed TLS 81 920 B, SQLite
143 744 B, TinyCC 160 256 B.

#### A.4 Buffer size of each image

`tools/embedded/min_buffer.py TRACE` reads the **newest** `results/raw/*/budget.csv`
(lexicographic order of the directory names, which is `20261013-143828-paper` today), takes the row
`names == packed, budget_factor == 1.00`, and rounds `min_buffer_bytes` **up to a whole KiB**:
zlib 16 128 -> 16 384, littlefs 20 480, cJSON 30 720, Lua 36 800 -> 36 864, FreeRTOS 45 056.
Consequence: the images run with the smallest buffer that replays the trace (peak used 16 128 of 16 384,
20 468 of 20 480, 30 704 of 30 720, 36 776 of 36 864, 45 008 of 45 056 B), which is the strictest
possible test of "fits". If a newer run directory with a `budget.csv` is ever added, `min_buffer.py` would
silently pick it up. When no row is found it falls back to 32 768 B.

#### A.5 The reported stack (492 B) and code (2 715 B)

**Stack, 492 B.** Procedure (`startup.c`, `main.cpp`):

1. `reset_handler` copies `.data`, zeroes `.bss`, then **paints** the words from `_stack_bottom` up to
   `_stack_top - 16 words` with `0xA5A5A5A5`, then calls `main()`.
2. `main()` runs the whole replay (`replay()`: all operations of the trace, including every table
   re-creation), then scans upward from `_stack_bottom` while the words are still `0xA5A5A5A5`; the first
   non-painted word `p` is the deepest point the stack ever reached.
3. "stack bytes used" = `_stack_top - p`, printed through semihosting **after** the scan (so the output
   routines are not part of the figure).

What the figure is and is not:

* It is a dynamic high-water mark of one execution of one trace. It is **not** a static worst-case
  analysis (no `-fstack-usage`, no call-graph analysis is recorded).
* It includes `reset_handler`, `main`, `replay()` and the table calls; it excludes exception/interrupt
  stacking (no interrupt is enabled; every fault handler is an endless loop).
* The top 16 words (64 B) of the stack region are never painted, so they are always counted: the figure
  is at least 64 B by construction.
* The value is the same, 492 B, for all five fixed-mode runs, and 484 B for all five bounded-mode runs
  (`qemu_cortex_m3_bounded.txt`). The paper's `\EmbStack` is read from the first `stack bytes used` line
  of `qemu_cortex_m3.txt` (`manuscript/tools/make_numbers.py`), i.e. the fixed-mode value; the paper's
  sentence about bounded mode does not give a stack figure.

**Code, 2 715 B.** Procedure (`run.sh`, last lines of each block):

```
arm-none-eabi-nm --size-sort -S -C build/embedded/main.o | awk '/strata::/ {n += strtonum("0x" $2)} END {print n}'
```

i.e. the sum of the sizes of all symbols in the **object file** `main.o` (compiled with `-Os`,
`-ffunction-sections`, Thumb-2) whose demangled name contains `strata::`. Consequences: (a) it is the
size of the table's own functions and template instantiations that the replay uses, before linking and
before `--gc-sections`; (b) it does not include the wrapper `Tab`, the replay loop, the semihosting
output code, `startup.c`, or any C-library routine the table calls (e.g. a `memcpy`), because those
are not `strata::` symbols of `main.o`; (c) it does not include read-only data of the table (there is none
recorded) or its 364 B of statics; (d) it is identical (2 715 B) in the fixed-mode and the bounded-mode builds
because both compile the same runtime-configured `strata::Table` code. The size of the arena table's code
was **not** measured. Not recorded: the size of the complete linked image without the embedded trace.

#### A.6 Bounded mode on the same target

`bounded.sh` builds with `-DTABLE_BOUNDED -DINDEX_SLOTS=<s> -DMAX_PROBE=512` where `<s>` is the third
column of the first matching row of `results/hardening/traces.csv` (zlib 1 024, littlefs 1 024,
cJSON 2 048, Lua 2 048, FreeRTOS 2 048 slots), the same buffer as the fixed-mode image, and the keyed hash
(HalfSipHash-1-3). The **key is a hard-coded constant** (`0x0a1b2c3d`, `0x4e5f6071`, with the comment
"a device would draw this from its entropy source"); no entropy source or key derivation exists in the
emulated image. The pass criterion is the same checksum as the host's ordinary fixed-buffer run, which
also shows that nothing was refused. `TEST_RESULTS.md` (E2) still says "probe limit 64"; the script
and the result file (`probe limit 512`) are the authority and agree with the paper.

#### A.7 Equal-buffer comparison with the arena table (`fit.sh`, `fit_cortex_m3.txt`)

The expected checksum comes from a host run with a 4 MiB buffer; each image is then run with the stated
buffer. Recorded: FreeRTOS 48 KiB: STRATA 0 refused, arena **420** refused ("DOES NOT FIT", peak 49 152);
FreeRTOS 56 KiB: both pass (STRATA peak 45 008, arena 54 892); Lua 40 KiB: STRATA 0, arena **2 214**;
cJSON 32 KiB: STRATA 0, arena **822**. The arena table in `fit.sh` is built with `-DTABLE_ARENA` and no
other change.

#### A.8 What the emulated runs do not show

No timing (QEMU), no flash wait states or caches, no real memory protection, no interrupts, no second
core, no entropy source, no 32-bit host build of the unit tests (blocked in the audit: multilib missing,
`reports/TEST_RESULTS.md` section 4). The checksum covers every declare result and every lookup value;
`check_invariants()` is not run on the target.

### B. chibicc end to end

#### B.1 What was built (`tools/chibicc/build.sh`)

chibicc commit `90d1f7f199cc55b13c7fdb5839d1409806633fdb`, patched by `tools/chibicc/apply_patch.py`, built three
times from the same patched `parse.c`:

| Build | Variable-scope table | Compile |
|---|---|---|
| `chibicc-orig` | the original per-scope hash maps (plus the trace hook) | `cc -std=c11 -O2 -fno-common -w` on all `*.c`; linked with `cc` |
| `chibicc-strata` | `strata::Table` (growable mode), `-DCDES_BACKEND` | C files as above; `g++ -std=c++14 -O2 -fno-exceptions -fno-rtti -DBACKEND_STRATA -Iinclude -Ibenchmarks/baselines -c tools/chibicc/cdes_backend.cpp`; linked with `g++` |
| `chibicc-arena` | `arena_chain::Table`, `-DBACKEND_ARENA` | same, `-DBACKEND_ARENA` |

Only the variable-scope maps are replaced; tags, labels, macros, keywords and chibicc's data structures
are unchanged (`docs/EVIDENCE.md`, part 1, section 7). All three builds contain the trace-hook code
(`CDES_TRACE` is unset during timing, so no file is written). Each build is copied to
`~/cdes/cc-<variant>/chibicc` with chibicc's `include/` next to it. Smoke test in `build.sh`: a small
program with a shadowed variable compiled by each build must run and return 0.

Note (not analysed in the repository): the STRATA and arena builds are linked with `g++`, the original
with `cc`, so the two C++ builds also load the C++ runtime library at process start; whether that adds
a constant start-up cost per compiler invocation was not measured.

#### B.2 Commands and verification (`python3 tools/chibicc/evaluate.py [workdir] [rounds=21]`)

For each of the seven projects (cJSON, littlefs, zlib, Lua, FreeRTOS, Mbed TLS, SQLite):

1. For every translation unit, run the **original** build: `chibicc -S <flags> -o orig.s <file>` with
   `CDES_TRACE` set. If it exits non-zero the unit is excluded and recorded with `original_compiles=0`
   (12 of 170 units, listed in `docs/EVIDENCE.md` part 1, section 3). The STRATA/arena builds are not tried on
   excluded units.
2. **Byte-identical assembly check.** The same unit is compiled by the STRATA and the arena builds with
   `-S`, and each output is compared **byte for byte** with the original's after one normalisation: the
   string `cc-<variant>/include` is replaced by `cc-X/include` in both (the `.file` lines contain the directory
   of the compiler's own headers, which differs between the three install directories). A build that
   fails to compile the unit counts as not identical. Result (`units.csv`): 158 of 158 units identical for
   STRATA and 158 of 158 for the arena table. Only the assembly text is compared (not linked
   binaries, not executed output), and only for units the original accepts.
3. The scope trace of the original is stored as `workloads/traces/chibicc_<project>.trace.gz`.
4. **Peak memory**: `/usr/bin/time -f %M` on one run per build per unit (`rss.csv`, 158 rows; one run, no
   repetition). The paper's "median of 0.18 percent" is the median over units of
   `|strata_rss / orig_rss - 1| * 100` (absolute change, so a decrease and an increase both count positive).
   Largest peaks are about 535 to 539 MB for the biggest unit (`orig`, `strata` and `arena` within 0.7 percent).
5. **Time**: for each project, 1 warm-up round (round -1, discarded) and 21 measured rounds. In each round
   each of the three builds compiles all of the project's accepted units (`-S ... -o /dev/null`, one process
   per unit) and the wall time of the loop is recorded with `time.perf_counter`; the order of the three
   builds is rotated by one in every round (`(rnd+1+k) mod 3`). The process start-up, preprocessing, parsing
   and code generation are all in the time. The script does **not** pin a core (no `taskset`); the paper's
   statement that the benchmark was pinned to one core applies to the replay benchmarks (`scripts/run_all.sh`).
   Whether `evaluate.py` was run under an external `taskset` is not recorded.

Environment file (`results/chibicc/environment.txt`): WSL2 kernel `6.18.33.2-microsoft-standard-WSL2`,
host cc 11.4.0; date and commit not recorded (it was committed in `cddcb25`, 2026-10-13; the older
`results/chibicc-20261011/` is kept as history, made with an older STRATA header, and the paper does not use
it). `evaluate.py` takes about 12 minutes (`submission/REPRODUCE.md`).

#### B.3 How the confidence intervals are formatted (`manuscript/tools/make_numbers.py`, `paired()`)

Each cell of `tables/tab_chibicc.tex` reads `m [lo, hi]` followed by a verdict:

* `m` = median over the 21 rounds of `100 * (t_variant / t_orig - 1)`, where `t` is that round's wall time
  for the project (paired by round). Negative = faster than the original.
* `[lo, hi]` = percentile bootstrap interval: 2 000 resamples of the 21 per-round ratios (with
  replacement, size 21), the median of each resample, sorted; `lo` is the 50th smallest (0-based index
  49, the 2.5th percentile) and `hi` the 1 950th (index 1 949, the 97.5th percentile). The intervals are
  nominal 95 percent, uncorrected for the 14 intervals of the table.
* Verdict: `faster` if `hi < 0`, `slower` if `lo > 0`, otherwise `n.e.` (not established).
* Signs are typeset as `$-$` and `$+$`, one decimal place; the first numeric column is the median of the
  original compiler's 21 times in seconds, two decimals; "Units compiled" is the number of accepted units.
* The random generator is `random.Random(20261013)`, shared by all calls of the script, so the interval
  endpoints reproduce only when the script is run as a whole in the same order.

Reading the table honestly: with STRATA, Mbed TLS is `slower` (+1.4 [+0.2, +2.4]) and no project is `faster`;
with the arena table littlefs, Lua and SQLite are `faster` and none `slower`. The sentence in the paper
("changes by between -3.7 and +2.2 percent") quotes the medians and does not mention the established
Mbed TLS slowdown (the macro `\ChibiStrataSlower` = 1 exists but is not used in the text).


## 3. Hash flooding and the adaptive-key experiment

Sources: `benchmarks/hardening_main.cpp` (`--mode flood`), `results/hardening/{flood.csv,
flood_verification.txt,environment.txt}`, `scripts/audit/hardening.sh`, `include/strata/strata.hpp`,
`theory/verify/adaptive_key_demo.{cpp,out}`, `docs/ADDENDUM_2026-10-17.md`, `docs/LIMITATIONS.md`.
`tools/review/flood_summary.py` prints the tables below from `flood.csv` (all sizes with argument `0`).

### 1. The flooding experiment as run

Run: `bash scripts/audit/hardening.sh 5`, i.e. `taskset -c 2 ./build/hardening --mode flood --reps 5`
(`results/hardening/environment.txt`: 2026-10-13T16:34:48Z, g++ 11.4.0, Intel Core Ultra 7 258V,
WSL2 kernel 6.18.33.2, **git commit `2382cb55...` plus 27 uncommitted paths**, 5 repetitions, the
median is reported). Build flags `-std=c++14 -O2 -Wall -Wextra` (`scripts/build.sh`).

Inputs. `colliding_names(32768, 15)` builds 2^15 distinct valid C identifiers of 150 characters that
have **one common hash value** for the default (unkeyed MurmurHash3-style) hash, for every seed
(Aumasson-Bernstein style multicollisions on 5-character words). Before any timing the program checks
that all 32 768 are distinct, share hash `d741b050` under the built-in seed and still collide under 8 further seeds
(`flood_verification.txt`; `reports/TEST_RESULTS.md` calls this "9 seeds" = the built-in one plus 8). The control
input is `ordinary_names`: 32 768 random identifiers of the same length (150), made distinct by an 8-digit
suffix. For each size n in 1 024, 2 048, ..., 32 768, each input and each of four configurations, one
fresh table receives n `declare` calls and then n `resolve` calls:

| Config | Hash | Index | Probe limit |
|---|---|---|---|
| `default` | unkeyed | grows | none |
| `keyed` | HalfSipHash-1-3, key drawn at run time | grows | none |
| `bounded` | unkeyed | static, smallest power of two with `slots*3 >= 4n` (65 536 slots for n = 32 768), in a 16 MiB buffer | 64 |
| `bounded_keyed` | keyed | as `bounded` | 64 |

Pass criterion (`correct`): every stored name resolves to its value, every refused name does not
resolve, and `check_invariants()` holds. All 48 rows have `correct = 1`.

### 2. Admitted versus refused, n = 32 768 (`docs/flood_summary.txt`)

| Input | Config | Submitted | **Admitted** | **Refused** | Longest probe | Declare ms | Lookup ms |
|---|---|---|---|---|---|---|---|
| ordinary | default | 32 768 | 32 768 | 0 | 175 | 6.52 | 3.67 |
| ordinary | keyed | 32 768 | 32 768 | 0 | 86 | 9.33 | 5.07 |
| ordinary | bounded (L = 64) | 32 768 | 32 768 | 0 | 26 | 3.11 | 3.19 |
| ordinary | bounded_keyed | 32 768 | 32 768 | 0 | 20 | 5.22 | 5.00 |
| colliding | default | 32 768 | 32 768 | 0 | **32 768** | **1 953.86** | **1 684.09** |
| colliding | keyed | 32 768 | 32 768 | 0 | 106 | 10.80 | 5.38 |
| colliding | bounded (L = 64) | 32 768 | **64** | **32 704** | 64 | 7.72 | 7.15 |
| colliding | bounded_keyed | 32 768 | 32 768 | 0 | 26 | 5.56 | 5.77 |

Reading, with the paper's sentence "the capped table rejects 32 704 of 32 768 names":

* **Unkeyed, no limit**: nothing is refused, all work is "useful" (all 32 768 stored and found), but it
  costs 1 954 ms against 6.5 ms for ordinary names (ratio 300, `\FloodRatio`); every new name scans the
  cluster of all earlier ones (the longest probe sequence equals n).
* **Unkeyed, limit 64**: the first 64 colliding names are stored (a cluster of 64 consecutive cells) and
  each of the other 32 704 is refused with `kProbeLimit` after examining at most 64 cells; the table is
  unchanged by a refusal. Time stays linear (7.72 ms, ratio 2.5 to the bounded ordinary run). The refused
  names are the **attacker's own names**: from the compiler's point of view this is a rejected input, not
  corrupted state; every later lookup of a refused name correctly reports "not declared".
* **Keyed, with or without the limit**: the same names are ordinary names under a key their author
  did not know; all are admitted, and the ratio to ordinary input is 1.2 (default keyed) and 1.1 (bounded keyed).
* Per-size counts for the bounded unkeyed configuration on colliding input: always 64 admitted, so refused =
  n - 64: 960 (n = 1 024), 1 984, 4 032, 8 128, 16 320, 32 704 (n = 32 768). No other configuration refuses
  anything at any size.

What the experiment does **not** measure (gaps, not recorded anywhere in the repository):

* "Useful work completed" for honest names that arrive **after or between** the flood: the flood and the
  ordinary inputs are run in separate tables, never mixed. The experiment therefore shows that the
  attacker's names cannot make the table slow or inconsistent, but it does not count how many honest
  declarations a limit-64 table with 64 colliding names in it would also refuse. The nearest measurement
  is the adaptive-key experiment below (700 honest names after 400 to 800 attacker names), which uses
  a different attack and limit 512.
* Variance: five repetitions, median only, no interval, one pinned core, one machine, one compiler.
* Memory use under flooding (peak bytes) is not recorded in `flood.csv`.

### 3. How keys are generated, derived and persisted: what the code and documents say

**Library** (`include/strata/strata.hpp`, `struct Options`): `bool keyed` and `uint32_t key[2]` ("secret 64-bit
key for `keyed`; must come from a source the input's author cannot predict"). The default is `keyed = false`
and `key = {0, 0}`. The library does **not** generate, derive, rotate, store or count keys, offers no
API for them, and contains no counter. It hashes with HalfSipHash-1-3 under the key it is given, checked
against the reference implementation on little-endian hosts only (200 000 random inputs, 0 mismatches,
`reports/artifacts/halfsiphash_conformance.log`).

**Documents.** The recommendation is "one key per translation unit, derived from a device secret and a
never-repeating counter" (manuscript Section "Keyed Hash and the Lifetime of a Key";
`docs/ADDENDUM_2026-10-17.md` lines 57-61; `theory/paper/main.tex` line 432: `K_i = PRF(K_0, i)`, "never
reuse a counter value (a device that resets its counter reuses keys)"). The PRF is not specified, no
implementation exists, and there is no description of how a counter would be persisted (non-volatile
storage, atomic increment, behaviour after power loss or reset, multi-process or parallel compiler
runs). `docs/LIMITATIONS.md` line 120: "Where the key comes from on a device without an entropy source is
not addressed." The work bound (at most L index slots per call) does not depend on the key; only the
absence of refusals does.

**Keys actually used in the experiments** (none comes from an operating-system or hardware entropy source):

| Experiment | Key | Source |
|---|---|---|
| flooding (`hardening_main.cpp: flood_once`) | `{0x6b657931 ^ rnd32(), 0x6b657932 ^ rnd32()}`, new for every table | xorshift64 `g_rng`, fixed initial state `0x243F6A8885A308D3`, so the sequence is the same in every run; names are generated before and independently of the key (the collisions hold for all seeds) |
| bounded mode on the 15 traces (`mode_traces`), the keyed timing variant `StrataKeyed` (`benchmarks/baselines/tables.hpp`), the Cortex-M3 bounded image | the constant `{0x0a1b2c3d, 0x4e5f6071}`, the same in **every** translation unit | hard-coded; there is no adversary in these runs, but they are a persistent key, which is the setting the paper says to avoid |
| refusal-law check (`theory/verify/law_vs_table.cpp`) | a new key for every trial | `std::mt19937_64` seeded with `1000 + m + n + L`; "fresh random key per trial" in the paper means a fresh pseudo-random key, reproducible by seed |
| adaptive-key demo | persistent key per seed, and an independent "fresh" key per table | `std::mt19937_64(1000 + seed)` |
| chibicc integration | unkeyed | n/a |

### 4. What the adaptive-key experiment models (`theory/verify/adaptive_key_demo.cpp`)

Command (`theory/verify/run_all.sh`): `adaptive_key_demo 2048 512 700 5 400 512 600 700 800`; output stored in
`theory/verify/adaptive_key_demo.out` and turned into `th_tab_adaptive.tex` by `adaptive_to_tex.py`.

* Table: real `strata::Table`, static index m = 2 048 slots, probe limit L = 512, keyed hash.
* **Oracle (idealised).** For a candidate name, the attacker builds a fresh table with the persistent
  secret key, declares an anchor name `anchor_name` and then the candidate, and reads
  `Stats::longest_probe`; the value 2 means that the candidate's home slot equals the anchor's. This is a
  noise-free, per-call, exact probe-length reading taken from the library's own statistics structure.
  It is **not** a timing measurement; no timing channel, no noise, no amount of repetition needed to
  average out jitter, and no way for a real adversary to read `Stats` is modelled or measured. It "stands in
  for" a timing side channel (the file's own comment says so; `theory/PROOF_AUDIT.md`: "the model oracle is not
  a timing channel"). The attacker never sees the key.
* Learning: random 12-letter lowercase candidates are tried until `cmax` (800) colliders are found; one
  collider costs on average 2 071 oracle queries (about m = 2 048, as the geometric argument predicts).
* Victim runs, per seed, per number c of colliders (400, 512, 600, 700, 800): a table is created, the
  anchor and the first c learned colliders are declared, then 700 honest names (`honest_` plus 10 random
  letters) are declared and the refusals (`kProbeLimit`) counted. Three variants: **same key** (persistent
  key), **fresh key** (an independent key for the victim's table), **random names** (c random names instead of
  the colliders, same persistent key).

| Colliders c | Refused honest names, same key (mean % of 700, max over 5 seeds) | fresh key | random names |
|---|---|---|---|
| 400 | 1.00 % (max 1.29 %), about 7 names | 0 | 0 |
| 512 | 5.51 % (max 6.14 %), about 39 names | 0 | 0 |
| 600 | 4.71 % (max 6.00 %) | 0 | 0 |
| 700 | 5.14 % (max 5.71 %) | 0 | 0 |
| 800 | 5.14 % (max 6.00 %) | 0 | 0 |

The paper's "1 to 5.5 percent" is the range of the **means**; the maximum over seeds is 6.14 percent. The
effect appears once the colliders form a run of about L cells. The model has no real sequence of
compilations: the same key is simply reused by the attacker's queries and by the victim's table. `review/adaptive_oracle_check.cpp` is a
separate feasibility check of the same idea; its output is not stored.

What it shows: if one key is reused across tables and probe lengths leak, an attacker can plant names
that refuse honest names; with a fresh key per table the learned colliders are useless. What it
does not show: that such a leak exists in a real compiler or on a real device, how many queries a
noisy timing channel would need, or any defence beyond "fresh key per table".

### 5. Gaps to state in the paper or answer in the response

1. No honest-plus-hostile mixed flood with the default hash and limit 64.
2. No implementation, test or measurement of key derivation or counter persistence; the experiment keys
   are pseudo-random or constant.
3. The hardening run records commit `2382cb55` with 27 uncommitted paths; the exact code state of that
   run cannot be recovered from the repository.
4. Single machine, five repetitions, no intervals for the flooding times.


## 4. Encodings and limits

Every fact below is read from `include/strata/strata.hpp` (line numbers refer to that file) and is
checked by `tests/test_review.cpp` (T3; run `build/review_tests/test_review`, log in
`reports/artifacts/review_tests.log`). All words are `uint32_t`.

### Buffer regions (lines 3-14, 500-511)

```
word 0              idx_                      idx_+itop_                 cap_-undo_        cap_
| index (idx_ slots) | identifier stack ->  | free gap                 | <- undo stack   |
```

* `idx_` is a power of two >= 16 (`kInitialIndex`, line 486; bounded mode: `Options::index_slots`).
* The identifier stack starts at word `idx_`. Its word 0 is **reserved** (`itop_ = 1`, line 503) so that
  reference 0 can mean "none". That word is never written (T1 checks that it keeps the caller's fill value
  in 66,582 of 66,582 scope exits).
* There is no header in the buffer. All counters (`idx_`, `itop_`, `undo_`, `mark_`, `ndecl_`, `nident_`,
  `depth_`, `cap_`, `peak_`, ...) live in the `Table` object (lines 661-672), not in the supplied words.
  The buffer is therefore self-describing only together with the object.

### Index word (lines 8, 513-516, 541-545)

```
bit 31..24  fingerprint = hash >> 24, with 0 mapped to 1      (slot_word, line 514-515)
bit 23..0   identifier reference (kRefMask = 0x00FFFFFF), >= 1
word == 0   empty slot
```

A used word is non-zero because the reference is >= 1 (the "0 mapped to 1" rule for the fingerprint is
therefore not needed for non-emptiness; it only keeps the fingerprint comparison `(s >> 24) != fp` total).
The reference is the offset of the record from the start of the identifier region (`ident(ref) = w_ + idx_ + ref`,
line 508). Home slot = `hash & (idx_-1)` (line 521). Verified for `"abc"`: word `0xdc000001` at slot 9.

### Identifier record (lines 9, 482-483, 311-315)

```
word 0   value (int32 stored as uint32)
word 1   meta:
           bits  0- 6  n, number of name words (1..64; kWordsMask 0x7F)
           bit      7  raw flag
           bits  8- 9  raw length mod 4 ("tail"), 0 for packed names
           bits 10-17  type tag (8 bits, 0..255)
           bits 18-31  scope depth of the innermost declaration (14 bits, 0..16383)
word 2.. name words (n of them)
```

`kKeyBits = 0x3FF` (line 486) is the identity part of meta (bits 0-9: n, raw, tail); `find()` compares it
(line 542) and then the name words. Type and depth (bits 10-31) are the mutable part. Record length is `2 + n`
words (line 316). Verified: meta of `"abc"`, type 0xA5, depth 0 is `0x00029401`.

### Name encoding (lines 433-474, 114-126)

* **Packed** (`pack_names`, all bytes in `[A-Za-z0-9_]`): 5 characters per word, 6 bits each, character `i`
  of a word at bits `6*i .. 6*i+5`; bits 30-31 are 0. Codes: `a..z = 1..26`, `A..Z = 27..52`, `0..9 = 53..62`,
  `_ = 63`. **No identifier character has code 0**; code 0 is "not an identifier character" and forces the
  raw path. Hence zero bits in the last word are unambiguous padding, no length is stored
  (comment line 468), `meta = n`. Packed length n = ceil(len/5) (51 words for 255 characters).
* **Raw** (`pack_names == false`, or any byte outside the alphabet anywhere in the name, including the
  partial last word): `n = ceil(len/4)`, the bytes are `memcpy`'d (line 465) after zeroing the last word
  (line 464), `raw = 1`, `tail = len & 3` (line 466). The tail is needed because a raw name may itself end in
  NUL bytes. Raw 255 bytes = 64 words (`kMaxNameWords`), tail 3. A high-bit byte (>= 0x80) is read through
  `unsigned char` (line 437) and is simply "not an identifier character" -> raw.
* A packed and a raw name can never be confused: the raw bit is part of the compared key bits.
* Tested (T3): lengths 1..255 packed and raw (word counts, meta fields, padding bits, unpack equals input,
  declare/resolve with type and value); `a, a_, a__, ...` and `_ .. ______` families; every string over
  {NUL, 'a'} of length 1..8 (510 strings) plus the families, all single bytes 1..255, high-bit bytes at the
  front and in the middle: 1,030 pairwise distinct names resolve to their own values in packed and raw mode;
  non-identifier byte at each of 12 positions; 255-byte packed and raw names; 256 -> `kNameTooLong`; 0 ->
  `kEmptyName`; all 256 type tags with extreme `int32` values.

### Undo stack (lines 10-14, 243-256, 293-302, 229-233)

The undo stack grows downward from `w[cap_]`; an entry's first word is at the lowest address.

| entry | words (lowest address first) | pushed by |
|---|---|---|
| first declaration of a name (1 word) | `[index slot]` (< `idx_` <= 2^23, so bit 24 is 0) | `declare`, line 329-330 |
| shadowing declaration (3 words) | `[ref | kShadowBit]` (`kShadowBit = 1<<24`), `[hidden value]`, `[hidden meta & ~kKeyBits]` (type and depth only) | `declare`, line 295-299 |
| scope mark (2 words, `kMarkWords`) | `[identifier-stack top at entry (itop_)]`, `[previous mark_]` | `enter_scope`, line 229-233 |

`mark_` is the undo-stack size just after pushing the mark, i.e. a position counted from the end of the
buffer; marks therefore chain without touching references. The shadow bit (bit 24) is distinguishable from a
slot entry because a slot is always < 2^23. Verified byte for byte in T3: slot entry `0x00000009`, shadow
entry `[0x01000001][-2][0x00029400]`, marks `[4][0]` and `[4][3]`.
During an index rebuild, `stash_undo`/`reindex` (lines 563-588) temporarily swap the record's value word with
the 1-word entry; this is never visible across an API call.

### The 24-bit reference unit and the effective maximum buffer size

* A reference is a **word** offset (not bytes) into the identifier region, 24 bits, 0 reserved (line 503).
* `kMaxWords = 0x00FFFFFF = 16,777,215` words (line 485), applied in the fixed constructors (lines 182, 196),
  the growable constructor (line 212) and growth (line 604). So the largest buffer the table uses is
  **16,777,215 words = 67,108,860 bytes = 64 MiB - 4 bytes**. The paper's "64 MiB" is this value rounded;
  "buffer <= 64 MiB" (line 46) is correct as an upper bound but not tight: 2^24 words are never used.
  T3 offers 128 MiB and checks `capacity_bytes == 67,108,860` and that the words beyond are untouched.
* Reference 0 being reserved costs one word (the reserved word), not a reduced limit: the largest reference
  that can occur is `cap_ - idx_ - 1 - ...` < `0xFFFFFF` (idx_ >= 16), so the limit `kMaxWords` is a safe
  conservative choice rather than one forced by the reference field. The guard at line 307
  (`itop_ + 2 + k.n > kRefMask`) is consequently **unreachable**: `itop_ + idx_ <= cap_ <= 0xFFFFFF` and
  `idx_ >= 16`. It is kept as defence in depth.
* Other fields do not tighten it: n (7 bits, max used 64), type (8 bits), depth (14 bits, exactly
  `kMaxDepth = 16383 = 2^14-1`; the depth guard is line 227), undo slot (< 2^23), `mark_`/`itop_` words are
  full 32-bit.
* Reachability (measured, T3): default growable-index mode with 8-byte names fills the 64 MiB buffer with
  2,516,582 names; the index has grown to 2^22 slots and the identifier stack ends at word 10,066,329. With
  a static 2^19-slot index and 255-byte raw names (66 words per name) the buffer fills with 242,580 names and
  the identifier stack ends at word 16,010,281 of the 16,777,215 range. In both cases the refusal is
  `kNoMemory` from the buffer, never from the reference field.
* Minimum buffer: 32 words (`kMinWords`, line 485); 31 words gives an invalid table (every call `kNoMemory`).
* The largest index is 2^23 slots (a power of two below `kMaxWords`); with the 3/4 load limit that is at most
  6,291,456 names in the index, but the default-mode buffer is exhausted earlier (above).

### Scope depth and name limits

`kMaxDepth = 16383` open scopes (14-bit depth field, bits 18-31 of meta); depth 0 is the outermost scope, so
16383 `enter_scope` calls succeed and the 16384th returns `kTooDeep`. Each costs 2 words. T3 nests 16383
scopes, shadows `x` at every level, checks the stored depth field `0x3FFF`, then unwinds. Names are 1..255
bytes (`kMaxNameLen`, lines 434-435); type tag is the full `uint8_t`.

### Endianness and alignment assumptions

* The buffer must be aligned for `uint32_t` (line 181) and `uint32_t` must be 32 bits.
* Packed names are built arithmetically from codes, so the word values do not depend on endianness.
* Raw names are `memcpy`'d (line 465): the first byte of the name is the least significant byte of word 0 on
  a little-endian host and the most significant on a big-endian host. Tables are therefore not portable
  between hosts of different endianness through their buffer contents when raw names are present.
* The keyed hash (line 158) takes name words in host order; its agreement with reference HalfSipHash is
  only claimed (and tested, `tests/halfsiphash_conformance.cpp`) on little-endian hosts (line 47). The unkeyed
  hash is endianness-independent given the same word values. `test_review` asserts the host is little endian.
* The caller's buffer is accessed through `uint32_t*` obtained from `void*` (lines 181, 195); the aliasing
  of the caller's storage is the caller's responsibility.


## 5. The exhaustive enumeration harness

This describes exactly the harness behind the "80,621,568 sequences of nine operations" figure. The number
was reproduced by running `./exhaustive_small 9` (build `-std=c++14 -O2`); the log is
`reports/artifacts/review_exhaustive_9.log`:

```
depth 9: 80621568 sequences, 725594112 operations, 130361632 refusals
         (no memory 75575944, too deep 0, probe limit 54785688), 0 failures      (3m21s)
```

### Alphabet and sequences

Six operations (`enumerate`, line 103: digits 0..5):
`0 enter_scope`, `1 exit_scope`, `2 declare("a")`, `3 declare("bb")`, `4 declare("x::y")`,
`5 declare("long_identifier_name_0")` (`kNames`, line 32; `x::y` is non-identifier, so it is stored raw even in
packed mode). A declaration passes `value = step number (1-based)` and `type = step` (line 62), so every
declaration is distinguishable.

A sequence is an element of {0..5}^9: 6^9 = 10,077,696 sequences per configuration, as an odometer over all
of them (lines 86-105). Exit at depth 0 (kNoScope) is part of the alphabet and occurs often.

### Configurations (eight, lines 110-120)

| label | buffer | pack | all keys one home slot | keyed | index slots | max probe |
|---|---|---|---|---|---|---|
| fixed 128 B, packed | 128 | yes | no | no | grow | - |
| fixed 128 B, raw names | 128 | no | no | no | grow | - |
| fixed 160 B, one cluster | 160 | yes | yes | no | grow | - |
| fixed 136 B, keyed hash | 136 | yes | no | yes | grow | - |
| static 16 slots, 144 B | 144 | yes | no | no | 16 | 0 |
| static 16, limit 1, one cluster | 256 | yes | yes | no | 16 | 1 |
| static 16, limit 2, one cluster | 256 | yes | yes | no | 16 | 2 |
| static 16, limit 2, keyed, 152 B | 152 | yes | no | yes | 16 | 2 |

("one cluster" = `Table::degenerate_hash()` test hook, home slot always 0.) Keys for the keyed variants are
`{0x1234, 0x5678}`. 8 x 10,077,696 = **80,621,568** sequences (the paper's figure).

### Start state and resets

Each sequence is replayed **from scratch**: a new buffer of `bytes/4` words filled with `0xDEADBEEF`, a new
`Table` over it and a new `ReferenceModel` (`make`, line 36; `enumerate`, lines 87-89). Nothing carries over
between sequences, which is what makes the enumeration cover all prefixes: the first k operations of each
length-9 sequence are the k-prefix, reached identically. After the nine operations, the harness unwinds any
open scopes with `exit_scope` (line 91, these calls are not counted as operations) and checks
`size() == model.live()` and `check_invariants()` (line 92).

### Per-operation checks (`apply`, lines 49-79)

After **every** operation (all nine of every sequence):

1. its result equals the reference model's: accepted operations (`kOk`, `kRedeclared`) are applied to the
   model, whose status must agree; a refused operation (any other status) is **not** applied to the model;
   `exit_scope` at depth 0 must return `kNoScope`;
2. every refusal, and the `kNoScope` case, leaves `state_digest()` unchanged (the 64-bit FNV-style digest of
   counters, index and both stacks);
3. all four names resolve exactly as in the model (value and type);
4. `size()`, `depth()`, `live_identifiers` equal the model's, and `check_invariants()` holds.

It checks the 64-bit digest, **not** a byte comparison of the buffer; whole-buffer memcmp atomicity is in
`tests/test_review.cpp` (T2).

### Operation accounting

Operations counted: each of the 9 steps of each sequence = 9 x 80,621,568 = **725,594,112** (`g_operations`
is incremented once per `apply`). The final unwinding exits are not counted. A "refusal" is an `enter_scope` with any
non-`kOk` status or a `declare` with any status other than `kOk`/`kRedeclared`; the `exit_scope` -> `kNoScope` case is checked but
**not** counted as a refusal. Status counters at depth 9: no memory 75,575,944, probe limit 54,785,688,
too deep 0 (depth 16383 is unreachable in nine operations), total 130,361,632 = 75,575,944 + 54,785,688.
Per configuration refused operations: 20,888,172; 20,975,655; 3,706,705; 13,450,460; 10,869,042; 37,188,600;
17,597,088; 5,685,910.

Failures: 0. Scope of the claim: all sequences of length 9 (hence all shorter prefixes) over this
six-symbol alphabet and these eight configurations; this is a bounded check, not a proof. `kNameTooLong`
and `kEmptyName` cannot occur (the alphabet has no such name).


## 6. Tests added after the reviewer report

Branch `reviewer-report-revision`; `include/strata/strata.hpp` unchanged; no bug found. Builds are in
`build/review_tests/` (and, for `scripts/test.sh`, `build/`). Full log: `reports/artifacts/review_tests.log`.

| item | result |
|---|---|
| `scripts/test.sh` (extended with `tests/test_review.cpp`, -O2 and ASan/UBSan) | all pass: test_strata 2,732,358 checks (plain + sanitizers), exhaustive depth 7, test_review 1,673,523 checks (plain + sanitizers), 0 failures |
| `exhaustive_small 9` (`reports/artifacts/review_exhaustive_9.log`) | 80,621,568 sequences, 725,594,112 operations, 130,361,632 refusals (no memory 75,575,944, probe limit 54,785,688, too deep 0), 0 failures, 3m21s. Matches the paper |
| libFuzzer (`tests/fuzz_strata.cpp`, clang, ASan+UBSan, 60 s) | 348,786 runs, no crash (`reports/artifacts/review_fuzz.log`) |

### T1 whole-buffer equality (66,582 scope exits, 9 configurations: fixed packed/raw/sparse, bounded, bounded+probe+keyed, tiny fixed with refusals, three growable)

* (a) logical state (accessors, every name resolves like the model and like the fresh table, invariants): 66,582/66,582. Always.
* (a') `state_digest` vs a natural fresh replay: 47,580/66,582; differs exactly when the index (13,945 exits) or the buffer (11,388 exits, growable) has another size. Never differs otherwise.
* (b) allocated region (index, identifier stack, undo stack; the reserved word excluded): equal in 52,637/52,637 exits where the index has the same size. The identifier stack alone is equal in 66,582/66,582 exits (references are relative). Index words and slot undo entries differ across index sizes by construction.
* (c) literally every supplied word vs a natural fresh table: 0/55,194. Never holds, even for one exit: the exited scope's mark words (and any dead record/undo entry) remain in the free gap.
* (d) vs a fresh bounded table with the same index and buffer size: digest and allocated region 66,582/66,582 (always); literal words 0/66,582, and in every case the only differing words lie inside the free gap between the stacks (0 exits with a difference elsewhere).
* Legitimately different: dead data in the gap; `peak_used_bytes` (differs at nearly every exit), `rebuilds`, `longest_probe` (high-water marks); index size after growth (fixed grow-in-place and growable never or only lazily shrink); buffer capacity (growable). Not differing: the reserved identifier word (never written, 66,582/66,582), bytes beyond the used words including a 3-byte tail of an odd-sized buffer.
* Dead data is **not cleared**: 15.3% of gap words (3,926,002 of 25,721,149 sampled) hold non-fill data after exits. Only the index slot of a removed name is zeroed; identifier records, shadow/slot undo entries and mark words stay. (Consequence for confidentiality: names/values of exited scopes persist in the caller's buffer.)

### T2 refusal atomicity

783,955 refusals checked by direct `memcmp` of the entire buffer (plus tail bytes), `Stats`, digest, depth, size, validity: all unchanged. Sweeps: capacity word by word 32..220 (48..240) for six fixed/bounded configurations (317k-324k ops each); exact-threshold test in bounded mode (118 capacities x 46 fill levels x 12 operation classes): verdict predicted from `stats()` alone, accepted iff free words >= need (enter 2, shadow 3, new name 3 + w(x)) and index load allows; 529 probes at exactly `free == need` all accepted, 1,592 at `free == need - 1` all refused; growable budget sweep 128..1500 B and allocator failure injected at call 1..12 (block pointer and contents unchanged); depth limit at buffer sizes one word short, exact and ample.

Status precedence observed (all refusals atomic): invalid table (kNoMemory) > name checks: empty (kEmptyName) and too long (kNameTooLong) come before any memory check; for enter: kTooDeep > kNoMemory (the 16384th enter in a buffer with exactly 16383 marks of room is kTooDeep); for a new name: kNoMemory (buffer or index load, checked in `ensure`) > kProbeLimit; kRedeclared never needs memory and succeeds with 0 free; a shadow declaration needs 3 words; `exit_scope` at depth 0 is kNoScope (kNoMemory only if the table is invalid).

### T3 encodings

Round trips for lengths 1..255 (packed and raw), padding families, strings over {NUL, 'a'}, high-bit bytes, 255-byte names, all type tags, depth 16383 (nested, shadowed at every level, stored depth field 0x3FFF), bit layouts of index word, record, undo entries, marks, verified in memory: all pass. Written up in `docs/REVIEW_ENCODINGS.md`.

### Findings

* No bug. All asserted properties hold.
* The paper's "64 MiB" is exactly 16,777,215 words = 64 MiB - 4 B (`kMaxWords`); reference 0 is a reserved word, not a reduced limit; the guard at `strata.hpp:307` (`itop_ + 2 + n > kRefMask`) is unreachable. The default-mode buffer is exhausted before the reference range (ident stack reaches word 10,066,329 or, with a static 2^19-slot index and 255-byte names, 16,010,281 of 16,777,215).
* Whole-buffer byte equality with a fresh table is false by design (dead data is not scrubbed); equality holds for the allocated region once the index size and buffer size are matched.
* The `exit_scope` -> `kNoScope` case is not counted as a refusal in the exhaustive harness.
