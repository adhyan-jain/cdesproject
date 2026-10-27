# Evidence behind the paper's claims

> **Removed sources.** Citations in this file to `docs/EXECUTION_LOG.md`, `docs/ADDENDUM_2026-10-17.md`, `docs/RELATED_WORK.md`, `reports/TEST_RESULTS.md`, `submission/REPRODUCE.md`, `theory/PROOF_AUDIT.md`, `SUBMISSION_READINESS.md` and similar process documents refer to files deleted in the repository cleanup. They are kept in the git tag `pre-cleanup` (`git show pre-cleanup:<path>`).

One document for the supporting facts that the article summarizes: how the traces are defined, the embedded and compiler experiments, the flooding experiments, the bit-level encodings, the exhaustive harness and the tests added after the reviewer report. Everything was read from the files and logs it names; "not recorded" means the repository does not say. The command-to-table map is in `REVIEW_MANIFEST.md`.


## 1. Compiler traces: schema, semantics, pinned sources

Everything below was read from the files named in it. "Not recorded" means that the repository
does not say. Commit of this document: `c5d8eb8ae9f313001181b73ef76c54f2376714c8` (branch
`reviewer-report-revision`; the working tree was not clean when this was written, see
part 7 below). The traces themselves were last changed in commit `2d8672b`
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
  (part 9 below). The include path of TinyCC itself (its `include/` directory) is not
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

## 7. Manifest: command to table, figure and number


> **Removed sources.** Citations in this file to `docs/EXECUTION_LOG.md`, `docs/ADDENDUM_2026-10-17.md`, `docs/RELATED_WORK.md`, `reports/TEST_RESULTS.md`, `submission/REPRODUCE.md`, `theory/PROOF_AUDIT.md`, `SUBMISSION_READINESS.md` and similar process documents refer to files deleted in the repository cleanup. They are kept in the git tag `pre-cleanup` (`git show pre-cleanup:<path>`).

Scope: every table and figure of `manuscript/ieee_access/` (`body.tex`, `tables/`, `figures/`,
`generated_numbers.tex`). Facts come from `body.tex`, `main.tex`, `README.md` of the manuscript,
`manuscript/tools/make_numbers.py`, `theory/verify/run_all.sh`, `submission/REPRODUCE.md`,
part 9 below, `docs/EXECUTION_LOG.md`, `reports/TEST_RESULTS.md` and
`reports/artifacts/final_verification.log`. "Not recorded" = the repository does not say.

### 0. Pinned commit and state

* Commit of this manifest: **`c5d8eb8ae9f313001181b73ef76c54f2376714c8`** (`git rev-parse HEAD`, branch
  `reviewer-report-revision`, 2026-10-27 session). **The working tree was not clean** when it was written:
  other work in progress modified `benchmarks/{bench_main,budget_main}.cpp`, `benchmarks/baselines/tables.hpp`,
  `scripts/test.sh`, `theory/verify/{law_vs_table.cpp,run_law_check.py,wrap_tables.py}`,
  `theory/paper/tables/*lawcheck*`, `manuscript/ieee_access/{body.tex,main.tex,tables/th_tab_lawcheck.tex}` and
  added untracked files. Numbers below describe the **committed** data; any run made from the modified
  tree is a new run, not the one the paper reports.
* The data the paper reports were produced at earlier commits; the HEAD above only contains them:

| Data | Produced at | Where recorded |
|---|---|---|
| main benchmark run `results/raw/20261013-143828-paper` (Tables workloads/memory/time/latency/ablation/synthetic/unitfit/sweep, Figs minbuffer/time) | `36f9f6c` (2026-10-13T14:39Z; the extra experiments `units.csv`, sweep, chibicc replays at 14:47Z, same commit) | `results/raw/.../environment.txt` |
| "before" run for the artifact comparison `results/raw/20261013-120345-audit` (Table/Fig. time) | `65db7eb` | `submission/REPRODUCE.md` section 4 |
| `results/hardening/` (Tables flood-config, bounded; Fig. flood) | `2382cb55` **+ 27 uncommitted paths**, 2026-10-13T16:34Z | `results/hardening/environment.txt` |
| `results/chibicc/` (Table chibicc) | commit not recorded (committed in `cddcb25`, 2026-10-13); host cc 11.4.0, WSL2 | `results/chibicc/environment.txt` |
| `results/embedded/` (Section "An Emulated Microcontroller") | commit not recorded (committed in `cddcb25`) | the three `.txt` files |
| verification logs (`final_verification.log`, `exhaustive_small.log`, `fuzz_strata*.log`, `mutation_check.log`) | clean copy of source commit `e1d099c` + uncommitted changes, 2026-10-13T16:56Z (`final_verification.log`, line 1) | `reports/artifacts/` |
| theory tables/figure data `theory/paper/tables`, `theory/paper/data` | last committed in `a143804` (2026-10-18); regenerated by `theory/verify/run_all.sh` | `theory/paper/tables/*.tex` |

* Host of all measurements: Intel Core Ultra 7 258V, 8 logical cores, 15.7 GiB visible to the guest, Windows 11,
  WSL2, Ubuntu 22.04, kernel 6.18.33.2-microsoft-standard-WSL2, glibc 2.35, g++ 11.4.0 `-std=c++14 -O2`,
  clang 21.1.8 (fuzzing, static analysis), Python 3.10.12 (pipeline), benchmarks pinned with `taskset -c 2`
  (`submission/REPRODUCE.md` section 2, `reports/artifacts/environment.txt`).
* The generated numbers (`generated_numbers.tex`) are byte-identical to `paper/generated_numbers.tex`, and the
  16 `tables/tab_*.tex` files are byte-identical to `paper/tables/` (checked with `cmp`). `make_numbers.py` writes to
  `paper/`; the manuscript directory keeps its own copy; `manuscript/ieee_access/` (README removed; see the main README)
  names `../tools/make_numbers.py` as the origin.

### 1. Tables

Common prefix: `R = results/raw/20261013-143828-paper`. `NUM` = `python3 manuscript/tools/make_numbers.py $R`
(writes `paper/generated_numbers.tex`, `paper/tables/tab_*.tex`, `manuscript/figures/source/data_*.csv`).
`TH` = `bash theory/verify/run_all.sh` followed by `python3 manuscript/ieee_access/tools/theory_tables.py`
(copies `theory/paper/tables/tab_*.tex` to `tables/th_*.tex`, only the rules change).

| Table (label) | Content | Command that produces it | Raw input |
|---|---|---|---|
| I `tab:comparison` | properties of scoped symbol tables | **hand-written** (literature), no command | `RELATED_WORK.md`, `references.bib` |
| II `tab:encoding` | bit-level layout | **hand-written** from `include/strata/strata.hpp` and `docs/CORRECTNESS.md` | the header |
| `tab:orphan` (`th_tab_orphan`) | orphan law | TH: `theory/verify/orphan_law.py` | exact enumeration |
| `tab:design` (`th_tab_design`) | smallest L for given eps | TH: `design_rule.py` (writes `design_rule.csv`, `tab_design.rows`), `design_table.py` | exact law, Python |
| `tab:adaptive` (`th_tab_adaptive`) | persistent vs fresh key | `g++ -std=c++14 -O2 -I include theory/verify/adaptive_key_demo.cpp; ./a.out 2048 512 700 5 400 512 600 700 800`, then `adaptive_to_tex.py` | real `strata::Table` (stored: `theory/verify/adaptive_key_demo.out`) |
| `tab:workloads` | the eight traces | NUM | `$R/compiler_summary.csv`, traces |
| `tab:memory` | smallest buffers, heap peaks | NUM | `$R/budget.csv`, `$R/compiler_summary.csv` |
| `tab:ledger` (`th_tab_ladder`) | space ledger | TH: `space_model.py`, `make_figdata.py` | stored traces in `workloads/traces` and the measured minima in `results/raw/*/budget.csv` (`space_model.py`) |
| `tab:time` | replay-time ratios (31 rounds) | NUM | `$R/compiler_replays.csv` |
| `tab:latency` | p95 per-operation latency | NUM | `$R/compiler_summary.csv` |
| `tab:ablation` | variants vs default | NUM | `$R/compiler_summary.csv`, `compiler_replays.csv` |
| `tab:synthetic` | 9 synthetic traces | NUM | `$R/synthetic_*.csv` (traces from `scripts/gen_synthetic.py`) |
| `tab:floodconfig` | flooding, 4 configs | NUM | `results/hardening/flood.csv` |
| `tab:lawcheck` (`th_tab_lawcheck`) | exact law vs real table | TH: `theory/verify/run_law_check.py $BUILD/law_vs_table 400000` | real `strata::Table`, 7 settings x 400 000 trials |
| `tab:bounded` | bounded mode on 15 traces | NUM | `results/hardening/traces.csv` |
| `tab:unitfit` | units that fit a budget | NUM | `$R/units.csv` (from `scripts/run_extra.sh`) |
| `tab:sweep` | shadowing / name length sweep | NUM | `$R/sweep_minbuf.csv`, `sweep_summary.csv`, `sweep_replays.csv` (traces from `scripts/gen_sweep.py`) |
| `tab:chibicc` | chibicc end to end | NUM | `results/chibicc/{units,times,rss}.csv` (from `python3 tools/chibicc/evaluate.py`) |
| `tab:lawproc` (`th_tab_lawproc`) | processes P3 and P4, coupling violations | TH: same run as `tab:lawcheck` (`run_law_check.py`, `wrap_tables.py`) | real `strata::Table`, 7 settings x 400 000 trials |
| `tab:c1` | smallest buffer of S, C0, C1, S raw; savings | `python3 manuscript/tools/make_sessions_tables.py` | `results/review/r13_minbuf.csv`, `r13_savings.csv` (`budget r13`) |
| `tab:sessions` | five timing sessions, t intervals, TOST | `bash scripts/review_sessions.sh`, `python3 scripts/review_analyze.py`, then `make_sessions_tables.py` | `results/review/sessions/s1..s5/`, `analysis_pooled.csv` |
| `tab:instr` | user-space instructions per replay | `g++ -std=c++14 -O2 -o build/instr_count benchmarks/instr_count.cpp`; per trace `taskset -c 2 ./build/instr_count --trace T --name N --reps 5 >> results/review/instr_counts.csv`; then `python3 manuscript/tools/make_instr_table.py` (seconds per trace) | decompressed traces in `build/review_bench/traces/` |

Prepared-name numbers in the text (instruction-count paragraph): `g++ -std=c++14 -O2 -o build/prepared_count benchmarks/prepared_count.cpp`; per trace `./build/prepared_count T N` -> `results/review/prepared_counts.txt`.

Files in `tables/` not used by `body.tex`: `tab_beforeafter`, `tab_flood_scale`, `tab_limits`, `tab_probe`,
`tab_short`.

### 2. Figures

| Figure | File | Produced by | Input |
|---|---|---|---|
| `fig:arch`, `fig:undo`, `fig:dep`, `fig:flow`, `fig:law`, `fig:ledger`, `fig:lawz` | `figures/fig_{arch,undo,dep,flow,law,ledger,lawz}.pdf` | pages of `theory/template/build/{diagrams,plots}.pdf` (`python3 theory/template/make_figures.py`); data from `make_figdata.py` / `tables/*.rows` | `theory/paper/{data,tables}` (`fig_law`: exact law plus the 10 million-sample simulation in `results/hardening/probes.csv`; `fig_lawz`: the `tab_lawcheck` rows) |
| `fig:layout`, `fig:pipeline` | `fig_layout.pdf`, `fig_pipeline.pdf` | **drawn by hand** in TikZ: `manuscript/figures/source/fig_{layout,pipeline}.tex` (compiled PDFs stored) | none |
| `fig:minbuffer`, `fig:time`, `fig:flood` | `fig_{minbuffer,time,flood}.pdf` | `python3 manuscript/figures/source/make_plots.py` | `data_{minbuffer,time,flood}.csv` written by NUM from `$R/budget.csv`, `$R/compiler_replays.csv` (+ the "audit" run for the before series), `results/hardening/flood.csv` |
| `fig:tool` | `screenshot_analyse.png` | screenshot of the frontend's Analyse page (`frontend/web`, `npm run dev`); capture procedure and date **not recorded** | a pasted C program (not recorded) |

Files in `figures/` not used by `body.tex`: `fig_probe.pdf`, `fig_design.pdf`.

### 3. Numbers in the text

Macros (`generated_numbers.tex`) are written by NUM from the run directories above. Exceptions that are
not data-driven: `\Rounds` is the literal `"31"` in `make_numbers.py`. Numbers read from logs by NUM
(`grab()`): `\UnitChecks` (2 732 358) from `final_verification.log`; `\ExhSeq/\ExhOps/\ExhRefusals` from
`exhaustive_small.log`; `\Mutants` from `mutation_check.log`; `\FuzzFinal`/`\FuzzBefore` (sum of
`number_of_executed_units` in `fuzz_strata.log` = 2 476 136; `fuzz_strata_before_changes.log` = 9 773 374);
`\EmbPass`, `\EmbCode`, `\EmbStack`, `\EmbBoundedPass` from `results/embedded/*.txt`.

**Typed by hand in `body.tex`, not generated** (they can drift from the data): 258 / 260 / 455 / 121 / 52
(design values; source `theory/paper/tables/tab_design.tex`, `design_rule.csv`); 488 919 state
comparisons, 397 562 pairs, 258 and 481 cases (sources `theory/paper/tables/{lifo,orphan,exact,proof}_summary.tex`,
macros `\UndoComparisons`, `\SafeOrderPairs`, `\ExactTriples`, `\KnuthCases` exist but are not used);
"seven settings of 400 000 trials" and "largest |z| = 1.96" (`lawcheck_summary.tex`; this file and
`run_law_check.py` are being modified in the working tree); "2.4 x 10^-11" (`docs/ADDENDUM_2026-10-17.md`);
"37 automated checks" (`frontend/README.md`); the 48 KiB / 40 KiB / 32 KiB and the 420 / 2 214 / 822 refusals
(`results/embedded/fit_cortex_m3.txt`).

### 4. Expensive commands: run time and resources

All times are from the development host above; they are wall-clock times recorded in the named file.
Memory and disk use are **not recorded** for any command unless stated.

| Command | Produces | Run time | Source of the time |
|---|---|---|---|
| `bash scripts/test.sh` (unit tests -O2 + ASan/UBSan + exhaustive depth 7) | 2 732 358 checks, depth-7 enumeration | 24 s (step V01); "about 15 s" in REPRODUCE, "about 2 minutes" in the 2026-10-11 document | `final_verification.log` |
| `bash scripts/audit/exhaustive.sh 9` | 80 621 568 sequences, 725 594 112 ops, 130 361 632 refused, 0 failures | **1 min 54 s** | `reports/TEST_RESULTS.md` X2 |
| `bash scripts/audit/fuzz.sh 600 3` (libFuzzer, ASan+UBSan) | 9.8 M executions before / 2.5 M after | 3 jobs x 600 s each (the executions are counts, not time) | `fuzz_strata*.log` header |
| `python3 scripts/audit/mutation_check.py` | 9 of 9 mutants detected | 20 s | V08 |
| `bash scripts/audit/halfsiphash_check.sh` | 200 000 inputs, 0 mismatches | 140 s | V06 |
| `bash scripts/audit/final_verify.sh` (12 steps from a clean copy of 539 files) | the audit | steps sum to 513 s (about 8.5 min) in the log; REPRODUCE says "about 6 min" | `final_verification.log` |
| `bash scripts/run_all.sh paper` | `$R` (8 TinyCC traces + 9 synthetic + 4 legacy, 13 tables, 31 rounds, pinned core) | **8 min 48 s**; "about 9 min" in REPRODUCE (an older figure of 45 min is superseded) | part 9 of this document update |
| `bash scripts/run_extra.sh $R all` | `units.csv`, sweep, chibicc replays | **1 min 48 s** | same |
| `PROBE_TRIALS=500 bash scripts/audit/hardening.sh 5` | `results/hardening/*` | about 2 min (45 s with reps 1 and 200 trials); the flood uses a 16 MiB buffer | REPRODUCE; V09 |
| `bash tools/embedded/run.sh ...` / `bounded.sh` | `results/embedded/*` | 10 s / 11 s (5 images each, incl. compilation) | V10, V11; needs ARM toolchain and QEMU |
| `bash tools/chibicc/build.sh && python3 tools/chibicc/evaluate.py` | `results/chibicc/*` | about 12 min; peak resident set up to about 540 MB for one compile of `sqlite3.c` (`rss.csv`) | REPRODUCE; `rss.csv` |
| `tools/tcc-trace/build_tcc.sh`, `make_traces.sh` | the 8 traces | **not recorded** (network; sources fetched at run time) | - |
| `bash theory/verify/run_all.sh` | `theory/paper/{tables,data}`, theory PDF | the script header says "about 6 minutes (the end-to-end check against the real table dominates)"; `theory/README.md` says "about 9 minutes"; the two are not reconciled | script / README |
| `python3 manuscript/tools/make_numbers.py $R`, `make_plots.py`, `crosscheck.py` | tables, macros, plots | **not recorded** (2 000-resample bootstraps; seconds to a minute is a guess and is not a record) | - |
| `cd frontend/web && npm test` (37 checks) | frontend verification | **not recorded** | - |

Network: only for `scripts/fetch_third_party.sh` (METIS `7b3dacf`, parallel-hashmap v1.4.1 `22a7f6c`), the HalfSipHash
reference source, and trace regeneration. The paper's tables can be rebuilt from the stored `results/` without network.

### 5. Where independent oracles exist for the exact refusal law

The law: P(refuse) = (k/m) * sum_{g>L} (g-L) B(g) Q_{k-1}(m-g) / Q_k(m), k = m - n (called "Theorem 4" in the
docstring of `exact_law.py` and "Theorem 7" in the manuscript and in `frontend/web/src/lib/theory.ts`: old numbering).

| # | Oracle | What it compares | Scope actually covered | Independent? |
|---|---|---|---|---|
| 1 | `theory/verify/exact_law.py` | closed form in exact rationals (`fractions.Fraction`) against **brute-force enumeration of every home sequence** | m = 2..9, every n < m, L = 1..m with m^n <= 2 000 000: **258** (m,n,L) triples, 0 mismatches | yes: enumeration shares no formula |
| 2 | `theory/verify/fill_law.py` | the related refusal-free-fill law against brute force; float and 60-digit decimal evaluations against exact | 135 cases (m <= 8 for the exhaustive part, per `theory/PROOF_AUDIT.md`) | yes for small m |
| 3 | `theory/verify/proof_checks.py: check_knuth_route` | a second derivation by Knuth's Abel-binomial counting against the theorem | **481** cases: exact for m <= 14, floats up to m = 2^20, worst relative difference 2e-10 | partly: second derivation, same authors, same language |
| 4 | `theory/verify/design_table.py` vs `results/hardening/probes.csv` | float (log-gamma) evaluation against a stored simulation of insertion probe lengths (24 configurations x 10 000 000 samples = 240 000 000) | m = 2^10, 2^13, 2^16; loads 3/8..3/4; resolution about 1e-7 | yes (a simulation of the process); cannot resolve values below about 1e-7 |
| 5 | **C++ `theory/verify/law_vs_table.cpp` + `run_law_check.py`** | counts the probes a **real `strata::Table`** (keyed, static index) needs for a fresh name and compares the observed frequency of ">L" with the Python value (z-test) | 7 settings x 400 000 trials, m = 256 and 1 024, L = 8..96, largest |z| = 1.96; plus lock-step with and without the limit | yes (the implementation), but the **formula itself is evaluated only in Python** |
| 6 | TypeScript `frontend/web/src/lib/theory.ts: refusalProbability` | against Python reference values (`make_frontend_reference.py` -> `frontend/web/tests/theory_reference.json`, which calls `fill_law.R_refusal`) | 9 grid points (m = 256, 1 024, 4 096; n = 3m/4), relative tolerance 1e-9; part of `npm test` | **no**: a transcription check of the same formula against the Python result |
| 7 | `review/borel_probe_tail.py` | the m -> infinity Borel/Poisson limit against the 10 million-sample measurements and against the Chernoff-type bound | m = 65 536 rows of `probes.csv` | a separate Python implementation of the limit |

There is **no** C++ implementation of the closed-form probability (searched for `lgamma`/Borel in all `.cpp`/`.hpp`
files; only Python files contain it), and no implementation of it outside Python and TypeScript.

### 6. Gaps (stated plainly)

1. Brute-force verification of the law covers only m <= 9; at design scale (m = 2^16, L = 258) the law is checked
   only through the formula, its second derivation (oracle 3), the process simulation (oracle 4, resolution about 1e-7,
   whereas the design target is 1e-6 per declaration) and real-table runs at m <= 1 024. No real-table run exists at m = 2^16.
2. Oracles 1, 3, 6 are written by the same authors; no third-party implementation or outside check is recorded.
3. The working tree was modified after the commit that holds the reported data; the hardening run was made at
   `2382cb55` with 27 uncommitted paths; for `results/chibicc` and `results/embedded` the commit is not recorded.
4. The ARM toolchain and QEMU were not available for this review, so Section A of `EVIDENCE.md` part 2 is a
   reading of the stored logs, not a re-run. The same is true for the chibicc build (sources under `~/cdes` do not exist on this machine).
5. Run times for trace generation, `make_numbers.py`, `make_plots.py`, `crosscheck.py` and `npm test` are not recorded;
   peak memory is not recorded for any command except the chibicc compile (up to about 540 MB) and the 16 MiB flooding buffer.
6. The screenshot (`fig:tool`) has no capture procedure.
7. Hand-typed numbers in `body.tex` (section 3) are not generated and are only checked by reading.
8. `docs/EXECUTION_LOG.md` covers only the sessions of 2026-10-11; later sessions are documented in `reports/`, `SUBMISSION_READINESS.md`
   and `docs/ADDENDUM_2026-10-17.md`, not in an execution log.
9. The nine synthetic traces and the sweep traces are regenerated by seeded scripts but their checksums are not recorded
   (`tools/review/trace_checksums.sh` covers only `workloads/traces/`).

## 8. The stronger baseline, monotonicity scan and timing sessions


All of this was run on 2026-10-26/27 (UTC) on branch `reviewer-report-revision`, code base commit `c5d8eb8` plus the uncommitted changes listed in section 1.
Nothing here was copied from the paper; every number comes from `results/review/`. Where a result differs from the paper it is said so in section 0.

### 0. Summary (read this first)

* **R13 (memory).** The ledger prediction holds: the measured smallest buffer of the real C1 table (conventional arena table WITHOUT the stored hash word) equals the `chain_nohash` prediction of `theory/verify/space_model.py` exactly, on all 8 traces. STRATA's saving is **16.4-17.9 % against C0** (paper headline; here 16.38-17.95 %, pooled 17.33 %) but only **5.3-9.0 % against C1** (5.26-9.03 %, median 6.84 %, pooled 7.46 %). The paper's 5-9 % estimate against C1 is confirmed by measurement, and so is the reviewer's point: roughly 11 percentage points of the headline come from the stored hash word of C0, not from STRATA's design. STRATA with raw (unpacked) names needs the same buffer as C1 to within 64 bytes (0 to -0.38 %): the saving against C1 is almost entirely the 5-per-word name packing.
* **R13 (time).** Removing the hash word makes the arena table SLOWER (C1/C0 = 1.04-1.12 in the pooled median, 7 of 8 traces established slower, sqlite not established). STRATA is slower than C0 on every trace (pooled ratio 1.08-1.20, all 8 established; within +-10 % equivalence on none: 6 outside the margin, zlib and sqlite inconclusive). STRATA against C1: ratio 0.995-1.131; 6 of 8 traces are slower by an established amount (cjson 1.04, littlefs 1.11, freertos 1.07, lua 1.07, mbedtls 1.05, tinycc 1.13), zlib and sqlite are not established; equivalence within +-10 % is shown on 6 of 8 traces (not littlefs - inconclusive - and tinycc - outside). STRATA is faster than METIS-X on all 8 traces (ratio 0.69-0.93, all established); keyed STRATA is 1.20-1.28x slower than unkeyed STRATA (all established). The paper's qualitative conclusions on time (STRATA slower than the arena table, faster than METIS-X) are reproduced; no verdict was reversed. The paper's per-trace magnitudes should be replaced by the numbers below because the compiler (g++ 16.2.1 vs 11.4) and machine differ.
* **R14 (monotonicity).** On all 8 traces and all four fixed-buffer tables (STRATA packed, STRATA raw, C0, C1) the scan found **0 non-monotone points**: below the threshold every capacity fails, from the threshold up every capacity succeeds (section 4).
* **R15/R16 (repeatability).** 5 independent sessions, each a fresh process per trace, 31 rounds (+2 warm-up), pinned to cpu 4, 5 minutes apart. Within one session the intervals are narrow, but the absolute times of different sessions differ by up to 1.5x (CPU frequency state, see 6.3), so ratios, not absolute times, are the only comparable quantity; the between-session spread of the ratios is mostly 1-4 % but the per-session medians of STRATA/C0 span 1.058-1.144 on sqlite and 1.149-1.226 on tinycc so that for sqlite STRATA/C0 and STRATA/C1 the session-level evidence is weaker than any single session's interval suggests (section 5).

### 1. What was implemented (files)

| file | content |
|---|---|
| `benchmarks/baselines/arena_chain_nohash.hpp` | **new**: layout C1 = `arena_chain.hpp` with the hash word removed. Entry `[next][value][len\|depth<<16][name words]` = 3+wc words instead of 4+wc. Same MurmurHash3 mixer over the zero-padded name words, same load factor 1 (buckets double when live declarations would exceed buckets), same 1.5x growth in growable mode, same refusal-without-state-change, same 64-byte-resolution bisection. The hash is **recomputed from the stored name** in `exit_scope` (bucket of each popped entry) and in the bucket-array rebuild (re-linking); the chain walk compares length then name words (no hash pre-filter). |
| `benchmarks/baselines/tables.hpp` | added `ArenaChainNoHash` (id `arena_nohash`); nothing else changed. |
| `benchmarks/bench_main.cpp` | registered `ArenaChainNoHash` after `ArenaChain`; added option `--rot K` (default 0 = old behaviour) shifting the rotation of the start order. |
| `benchmarks/budget_main.cpp` | new modes `r13` and `scan`, generic checked replay (variant 4 = C1). Existing modes unchanged. |
| `benchmarks/review_aux.cpp` | `sizes` (control struct sizes) and `timer` (empty interval) |
| `scripts/review_sessions.sh`, `scripts/review_analyze.py` | session driver and statistics |

Correctness of C1: in the growable benchmark (`bench`) the check pass compares every lookup result and declaration status with `tests/reference_model.hpp`; for all traces `wrong_lookups = wrong_declares = refused = 0` for `arena_nohash` (columns in `results/review/sessions/s*/summary.csv`). In fixed-buffer mode every result was compared with the reference model at the smallest buffer for all four tables: 0 wrong, 0 refused; with 64 bytes less each table refuses an operation (`results/review/r13_minbuf.csv`).

Build (everything under `build/review_bench/`; same flags as `scripts/build.sh`, `-std=c++14 -O2 -Wall -Wextra`; METIS-X is the unmodified commit `7b3dacf`, extracted with `git archive` from `/home/adhyan/Desktop/Compiler` because `third_party/` is not in this checkout; parallel-hashmap was not needed):
```
mkdir -p build/review_bench/traces build/review_bench/third_party/metis
git -C /home/adhyan/Desktop/Compiler archive 7b3dacfa5405ec3e6a03b718f485b473d779123d include | tar -x -C build/review_bench/third_party/metis
for f in workloads/traces/*.trace.gz; do b=$(basename $f .trace.gz); case $b in chibicc_*) continue;; esac; gunzip -c $f > build/review_bench/traces/$b.trace; done
g++ -std=c++14 -O2 -Wall -Wextra -DCDES_HAVE_METIS -Ibuild/review_bench/third_party/metis/include -o build/review_bench/bench benchmarks/bench_main.cpp
g++ -std=c++14 -O2 -Wall -Wextra -DSTRATA_TEST_HOOKS -o build/review_bench/budget benchmarks/budget_main.cpp
g++ -std=c++14 -O2 -Wall -Wextra -o build/review_bench/review_aux benchmarks/review_aux.cpp
```
(`budget_main.cpp` defines `STRATA_TEST_HOOKS` itself; the duplicate `-D` gives a harmless redefinition warning, as in `scripts/build.sh`.)

The eight traces are the stored TinyCC traces `workloads/traces/{zlib,cjson,littlefs,freertos,lua,mbedtls,tinycc,sqlite}.trace.gz` (the `chibicc_*` ones are not used); they are the same files as in the paper run `results/raw/20261013-143828-paper/`.

### 2. R13 - smallest fixed buffer (verification of the ledger)

Commands (one per trace, pinned to cpu 4; not timed): 
```
cd build/review_bench
for t in zlib cjson littlefs freertos lua mbedtls tinycc sqlite; do taskset -c 4 ./budget --mode r13 --trace traces/$t.trace --name $t --out ../../results/review/r13_minbuf.csv; done
python3 theory/verify/space_model.py          # prints the ledger prediction next to the paper run's budget.csv
```
Method: bisection to 64-byte resolution of the smallest caller-provided buffer with which the whole trace (a new table per translation unit, all 8 traces' units) replays without a single refused operation. Raw data: `results/review/r13_minbuf.csv` (also peak words used, wrong results, refusals at min-64). Derived: `results/review/r13_savings.csv`. Saving = (baseline - STRATA) / baseline.

##### Smallest fixed buffer (bytes, 64-byte bisection)

| trace | STRATA | STRATA raw | C0 (hash word) | C1 (no hash word) | saving vs C0 | saving vs C1 | C1 vs C0 | raw-name STRATA vs C1 |
|---|---|---|---|---|---|---|---|---|
| zlib | 16128 | 17088 | 19328 | 17024 | 16.56% | 5.26% | 11.92% | -0.38% |
| cjson | 30720 | 32512 | 36736 | 32512 | 16.38% | 5.51% | 11.50% | 0.00% |
| littlefs | 20480 | 22016 | 24832 | 21952 | 17.53% | 6.71% | 11.60% | -0.29% |
| freertos | 45056 | 48896 | 54912 | 48896 | 17.95% | 7.85% | 10.96% | 0.00% |
| lua | 36800 | 39040 | 44480 | 39040 | 17.27% | 5.74% | 12.23% | 0.00% |
| mbedtls | 81920 | 90048 | 99200 | 90048 | 17.42% | 9.03% | 9.23% | 0.00% |
| tinycc | 160256 | 172352 | 194304 | 172288 | 17.52% | 6.98% | 11.33% | -0.04% |
| sqlite | 143744 | 156544 | 173504 | 156480 | 17.15% | 8.14% | 9.81% | -0.04% |

saving_vs_c0_pct: min 16.38, median 17.34, max 17.95; pooled (sum of bytes) 17.33

saving_vs_c1_pct: min 5.26, median 6.84, max 9.03; pooled (sum of bytes) 7.46

c1_vs_c0_pct: min 9.23, median 11.41, max 12.23; pooled (sum of bytes) 10.67


Ledger check (`theory/verify/space_model.py`, columns `arena_chain`, `chain_nohash`): predicted C0 = 19328, 36736, 24832, 54912, 44480, 99200, 194304, 173504 and predicted C1 = 17024, 32512, 21952, 48896, 39040, 90048, 172288, 156480 bytes (zlib ... sqlite). The measured values above are identical in all 16 cases, i.e. the ledger is "exact to 64 bytes" (in fact exact). (The script itself also reports `model==measured` for C0, raw and packed STRATA on all 8 traces against the paper run's `budget.csv`.)

Honest reading: against the conventional baseline WITHOUT the stored hash the saving is 5.3-9.0 %, not 16.4-17.9 %. The larger figure is a comparison with a table that spends one word per declaration on a cached hash. Whether a conventional table stores the hash is a design choice, and C1 is a legitimate baseline. Unlike C0, C1 pays for the saved memory with time (section 5).

### 3. Layout/state accounting for R14: what counts as "buffer"

From `include/strata/strata.hpp`, `benchmarks/baselines/arena_chain*.hpp`, and `results/review/control_struct_sizes.txt`:

* **Buffer (counted in the minimum):** every word of the single caller-supplied block: for STRATA the index slots, identifier records (name + meta + value) and the undo/scope stack; for the arena tables the bucket heads, the entry stack and the scope marks. `peak_used_bytes` (`budget.csv` column `peak_used_bytes_at_min`) is the high-water mark of the words in use; the minimum buffer is that value rounded up to the 64-byte bisection step (it equals it, within 64 bytes, in all rows).
* **Not counted (external, outside the buffer):** the control struct (`sizeof(strata::Table)` = 144 bytes; `arena_chain::Table` and `arena_chain_nohash::Table` = 48 bytes each); the stack temporaries of one operation (STRATA `strata::Key` = 268 bytes; the arena tables' `uint32_t key[64]` = 256 bytes); one process-wide 256-byte character-code table in STRATA (`detail::code_table()`, static, shared by all tables). The key material (the caller-supplied 64-bit key in keyed mode) is in the control struct's `Options`. No scratch space is used outside the buffer. In **fixed mode no heap allocation is made** (only the caller's buffer is touched; the growable mode calls the allocator and is not part of this experiment). The trace data, names and the reference model of the benchmark are the harness's, not the table's.
* Consequently "smallest fixed buffer" compares the data bytes of the structures; a total-footprint comparison would add 144 bytes (STRATA) versus 48 bytes (arena) of control struct plus 268 versus 256 bytes of stack, i.e. a constant of about 100 bytes that does not change with the trace.

### 4. R14 - is "replay succeeds" monotone in the buffer capacity?

Command (per trace; the 5 small traces ran sequentially on cpu 6, tinycc and sqlite on cpus 8 and 10 in parallel - the scan is not timed - and their outputs were concatenated into one file):
```
cd build/review_bench
taskset -c 6 ./budget --mode scan --trace traces/$t.trace --name $t --out ../../results/review/r14_scan.csv --detail ../../results/review/r14_scan_detail.csv
```
Method (`mode_scan` in `benchmarks/budget_main.cpp`): for each of the four tables, first bisect the minimum m, then replay the whole trace at (a) **every capacity from 64 B to 2m at 64-byte resolution**, (b) **every 4 bytes** (the word size; the tables use `bytes/4` words, so this is every distinct capacity) from m-2048 to m+2048, and (c) every 4 KiB from 2m to 8m. "Success" = no refused operation anywhere in the whole trace (all translation units). At every success all lookup results and declaration statuses were compared to the reference model. The buffer was **not** cleared between replays (it holds the garbage of the previous replay), so the result also shows independence from initial contents. Raw per-capacity outcomes: `results/review/r14_scan_detail.csv` (57 645+24 722+26 976 rows). Non-monotone point = a failure at a capacity larger than the smallest success.

| trace | table | bisected min (B) | capacities tested | successes | failures | non-monotone points | wrong results at successes |
|---|---|---|---|---|---|---|---|
| zlib | strata_packed | 16128 | 1553 | 790 | 763 | 0 | 0 |
| zlib | strata_raw | 17088 | 1585 | 821 | 764 | 0 | 0 |
| zlib | arena_C0_hash | 19328 | 1658 | 855 | 803 | 0 | 0 |
| zlib | arena_C1_nohash | 17024 | 1582 | 810 | 772 | 0 | 0 |
| cjson | strata_packed | 30720 | 2031 | 1044 | 987 | 0 | 0 |
| cjson | strata_raw | 32512 | 2089 | 1072 | 1017 | 0 | 0 |
| cjson | arena_C0_hash | 36736 | 2227 | 1142 | 1085 | 0 | 0 |
| cjson | arena_C1_nohash | 32512 | 2089 | 1081 | 1008 | 0 | 0 |
| littlefs | strata_packed | 20480 | 1696 | 868 | 828 | 0 | 0 |
| littlefs | strata_raw | 22016 | 1746 | 905 | 841 | 0 | 0 |
| littlefs | arena_C0_hash | 24832 | 1838 | 939 | 899 | 0 | 0 |
| littlefs | arena_C1_nohash | 21952 | 1744 | 902 | 842 | 0 | 0 |
| freertos | strata_packed | 45056 | 2500 | 1297 | 1203 | 0 | 0 |
| freertos | strata_raw | 48896 | 2625 | 1350 | 1275 | 0 | 0 |
| freertos | arena_C0_hash | 54912 | 2822 | 1456 | 1366 | 0 | 0 |
| freertos | arena_C1_nohash | 48896 | 2625 | 1354 | 1271 | 0 | 0 |
| lua | strata_packed | 36800 | 2229 | 1149 | 1080 | 0 | 0 |
| lua | strata_raw | 39040 | 2303 | 1188 | 1115 | 0 | 0 |
| lua | arena_C0_hash | 44480 | 2481 | 1278 | 1203 | 0 | 0 |
| lua | arena_C1_nohash | 39040 | 2303 | 1190 | 1113 | 0 | 0 |
| mbedtls | strata_packed | 81920 | 3706 | 1915 | 1791 | 0 | 0 |
| mbedtls | strata_raw | 90048 | 3971 | 2058 | 1913 | 0 | 0 |
| mbedtls | arena_C0_hash | 99200 | 4271 | 2219 | 2052 | 0 | 0 |
| mbedtls | arena_C1_nohash | 90048 | 3971 | 2064 | 1907 | 0 | 0 |
| tinycc | strata_packed | 160256 | 6268 | 3262 | 3006 | 0 | 0 |
| tinycc | strata_raw | 172352 | 6664 | 3470 | 3194 | 0 | 0 |
| tinycc | arena_C0_hash | 194304 | 7382 | 3835 | 3547 | 0 | 0 |
| tinycc | arena_C1_nohash | 172288 | 6662 | 3464 | 3198 | 0 | 0 |
| sqlite | strata_packed | 143744 | 5728 | 2976 | 2752 | 0 | 0 |
| sqlite | strata_raw | 156544 | 6147 | 3197 | 2950 | 0 | 0 |
| sqlite | arena_C0_hash | 173504 | 6702 | 3492 | 3210 | 0 | 0 |
| sqlite | arena_C1_nohash | 156480 | 6145 | 3190 | 2955 | 0 | 0 |

Result: **0 non-monotone points and 0 wrong results in all 32 trace x table combinations (about 120 000 capacities)**. All 8 traces were scanned (the request was at least 3). The threshold is sharp and at the word level: the smallest successful capacity equals the table's peak words in use and the capacity 4 bytes below it fails (columns `first_success_bytes`, `last_failure_bytes` in `r14_scan.csv`). Reason (from the code): in fixed mode the layout and every accept/refuse decision are a deterministic function of the operation sequence and of the number of words that would be needed, not of the capacity, so the success predicate is "capacity >= peak words", which is monotone. This was tested only in the fixed (caller-buffer) mode; the growable mode, `index_slots` bounded mode and the sparse variant are not covered, and the scan is for these 8 traces, not a proof. Bisection with 64-byte steps is therefore valid for these tables and traces.

### 5. R15/R16 - replay-time comparison in 5 independent sessions

#### 5.1 Protocol

Command (the same for every session; `scripts/review_sessions.sh 5 300 4 31`):
```
scripts/review_sessions.sh 5 300 4 31      # SESSIONS=5, GAP=300 s, CORE=4, REPS=31
```
For each session s = 1..5 the script launches, for each of the 8 traces in a trace order rotated by s-1, a **new process**
```
taskset -c 4 ./build/review_bench/bench --trace build/review_bench/traces/$t.trace --name $t --reps 31 --rot $((s-1)) \
      --impls strata,strata_keyed,arena_chain,arena_nohash,metis_x --summary results/review/sessions/s$s/summary.csv --raw results/review/sessions/s$s/replays.csv
```
and sleeps 300 s before the next session (start times in 6.4: sessions began 19:30:23, 19:35:35, 19:40:47, 19:46:00, 19:51:13 UTC on 2026-10-26, i.e. about 5 min 12 s apart; each session itself took 9-13 s). **31 measured rounds + 2 warm-up as in the existing protocol (no reduction was needed)**: a session is short because the 5 tables are fast on these traces. In each round every table replays the whole trace once (one timed interval per replay, table construction and destruction included), the start table rotates from round to round, and `--rot` additionally shifts the rotation by s-1 so that the table that starts the first round differs between sessions; STRATA ids: `strata` = STRATA default, `strata_keyed` = STRATA with HalfSipHash-1-3 keyed hash, `arena_chain` = C0, `arena_nohash` = C1, `metis_x` = METIS-X. Raw paired rounds: `results/review/sessions/s{1..5}/replays.csv` (trace, impl, round, replay_ns), summaries `summary.csv`, environment per session `context.txt`.

Analysis: `python3 scripts/review_analyze.py results/review > results/review/analysis_tables.md`
(outputs `analysis_per_session.csv`, `analysis_pooled.csv`, `analysis.json`, `r13_savings.csv`, `p95_latency.csv`).

* Statistic: the ratio num/den of the two replay times in the SAME round (paired). Ratio < 1: the first table is faster. Per session: the median of the 31 ratios with a 95 % percentile bootstrap CI (10 000 resamples of rounds, seed fixed in the script). "Difference established" = 95 % CI excludes 1.
* **TOST** equivalence: margin = ratio in [0.90, 1.10] (+-10 %, a stated practical margin, not derived from the data); a pair is "equivalent" if the **90 %** CI lies completely inside the margin (equivalent to two one-sided tests at alpha = 0.05); "outside margin" if the 90 % CI lies completely beyond one bound; otherwise "inconclusive".
* Between-session variability: the min-max of the five per-session medians, SD and DerSimonian-Laird I^2 of them (`analysis_pooled.csv` columns `session_median_min/max`, `between_session_sd_pct`, `I2_pct`).
* **Pooled analysis**: three intervals for the pooled median of log ratio: (t) Student-t interval over the five session medians (df = 4, session = unit of replication; this contains between-session variability; **the verdicts in the tables below use this one**), (boot2) two-level bootstrap (resample sessions, then rounds within sessions), and (rounds) a plain bootstrap of all 155 pooled pairs ignoring sessions (too narrow, kept only to show the difference; in `analysis_pooled.csv`). With only five sessions the t interval is wide-tailed by construction; it is the conservative choice.

The cell format in the tables is `median ratio [95% CI]` for sessions 1 to 5 in order. "pooled median" is the median of all 155 paired ratios; "t-CI95 over sessions" is the 95 % t-interval of the mean of the session log medians (so it is not centred on the pooled median).


##### STRATA / arena C0 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.095 [1.092, 1.107]; 1.127 [1.116, 1.134]; 1.116 [1.109, 1.129]; 1.101 [1.098, 1.107]; 1.126 [1.108, 1.132] | 1.095-1.127 | 1.110 | [1.095, 1.131] | established | [1.099, 1.127] | inconclusive | established / outside margin |
| cjson | 1.142 [1.128, 1.148]; 1.171 [1.168, 1.176]; 1.152 [1.138, 1.163]; 1.169 [1.159, 1.176]; 1.158 [1.152, 1.167] | 1.142-1.171 | 1.158 | [1.143, 1.174] | established | [1.147, 1.170] | outside margin | established / outside margin |
| littlefs | 1.204 [1.193, 1.217]; 1.218 [1.210, 1.228]; 1.204 [1.183, 1.218]; 1.198 [1.186, 1.207]; 1.193 [1.181, 1.198] | 1.193-1.218 | 1.204 | [1.192, 1.215] | established | [1.195, 1.212] | outside margin | established / outside margin |
| freertos | 1.199 [1.184, 1.202]; 1.196 [1.192, 1.200]; 1.168 [1.152, 1.175]; 1.195 [1.193, 1.197]; 1.185 [1.177, 1.191] | 1.168-1.199 | 1.192 | [1.173, 1.204] | established | [1.177, 1.200] | outside margin | established / outside margin |
| lua | 1.161 [1.159, 1.167]; 1.157 [1.156, 1.159]; 1.188 [1.183, 1.199]; 1.189 [1.188, 1.194]; 1.175 [1.166, 1.183] | 1.157-1.189 | 1.176 | [1.156, 1.193] | established | [1.160, 1.188] | outside margin | established / outside margin |
| mbedtls | 1.160 [1.152, 1.169]; 1.168 [1.164, 1.182]; 1.168 [1.138, 1.187]; 1.168 [1.160, 1.182]; 1.165 [1.159, 1.172] | 1.160-1.168 | 1.166 | [1.161, 1.170] | established | [1.162, 1.169] | outside margin | established / outside margin |
| tinycc | 1.204 [1.200, 1.215]; 1.149 [1.145, 1.156]; 1.190 [1.184, 1.197]; 1.180 [1.177, 1.187]; 1.226 [1.208, 1.237] | 1.149-1.226 | 1.191 | [1.154, 1.226] | established | [1.162, 1.217] | outside margin | established / outside margin |
| sqlite | 1.144 [1.141, 1.148]; 1.058 [1.057, 1.060]; 1.083 [1.082, 1.089]; 1.067 [1.064, 1.070]; 1.098 [1.093, 1.103] | 1.058-1.144 | 1.084 | [1.049, 1.132] | established | [1.058, 1.122] | inconclusive | established / inconclusive |

Geometric mean over the 8 traces of the pooled median ratio: 1.159.  t-verdict counts: faster-established 0, slower-established 8, not established 0; TOST equivalent 0, outside margin 6, inconclusive 2.

##### STRATA / arena C1 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 0.996 [0.985, 1.000]; 1.007 [1.001, 1.018]; 0.996 [0.989, 1.003]; 0.987 [0.980, 0.998]; 0.974 [0.971, 0.983] | 0.974-1.007 | 0.995 | [0.976, 1.007] | not established | [0.980, 1.004] | equivalent | not established / equivalent |
| cjson | 1.043 [1.027, 1.050]; 1.045 [1.044, 1.052]; 1.047 [1.042, 1.054]; 1.043 [1.037, 1.053]; 1.036 [1.025, 1.041] | 1.036-1.047 | 1.043 | [1.038, 1.048] | established | [1.039, 1.047] | equivalent | established / equivalent |
| littlefs | 1.110 [1.105, 1.126]; 1.085 [1.083, 1.096]; 1.116 [1.105, 1.134]; 1.116 [1.112, 1.122]; 1.103 [1.096, 1.130] | 1.085-1.116 | 1.108 | [1.090, 1.122] | established | [1.094, 1.119] | inconclusive | established / inconclusive |
| freertos | 1.083 [1.074, 1.089]; 1.076 [1.074, 1.079]; 1.069 [1.061, 1.080]; 1.056 [1.053, 1.061]; 1.077 [1.068, 1.082] | 1.056-1.083 | 1.072 | [1.059, 1.085] | established | [1.062, 1.082] | equivalent | established / equivalent |
| lua | 1.065 [1.057, 1.068]; 1.047 [1.046, 1.049]; 1.075 [1.067, 1.086]; 1.073 [1.071, 1.079]; 1.069 [1.066, 1.075] | 1.047-1.075 | 1.068 | [1.052, 1.080] | established | [1.055, 1.077] | equivalent | established / equivalent |
| mbedtls | 1.044 [1.039, 1.050]; 1.047 [1.029, 1.071]; 1.051 [1.029, 1.059]; 1.034 [1.024, 1.051]; 1.053 [1.049, 1.057] | 1.034-1.053 | 1.047 | [1.037, 1.055] | established | [1.039, 1.053] | equivalent | established / equivalent |
| tinycc | 1.148 [1.139, 1.154]; 1.110 [1.101, 1.114]; 1.129 [1.127, 1.134]; 1.132 [1.125, 1.137]; 1.138 [1.128, 1.145] | 1.110-1.148 | 1.131 | [1.114, 1.149] | established | [1.118, 1.145] | outside margin | established / outside margin |
| sqlite | 0.982 [0.980, 0.984]; 1.040 [1.038, 1.041]; 1.039 [1.037, 1.046]; 1.030 [1.028, 1.035]; 1.043 [1.037, 1.048] | 0.982-1.043 | 1.037 | [0.995, 1.060] | not established | [1.002, 1.052] | equivalent | not established / equivalent |

Geometric mean over the 8 traces of the pooled median ratio: 1.062.  t-verdict counts: faster-established 0, slower-established 6, not established 2; TOST equivalent 6, outside margin 1, inconclusive 1.

##### arena C1 / arena C0 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.104 [1.096, 1.113]; 1.117 [1.112, 1.120]; 1.123 [1.119, 1.128]; 1.112 [1.109, 1.127]; 1.145 [1.141, 1.153] | 1.104-1.145 | 1.120 | [1.102, 1.139] | established | [1.106, 1.135] | outside margin | established / outside margin |
| cjson | 1.102 [1.091, 1.109]; 1.117 [1.111, 1.123]; 1.099 [1.092, 1.104]; 1.115 [1.111, 1.123]; 1.122 [1.114, 1.132] | 1.099-1.122 | 1.111 | [1.099, 1.123] | established | [1.102, 1.120] | outside margin | established / outside margin |
| littlefs | 1.083 [1.068, 1.092]; 1.124 [1.117, 1.126]; 1.081 [1.065, 1.092]; 1.075 [1.071, 1.080]; 1.072 [1.056, 1.085] | 1.072-1.124 | 1.084 | [1.061, 1.113] | established | [1.067, 1.107] | inconclusive | established / inconclusive |
| freertos | 1.112 [1.101, 1.116]; 1.110 [1.107, 1.114]; 1.085 [1.077, 1.103]; 1.130 [1.126, 1.135]; 1.098 [1.090, 1.105] | 1.085-1.130 | 1.110 | [1.086, 1.128] | established | [1.091, 1.123] | inconclusive | established / inconclusive |
| lua | 1.097 [1.090, 1.099]; 1.103 [1.100, 1.106]; 1.103 [1.100, 1.113]; 1.107 [1.104, 1.109]; 1.096 [1.093, 1.099] | 1.096-1.107 | 1.102 | [1.095, 1.107] | established | [1.097, 1.106] | inconclusive | established / inconclusive |
| mbedtls | 1.114 [1.107, 1.118]; 1.109 [1.102, 1.118]; 1.110 [1.087, 1.114]; 1.121 [1.120, 1.129]; 1.107 [1.105, 1.111] | 1.107-1.121 | 1.112 | [1.105, 1.119] | established | [1.107, 1.118] | outside margin | established / outside margin |
| tinycc | 1.056 [1.046, 1.066]; 1.037 [1.031, 1.052]; 1.050 [1.040, 1.063]; 1.042 [1.040, 1.054]; 1.077 [1.076, 1.088] | 1.037-1.077 | 1.053 | [1.033, 1.072] | established | [1.038, 1.068] | equivalent | established / equivalent |
| sqlite | 1.165 [1.164, 1.168]; 1.017 [1.016, 1.019]; 1.044 [1.042, 1.046]; 1.034 [1.033, 1.036]; 1.052 [1.049, 1.058] | 1.017-1.165 | 1.044 | [0.993, 1.134] | not established | [1.008, 1.117] | inconclusive | established / inconclusive |

Geometric mean over the 8 traces of the pooled median ratio: 1.092.  t-verdict counts: faster-established 0, slower-established 7, not established 1; TOST equivalent 1, outside margin 3, inconclusive 4.

##### STRATA / METIS-X (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 0.767 [0.757, 0.770]; 0.766 [0.762, 0.772]; 0.775 [0.771, 0.777]; 0.767 [0.763, 0.772]; 0.767 [0.763, 0.769] | 0.766-0.775 | 0.769 | [0.764, 0.773] | established | [0.765, 0.772] | outside margin | established / outside margin |
| cjson | 0.823 [0.816, 0.829]; 0.832 [0.828, 0.835]; 0.828 [0.821, 0.832]; 0.827 [0.819, 0.832]; 0.827 [0.823, 0.835] | 0.823-0.832 | 0.828 | [0.823, 0.831] | established | [0.824, 0.830] | outside margin | established / outside margin |
| littlefs | 0.810 [0.803, 0.822]; 0.833 [0.826, 0.840]; 0.820 [0.807, 0.832]; 0.829 [0.822, 0.836]; 0.829 [0.821, 0.836] | 0.810-0.833 | 0.825 | [0.812, 0.836] | established | [0.815, 0.833] | outside margin | established / outside margin |
| freertos | 0.707 [0.704, 0.711]; 0.705 [0.702, 0.707]; 0.708 [0.705, 0.716]; 0.709 [0.707, 0.711]; 0.712 [0.709, 0.715] | 0.705-0.712 | 0.708 | [0.705, 0.712] | established | [0.706, 0.711] | outside margin | established / outside margin |
| lua | 0.762 [0.757, 0.764]; 0.757 [0.755, 0.758]; 0.760 [0.757, 0.764]; 0.755 [0.753, 0.757]; 0.757 [0.755, 0.759] | 0.755-0.762 | 0.757 | [0.755, 0.762] | established | [0.756, 0.761] | outside margin | established / outside margin |
| mbedtls | 0.693 [0.686, 0.701]; 0.689 [0.679, 0.693]; 0.692 [0.683, 0.697]; 0.689 [0.681, 0.694]; 0.692 [0.690, 0.695] | 0.689-0.693 | 0.692 | [0.689, 0.693] | established | [0.689, 0.693] | outside margin | established / outside margin |
| tinycc | 0.902 [0.897, 0.906]; 0.904 [0.900, 0.906]; 0.908 [0.904, 0.910]; 0.904 [0.901, 0.909]; 0.898 [0.891, 0.904] | 0.898-0.908 | 0.904 | [0.899, 0.908] | established | [0.900, 0.907] | inconclusive | established / equivalent |
| sqlite | 0.932 [0.929, 0.935]; 0.931 [0.929, 0.933]; 0.929 [0.927, 0.933]; 0.930 [0.926, 0.930]; 0.929 [0.926, 0.931] | 0.929-0.932 | 0.930 | [0.928, 0.932] | established | [0.929, 0.932] | equivalent | established / equivalent |

Geometric mean over the 8 traces of the pooled median ratio: 0.798.  t-verdict counts: faster-established 8, slower-established 0, not established 0; TOST equivalent 1, outside margin 6, inconclusive 1.

##### STRATA keyed / STRATA (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.278 [1.269, 1.292]; 1.275 [1.267, 1.280]; 1.314 [1.308, 1.318]; 1.276 [1.264, 1.281]; 1.280 [1.267, 1.292] | 1.275-1.314 | 1.284 | [1.264, 1.305] | established | [1.269, 1.300] | outside margin | established / outside margin |
| cjson | 1.236 [1.222, 1.259]; 1.239 [1.236, 1.245]; 1.237 [1.232, 1.245]; 1.240 [1.226, 1.250]; 1.244 [1.234, 1.260] | 1.236-1.244 | 1.238 | [1.235, 1.243] | established | [1.236, 1.242] | outside margin | established / outside margin |
| littlefs | 1.299 [1.280, 1.308]; 1.272 [1.263, 1.281]; 1.287 [1.260, 1.305]; 1.284 [1.276, 1.294]; 1.288 [1.275, 1.306] | 1.272-1.299 | 1.284 | [1.274, 1.298] | established | [1.276, 1.295] | outside margin | established / outside margin |
| freertos | 1.234 [1.230, 1.243]; 1.237 [1.231, 1.240]; 1.243 [1.236, 1.254]; 1.238 [1.237, 1.241]; 1.233 [1.230, 1.237] | 1.233-1.243 | 1.237 | [1.232, 1.242] | established | [1.233, 1.241] | outside margin | established / outside margin |
| lua | 1.212 [1.207, 1.219]; 1.210 [1.206, 1.212]; 1.208 [1.204, 1.213]; 1.212 [1.210, 1.214]; 1.214 [1.210, 1.218] | 1.208-1.214 | 1.211 | [1.209, 1.214] | established | [1.209, 1.213] | outside margin | established / outside margin |
| mbedtls | 1.245 [1.237, 1.257]; 1.241 [1.232, 1.248]; 1.243 [1.224, 1.263]; 1.244 [1.224, 1.248]; 1.242 [1.235, 1.253] | 1.241-1.245 | 1.243 | [1.241, 1.245] | established | [1.241, 1.244] | outside margin | established / outside margin |
| tinycc | 1.202 [1.194, 1.209]; 1.203 [1.200, 1.206]; 1.203 [1.198, 1.205]; 1.208 [1.196, 1.210]; 1.214 [1.207, 1.227] | 1.202-1.214 | 1.204 | [1.200, 1.212] | established | [1.201, 1.211] | outside margin | established / outside margin |
| sqlite | 1.225 [1.220, 1.229]; 1.223 [1.221, 1.225]; 1.222 [1.218, 1.225]; 1.223 [1.216, 1.226]; 1.224 [1.219, 1.227] | 1.222-1.225 | 1.224 | [1.222, 1.225] | established | [1.222, 1.224] | outside margin | established / outside margin |

Geometric mean over the 8 traces of the pooled median ratio: 1.240.  t-verdict counts: faster-established 0, slower-established 8, not established 0; TOST equivalent 0, outside margin 8, inconclusive 0.


#### 5.2 Median replay times per session (ms)

The absolute medians differ a lot between sessions (e.g. mbedtls STRATA 23.2 to 34.9 ms), so only paired ratios within a session are interpreted. 

##### Median replay time per session (ms)

| trace | session | strata | strata_keyed | arena_chain | arena_nohash | metis_x |
|---|---|---|---|---|---|---|
| zlib | 1 | 1.110 | 1.420 | 1.017 | 1.124 | 1.462 |
| zlib | 2 | 1.395 | 1.781 | 1.244 | 1.383 | 1.823 |
| zlib | 3 | 1.395 | 1.830 | 1.251 | 1.401 | 1.804 |
| zlib | 4 | 1.412 | 1.793 | 1.275 | 1.424 | 1.834 |
| zlib | 5 | 1.094 | 1.403 | 0.978 | 1.122 | 1.430 |
| cjson | 1 | 0.418 | 0.520 | 0.367 | 0.404 | 0.505 |
| cjson | 2 | 0.591 | 0.732 | 0.508 | 0.566 | 0.712 |
| cjson | 3 | 0.560 | 0.691 | 0.482 | 0.534 | 0.673 |
| cjson | 4 | 0.651 | 0.800 | 0.554 | 0.620 | 0.782 |
| cjson | 5 | 0.412 | 0.512 | 0.354 | 0.397 | 0.496 |
| littlefs | 1 | 0.435 | 0.560 | 0.362 | 0.391 | 0.536 |
| littlefs | 2 | 0.589 | 0.749 | 0.482 | 0.540 | 0.705 |
| littlefs | 3 | 0.442 | 0.565 | 0.363 | 0.391 | 0.533 |
| littlefs | 4 | 0.660 | 0.848 | 0.549 | 0.590 | 0.793 |
| littlefs | 5 | 0.435 | 0.562 | 0.367 | 0.391 | 0.525 |
| freertos | 1 | 0.880 | 1.086 | 0.735 | 0.813 | 1.246 |
| freertos | 2 | 1.237 | 1.530 | 1.033 | 1.148 | 1.754 |
| freertos | 3 | 0.885 | 1.100 | 0.754 | 0.827 | 1.250 |
| freertos | 4 | 1.027 | 1.274 | 0.861 | 0.974 | 1.451 |
| freertos | 5 | 0.867 | 1.074 | 0.736 | 0.805 | 1.220 |
| lua | 1 | 4.213 | 5.112 | 3.623 | 3.959 | 5.529 |
| lua | 2 | 5.296 | 6.407 | 4.579 | 5.050 | 6.984 |
| lua | 3 | 4.271 | 5.164 | 3.600 | 3.963 | 5.628 |
| lua | 4 | 5.912 | 7.155 | 4.965 | 5.513 | 7.827 |
| lua | 5 | 4.185 | 5.080 | 3.554 | 3.898 | 5.510 |
| mbedtls | 1 | 31.682 | 39.844 | 27.471 | 30.102 | 46.152 |
| mbedtls | 2 | 31.088 | 38.762 | 26.706 | 29.383 | 45.012 |
| mbedtls | 3 | 33.971 | 41.289 | 28.962 | 32.235 | 47.866 |
| mbedtls | 4 | 34.920 | 43.613 | 29.493 | 33.294 | 50.259 |
| mbedtls | 5 | 23.228 | 29.051 | 19.899 | 22.048 | 33.537 |
| tinycc | 1 | 2.969 | 3.578 | 2.443 | 2.594 | 3.345 |
| tinycc | 2 | 2.319 | 2.796 | 2.005 | 2.100 | 2.583 |
| tinycc | 3 | 2.598 | 3.118 | 2.202 | 2.296 | 2.873 |
| tinycc | 4 | 2.439 | 2.931 | 2.055 | 2.162 | 2.694 |
| tinycc | 5 | 1.855 | 2.250 | 1.516 | 1.633 | 2.063 |
| sqlite | 1 | 7.133 | 8.703 | 6.224 | 7.262 | 7.637 |
| sqlite | 2 | 6.210 | 7.588 | 5.857 | 5.966 | 6.654 |
| sqlite | 3 | 7.659 | 9.328 | 7.011 | 7.325 | 8.271 |
| sqlite | 4 | 6.692 | 8.212 | 6.285 | 6.503 | 7.208 |
| sqlite | 5 | 4.973 | 6.096 | 4.537 | 4.768 | 5.374 |


#### 5.3 What the timing results say

* STRATA vs C0 (stored hash): STRATA is slower on every trace, ratio 1.08-1.20 (pooled medians 1.110, 1.158, 1.204, 1.192, 1.176, 1.166, 1.191, 1.084), all 8 differences established; geometric mean 1.159. Equivalence within +-10 % holds on none (6 outside the margin, zlib and sqlite inconclusive).
* STRATA vs C1 (real no-hash table): ratio 0.995-1.131, geometric mean 1.062. Slower by an established amount on 6 traces, not established on zlib and sqlite. TOST equivalence within +-10 % on zlib, cjson, freertos, lua, mbedtls, sqlite; inconclusive on littlefs; outside the margin (slower) on tinycc (1.131). Thus the time gap to the arena table shrinks from about 16 % to about 6 % when the stored hash is removed from the baseline, because C1 itself is about 9 % slower than C0 (geometric mean 1.092; 7 of 8 established; C1 is not equivalent to C0 within +-10 % on 3 traces, inconclusive on 4, equivalent on tinycc).
* STRATA vs METIS-X: ratio 0.69-0.93 (STRATA faster, all 8 established); equivalence only on sqlite (0.930), tinycc inconclusive. Keyed STRATA vs unkeyed: 1.20-1.28, all established and outside the margin.
* Between-session variability: SD of the session-median ratios is below 1.3 % for METIS-X and keyed comparisons and 1-4 % for the arena comparisons, with large outliers on sqlite (STRATA/C0 session medians 1.058-1.144; C1/C0 1.017-1.165; STRATA/C1 0.982-1.043) and tinycc (STRATA/C0 1.149-1.226). The cause was not isolated; CPU frequency state (6.3) is a plausible but untested candidate. Heterogeneity is also visible in `I2_pct` (up to 95 % for zlib keyed/unkeyed, because the within-session CIs are very narrow). Verdicts with the 'not established' label (STRATA vs C1 on zlib and sqlite; C1 vs C0 on sqlite) are exactly the ones where session heterogeneity matters.
* Compared with the paper: the paper's verdicts of "STRATA slower than the arena table, faster than METIS-X" are reproduced. New with C1: the speed gap to a hash-less arena table is smaller and on zlib/sqlite not established.

#### 5.4 p95 per-operation latency (secondary)

Median over the five sessions of the lookup p95 in ns (min-max over sessions in brackets). Sampling: `run_impl` in `bench_main.cpp` replays the trace three times with an `rdtscp` read before and after every single operation; samples of one operation kind are collected over **the whole trace, all translation units pooled** (the table is rebuilt at each `U` record but the sample vector is not reset), the p95 is `nth_element` at index floor(0.95 (n-1)) of the whole vector, the timer overhead (median of 4001 back-to-back `rdtscp` pairs, about 13 ns) is subtracted and the median of the three replays' p95 is stored. No per-unit aggregation is done. These values are within a few times the timer overhead and its tick (0.34 ns) and are meaningful only for comparing tables; `p95_latency.csv` has declare/enter/exit as well.

| trace | STRATA | arena C0 | arena C1 | METIS-X | STRATA keyed |
|---|---|---|---|---|---|
| zlib | 41.1 (32.2-43.9) | 39.1 (30.2-41.1) | 41.8 (32.2-42.5) | 38.4 (29.5-39.1) | 49.3 (37.7-52.1) |
| cjson | 46.6 (37.0-54.1) | 42.5 (34.3-49.3) | 43.9 (35.0-50.7) | 43.9 (34.3-50.0) | 54.1 (43.9-63.0) |
| littlefs | 38.4 (37.0-57.6) | 33.6 (32.2-50.0) | 32.9 (32.2-48.0) | 33.6 (33.6-51.4) | 45.2 (43.9-67.8) |
| freertos | 41.1 (39.7-56.9) | 37.0 (36.3-51.4) | 38.4 (37.7-53.5) | 39.1 (38.4-55.5) | 48.7 (48.0-67.2) |
| lua | 37.0 (36.3-48.7) | 35.6 (34.3-44.5) | 37.7 (35.6-45.9) | 35.6 (34.3-43.2) | 42.5 (41.8-55.5) |
| mbedtls | 49.3 (41.8-63.7) | 47.3 (40.4-64.4) | 47.3 (40.4-63.7) | 47.3 (42.5-65.8) | 61.7 (51.4-74.7) |
| tinycc | 48.0 (37.7-54.1) | 41.1 (33.6-49.3) | 42.5 (31.5-47.3) | 46.6 (35.0-52.8) | 55.5 (43.9-62.4) |
| sqlite | 48.7 (36.3-57.6) | 50.7 (35.6-66.5) | 50.0 (35.6-56.9) | 52.1 (37.0-58.3) | 58.9 (43.2-71.3) |

### 6. Measurement description and environment

#### 6.1 Timer, batching, overhead
* **Replay time:** `std::chrono::steady_clock` (libstdc++: `clock_gettime(CLOCK_MONOTONIC)`, resolution 1 ns per `clock_getres`), one interval per whole-trace replay, **no batching** of replays inside an interval; table construction and destruction are inside the interval. Replay times are 0.35 ms to 50 ms, so the timer overhead (20 ns) is below 0.01 % of every interval and was not subtracted.
* **Empty-timer overhead** (`review_aux timer`, 200 001 samples, cpu 4, `results/review/timer_overhead.txt`): `steady_clock` pair: median 20.0 ns (min 17, p99 22); raw `clock_gettime`: median 18 ns; `rdtscp` pair: median 13.0 ns (0.3427 ns/tick, calibrated against `steady_clock` over 100 ms).
* **Per-operation latency** uses `rdtscp` with the median pair overhead subtracted (section 5.4).
* A volatile `guard`/`sink` keeps the compiler from removing lookups; the first 2 rounds are discarded as warm-up.

#### 6.2 Machine
```
uname -a: Linux adhyan-omarchy 7.2.4-arch1-2 #1 SMP PREEMPT_DYNAMIC Tue, 08 Sep 2026 10:22:31 +0000 x86_64 GNU/Linux
g++: g++ (GCC) 16.2.1 20260810
cpu:  13th Gen Intel(R) Core(TM) i7-13620H
ldd: ldd (GNU libc) 2.44
python: Python 3.14.7 numpy 2.5.2
git: c5d8eb8ae9f313001181b73ef76c54f2376714c8 branch reviewer-report-revision
metis: 7b3dacfa5405ec3e6a03b718f485b473d779123d (git archive from /home/adhyan/Desktop/Compiler)
date: 2026-10-26T19:30:29Z
CPU max MHz:                             4900.0000
CPU min MHz:                             400.0000
L1d cache:                               416 KiB (10 instances)
L2 cache:                                9.5 MiB (7 instances)
L3 cache:                                24 MiB (1 instance)
```
`uname -a`, CPU, compiler and library as above. Differences from the paper's environment: **native Linux (Arch), not WSL2**; kernel 7.2.4-arch1-2 instead of 6.18.33.2-microsoft-standard-WSL2; CPU i7-13620H (Raptor Lake, 6 P + 4 E cores, 16 threads) instead of Core Ultra 7 258V; **g++ 16.2.1 instead of 11.4.0**; glibc 2.44 instead of 2.35. The compiler change matters for absolute and possibly relative timing and for `malloc_usable_size`-based heap figures (not used here: the memory results of this document are the fixed-buffer word counts, which are compiler-independent and did reproduce the ledger and the paper run's STRATA/C0 minima).

#### 6.3 Frequency governor, pinning, other load
* cpufreq driver `intel_pstate`, **governor `powersave`** (the only intel_pstate governors are `powersave` and `performance`; I did not change it: no root), energy_performance_preference `performance`, `no_turbo = 0` (turbo allowed), cpuinfo max 4.9 GHz, min 0.4 GHz. So the frequency is NOT fixed: it ramps up under load. `scaling_cur_freq` of cpu 4 sampled at session start/end: 4.70 GHz / 0.40 GHz (s1), 0.61 / 0.40 (s2), 3.43 / 3.12 (s3), 0.62 / 3.20 (s4), 1.50 / 0.40 GHz (s5) - the end-of-session samples mostly show the idle drop after the run, but the start values show the core was not in a steady state at launch. This is a plausible, untested cause of the large differences in absolute time between sessions (up to 1.5x) and of part of the between-session ratio variability (not tested separately). Rounds inside a process interleave all tables, which is why ratios are much more stable than times.
* **Pinning:** `taskset -c 4` (logical cpu 4; its SMT sibling is cpu 5). Not isolated: no `isolcpus`, no `nohz_full`; the sibling hardware thread can be used by other processes, and was only lightly used (1.4-5.8 % busy over the sessions; the pinned cpu was 99.5-99.9 % busy).
* **Background load:** the machine is a desktop shared with a browser, a desktop session and, during preparation (not during the timing sessions), other long-running test jobs of the same project (load average 4-10 at that time). During the 5 timing sessions the coordinator ran no heavy jobs; the load average at session start was 0.40-2.54 (below); `busy_processes_start` in `context.txt` lists processes using at least 20 % of a cpu. The first list may include my own script's helper commands. This is an uncontrolled environment, not a quiet benchmark rig.

#### 6.4 Per-session context (verbatim `context.txt`)
#### Session 1
```
session: 1 of 5
start_utc: 2026-10-26T19:30:23Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 0
loadavg_start: 0.73 1.26 1.95 8/3172 419298
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 4700000
busy_processes_start (>=20% cpu, excluding this script):
 419242   4 66.6 MainThread
 419241  10 33.3 MainThread
 419243   8 33.3 MainThread
end_utc: 2026-10-26T19:30:35Z
loadavg_end: 0.85 1.27 1.95 1/3133 421475
cur_freq_khz_end: 400222
pinned_cpu4_busy_fraction_over_session: 0.997
sibling_cpu5_busy_fraction_over_session: 0.048
```
#### Session 2
```
session: 2 of 5
start_utc: 2026-10-26T19:35:35Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 1
loadavg_start: 0.45 0.82 1.56 3/3128 462901
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 606321
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:35:47Z
loadavg_end: 1.09 0.95 1.59 1/3133 464905
cur_freq_khz_end: 400350
pinned_cpu4_busy_fraction_over_session: 0.999
sibling_cpu5_busy_fraction_over_session: 0.050
```
#### Session 3
```
session: 3 of 5
start_utc: 2026-10-26T19:40:47Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 2
loadavg_start: 1.09 1.04 1.45 1/3136 508921
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 3430728
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:41:00Z
loadavg_end: 1.30 1.09 1.46 8/3127 510299
cur_freq_khz_end: 3123973
pinned_cpu4_busy_fraction_over_session: 0.998
sibling_cpu5_busy_fraction_over_session: 0.058
```
#### Session 4
```
session: 4 of 5
start_utc: 2026-10-26T19:46:00Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 3
loadavg_start: 2.54 1.51 1.49 2/3152 549770
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 621541
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:46:13Z
loadavg_end: 2.65 1.59 1.52 4/3137 551184
cur_freq_khz_end: 3200032
pinned_cpu4_busy_fraction_over_session: 0.996
sibling_cpu5_busy_fraction_over_session: 0.043
```
#### Session 5
```
session: 5 of 5
start_utc: 2026-10-26T19:51:13Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 4
loadavg_start: 0.40 0.90 1.23 2/3112 580450
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 1502325
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:51:22Z
loadavg_end: 0.57 0.92 1.24 2/3118 581325
cur_freq_khz_end: 400137
pinned_cpu4_busy_fraction_over_session: 0.995
sibling_cpu5_busy_fraction_over_session: 0.014
```

### 7. Limitations (additional to the paper's)
* 5 sessions within about 25 minutes of one afternoon on one machine; sessions are independent processes but not days apart. The t-intervals have 4 degrees of freedom.
* The CPU frequency was not fixed (powersave governor, no root), the system was not isolated, and a different compiler than in the paper was used. The ratios, not the absolute times, are reportable.
* The TOST margin of +-10 % is a practical choice, not derived from an application requirement; with +-5 % none of the 'equivalent' labels for STRATA/C1 would survive on most traces (the 90 % CIs are 0.98-1.06).
* Replay is not compilation; hashing/compare cost differences between C0 and C1 depend on name length distribution of these 8 traces.
* Monotonicity is shown empirically for fixed mode on 8 traces; it is not a proof.
* The paper's `results/raw/20261013-143828-paper` data and manuscript were not modified by this work.

### 8. Files
`results/review/`: `r13_minbuf.csv`, `r13_savings.csv`, `r14_scan.csv`, `r14_scan_detail.csv`, `sessions/s1..s5/{replays,summary}.csv + context.txt`, `sessions_run.log`, `analysis_per_session.csv`, `analysis_pooled.csv`, `analysis.json`, `analysis_tables.md`, `p95_latency.csv`, `timer_overhead.txt`, `control_struct_sizes.txt`, `environment.txt`.

## 9. Rerunning from a clean checkout


### Requirements

* Linux on x86-64 (the benchmarks use glibc's `malloc_usable_size`, `rdtscp` and `taskset`).
  Developed under WSL 2, Ubuntu 22.04.
* `g++` with C++14 (11.4 used), `git`, `python3`, `gzip`.
* For tables and figures: Python with `pandas`, `tabulate`, `matplotlib`.
* Network access for the two baseline repositories.

The core library and its tests need only a C++14 compiler.

### Steps

```bash
git clone <this repository> cdesproject && cd cdesproject

# 1. correctness tests: -O2, then AddressSanitizer + UndefinedBehaviorSanitizer
bash scripts/test.sh

# 2. baselines (not stored in this repository)
bash scripts/fetch_third_party.sh        # METIS @ 7b3dacf, parallel-hashmap v1.4.1

# 3. everything: build, unpack traces, generate synthetic traces, run all experiments
bash scripts/run_all.sh mylabel          # REPS=31 rounds, CORE=2 by default
#    -> results/raw/<UTC timestamp>-mylabel/

# 4. tables and figures
pip install pandas tabulate matplotlib
python3 scripts/analyze.py results/raw/<run>
#    -> results/summary/<run>/tables.md, *.csv, fig_*.png, fig_*.pdf
```

Expected duration on the development machine: tests about 2 minutes, full pipeline about 45
minutes (most of it the old arena baseline). The emulated target run is separate:
`bash tools/embedded/run.sh` (needs `gcc-arm-none-eabi`, `libnewlib-arm-none-eabi`,
`libstdc++-arm-none-eabi-newlib`, `qemu-system-arm`).

Without step 2 the pipeline still runs; the METIS and Swiss-table baselines are left out
and the old-versus-new tables are not produced.

### What is stored and what is regenerated

| Artifact | Stored | Regenerated by |
|---|---|---|
| Compiler traces | `workloads/traces/*.trace.gz` (2.2 MB) | optional: `tools/tcc-trace/build_tcc.sh` then `make_traces.sh` |
| Synthetic traces | no | `scripts/gen_synthetic.py` (fixed seeds) |
| Regex traces of the earlier work | no | fetched with METIS |
| Raw measurements | `results/raw/<run>/` | `scripts/run_all.sh` |
| Tables and figures | `results/summary/<run>/` | `scripts/analyze.py` |

### Regenerating the compiler traces (optional)

```bash
bash tools/tcc-trace/build_tcc.sh ~/cdes        # clones TinyCC @ 43c7708, patches, builds
bash tools/tcc-trace/make_traces.sh ~/cdes workloads/traces-new
```

The traces depend on the system's C headers (glibc 2.35 here), because the compiler reads
them. With other headers the event counts will differ slightly; the stored traces are the
reference for the reported numbers.

### Which file backs which number

| Reported in | Comes from |
|---|---|
| peak heap, allocator calls, per-operation latency | `results/raw/<run>/{compiler,synthetic,legacy}_summary.csv` |
| replay time, intervals | `results/raw/<run>/*_replays.csv` -> `results/summary/<run>/*_replay_time.csv` |
| old versus new | `results/summary/<run>/*_old_vs_new.csv` |
| minimum buffer | `results/raw/<run>/budget.csv` -> `results/summary/<run>/budget_min_buffer.csv` |
| worst case | `results/raw/<run>/worstcase.csv` |
| environment | `results/raw/<run>/environment.txt` |

Counts and correctness results are deterministic. Memory figures depend on glibc's block
sizes; between our two runs 189 of 208 table/trace pairs had the same peak heap to within
64 bytes. Timings will not reproduce exactly: expect individual medians to move by about 5%
typically and by tens of percent occasionally.

### Runs in this repository

| Run | Code | Note |
|---|---|---|
| (the four 2026-10-11 runs below were dropped from the working tree in the cleanup; the git tag `pre-cleanup` keeps them) | | |
| `20261011-160113-full` | commit `8169bf5` | first complete run; before the `sparse_index` option existed |
| `20261011-161306-final` | commit `3aee381` | second run of the same table code (version 1) |
| `20261011-163944-v2` | commit `e511819` | version 2 of the table (fast scope exit, delayed shrinking) |
| `20261011-165103-v3` | commit `8786eac` | **the run reported in the (regenerable) `docs/RESULTS.md` and the paper**: adds `arena_chain`, 31 interleaved rounds |

The timestamps in the run names come from the clock inside WSL, which was not checked against
real time. The twelve-minute gap they suggest is too short: the first run alone took longer
than that.

### Update of 2026-10-13

The complete command-to-result map is part 7 above. On the
development machine the full pipeline (`scripts/run_all.sh`) took 8 min 48 s and
`scripts/run_extra.sh` 1 min 48 s for run `20261013-143828-paper`; the 45 minutes stated
above were measured with an earlier version. Numbers and tables of the paper are generated by
`manuscript/tools/make_numbers.py`; `scripts/make_report.py` still generates
`docs/RESULTS.md` (generated, not tracked; `python3 scripts/make_report.py <run>`) and `paper/generated.tex`, and `manuscript/tools/crosscheck.py` verifies
that the two generators agree.


## 10. Instruction counts and the attempts to make STRATA faster (2026-10-27)

Wall-clock time on the shared desktop varies with clock frequency and load, so the replay cost was also counted as
user-space instructions with the CPU's performance counters (`benchmarks/instr_count.cpp`; needs
`/proc/sys/kernel/perf_event_paranoid` <= 2). Five replays of a table on a trace differ by at most 0.03 percent.
Raw counts: `results/review/instr_counts.csv`; table: `python3 manuscript/tools/make_instr_table.py`.
These are x86-64 `g++ -O2` counts, not Thumb-2 and not times.

| Comparison (8 traces) | Instructions |
|---|---|
| STRATA vs conventional table with stored hash (C0) | 31 to 41 percent more |
| STRATA vs the table without it (C1) | 21 to 29 percent more |
| keyed vs unkeyed STRATA | 47 to 58 percent more |

Where the instructions go (per declare or lookup on Lua and SQLite): turning a name into a packed key costs about 77
instructions and hashing about 32; with prepared names (`benchmarks/prepared_count.cpp`, `strata::Table::make_key` then
`declare(const Key&, ...)` / `resolve(const Key&, ...)`, and the same for the baseline) STRATA uses 38 to 45 percent fewer
instructions and C0 about one third fewer, so the gap to C0 falls from 43-54 to 18-44 percent. A step-by-step count of
`declare` puts the rest into the capacity check with its index rebuilds (every name is hashed again because none is
stored) and the writes of record, index slot and undo entry.

Changes kept (6 to 8 percent fewer instructions, results identical, all tests rerun with `g++` and `clang`):
a compile-time character table with one validity test per packed word; a fast path in `ensure()`; a plain loop for the
short record copy. Tried and dropped: a cheaper hash step (no gain), a one-entry cache of the last lookup (hit on 17 to
28 percent of lookups, but the miss path cost as much as the hits saved), raw names (8 to 9 percent fewer instructions
but the buffer saving is lost), a larger starting buffer or a fixed index (under 0.5 percent). STRATA is still not
faster than a conventional single-buffer table.

Tests that cover this: `tests/test_review.cpp` T4 (prepared names equal plain calls in default, bounded and keyed
modes); the full suite (`bash scripts/test.sh`, and with `CXX=clang++`), the depth-9 enumeration (identical counts),
2.3 million further fuzzing executions and the mutation check (9 of 9 caught, each within 2.4 s)
(`reports/artifacts/*.log`).
