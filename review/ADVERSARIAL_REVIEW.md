# Adversarial review of STRATA / cdesproject

2026-10-17. Reviewer: Claude (Sonnet 5.5), working in a fork of `shubhisingh1510/cdesproject` at
`main` = `ef8345f`. Scope: the claims of `paper/body.tex`, `NOVELTY_GATE.md`, `include/strata/strata.hpp`,
`docs/CORRECTNESS.md`, `docs/PROBE_LIMIT_ANALYSIS.md`. Goal: find what breaks, then what to build so
that a **non-empirical** paper can stand on its own.

What was and was not checked is stated in section 6. Nothing here has been committed or pushed.

## 1. Bottom line

* The engineering is sound and reproducible. The two propositions are **correct as stated**.
* The paper's weakness is not errors. It is that (i) the novelty is thin and the authors say so
  themselves (their own rubric: 6.0/10, "workshop level"), (ii) the headline memory result rests on a
  baseline the authors wrote and the gate admits is not the strongest, (iii) the **security claim for
  the keyed bounded mode is not justified against an adaptive adversary**, and (iv) the probe-limit
  analysis is loose enough to give a wrong recommendation (512 where ~260 suffices).
* Two openings for a real theory contribution exist (section 4): a **separation result for
  stack-ordered deletions in open addressing**, and an **exact probe-limit law**.

## 2. Attacks that failed (claims that held up)

| Attack | Result |
|---|---|
| Re-run the test suite on a different toolchain (g++ 16.2.1; authors used 11.4) | `2732358 checks, 0 failed`; exhaustive depth 7: 2 239 488 sequences, 0 failures. Matches the paper's count exactly |
| Proposition 1 (canonical state): look for an operation that breaks the induction | none found. Redeclaration, shadowing, exit, refusals all covered. Holds for the fixed index, as stated |
| Proposition 2 proof (interval + Chernoff): wrap-around, adaptivity of the table content | proof is valid; the bound is correct, only loose (see F4) |
| Collision algebra in the attack (`hash_step`, bit 18 -> bit 31, multiply by 5) | correct; the cancellation across two words is as described |
| Memory formula (eq. 1) against `declare()` / `exit_scope()` | consistent with the code |
| Probe-count identity: exact law below reproduces Knuth's mean `1/2(1+1/(1-a)^2)` | matches to 3 decimals at four loads |

## 3. Findings (most serious first)

**F1 (critical). Proposition 2 is applied to adversarial input without justification.**
`body.tex` section "Keyed Hash": "With a keyed hash, Proposition 2 applies to adversarial input under that
assumption". PRF security makes home slots look independent for names chosen *without feedback*. The
probe limit creates feedback: a refusal (and, realistically, timing) tells the author of the source
which names share a home slot. The key never has to be recovered.
*Check run* (`theory/verify/adaptive_key_demo.cpp`, 5 seeds; the first single-seed run in
`review/adaptive_oracle_check.cpp` reported 9.2 %, which was an overestimate: it used 1000 honest names
and one seed): keyed bounded table, m = 2048, L = 512, key unknown to the attacker, persistent across
compilations. Oracle = `Stats::longest_probe` (an idealised stand-in for a timing channel, **not a
measured timing attack**). Learning one same-home name cost about 2 071 queries (about m, as a geometric
argument predicts). Declared first in a fresh table, the learned names cause **1 % to 5.5 %** of 700
subsequent honest names to be refused, against 0.00 % for random names and 0.00 % when the same names
meet a freshly keyed table. The probe limit itself caps a single-home attack at L - 1 stored names, so
the damage comes from honest names extending the planted cluster. The threat model excludes "key
recovery" and timing precise enough for it, but this attack needs neither. Fix direction: key lifetime = table lifetime (rekey per translation unit) plus a theorem
(section 4, T3). On a Cortex-M3 class device that requires an entropy source per unit, which the repo
says it does not address.

**F2 (critical). The threat model never says who the victim is.** The adversary supplies *all* names
(section Threat Model), so "legitimate declarations refused" is only meaningful if trusted and untrusted
names share one table (a trusted prelude/headers plus attacker code). Without that scenario R5 under
attack is vacuous. The guarantee that does not depend on any hash assumption is R4 (bounded work per
call). The paper should separate the two goals and say which scenario motivates R5.

**F3 (critical for the empirical paper, avoidable for a theory paper). The 16.4-17.9 % memory saving
depends on the authors' own baseline.** `arena_chain` stores a chain link *and* a 4-byte hash per entry.
`NOVELTY_GATE.md` section 8 concedes a hash-free conventional table was not built. A conventional design
that keeps an open-addressed index over an entry stack and recomputes hashes is STRATA minus packing and
compact undo entries; the saving may shrink to a few percent. Calling `arena_chain` "the strongest
conventional design we could build" is therefore not supportable. Resolvable analytically (T4).

**F4 (major). The probe-limit analysis is too loose and states it inaccurately.**
Exact law (below) vs the paper's bound `rho^L/(1-rho)`, m = 65 536, 10^7 samples per cell:

| load | L | measured | exact (Borel law) | paper bound | bound / exact |
|---|---|---|---|---|---|
| 0.75 | 64 | 7.71e-3 | 7.74e-3 | 2.4 | 313 |
| 0.75 | 128 | 3.14e-4 | 3.30e-4 | 0.22 | 659 |
| 0.75 | 256 | 2.0e-7 | 1.14e-6 | 1.7e-3 | 1532 |
| 0.75 | 512 | 0 / 10^7 | **2.9e-11** | **1.1e-7** | 3850 |

The paper says the bound is loose "by about two orders of magnitude"; it is 140x to 7 500x, growing
with L. For a per-declaration refusal probability of 1e-6 at load 3/4 the bound demands L = 455, the
exact law needs **L = 260** (half-full index: 81 vs 52). The recommended 512 over-provisions by ~2x and
sets the worst-case scan to 2 KiB per call. The exact law is classical in form (cluster sizes in linear
probing are Borel-distributed; Knuth, Flajolet-Poblete-Viola, Janson) - the new part would be its use as
a refusal law for a probe-limited table and the resulting design rule.

**F5 (major). The "canonical state" property is a corollary of a more general fact, and the
related-work context is missing.** Clearing the slot of the newest key restores the previous state for
*any* non-reordering open-addressing scheme, not only linear probing. Missing from the paper:
(a) Sanders, "Hashing with Linear Probing and Referential Integrity", arXiv:1808.04602 - position-stable
linear probing with tombstone minimisation: the nearest prior art for "slots recorded elsewhere must not
move" (only the abstract page was read); (b) Knuth's backward-shift deletion (Algorithm R), which also
yields a canonical table for *arbitrary* deletion order but moves keys - the real reason STRATA cannot
use it is that undo entries store slot indices, and the paper never says so; (c) the
open-addressing-without-reordering theory (Farach-Colton, Krapivin, Kuszmaul, arXiv:2501.02305, which
lists dynamic linear probing as open) and the lower bound it cites (Bender et al., *Tiny Pointers*,
Thm 3; read directly, see T1 for what it does and does not say). Tiny Pointers also notes that dynamic
linear probing is analysed only for random deletions (Larson 1982), which is the other nearest prior
statement. **Literature status of T1:** web searches ("LIFO/stack-order/undo/rollback deletion in open
addressing") found no source stating it. That is absence from a few searches, not proof of novelty;
it is also likely that the undo observation is folklore in SAT/backtracking hash tables and in
persistent-data-structure code, which searches of the kind run here would not index.

**F6 (major). Verification is evidence, not proof.** 80.6M enumerated sequences cover 9 operations over
4 names in 8 tiny configurations; the fuzzer is differential against an author-written model. The
authors list a machine-checked proof as future work. For a non-empirical paper this is the most
credible way to raise the technical standard (section 4, T5).

**F7 (moderate). Timing evidence is unstable by the authors' own account** (verdicts on 6 of 8 traces
flip between two runs of identical code). A paper whose claims rest on "within about 10 %" cannot carry
a paper by itself.

**F8 (moderate). Prior art to read and cite, not verified here:** lcc (Fraser & Hanson, *A Retargetable
C Compiler*, 1995: arena-allocated per-scope symbol tables) and GCC's obstack-based scope/binding
structures are the nearest "arena + scope" designs; my search did not return their source. Also
unread: US patents titled "probe-limited open-address hashing" (US 9104678, 10204127, 11468033; a
caching technique) - prior art for the *probe-limited table* idea that must be read before the bounded
mode is called new. Also
verified-compiler work on allocation failure (CompCert's allocator/runtime is unverified per its own
page; CakeML not checked).

**F9 (process, not science).** The README states the work was produced by an AI assistant and that the
second author had not reviewed it; `SUBMISSION_READINESS.md` section 10 lists unresolved authorship,
AI-use disclosure and release items. A journal will require an AI-use statement and authors who can
defend every claim. These are human decisions and are not touched here.

**F10 (minor).** `NOVELTY_ASSESSMENT.md` still quotes "223x" for the flood slowdown; the paper and the
data give 300x (1 954 ms vs 6.5 ms at 32 768 names). Superseded text should be marked or removed.

## 3a. Status of each finding after the work of 2026-10-17

| Finding | Status |
|---|---|
| F1 adaptive adversary | formalised and quantified in the theory manuscript, Section 5 (Propositions on fresh key, persistent key, weak oracle); the library is unchanged |
| F2 threat model | addressed in Section 5 (what the adversary may observe) and in the key-lifetime rule |
| F3 baseline dependence | resolved analytically: Section 6 ledger; a hash-free conventional layout is within 0.4 % of the interned layout, and the saving over the repository's baseline is a hash word (9.2-12.2 %) plus packing (5.3-9.0 %); `docs/ADDENDUM_2026-10-17.md` |
| F4 loose probe analysis | replaced by the exact law (Theorem 7 of the manuscript): L = 258 instead of 455 at load 3/4, eps = 1e-6 (large tables); validated against the real table |
| F5 related work | covered in Section 7 of the manuscript; lcc read at source level; two items remain unread (Sanders beyond the abstract; the patent's claims) |
| F6 proofs only tested | the theory results are checked by exhaustive enumeration in exact arithmetic and by a statistical test; a machine-checked proof is still future work |
| F7 unstable timing | unchanged; the theory manuscript makes no timing claim |
| F8 prior art | lcc read; the probe-limited-cache patent read in part |
| F9 process | `docs/AI_USE_DISCLOSURE.md`; the human items remain open |
| F10 "223x" | corrected in `reports/NOVELTY_ASSESSMENT.md` by a pointer to `docs/ADDENDUM_2026-10-17.md` |

## 4. What would strengthen the novelty (non-empirical program)

Working thesis: **STRATA's algorithm is textbook, but its deletion discipline is a clean, general
object. Stack-ordered ("LIFO") deletion in open addressing is exactly analysable, and the analysis
exposes results the unrestricted-deletion literature does not have.** Each item below is a theorem
plus proof, not a new benchmark.

* **T1. Undo theorem and a separation (candidate headline).** For every non-reordering open-addressing
  scheme whose insertion writes one cell and updates restorable control state, LIFO deletion by clearing
  is exact undo, so the table after any push/pop sequence equals the insertion-only table of the live
  sequence. Consequences: (i) every insertion-only bound transfers *exactly* - Knuth for linear probing,
  and the Farach-Colton-Krapivin-Kuszmaul bounds (greedy O(log^2 d^-1), elastic O(log d^-1) worst-case
  expected) - versus the d^(-Omega(1)) amortised lower bound for dynamic open addressing that
  2501.02305 section 1 attributes to Tiny Pointers, Thm 3. **Checked against the primary text
  (arXiv:2111.12800 v-latest, section 5):** Thm 3 is a lower bound on tiny-pointer *size*, s =
  Omega(log d^-1) bits for variable-size tiny pointers at load 1-d, proved on a workload that alternates
  random insertions with deletions of random present elements. A pointer of value i costs about log i
  bits, so the bound gives expected probe index d^(-Omega(1)) (Jensen), but only for that
  **random-order** workload. The formal mapping from "dereference table" to "open addressing without
  reordering" must be written out in the paper, not assumed. That is a polylog-versus-polynomial
  separation by deletion order, once the mapping is proved. (ii) A converse: clearing is correct for *every* hash assignment iff the deletion order is
  consistent with reverse insertion order, so LIFO is the exact class for which tombstone-free,
  position-stable deletion works. Caveats: the amortised bound degrades to the worst-case-expected bound
  under an adversarial push/pop schedule at maximum load; and the literature check must find no prior
  statement.
* **T2. Exact refusal law for probe-limited tables.** Poisson-limit refusal probability
  `P(L) = (1-a) * sum_{n>L} (n-L) * Borel(n;a)` with `Borel(n;a) = e^{-an} (an)^{n-1} / n!`
  (derivation: linear probing = discrete M/D/1 queue; an occupied run is a busy period).
  **Done** (manuscript Theorem 7 and Appendix A): the finite-size form
  `R_m(n,L) = (k/m) * sum_{g>L} (g-L) * B(g) Q_{k-1}(m-g) / Q_k(m)`, k = m-n, proved by cutting the ring at
  its empty cells (each block is Borel distributed, by the cycle lemma); exact on all 258 enumerated
  cases, within sampling error of the real table; Poisson limit and the `~ C rho^L L^{-3/2}` tail proved;
  design rule L = 258 vs 455 (large tables, load 3/4, eps = 1e-6). The *de-Poissonisation* is not needed.
* **T3. Adaptive-adversary theorem and key-lifetime rule.** Formal game with a refusal/probe oracle:
  with a persistent key an adversary needs about m queries per collider and a run of length L costs
  about m*L queries irrespective of the PRF (consistent with the 1.42M queries for 700 names at
  m = 2048); with a fresh key per table and no intra-table feedback, Proposition 2 holds up to the PRF
  advantage. Output: the corrected statement of what the keyed mode guarantees.
* **T4. Exact space model and baseline family.** Turn eq. (1) into a theorem comparing STRATA with a
  parametrised family of conventional single-buffer designs (stored/recomputed hash, link width, packed
  or raw names, load factor): closed-form saving in shadowing factor and name length, crossover
  conditions, and the name-payload overhead against the log2(63) = 5.98 bits/char lower bound. This
  answers F3 without a new experiment and may *reduce* the headline saving - the paper must be allowed
  to say so.
* **T5. Mechanised refinement (optional, expensive).** A proof-assistant model of the buffer proving
  atomic refusal, canonical state and the probe bound against an abstract scoped-environment
  specification. Lean/Coq/Isabelle are **not installed** here.

Honest outlook: T1+T2+T3(+T4) together make a coherent theory-of-stack-disciplined-hashing paper with
a compiler motivating example. T1's proof is short and a reviewer may call it simple; its value is the
framing (deletion order as the variable) and the separation. Do not oversell it until the literature
check is done.

## 5. Decisions needed from the authors

1. Is "non-empirical" = theory/analysis paper (T1-T4, all claims proved, existing repo data used only
   for sanity checks)? Recommendation: yes.
2. Include T5 (mechanised proofs)? It needs installing a proof assistant and is the largest cost.
3. Authorship/AI-disclosure/IP (F9): who handles them, and which authors will sign off.
4. Venue choice is deferred until T1 survives the literature check.

## 6. Scope and limits of this review

Done: read paper, library, correctness and probe docs, gate and readiness files; reran the full test
suite; recomputed the probe tail independently against the stored 240M-sample simulation; built and ran
the oracle check; read the primary text of arXiv:2501.02305 and the abstract page of 1808.04602;
ran about 10 web searches.
Not done: benchmarks were **not** re-run (timing is machine-dependent); traces not regenerated; the
paper's table values were not independently re-derived from raw CSVs beyond the flooding ratio and the
probe table; the literature search is shallow (searches only, not a systematic review; *Tiny Pointers*,
Iceberg hashing, Bender et al. FOCS'21 and Knuth 6.4 were not read in full); lcc/GCC not inspected.
The derivations (T1-T4) are now written as proofs in `theory/paper/main.tex` and are validated by the
programs in `theory/verify/`; they are **not machine-checked and have not been read by the authors**. The oracle experiment uses an idealised oracle, not wall-clock timing.

Files: `review/borel_probe_tail.py` (run from `review/`), `review/adaptive_oracle_check.cpp`
(`g++ -std=c++14 -O2 -I../include`).
