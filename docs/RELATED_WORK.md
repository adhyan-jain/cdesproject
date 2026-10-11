# Related Work and Novelty Assessment

Sources marked **[impl]** were read as source code, **[doc]** as documentation or a paper's
abstract page during this project, **[book]** are standard references cited from memory of
their content and not re-read here. Nothing below is cited for a number we rely on.

## 1. Prior techniques

| # | Technique | Source | Problem it addresses | Relation to STRATA |
|---|---|---|---|---|
| 1 | One hash map per scope, searched innermost-out | Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed., 2006 **[book]** | scoping with standard containers | baseline `scope_map_stack` |
| 2 | Single hash table + auxiliary undo stack; `beginScope` pushes a marker, `endScope` pops and restores | A. W. Appel, *Modern Compiler Implementation in C*, 1998, ch. 5 **[book]**; described the same way in several university lecture notes found in our search **[doc]** | O(1) lookup independent of nesting; O(k) scope exit | **the algorithm STRATA uses**. Not new. |
| 3 | `ScopedHashTable`: map from key to innermost value, values chained per scope and per key | LLVM, `llvm/ADT/ScopedHashTable.h` **[impl/doc]** | the same, as a reusable C++ container | same algorithm as #2 on `DenseMap`; baselines `std_undo_log`, `swiss_undo_log` reproduce it on other maps |
| 4 | Identifier interning separated from scope resolution: `IdentifierTable` maps spellings to `IdentifierInfo`; `IdentifierResolver` chains declarations per identifier | Clang, `clang/lib/Basic/IdentifierTable.cpp`, `clang/include/clang/Sema/IdentifierResolver.h` **[doc]** | hash each spelling once; resolve by pointer | STRATA merges the two steps in one structure; baseline `swiss_interned` mirrors the split |
| 5 | Token table + per-token symbol pointer + symbol stacks popped at scope exit | Tiny C Compiler, `tccpp.c` (`tok_alloc`), `tccgen.c` (`sym_push`, `sym_pop`, `sym_find`) **[impl]**, read and instrumented for this project | a complete small compiler's symbol management | the workload source; functionally what STRATA would replace |
| 6 | Robin Hood hashing | P. Celis, P.-A. Larson, J. I. Munro, "Robin Hood hashing", FOCS 1985 **[book]** | probe-length variance in open addressing | used by METIS-X; deliberately **not** used in STRATA (see #9) |
| 7 | Control bytes / fingerprints checked before the key | Abseil "Swiss Tables" design notes, abseil.io **[doc]**; port: G. Popovitch, parallel-hashmap v1.4.1 **[impl]** | avoid key comparisons and cache misses on probes | STRATA keeps an 8-bit fingerprint in the same word as the reference (no SIMD); parallel-hashmap is a baseline |
| 8 | Tombstones and their effect on linear probing | M. A. Bender, B. C. Kuszmaul, W. Kuszmaul, "Linear Probing Revisited: Tombstones Mark the Demise of Primary Clustering", FOCS 2021, pp. 1171-1182 **[doc]** | deletion in linear probing | background: STRATA's deletions need neither tombstones nor shifting because they are LIFO (see #9) |
| 9 | Deleting the most recently inserted keys of a linear-probing table by emptying their slots | follows directly from the insertion rule (D. E. Knuth, *The Art of Computer Programming*, vol. 3, sec. 6.4 **[book]** treats general deletion); the METIS project observed the Robin Hood analogue empirically (phase 2) | scope exit without tombstones or backward shift | used in STRATA. We found no source that states it for scoped symbol tables, and we do not claim it is unknown: it is a one-line consequence of how linear probing inserts. |
| 10 | Packing identifier characters below 8 bits | DEC RADIX-50: three characters from a 40-symbol alphabet per 16-bit word, used in assembler and compiler symbol tables on DEC systems **[doc]** | name storage on small machines | STRATA's 5 characters per 32-bit word (63-symbol alphabet) is the same idea for C identifiers, with comparison done on the packed form |
| 11 | Small-string / inline key storage | common library practice; e.g. Blender `BLI_string_map.h` **[doc]** | avoid a pointer chase for short keys | METIS-X's inline buffer; STRATA stores every name in-buffer, so the question does not arise |
| 12 | Region / arena allocation by lifetime | D. R. Hanson, "Fast allocation and deallocation of memory based on object lifetimes", *Software: Practice and Experience* 20(1), 1990 **[book]**; C. W. Fraser and D. R. Hanson, *A Retargetable C Compiler*, 1995 **[book]** | cheap bulk deallocation in compilers | STRATA's two stacks are lifetime regions tied to scopes |
| 13 | Two stacks growing towards each other in one block | classic technique (Knuth, vol. 1, sec. 2.2.2 **[book]**) | share free space between two LIFO structures | the layout of STRATA's buffer |
| 14 | MurmurHash3 32-bit mixer | A. Appleby, SMHasher repository, public domain **[book]** | fast non-cryptographic hashing with 32-bit operations | STRATA's hash over packed words |
| 15 | Hashed symbol tables for block-structured languages | S. L. Graham, W. N. Joy, O. Roubine, "Hashed symbol tables for languages with explicit scope control", SIGPLAN Symposium on Compiler Construction, 1979 (citation seen in a comp.compilers bibliography **[doc]**; paper not read) | scoped tables with explicit scope control | historical background only |

A reference often given for scoped tables, R. P. Cook and T. J. LeBlanc, "A symbol table
abstraction to implement languages with explicit scope control" (IEEE TSE, 1983), could not
be confirmed in our search and is therefore **not** cited in the paper.

## 2. What is established and what is ours

Established, and used as is: the undo-stack algorithm (#2, #3), interning (#4), linear
probing, fingerprints (#7), character packing (#10), stack allocation (#12, #13), the hash (#14).

Specific to this project:

1. **The combination under a hard memory budget.** One caller-supplied buffer holds the
   interner, the scope mechanism and the declarations, with relative references so the index
   can grow in place, a defined `kNoMemory` result and a tested strong failure guarantee.
   We found no published or open-source scoped symbol table with these properties, but our
   search was a few web queries, not a systematic review.
2. **Compiler-generated traces for symbol-table evaluation.** Hooks in Tiny C Compiler record
   its real interning lookups, declarations and scope changes for eight pinned projects.
   The earlier work, and the course material we found, use synthetic or lexically extracted
   traces.
3. **Measurements**: memory per live declaration and replay time for ten tables on those
   traces, the minimum fixed buffer per project, and negative results (where STRATA is slower,
   where packing barely helps, the unprotected worst case).

## 3. Remaining gap

* No integration into a compiler: we replay what TCC did; we do not replace TCC's tables.
* No comparison with LLVM's actual `ScopedHashTable`/`DenseMap` or Clang's allocator-backed
  tables, only with re-implementations of the algorithm on other maps.
* No measurement on a microcontroller.

Experiments that would close the gap: (a) patch TCC to call STRATA instead of
`tok_alloc`/`sym_push`/`sym_pop` and measure compile time and peak memory; (b) build the
benchmark for a Cortex-M target and run the fixed-buffer mode on hardware; (c) add LLVM ADT
as a baseline.

## 4. Novelty assessment (internal rubric)

Scale per criterion: 0-2 none, 3-4 minor, 5-6 solid incremental, 7-8 clearly new, 9-10 major.

| Criterion | Score | Justification |
|---|---|---|
| Problem significance | 4 | Symbol tables are rarely a compiler's memory or time bottleneck; the embedded self-hosted-compiler niche is small. |
| Difference from closest implementations | 5 | Same algorithm as LLVM/Appel; different in being single-buffer, budgeted and failure-safe. |
| Technical originality | 3 | Every mechanism has a named precedent (table above). The contribution is an engineering synthesis. |
| Strength of experimental evidence | 6 | Real compiler events, ten tables, reference-checked, repeated runs with intervals, negative results reported; but one machine, replay only. |
| Practical value for embedded compilers | 5 | A fixed-buffer mode with measured minimum sizes is directly usable; not demonstrated inside a compiler or on a target. |
| **Overall** | **4.5 / 10** | |

The brief set a development goal of 8/10. **It was not reached, and we do not think it can be
reached honestly on this topic without the compiler integration and hardware results listed
in section 3**; originality in particular is capped by forty years of prior work on exactly
this data structure. The assessment is our own; reviewers may score differently.
