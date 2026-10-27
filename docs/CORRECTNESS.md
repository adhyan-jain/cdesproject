# Correctness Argument

This document states what STRATA guarantees, why, and which test checks each part. It is an
informal argument, not a machine-checked proof.

## 1. State

One buffer `w[0..cap)` of 32-bit words and five counters.

* **Index** `w[0..idx)`: slot = 0 (empty) or `fingerprint << 24 | identifier reference`.
* **Identifier stack** `w[idx..idx+itop)`: consecutive records `[value][meta][name words]`,
  oldest first. `meta` holds the number of name words, a raw flag, the type tag and the scope
  depth of the innermost declaration of that name.
* **Undo stack** `w[cap-undo..cap)`, newest at the lowest address, made of
  * *first-declaration entries* (1 word): the index slot of the name;
  * *shadow entries* (3 words): identifier reference with a flag, saved value, saved type and depth;
  * *scope marks* (2 words): identifier-stack top at scope entry, previous mark.

## 2. Invariants

After every public call returns:

* **I1 (reachability).** Every identifier record is found by probing linearly from its home
  slot without meeting an empty slot, and the index holds exactly one slot per record.
* **I2 (one record per visible name).** No two records hold the same name. A record exists
  if and only if the name has at least one live declaration.
* **I3 (innermost first).** A record's value, type and depth are those of the innermost live
  declaration of its name.
* **I4 (undo completeness).** Between the top of the undo stack and the current mark lie
  exactly the declarations made in the current scope, newest first: one first-declaration
  entry for each name whose record was created in this scope, one shadow entry for each
  declaration that hid an outer one, holding exactly what it hid.
* **I5 (stack order).** Records created in a scope lie above the identifier-stack top stored
  in that scope's mark, and their index slots were filled after every older record's slot.
* **I6 (accounting).** `idx + itop + undo <= cap`; the counters equal the numbers of records,
  declarations and marks.

`Table::check_invariants()` verifies I1, I2 (through the slot count), I4's structure, I5's
bounds and I6 in O(n); the tests call it throughout. I3 is checked against the reference
model, which resolves names independently.

## 3. Operations preserve the invariants

**Lookup** only reads.

**Declaration of a new name.** Space for the record, one undo word and (if needed) a larger
index is reserved first (Section 4). The record is appended, its slot is the first empty slot
on its probe path (I1), the slot index is pushed (I4), depth = current depth (I3).

**Declaration of a visible name from an outer scope.** Three undo words are reserved; the
record's value, type and depth are saved in a shadow entry (I4) and overwritten (I3). No
index or record is created (I2).

**Redeclaration in the current scope.** The record's depth equals the current depth. This
test is sound: a declaration at depth *d* that is still live belongs to the scope currently
open at depth *d*, because any earlier scope at that depth was closed and its declarations
undone. Value and type are replaced; nothing else changes.

**Scope exit.** Entries are undone from the top down to the mark.

* A shadow entry restores the saved value, type and depth: by I4 that is exactly the
  declaration hidden by the one being removed, so I3 holds for the outer scope.
* A first-declaration entry empties the recorded slot. **Claim:** this keeps I1 for every
  remaining record. *Proof.* In linear probing without displacement a key is stored in the
  first empty slot on its probe path at insertion time and never moves. So the path of a key
  *k* from its home to its slot consists of slots that were occupied when *k* was inserted,
  i.e. by keys older than *k*. The record being removed is, by I5 and the top-down order of
  undoing, the newest key in the index. It is therefore on no remaining key's path, and
  emptying its slot cuts no path. ∎ The same argument applies to each next entry, because
  after the removal the next one is again the newest.
* Finally the identifier-stack top is reset to the mark's value, which discards exactly the
  records whose slots were emptied (I5), and the mark is popped.

No tombstone is written and no key is moved, so repeated scope entry and exit returns the
index to exactly its earlier contents (`test_reclamation`, churn part: 20 000 cycles, used
bytes unchanged).

**Rebuild (index doubling or halving).** The slots recorded in first-declaration entries are
about to become meaningless, and each record will need its entry again. So first, using the
old index, every such entry and its record swap one word: the record's value word receives
the entry's position (relative to the end of the buffer), the entry keeps the value
(`stash_undo`). The two stacks are moved (references are relative to region start and buffer
end, so their contents stay valid), the index is cleared and the records are re-inserted
**oldest first**, which re-establishes the property used in the claim above: each key's path
holds only older keys. As each record is inserted, the swap is undone and the entry receives
the new slot (`reindex`). Every record has exactly one first-declaration entry (I4), so every
borrowed value word is restored. Each name is hashed once and no scratch memory is used.
(Until 2026-10-13 the entries were converted to references and back, which hashed every name
twice.)

**Buffer growth or shrink with an unchanged index size.** Only the undo stack moves, as a
block. The index, the records and the slots recorded in the undo stack are untouched, so
nothing is re-hashed. (Until 2026-10-13 every buffer growth rebuilt the whole index.)

**Insertion without a second walk.** `declare` first searches for the name. A search that
fails ends at the first empty slot of the name's probe path, which is exactly where linear
probing would insert it. That slot is remembered and used, unless the reservation step
rebuilt the index in between, in which case the path is walked again.
(`test_exit_under_collisions_and_rebuilds`, `test_canonical_state`, and the mutation check's
M7-M9, which break each of these three steps and are detected.)

## 4. All-or-nothing on exhaustion

**Guarantee.** If `declare` or `enter_scope` returns `kNoMemory`, `kTooDeep`, `kNameTooLong`
or `kEmptyName`, the complete state is bit-for-bit what it was before the call.

**Why.** Each operation has the form *validate, reserve, write*. `ensure(words, names)`
either returns true with at least `words` free words and index room for `names` more keys,
or returns false. In fixed mode it returns false before touching anything unless the space
needed for a larger index *and* the request fits. In growable mode the only fallible step is
the allocator call, which comes first; the undo entries are retargeted only after it has
succeeded. After a successful `ensure` no step can fail, so there is no partially written
state to undo. `exit_scope` cannot fail except at the outermost scope, where it returns
before doing anything.

A successful `ensure` may have rebuilt the index although the caller's own request is small;
that changes the layout, not the content, and only happens on calls that then succeed.

**Tests.** `test_all_or_nothing` computes `state_digest()` (a hash of the counters, the
index and both stacks) before every operation and requires it unchanged after every refusal:
30 configurations (5 buffer sizes x 3 workloads: random, deep shadowing, deep nesting; x normal
hash and all-keys-in-one-cluster hash), each also compared with the reference model and
unwound to empty afterwards. `test_fixed_capacity` and `test_allocation_failure` (allocator
failing after *k* = 1..10 calls, leak check) cover the same property through contents.

## 5. Adversarial collisions and deep shadowing

* **Collisions.** Correctness does not depend on the hash: with every key forced into one
  cluster (`degenerate_hash` test hook) all tests of sections 3 and 4 still pass. Only cost
  changes: a lookup scans the cluster (`docs/RESULTS.md`, regenerated by `scripts/make_report.py`; worst case). The fingerprint is a filter,
  never a decision: a match is confirmed by comparing length information and all name words.
* **Deep shadowing.** A name declared in *s* nested scopes uses one record and *s - 1* shadow
  entries; lookup cost is independent of *s*. `test_deep_shadowing` declares one name in
  5 000 nested scopes and unwinds them one by one. The depth field limits nesting to 16 383
  scopes; the next `enter_scope` returns `kTooDeep` and changes nothing
  (`test_invalid_scope_ops`).

## 6. What is not covered

* No formal proof and no model checking.
* Concurrency: the table is single-threaded by design.
* Behaviour when the caller passes a misaligned or overlapping buffer.
* 32-bit targets were exercised only through the Cortex-M3 emulator run
  (`results/embedded/`), which replays compiler traces and compares a checksum with the host;
  the full unit-test suite was not run there.

## 7. Bounded mode and keyed hash (added 2026-10-13)

`Table(buffer, bytes, options)` with `options.index_slots != 0` gives a fixed-mode table whose
index has a static size. `options.max_probe = L` adds a probe limit; `options.keyed` replaces
the hash by HalfSipHash-1-3 under `options.key`.

**B1 (no rebuild).** With a static index `ensure` never calls `relocate`: it returns false when
the load limit or the free space would be exceeded and true otherwise, without writing. So no
operation contains a step proportional to the number of live names, and the layout of the
index is only ever changed by one insertion (`declare` of a new name) or by emptying slots
(`exit_scope`).

**B2 (probe bound).** With `max_probe = L`, every stored name lies within the first L slots of
its probe path. *Argument.* A name is inserted only after `probe_fits` found an empty slot
among the first L slots of its path, and `index_insert` takes the first empty slot, which is
that one or an earlier one. A stored name never moves (B1), and scope exit only empties slots.
∎ Consequently `find` may stop after L slots without missing a stored name, and a lookup or
declaration examines at most L index slots. Each examined slot whose 8-bit fingerprint matches
costs one comparison of at most 64 words, so the work of one call is bounded by a constant
that depends on L and the name-length limit, not on the table's contents.

**B3 (refusal).** `declare` returns `kProbeLimit` before writing anything; the argument of
section 4 applies unchanged. A name that shadows a visible one needs no index slot and is
never refused for this reason.

**B4 (section 3 still holds).** Emptying the newest key's slot cuts no remaining key's path
(the claim of section 3 does not depend on the index size being able to change), and the stop
after L slots is sound by B2.

**B5 (configuration errors fail closed).** A probe limit without a static index, an index size
that is not a power of two of at least 16, or one that does not fit the buffer gives an invalid
table on which every call returns `kNoMemory`. Growable mode ignores both fields.

**Keyed hash.** Correctness never depended on the hash (section 5); the key only changes where
names are placed. Rebuilds in the other modes re-hash stored names with the same key
(`hash_of`). The implementation is compared with the reference HalfSipHash source on 200 000
random inputs (`tests/halfsiphash_conformance.cpp`, little-endian hosts only).

What the bound does **not** cover: `exit_scope` takes time proportional to the number of
declarations of the scope being left; `make_key` is linear in the name length (at most 255
bytes). The probe limit bounds work per call, it does not make an attack impossible to
*attempt*: with the unkeyed hash an attacker can still fill a cluster and have further names
refused. Whether the keyed hash resists a determined attacker rests on HalfSipHash-1-3 with a
64-bit key, which its authors and the Linux kernel documentation describe as adequate for
hash-table flooding only.

**Prepared names.** `make_key(name, len, key)` packs and hashes a name once; `declare(const Key&, ...)` and
`resolve(const Key&, ...)` then skip that work. The key depends on the table's options (packing, keyed hash and key),
so it is valid only for a table with the same options; using it on a differently configured table is a caller error
that no check catches. The plain `declare` and `resolve` are implemented as `make_key` followed by these overloads, so the
two forms cannot differ; `tests/test_review.cpp` (T4) checks this in default, bounded and keyed modes.

**Tests.** `test_bounded_mode` and `test_keyed_hash` in `tests/test_strata.cpp`;
`tests/exhaustive_small.cpp` (every operation sequence up to a fixed length over six
operations, eight configurations, five of them bounded or keyed); `tests/fuzz_strata.cpp`
(differential fuzzing of all modes under ASan + UBSan); `scripts/audit/mutation_check.py`
(injected defects that the fuzzer must detect). Results: `reports/artifacts/*.log` and `docs/EVIDENCE.md`.
