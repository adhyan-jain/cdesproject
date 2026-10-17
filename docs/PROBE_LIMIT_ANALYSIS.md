# The canonical-state property and how to choose the probe limit

> **Update 2026-10-17:** see `docs/ADDENDUM_2026-10-17.md`; the bound below is valid but looser than stated, and an exact law replaces it (`theory/`).


Added 2026-10-13. Two statements about STRATA, each with an argument and a test or
measurement. Neither uses a new technique: the first follows from the removal rule proved in
`CORRECTNESS.md`, the second is the standard interval-counting argument for linear probing
(see D. E. Knuth, *The Art of Computer Programming*, vol. 3, sec. 6.4, and M. Thorup, "Linear
Probing with 5-Independent Hashing", arXiv:1509.04549, for the technique). What is specific
to this project is that the first statement makes the second one applicable to a table with
deletions.

## 1. Canonical state

**Statement.** Consider a table with a static index. After any sequence of `enter_scope`,
`exit_scope` and `declare` calls (including refused ones), let *D* be the list of
declarations that are still live, in the order they were made, with their scopes. The
complete state of the table (index, identifier records, undo stack, counters) is
bit-for-bit the state of a fresh table into which exactly *D* was declared.

**Argument.** By induction over the operations. A refused call changes nothing
(`CORRECTNESS.md`, section 4). A successful `declare` or `enter_scope` appends to *D* and to
the table, and by the induction hypothesis the table before the call equals the fresh table
for the shorter list, so after the call it equals the fresh table for the longer one. A
redeclaration in the current scope overwrites value and type of the live declaration in place.
`exit_scope` removes the declarations of the innermost scope, which are a suffix of *D*. It
undoes them newest first, and undoing the newest declaration restores exactly the words that
making it changed: a shadow entry puts back the saved value, type and depth; a
first-declaration entry empties the one index slot that the insertion filled (linear probing
without displacement moves no other key) and the record is dropped by resetting the stack top.
The words above the two stack tops are not part of the state. So after the exit the table
equals the fresh table for *D* without that suffix. ∎

With a growing index the same holds for everything except the index size, which in fixed mode
never decreases; a rebuild re-inserts the names oldest first, which is again the order of *D*.

**Consequences.**

- The table does not age. No sequence of scope entries and exits leaves tombstones, displaced
  keys or longer probe paths behind. (General deletion in linear probing does: that is the
  subject of Bender, Kuszmaul and Kuszmaul, FOCS 2021.)
- At every moment the index is exactly what **insertion-only** linear probing produces for the
  currently visible names. Results about insertion-only tables therefore apply to STRATA at
  all times, which is what section 2 uses.
- The state is a function of the live declarations and their order. It is not
  history-independent in the sense of Naor and Teague or of Blelloch and Golovin (FOCS 2007),
  where the layout must not depend on insertion order either; here the order of the live
  declarations is visible in the layout.

**Test.** `test_canonical_state` in `tests/test_strata.cpp`: 30 000 random operations in each
of 6 configurations (packed and raw names, default and keyed hash, normal hash and all keys in
one cluster); every 500 operations a fresh table is built from the live declarations and
compared by state digest and by `memcmp` of index and records. 360 comparisons, all equal.
The bounded exhaustive check and the fuzzer exercise the same operations with refusals.

## 2. How often does a probe limit refuse a legitimate name?

**Setting.** An index of *m* slots holds *n* names, load α = *n*/*m* < 1. Home slots are
independent and uniform (an ideal hash). A new name is refused when the first *L* slots of
its probe path are all occupied.

**Bound.** With ρ = α·e^(1−α) (which is below 1 for every α < 1):

> P(a new name is refused) ≤ ρ^L / (1 − ρ).

**Argument.** Let *h* be the new name's home slot; it is independent of the table. If slots
*h* … *h*+*L*−1 are all occupied, let *s* ≤ *h* be the first slot of the run of occupied
slots that contains *h*. Slot *s*−1 is empty, and by section 1 the index is an insertion-only
table, so that slot was never occupied and no key was ever carried across it. Hence each of
the *h*+*L*−*s* keys stored in slots *s* … *h*+*L*−1 has its home in that same interval. So
for some *k* ≥ *L*, at least *k* of the *n* names have their home in the specific interval of
length *k* that ends at slot *h*+*L*−1. The number of names with home in a fixed interval of
length *k* is binomial with mean α*k*; by the Chernoff bound the probability that it reaches
*k* is at most (α·e^(1−α))^k = ρ^k. Summing over *k* ≥ *L* gives the claim. ∎

Because ρ grows with α, the bound for the maximum load of a table covers every lower load. For
a compilation that makes *N* declarations of new names, the probability that any of them is
refused is at most *N*·ρ^L / (1 − ρ).

**What the bound needs.** Independent uniform home slots. For the keyed hash this is the
usual modelling assumption for a pseudo-random function whose key the author of the input
does not know. For the default unkeyed hash it holds only for names that were not chosen to
collide, which is exactly what an attacker violates.

**Measurement.** `hardening --mode probes` fills an index by linear probing with random
identifiers (6 to 24 characters), using the table's own hash of each name, and records how
many slots an insertion of a fresh name would examine: 24 configurations (index sizes 2^10, 2^13, 2^16; four loads; both hashes), 500 tables and 10 million fresh names each (`results/hardening/probes.csv`). The measured probability never exceeded the bound in any of the 168 cells. Rows for 65 536 slots:

| Hash | Load | Mean probes (Knuth) | Longest seen | P(> 32): measured / bound | P(> 64) | P(> 128) | P(> 256) | P(> 512) |
|---|---|---|---|---|---|---|---|---|
| default | 0.375 | 1.78 (1.78) | 33 | 1.0e-07 / 3.8e-05 | 0 / 4.3e-10 | 0 / 5.5e-20 | 0 / <1e-30 | 0 / <1e-30 |
| default | 0.500 | 2.50 (2.50) | 58 | 8.2e-05 / 1.2e-02 | 0 / 2.4e-05 | 0 / 1.0e-10 | 0 / 1.9e-21 | 0 / <1e-30 |
| default | 0.625 | 4.05 (4.06) | 123 | 3.6e-03 / 5.3e-01 | 8.2e-05 / 2.5e-02 | 0 / 5.8e-05 | 0 / 3.0e-10 | 0 / 8.3e-21 |
| default | 0.750 | 8.50 (8.50) | 264 | 4.8e-02 / 8.1 | 7.7e-03 / 2.4 | 3.1e-04 / 2.2e-01 | 2.0e-07 / 1.7e-03 | 0 / 1.1e-07 |
| keyed | 0.375 | 1.78 (1.78) | 44 | 4.0e-07 / 3.8e-05 | 0 / 4.3e-10 | 0 / 5.5e-20 | 0 / <1e-30 | 0 / <1e-30 |
| keyed | 0.500 | 2.50 (2.50) | 63 | 8.4e-05 / 1.2e-02 | 0 / 2.4e-05 | 0 / 1.0e-10 | 0 / 1.9e-21 | 0 / <1e-30 |
| keyed | 0.625 | 4.05 (4.06) | 144 | 3.6e-03 / 5.3e-01 | 8.4e-05 / 2.5e-02 | 7.0e-07 / 5.8e-05 | 0 / 3.0e-10 | 0 / 8.3e-21 |
| keyed | 0.750 | 8.50 (8.50) | 258 | 4.8e-02 / 8.1 | 7.7e-03 / 2.4 | 3.3e-04 / 2.2e-01 | 2.0e-07 / 1.7e-03 | 0 / 1.1e-07 |

(A bound above 1 says nothing. "0" means not observed in 10 million samples.)

Reading the table:

- The measured mean matches Knuth's formula ½(1 + 1/(1−α)²) for insertion-only linear probing
  at every load, for both hashes. That is the section-1 property and the uniformity assumption
  seen in data.
- The bound was never exceeded. It is loose, by about two orders of magnitude where both
  numbers are non-zero; it is an upper bound, not an estimate.
- **A limit of 64 is not safe at load 3/4.** There, about 0.8% of fresh names need more than
  64 probes. The earlier observation "no refusal at a limit of 64 on 15 compiler traces" is
  true of those traces, whose tables are small and mostly well below their maximum load; it
  must not be read as a guarantee.

## 3. Choosing the limit

From the bound, the smallest *L* with *N*·ρ^L/(1−ρ) ≤ ε is
*L* = ⌈ ln(ε·(1−ρ)/*N*) / ln ρ ⌉.

| Maximum load | ρ | Limit for ε = 10⁻⁶ per declaration | Limit for ε = 10⁻⁶ over 10⁶ declarations |
|---|---|---|---|
| 3/4 (default index) | 0.9630 | 455 | 821 |
| 1/2 (`sparse_index`) | 0.8244 | 81 | 153 |
| 3/8 | 0.7006 | 43 | 82 |

Recommendation that follows: with the default index, use a limit of 512 (bound 1.1·10⁻⁷ per
declaration; a call then examines at most 512 consecutive index words, 2 KiB). With
`sparse_index`, 128 suffices (bound 1.0·10⁻¹⁰) at the price of a larger index. A limit of 64
with the default index is a reasonable *engineering* choice only if occasional refusals are
acceptable.

The limit bounds the work of one call whatever the hash does. The keyed hash makes the
probability statement above hold for input chosen by someone who does not know the key. Both
are needed for "bounded work and negligible refusals on untrusted input".

## 4. What this does not show

- The bound is for an ideal hash. HalfSipHash-1-3 is modelled as one; that is an assumption.
- Timing side channels through which an attacker might learn the key are not considered.
- `exit_scope` and name packing are outside the bound (`CORRECTNESS.md`, section 7).
- The measurement uses random identifiers, not program text. Real identifiers are far from
  random strings; what matters is that their hashes are spread uniformly, which the mean
  probe counts on the compiler traces are consistent with but do not prove.
