# Architecture Decision: Repair or Rebuild

**Decision: Path B, rebuild under the same research topic.** The earlier tables are kept as
unmodified baselines and every earlier finding that is still valid is carried over.

## Why not repair METIS-X

The audit (`INITIAL_AUDIT.md`) found defects of two kinds.

*Repairable in place:* the exception-safety of `rehash` (D3), the per-scope vectors (D7), the
silent `continue` (D8), the never-shrinking slot array (D5).

*Consequences of the architecture itself:*

1. **One 32-byte slot per declaration, with the name in or behind every slot.** A name declared
   in three scopes is stored three times. Names over 12 bytes need a heap block each (D4);
   in the compiler traces that is most names.
2. **All declarations of a name share one probe cluster.** This gives the O(s) lookup (D2) and,
   with the 8-bit probe distance, the hard failure at about 250 shadowing levels (D1). Widening
   the field removes the failure but not the scan.
3. **The table is keyed by the declaration, not by the name.** That is the root of the
   applicability problem the METIS project closed on (D15): compilers resolve scopes per
   *identifier*, after interning. A per-declaration string-keyed table duplicates the interner's
   work on every lookup and cannot be placed behind one.

Fixing (1)-(3) means changing what a slot is and what the key is. Nothing of the Robin Hood
slot array, the inline buffer or the frame back-references survives that change, so a
"repair" would be a rebuild that keeps the name. The brief also asks explicitly not to
reproduce the same Robin Hood table with cosmetic changes.

## What is rebuilt

A table keyed by identifier: each distinct visible name is interned once and its record
holds the innermost declaration; hidden declarations are saved on an undo stack. All of it
lives in one contiguous buffer that can be supplied by the caller. See `DESIGN_SPACE.md`
for the alternatives considered and `include/strata/strata.hpp` for the result.

## What is preserved from the earlier work

| Earlier asset | Use here |
|---|---|
| `include/metis_x.hpp` and two baselines | fetched at the audited commit, benchmarked unmodified |
| Four regex-extracted traces of the METIS-X manuscript | supplemental experiment E, labelled as heuristic |
| Heap accounting through an allocator hook | same method, with the harness kept out of the window |
| Phase-2 finding that reverse-order deletion restores the layout | the stack discipline of the new index |
| Phase-8 finding about TCC | motivates the identifier-keyed design and the TCC trace hooks |
| The METIS-X manuscript's limitations list | the checklist of `INITIAL_AUDIT.md` |

## Repository visibility

The brief prefers a public repository unless there is a material reason against it. There is
one: the METIS repository has
no licence file. Publication cannot be undone, and the co-author has not been asked. The new
repository was therefore created **private**, with the co-author invited. It contains no
METIS code. Making it public is one command (`gh repo edit --visibility public`) once both
authors agree.

## Language and dependencies

C++14, header-only core, no dependency beyond the C library. Benchmarks need Linux/glibc
(`malloc_usable_size`, `/proc`) and x86 (`rdtscp`); those parts are isolated in
`benchmarks/common.hpp`.

## Repository visibility: status on 2026-10-13

The section above records the decision of 2026-10-11 to keep the repository private because the
METIS repository has no licence file and because the co-author had not been asked.
On 2026-10-13 the repository owner (Shubhi Singh) made the repository **public** by explicit
instruction. This file does not record whether the
co-authors, the guide or the institution agreed. That
question is **open** and is a human decision; it is listed in `SUBMISSION_READINESS.md`. The
repository still contains no METIS code. Whatever its outcome, publication of this repository
is a public disclosure that cannot be undone.
