# Limitations and Threats to Validity

## What has not been shown

1. **No compiler integration.** STRATA was not put into Tiny C Compiler or any other
   compiler. The traces are what TCC's own tables were asked to do; replaying them measures
   the table, not a compile. No end-to-end compile time or compiler memory figure exists,
   and symbol tables are a small part of both.
2. **No hardware target.** Measurements ran on an x86-64 laptop under Linux (WSL 2). STRATA
   was also built for a bare-metal Cortex-M3 and run under QEMU with 64 KiB of RAM and no
   heap, where five traces replay with results identical to the host's. That shows the code
   is correct and fits on a 32-bit target; an emulator gives no timing, and no physical
   device was used. The three larger traces need more than 64 KiB and were not run there.
3. **One compiler's behaviour.** TCC looks identifiers up in its own way (for example it
   calls `sym_find` for keyword tokens, and it opens a scope for every prototype's parameter
   list). GCC or Clang would produce different event streams.
4. **C only.** No C++ traces; names with `::` take the unpacked path.

## Where STRATA is worse (measured; see `RESULTS.md`)

* **Speed against a conventional allocator-free table.** In the reported run
  (`20261011-165103-v3`) `arena_chain`, a plain chained table over an entry arena, was faster
  than STRATA on 7 of the 8 compiler traces (median 30%) while needing 16-18% more memory.
  The cause was found on 2026-10-13: STRATA rebuilt its whole index on every buffer growth,
  hashed every name twice per rebuild and walked the probe path twice per new name. With
  those three things removed (run `20261013-125704-final`) the two tables are level: STRATA is
  faster on 2 traces (by 4.5% and 10.7%), slower on 3 (by 1.7% to 7.0%), and on 3 the
  difference is not established. STRATA
  is still **not faster** than the conventional design; it now costs no time for its smaller
  buffer. Most of the improvement over METIS-X is still obtained by the simpler design too.

* **Speed against an interning flat map.** `swiss_interned` replays every compiler trace
  faster than STRATA. It never removes a name within a translation unit and so does almost
  nothing at scope exit; it pays with the largest memory of all tables.
* **Rebuilds.** Since version 2 the undo entries record index slots (which made scope exit
  77-86% faster than in version 1). Until 2026-10-13 the price was that every index rebuild
  re-hashed each live name twice; it is now once, and a buffer growth re-hashes nothing.
  A rebuild is still O(live names) inside one call.
* **Name packing costs time for little memory.** It reduces the minimum buffer by 5.5-9.0% and
  is slower than storing raw bytes on 5 of the 8 compiler traces (by up to 10%).
* **Lookup latency is not improved** over METIS-X on the compiler traces (p95 lower on 3 of
  8 traces); the per-call numbers are within the measurement's resolution of each other.
* **The default configuration has no protection against adversarial keys.** The default hash
  is unkeyed, and identifiers that collide in it for every seed can be constructed
  (`benchmarks/hardening_main.cpp`; measured in `results/hardening/flood.csv`: declaring
  32 768 such names takes hundreds of times longer than ordinary names). Since 2026-10-13 two
  opt-in defences exist: a keyed hash (`Options::keyed`) and, in fixed mode, a static index
  with a probe limit (`Options::index_slots`, `Options::max_probe`) that refuses instead of
  slowing down. They are off by default, the key must be supplied by the caller, and the
  keyed hash costs replay time (see `docs/RESULTS.md`). The baseline
  `arena_chain` uses the same unkeyed mixer and has no such option.

## Design limits

* Names: 1 to 255 bytes. Scope depth: 16 383. Buffer: 64 MiB. Type tag: 8 bits. Value: 32 bits.
* A table rebuild (index doubling, buffer growth or shrink) is O(live names) and happens in
  the middle of a `declare` or `exit_scope`; worst-case latency of those calls is therefore
  not bounded by a constant in the growable mode and in the plain fixed mode. The bounded
  mode added on 2026-10-13 (static index) never rebuilds; there `exit_scope` is still
  proportional to the number of declarations in the scope being left, and the caller must
  choose the index size in advance.
* One declaration record per name and scope: no overloading, no separate tag or label name
  spaces. A front end would use one table per name space.
* Not thread-safe; the character-code table is initialised on first use.

## Measurement

* **Noise.** Replays were pinned to one core, but the host is a laptop under a hypervisor.
  The interquartile range of the 15 replay times is reported per configuration in
  `*_replay_time.csv`; single outliers of several times the median occur. Differences are
  reported with bootstrap intervals, and "not established" is stated where they overlap.
  Two full runs of identical code are kept in `results/raw/`; their median replay times
  differ by 4.8% at the median and by up to 73% for single table/trace pairs. The reported
  run therefore interleaves all tables in 31 rounds and compares paired samples; the
  interquartile range of raw times is still about 16% of the median.
* **Per-operation latency** is measured with a serialising timestamp read around each call.
  The subtraction of the timer's own cost is approximate, the instruction stream is
  serialised around every call, and values of 20-60 ns are near the method's floor.
* **Memory** is what the allocator reports (`malloc_usable_size`), i.e. it depends on glibc.
  A moving `realloc` is charged for two blocks, which is pessimistic for large blocks that
  glibc remaps without copying. Growth in 1.5x steps quantises STRATA's peak heap, so two
  STRATA variants can show the same peak although they use different amounts inside the
  buffer; the fixed-buffer minimum is the finer measure.
* **Baselines.** `scope_map_stack`, `std_undo_log`, `swiss_undo_log` and `swiss_interned` were
  written for this project. They follow known designs and were written to be efficient, but
  they are not the production code of LLVM or Clang. The three METIS tables are used
  unmodified; the old arena table has a known quadratic redeclaration check and is slow for
  that reason.
* **Trace completeness.** Three Mbed TLS files do not compile with TCC and are missing. "G"
  events (file-scope declarations made from inside a function) are ignored. FreeRTOS was
  compiled with a configuration header written for this project.
* **The 85% target.** It is met for allocator calls against METIS-X on every compiler trace,
  for scope-exit latency on one trace (range 67-88%), and for memory only against the
  interning Swiss map on two traces. It is not met for memory against METIS-X.

## Unverified

* Reference details marked "[book]" in the related-work notes (removed in the repository cleanup, tag `pre-cleanup`) were not re-read.
* The exception-safety defect of METIS-X (audit item D3) was established by reading the code,
  not by triggering it.
* The correctness argument in `CORRECTNESS.md` is informal; nothing was machine-checked.
* Why STRATA was slower than `arena_chain` was not separated experimentally in the reported
  run. On 2026-10-13 it was: neither packing (raw names are no faster) nor open addressing as
  such, but rebuild work in `declare` (see above). A remaining difference of about 5-10% in
  lookup latency against a half-full index was not investigated further.
* The patch for TCC was applied to one commit only.

## Added after the third review round (run 20261011-165103-v3, extra experiments)

- **No C++ workloads.** Both instrumented compilers (TinyCC, chibicc) compile C only. The shadowing / name-length sweep covers heavier shadowing and longer names synthetically; no real C++ front end was traced.
- **No real hardware.** The Cortex-M3 results come from QEMU (mps2-an385). They show that the code runs without a heap in 64 KiB and which table fits a given buffer; they contain no timing.
- **The sweep found no time crossover.** We expected a shadowing factor beyond which STRATA is also the faster table. The data do not show one: time follows name length (faster with 6-character names, mostly slower with 12 and 24), and the values are not monotone in the shadowing factor. The cause was not isolated.
- **End to end, neither table helps a hosted compiler.** In chibicc, STRATA is established slower on 3 of 7 projects (up to about 4%) and the arena table shows no established difference; peak memory is unchanged (median 0.14% per unit).
- **The fit benefit is narrow.** The saving decides whether a translation unit fits only when the budget lies between the two tables' needs: at most 23 of 169 TinyCC units (at 16 KiB), and at most 2 at 64 KiB and above.
- **chibicc integration detail.** Only variable scopes were replaced; file-scope declarations are mirrored in a second table instance to answer chibicc's global lookups, which adds work the original compiler does not do.

## Added by the audit of 2026-10-13

- **The bounded mode was evaluated by replay only.** Zero refusals at a probe limit of 64 were observed on the 15 stored compiler traces with both hashes; that is an observation about these traces, not a guarantee for other programs. A program whose names cluster would see declarations refused.
- **The keyed hash is not a cryptographic claim of this project.** It is HalfSipHash-1-3 with a 64-bit key, checked against the reference source on a little-endian host. A big-endian target would compute different (still consistent) values and was not tested. Where the key comes from on a device without an entropy source is not addressed.
- **The collision construction is a known technique.** Seed-independent multicollisions of MurmurHash2/3 were published by Aumasson and Bernstein in 2012; what was done here is the restriction to words that are packings of identifier characters, and the measurement on this table.
- **Fuzzing and bounded exhaustive checking are evidence, not proof.** The exhaustive check covers every sequence of at most 9 operations over 6 operations and 4 names in 8 small configurations; larger states are covered only by randomized tests and fuzzing.
- **No 32-bit host build of the unit tests.** The 32-bit evidence is still the emulated Cortex-M3 replay (now also in bounded mode); a `-m32` multilib was not installed.
- **Sources for trace regeneration are not checksum-pinned.** `tools/tcc-trace/make_traces.sh` fetches projects by tag or URL. The stored traces, not a regeneration, are what the results use.
- **Not applicable rather than untested:** the project has no web interface, service, authentication or database; nothing was tested in a browser.

## Updated on 2026-10-13 by the full re-run (run `20261013-143828-paper`)

- **The chibicc integration was repeated with the final code** (`results/chibicc/`; the
  measurements of 2026-10-11 are kept in `results/chibicc-20261011/`). Assembly identical on
  158 of 158 units for both tables. Whole-project compile time with STRATA: between -3.7% and
  +2.2% against the original compiler, established slower on 1 of 7 projects (Mbed TLS, +1.4%)
  and faster on none. With the arena table: -3.1% to +4.3%, faster on 3. The earlier statement
  "STRATA established slower on 3 of 7 projects (up to about 4%)" described the older code.
  The conclusion is unchanged: end to end, in a hosted compiler, neither table matters.
- **Per-trace timing verdicts against `arena_chain` are not stable between runs.** Run
  `20261013-125704-final`: faster on 2, slower on 3, not established on 3 (-10.7% to +7.0%).
  Run `20261013-143828-paper` (same code): faster on 0, slower on 2, not established on 6
  (-10.6% to +10.7%). Both support "within about 10%", neither supports a ranking per trace.
- **The embedded bounded-mode test now uses a probe limit of 512**, the value the analysis
  supports; `PROBE_LIMIT=64 bash tools/embedded/bounded.sh` reproduces the earlier setting.
- `scripts/run_all.sh` measured the seven chibicc traces together with the eight TinyCC
  traces in this run (they were present in `build/traces/`). The analysis scripts now keep the
  two sets apart, and `run_all.sh` skips the chibicc traces in future runs; they are measured
  by `scripts/run_extra.sh`.
