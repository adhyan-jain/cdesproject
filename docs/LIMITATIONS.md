# Limitations and Threats to Validity

## What has not been shown

1. **No compiler integration.** STRATA was not put into Tiny C Compiler or any other
   compiler. The traces are what TCC's own tables were asked to do; replaying them measures
   the table, not a compile. No end-to-end compile time or compiler memory figure exists,
   and symbol tables are a small part of both.
2. **No embedded target.** Everything ran on an x86-64 laptop under Linux (WSL 2). The fixed
   buffer mode uses only 32-bit arithmetic and no allocator, but it was not built for or run
   on a microcontroller. "Suitable for embedded use" is therefore an argument from design and
   from measured buffer sizes, not a demonstration.
3. **One compiler's behaviour.** TCC looks identifiers up in its own way (for example it
   calls `sym_find` for keyword tokens, and it opens a scope for every prototype's parameter
   list). GCC or Clang would produce different event streams.
4. **C only.** No C++ traces; names with `::` take the unpacked path.

## Where STRATA is worse (measured; see `RESULTS.md`)

* **Speed against an interning flat map.** `swiss_interned` replays every compiler trace
  faster than STRATA. It never removes a name within a translation unit and so does almost
  nothing at scope exit; it pays with the largest memory of all tables.
* **Scope-exit latency.** STRATA's exit is slower per call than METIS-X's on the compiler
  traces: each name that dies is re-hashed to find its index slot.
* **Repeated large scopes.** With shrinking enabled, a 10 000-declaration scope entered 20
  times makes STRATA give the buffer back and regrow it each time (`big_scope_exit`).
  `shrink = false` removes the cost and keeps the memory.
* **Name packing costs time for little memory.** It reduces the minimum buffer by 5.5-9.0% and
  is slower than storing raw bytes on 5 of the 8 compiler traces (by up to 10%).
* **Lookup latency is not improved** over METIS-X on the compiler traces; the per-call
  numbers are within the measurement's resolution of each other.
* **No protection against adversarial keys.** The hash is unkeyed. With every key in one
  cluster a lookup scans the cluster (experiment D). A compiler that reads untrusted source
  and needs a bound would need a seeded hash or a probe limit.

## Design limits

* Names: 1 to 255 bytes. Scope depth: 16 383. Buffer: 64 MiB. Type tag: 8 bits. Value: 32 bits.
* A table rebuild (index doubling, buffer growth or shrink) is O(live names) and happens in
  the middle of a `declare` or `exit_scope`; worst-case latency of those calls is therefore
  not bounded by a constant. Fixed mode with a pre-grown index would avoid this; it is not
  implemented.
* One declaration record per name and scope: no overloading, no separate tag or label name
  spaces. A front end would use one table per name space.
* Not thread-safe; the character-code table is initialised on first use.

## Measurement

* **Noise.** Replays were pinned to one core, but the host is a laptop under a hypervisor.
  The interquartile range of the 15 replay times is reported per configuration in
  `*_replay_time.csv`; single outliers of several times the median occur. Differences are
  reported with bootstrap intervals, and "not established" is stated where they overlap.
  Two full runs are kept in `results/raw/`; their median replay times differ by 4.8% at the
  median and by up to 73% for single table/trace pairs (`RESULTS.md`, last section).
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
  and for memory only against one baseline on some traces (see `RESULTS.md`). It is not met
  for memory against METIS-X, and not for any latency metric.

## Unverified

* Reference details marked "[book]" in `RELATED_WORK.md` were not re-read.
* The exception-safety defect of METIS-X (audit item D3) was established by reading the code,
  not by triggering it.
* The patch for TCC was applied to one commit only.
