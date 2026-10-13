# Novelty assessment

> **Superseded in part by `ROUND_2_ADDENDUM.md`** (same day): STRATA is now level with the conventional table on speed, the suggested probe limit is 512, and the novelty score is 6.0/10. Read that file first; the text below is the first round as written.

Audit of 2026-10-13. This is one reviewer-style judgment made with a limited literature
search. A score is an opinion about evidence; it predicts nothing about acceptance anywhere.

**Result: 5.5 / 10 on the weighted rubric (4.9 before the audit's additions). An 8/10
assessment is not justified, and the audit did not find a way to reach it honestly within
this topic.**

## 1. Research problem and contribution

Problem: a scoped symbol table for a compiler that has a hard memory budget (one fixed
buffer, no allocator), must fail in a defined way when the budget is exhausted, and may be
fed source text its operator does not trust.

What the project contributes, after the audit:

| # | Contribution | Kind | New in the audit? |
|---|---|---|---|
| C1 | A measured decomposition: against the earlier table METIS-X, how much is gained by allocation-free arena storage alone (a conventional chained table) and how much by interning, undo entries and packed names on top | evaluation | no |
| C2 | STRATA: interner, scope mechanism and declarations in one caller-supplied buffer, with a tested all-or-nothing refusal | system design | no |
| C3 | Compiler-generated traces from two instrumented C compilers as the workload | methodology | no |
| C4 | A bounded mode: static index (no rebuild), probe limit with a defined refusal that keeps the all-or-nothing property, optional keyed hash | system design | yes |
| C5 | A demonstration that identifiers colliding in the table's Murmur-style hash for every seed can be built from valid C identifier characters, with the slowdown measured (223x at 32 768 names) and the two defences measured | security evaluation | yes |
| C6 | Verification evidence: differential fuzzing of all modes, exhaustive enumeration of all operation sequences up to length 9 in 8 configurations, a mutation check of the fuzzer | methodology | yes |

## 2. Precise novelty claim that the evidence supports

> For scoped symbol tables confined to one fixed buffer, we measure which design decisions
> buy memory and which cost time on compiler-generated workloads, and we show that such a
> table can also be given a per-operation work bound under adversarial identifiers, by a
> static index, a probe limit and a keyed hash, without giving up the guarantee that a
> refused operation changes nothing.

Claims the evidence does **not** support, and which must not be made:

- that any mechanism in STRATA is a new algorithm;
- that STRATA is faster than a conventional design (it is 11-34% slower than `arena_chain` on all 8 traces in the new run);
- that the collision attack is new (it is the 2012 Aumasson-Bernstein technique, restricted to an identifier alphabet);
- that the bounded mode never refuses legitimate programs (observed on 15 traces only);
- that anything was shown on hardware or inside a production compiler.

## 3. Closest related work

Verification level: **read** = the source or page was opened and read during this audit or the
project's earlier session; **listed** = bibliographic data confirmed, content not read;
**memory** = standard reference cited from memory.

| # | Work | Venue, year | Method | Similar to this project | Different | Level |
|---|---|---|---|---|---|---|
| R1 | A. W. Appel, *Modern Compiler Implementation in C*, ch. 5 | Cambridge Univ. Press, 1998 | hash table plus undo stack; `beginScope` pushes a marker, `endScope` pops and restores | **the algorithm STRATA uses** | heap-allocated; no budget, no failure semantics | memory; the same scheme is described in lecture notes found by search (EPFL, lara.epfl.ch/w/_media/cc12/lec13.pdf: listed) |
| R2 | LLVM `ScopedHashTable` (llvm.org/doxygen/ScopedHashTable_8h_source.html) | LLVM ADT, current | per-key and per-scope chains over `DenseMap`, allocator parameter | same semantics | allocator-backed nodes; no single buffer, no refusal guarantee, no probe bound | read (documentation) |
| R3 | Clang `IdentifierTable` / `IdentifierResolver` | Clang source | interning separated from scope resolution | the split that STRATA merges | allocator-backed, not budgeted | read (documentation, earlier session) |
| R4 | Tiny C Compiler `tccpp.c`, `tccgen.c` | TinyCC, commit 43c7708 | token table plus symbol stacks popped at scope exit | the functionality STRATA would replace; the trace source | malloc-based | read (source, instrumented) |
| R5 | S. L. Graham, W. N. Joy, O. Roubine, "Hashed symbol tables for languages with explicit scope control" | SIGPLAN Symp. on Compiler Construction, SIGPLAN Notices 14(8), pp. 50-57, 1979 | hash-chain rearrangement to encode visibility | historical root of hashed scoped tables | different scope model (import/export); fixed 64-entry table | listed (via Grune's annotated bibliography and Crossref) |
| R6 | M. A. Bender, B. C. Kuszmaul, W. Kuszmaul, "Linear Probing Revisited: Tombstones Mark the Demise of Primary Clustering" | FOCS 2021 | analysis of deletions in linear probing | background for deletion without tombstones | general deletions; STRATA's are LIFO only | listed |
| R7 | S. A. Crosby, D. S. Wallach, "Denial of Service via Algorithmic Complexity Attacks" (usenix.org/events/sec03/tech/full_papers/crosby/crosby_html) | USENIX Security 2003 | crafted keys degrade hash tables to lists | the threat model of C4/C5 | not about compilers | read (abstract and introduction via search) |
| R8 | J.-P. Aumasson, D. J. Bernstein, "SipHash: a fast short-input PRF" (eprint.iacr.org/2012/351); slides "Hash-flooding DoS reloaded" (aumasson.jp/siphash/siphashdos_appsec12_slides.pdf) | INDOCRYPT 2012, LNCS 7668, pp. 489-508 | seed-independent multicollisions of MurmurHash2/3; keyed PRF as remedy | **C5 is this attack**; slide 37: "A multicollision works for any seed" | here restricted to words that are 6-bit packings of identifier characters, and measured on a scoped table | slides read (text extracted); paper listed |
| R9 | Linux kernel `Documentation/security/siphash.rst` (kernel.org/doc/html/latest/security/siphash.html); reference code github.com/veorq/SipHash | Linux, current | HalfSipHash-1-3 for hash tables on 32-bit machines | the keyed hash of C4 | none: it is used as designed | read; reference code compiled and compared |
| R10 | CVE-2012-0839 (OCaml `Hashtbl`), CVE-2012-0876 (Expat) | NVD, 2012 | hash flooding of name tables in language tooling | precedent that name tables fed by untrusted input are attacked | runtimes and parsers, not compiler symbol tables | listed (NVD entries via search) |
| R11 | rustc-hash README (github.com/rust-lang/rustc-hash) | Rust project, current | unkeyed fast hash in the compiler; "these attacks aren't a concern in the compiler" | the opposite design choice, argued for hosted compilers | supports the view that C4/C5 matter only when the input is untrusted | read (README via search) |
| R12 | MicroPython `qstr` (docs.micropython.org/en/latest/develop/qstr.html) | MicroPython, current | interned identifier pools with stored hash and length, in very little RAM | closest deployed relative of the interning part | no scopes, no undo, linear pool search, no failure guarantee stated | read (documentation) |
| R13 | US 8,505,000 B2, "Compilation method without explicit symbol table for saving memory" (patents.google.com/patent/US8505000) | Ezurio, 2013 | on-device compiler that stores declarations in the object code instead of a table | same constraint, different answer | no table at all | abstract read |
| R14 | DEC RADIX-50 | DEC assemblers, 1960s-70s | three characters per 16-bit word | precedent for sub-byte identifier packing | 40-symbol alphabet | memory |
| R15 | METIS-X (github.com/adhyan-jain/Metis) | course project, 2026 | Robin Hood table with inline names | direct predecessor and baseline | multi-allocation; refuses deep shadowing | read (source) |

Searches that returned nothing relevant (which shows only that these queries found nothing):
a published scoped symbol table with a hard memory budget and a failure guarantee; a
published hash-flooding attack on a C compiler's identifier table; a hash table with a probe
limit and refusal analysed for worst-case execution time; LIFO deletion in linear probing
stated for scoped tables.

## 4. Comparison

| Property | Appel / LLVM ScopedHashTable | TinyCC | MicroPython qstr | arena_chain (our baseline) | STRATA |
|---|---|---|---|---|---|
| Scopes with shadowing | yes | yes | no | yes | yes |
| One caller-supplied buffer, no allocator | no | no | pools | yes | yes |
| Defined refusal, state unchanged | no | no | not stated | yes | yes, tested exhaustively to depth 9 |
| Lookup cost independent of shadowing depth | yes | yes | n/a | yes | yes |
| No rebuild inside an operation | no | no | n/a | no | bounded mode |
| Bound on index probes per call | no | no | no | no | bounded mode |
| Keyed hash | no | no | no | no | optional |
| Bytes per live declaration (8 traces) | not measured | not measured | not measured | 16-18% more than STRATA | 27-36 |
| Replay time | not measured (re-implementations only) | n/a | n/a | **11-34% faster than STRATA** | baseline |

## 5. Scores

Scale: 0-2 none, 3-4 minor, 5-6 solid incremental, 7-8 clearly new, 9-10 major.

| Criterion | Weight | Before audit | After audit | Justification for the current score |
|---|---|---|---|---|
| Problem novelty | 10% | 4 | 4.5 | Scoped symbol tables are a 45-year-old problem and rarely a bottleneck. The fixed-budget, untrusted-input setting for on-device compilers is less studied, and no direct precedent was found, but the audience is small. |
| Methodological novelty | 25% | 3 | 4 | Every mechanism has a named precedent (R1, R2, R8, R9, R14). What is original is the combination and two small observations: LIFO removal in linear probing needs no tombstones, and a probe-limit refusal composes with the all-or-nothing guarantee when the index is static. Both are short arguments, not new algorithms. |
| Technical contribution | 20% | 5 | 6 | Two working single-buffer tables, a bounded mode, a keyed option checked against reference code, a 2.7 KB footprint on Cortex-M3. Solid engineering. |
| Differentiation from closest work | 15% | 5 | 5.5 | None of R1-R4, R12 offers a budget, a refusal guarantee or a probe bound. But the differences are properties of an implementation, and the strongest competitor on speed is the project's own conventional baseline. |
| Experimental strength | 15% | 6.5 | 7 | Real compiler events from two compilers, 13 tables, paired statistics, negative results reported, an independent re-run that reproduced the claims, an attack demonstrated and measured. Still one machine, replay rather than a compiler built on the table, emulation rather than hardware. |
| Reproducibility | 10% | 7.5 | 8.5 | Scripts for everything, pinned baselines (now by commit), stored raw data, a clean-copy verification of 12 steps, deterministic results identical or within 0.22%. Trace regeneration is not checksum-pinned. |
| Practical significance | 5% | 4.5 | 5 | Usable where a compiler or interpreter front end must run in tens of kilobytes on untrusted input; that is a narrow field, and nobody has used it. |
| **Weighted total** | 100% | **4.9** | **5.5** | 0.45 + 1.00 + 1.20 + 0.825 + 1.05 + 0.85 + 0.25 = 5.6, reported as 5.5 |

Confidence: **moderate** for the range 5-6, **high** that the value is below 7. The main
uncertainty is the literature search: about twenty web queries, no access to ACM DL or IEEE
Xplore full texts, several sources confirmed bibliographically only. A systematic review could
find a closer precedent (which would lower criteria 2 and 4) but is unlikely to raise them.

## 6. Evidence for and against

For:
- No surveyed design combines scopes, one buffer, a refusal guarantee and a probe bound.
- The decomposition result (most of the gain over METIS-X comes from arena storage, not from the new design) is a useful negative finding that is rarely published.
- The attack was not hypothetical: 32 768 valid identifiers, verified collisions under nine seeds, 223-fold slowdown, and both defences measured.
- The guarantees are tested far beyond what the earlier work did.

Against:
- The core algorithm is textbook (R1) and the hash attack is from 2012 (R8).
- On ordinary C code the conventional baseline is faster on all 8 traces; STRATA's only advantage there is 16-18% less memory, and a prefix-sharing extension evaluated during the audit would add only 1-13% (section 8).
- The keyed hash costs 22-33% of replay time, which a paper must state next to the benefit.
- Symbol tables are a small part of a compiler; the chibicc integration showed no end-to-end gain.
- No hardware, no second machine, no C++ workloads, co-authors have not reviewed.

## 7. Is 8/10 reachable?

Not with honest scoring of the current work. Reaching a weighted 8 needs criteria 2 and 3
(45% of the weight) near 8 or above, that is a contribution a reviewer would call clearly
new. Options, in decreasing order of credibility:

| Step | What it would change | Realistic effect on the total | Cost |
|---|---|---|---|
| A | Replace TinyCC's own tables with STRATA (not just replay), build the compiler for a real Cortex-M board, compile untrusted input on the device under a fixed budget, measure time, memory and the attack end to end | experimental 7 -> 8.5, practical 5 -> 7, technical 6 -> 7: total about 6.2 | weeks; needs hardware |
| B | A machine-checked proof (for example in Coq, Isabelle or with a bounded model checker on the C++ code) of the invariants and the all-or-nothing property | technical +1, methodological +0.5: total about 6.0 | weeks; needs the skill |
| C | A probabilistic analysis of the probe limit: for a keyed hash at load 3/4, a bound on the probability that a table of n names refuses a declaration at limit L, checked against measurement | methodological 4 -> 5.5: total about 5.9 | days to weeks; this is where a real theoretical contribution could come from |
| D | Systematic literature review, C++ and other-language front ends, a second machine | differentiation and experimental +0.5 each: total about 5.7 | days |
| A + B + C + D together | | about 6.8-7.2 | months |

Even the combination stops near 7, because the method remains a known algorithm in a new
setting. An 8 would need a different research question, for example a data structure with a
provable space bound near the information-theoretic minimum for scoped dictionaries, or a
new result about deletion order in open addressing. That would be a new project, not an
improvement of this one, and the brief forbids replacing the method to obtain a score.

## 8. Experiments tried during the audit that did not help

- **Prefix sharing of names.** Because names are removed in LIFO order, a new name could safely refer to an older name's leading words. A simulation of STRATA's layout on the 8 traces (`scripts/audit/kill_prefix.py`; its no-sharing result matches the measured minimum buffers to within the 64-byte resolution of that measurement; output in `artifacts/kill_prefix.log`) gives 0.9-10.4% less peak memory when sharing with the previous record (median 2.7%) and 1.2-12.7% in the best possible case, any live record (median 4.5%). Not implemented: too small to carry a paper, and it would slow lookups further.

## 9. Suitable framing for a paper

A systems or experience paper, not an algorithms paper: "Bounded memory and bounded work for
scoped symbol tables: what a compact design buys, what it costs, and how to keep it safe on
untrusted input." Lead with the decomposition and the negative timing result, then the
bounded mode and the attack as a second contribution, and state plainly that the mechanisms
are known. Workshop or regional-conference level is the realistic target; that is a judgment,
not a prediction.

## 10. Threats to the validity of this assessment

- Limited search (section 5). Sources at level "listed" were not read.
- The scorer also wrote the audit's additions (C4-C6); independent reviewers may weigh them lower.
- The "before" column re-scores the earlier work on a rubric it was not written for; the project's own earlier figure of 4.5 used different criteria.
- The rounding from 5.6 to 5.5 is deliberate and conservative.
