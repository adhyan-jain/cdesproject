# Design Space

Four architectures were considered for a memory-constrained scoped symbol table. Byte counts
are for a 64-bit host unless stated; *n* = live declarations, *d* = distinct live names,
*s* = declarations of one name, *L* = average name length.

## A. Repaired METIS-X (flat Robin Hood, one slot per declaration)

| Criterion | Assessment |
|---|---|
| Memory | 32 B per slot at load <= 0.7 (>= 46 B per declaration) + heap block for names > 12 B + per-scope vector |
| Lookup | hash, probe, compare; O(s) under shadowing |
| Insert | Robin Hood displacement; allocation for long names |
| Scope exit | backward shift per entry, O(k x cluster) |
| Worst case | long clusters; hard limit on equal-hash keys unless the probe field is widened |
| Allocation | many small blocks; cannot run from a fixed buffer |
| Complexity | already written; fixes are local |
| Embedded fit | poor: fragmentation, no bounded-memory mode |
| Prior art | Robin Hood hashing (Celis et al.), backward-shift deletion, small-string storage |
| Hypothesis | "local fixes make METIS-X competitive in memory" - rejected on arithmetic: 46 B per declaration before any name longer than 12 B is stored |

## B. Per-scope hash maps (conventional stack of maps)

| Criterion | Assessment |
|---|---|
| Memory | a map per open scope; node and bucket overhead per declaration; name copied per declaration |
| Lookup | one probe per open scope until found: O(depth) |
| Insert | one map insert |
| Scope exit | destroy a map |
| Worst case | deep nesting multiplies lookup cost |
| Allocation | one node per declaration, one bucket array per scope |
| Complexity | trivial |
| Embedded fit | poor |
| Prior art | textbook (Aho et al.) |
| Hypothesis | used as a baseline only |

## C. Interned identifiers + binding chain + undo log, on general-purpose containers

One map from name to the innermost binding; an undo log restores shadowed bindings at scope
exit. This is the algorithm of LLVM's `ScopedHashTable` and of the imperative symbol table
in Appel's textbook.

| Criterion | Assessment |
|---|---|
| Memory | name stored once; map node (key string 32 B + value + node overhead) per name; log entry per declaration |
| Lookup | one map probe, independent of depth and shadowing |
| Insert | map insert or update + log push |
| Scope exit | pop the log: O(k) |
| Worst case | the map's |
| Allocation | per name (node maps) or amortised rehash (flat maps); cannot run from a fixed buffer |
| Complexity | low |
| Embedded fit | medium: right algorithm, heavy containers |
| Prior art | LLVM ADT, Appel, Clang's identifier table + resolver |
| Hypothesis | "the algorithm is right; the cost is in the containers" - tested: three baselines implement it (`std_undo_log`, `swiss_undo_log`, `swiss_interned`) |

## D. STRATA: the same algorithm in one stack-disciplined buffer (selected)

Interning, undo entries and scope marks in a single contiguous word buffer:
index at the bottom, identifier records growing up, undo stack growing down.

| Criterion | Assessment |
|---|---|
| Memory | per distinct name: 8 B header + packed name (ceil(L/5) words) + one 4 B index slot at load <= 0.75; per declaration: 4 B, or 12 B when it shadows; per open scope: 8 B |
| Lookup | pack + hash the query, probe with an 8-bit fingerprint, compare words; the record holds the answer |
| Insert | lookup + append; no allocation unless the buffer grows |
| Scope exit | pop undo entries; empty the index slots of names first seen in the scope (they are the newest keys, so no tombstones and no shifting) |
| Worst case | linear probing: a full cluster scan if the hash is defeated (measured in experiment D); table rebuild when the index doubles |
| Allocation | none in fixed mode; O(log n) reallocs in growable mode |
| Complexity | moderate; one 450-line header |
| Embedded fit | good: caller-supplied buffer, explicit `kNoMemory`, strong failure guarantee, 32-bit arithmetic only |
| Prior art | C + open addressing + 6-bit character packing (cf. DEC RADIX-50) + two-ended stack allocation |
| Hypothesis | **H1** it needs less memory than every other candidate on compiler-generated traces; **H2** it does so without being slower than METIS-X end to end; **H3** it runs a whole translation unit from a fixed buffer with no allocator |

## Why D and not C

C and D are the same algorithm. D exists because the three properties the topic asks for -
a memory budget, no allocation after initialisation, and defined behaviour at exhaustion -
cannot be added to C without replacing its containers, which is what D is.

## Options examined inside D

| Option | Outcome |
|---|---|
| Separate binding record per declaration (12 B) with a chain through shadowed bindings | first version; replaced. Storing the innermost declaration in the identifier record and saving only *hidden* declarations on the undo stack cut the minimum buffer for `sqlite3.c` from 177.7 KiB to 143.7 KiB (-19%) and removed one memory access from every lookup. |
| Initial index sized as 1/16 of the buffer | replaced by a fixed 16-slot start that doubles in place; a large initial index wasted memory in tight fixed buffers. |
| Buffer growth by doubling with a fresh allocation | replaced by 1.5x growth through `realloc`; doubling held two full copies at the peak. |
| 6-bit name packing | kept; measured against raw names (ablation `strata_raw`). The saving is modest because names are only part of a record. |
| Shrinking on scope exit | kept as the default; measured against `strata_noshrink`. It costs time when a large scope is re-entered repeatedly. |
| Non-power-of-two index (to hold the load factor near 0.75 at all times) | not done: estimated saving under 5%, at the cost of a multiply per probe start. |
| Prefix compression of names (front coding) | not done: the earlier project measured that reconstruction on the lookup path costs more than it saves (SymTabV3). |
| Robin Hood displacement in the index | not done: it would break the "newest keys can simply be emptied" property, which needs keys to stay where they were inserted. |
| Hash with 64-bit multiplies (e.g. wyhash) | not done: the target is 32-bit microcontrollers; MurmurHash3's 32-bit mixer is used on whole words. |

## Relation to the alternative METIS rejected

METIS phase 2 rejected a *displacement undo log* for its Robin Hood table: a log of slot
moves, replayed backwards at scope exit. The measurements were right: scope exit was under 8%
of replay time there, and the log taxed every insert. STRATA's undo stack is a different
object. It logs *declarations* (one word each), not slot moves, and it replaces the per-scope
frame vectors instead of adding to them. The earlier negative result is not contradicted.
