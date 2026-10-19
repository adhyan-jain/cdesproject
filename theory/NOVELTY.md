# Novelty audit of the theory manuscript

2026-10-18. One assessor's judgment (an AI assistant, see `../docs/AI_USE_DISCLOSURE.md`) after a
limited literature check. It is meant to be attacked. Every claim below is classified by what
the evidence supports; the manuscript was edited to claim no more than this file does.

## 1. Claims and their status

| # | Claim (manuscript) | Status | Why |
|---|---|---|---|
| 1 | **Undo** (Thm 2, Cor 3): for every non-reordering open-addressing scheme, popping the newest key by clearing its cell is an exact undo; the table is always the insertion-only table of the live sequence; insertion-only laws hold at every moment | **new as a stated theorem; elementary** | no source found stating it (searches below). Likely folklore in backtracking code; the *statement for a general class of schemes, with the transfer of distributional results*, appears unpublished |
| 2 | **Exactness** (Thm 4, Remark 1; Sanders arXiv:1808.04602 Sect. 2 has the single-deletion test): (a) for a given table the clear-safe deletion orders are exactly the linear extensions of the dependency relation `y < x` iff `y`'s probe path passes through `x`'s cell; (b) stack order is the *only* order safe for every hash assignment (greedy schemes) | **new to our knowledge; simple** | no source found; (a) is the exact characterisation of what a given table permits, (b) the universal converse, now derived from (a) |
| 3 | **Orphan law** (Prop 5): `orph(x) = Y_c - 1` with `Y` the queue length of the linear-probing chain; mean `alpha/(2(1-alpha))` (Knuth's displacement); explicit finite-size law (Lukasiewicz-path weights, exact); limit law = discrete M/D/1 queue, so the fraction of keys removable out of order is `(1-alpha)(e^alpha-1)/alpha` | **limit law is Janson's (TALG 2005, Thm 8.1, Eq. 8.4: Robin Hood displacement, `p(0) = (1-alpha)(e^alpha-1)/alpha`; his Sect. 2.2 has `H_{j+1} = X_{j+1} + (H_j-1)^+` and Rem. 3.3 the queue)**; new: the reading as orphans of a deletion, the exact finite-size law, order-independence | prior-art search (second pass) verified by hand that the generating function of `p_{j+1}/alpha` equals Janson's `psi^RH`; Janson never mentions deletion |
| 4 | **Probe complexity under stack discipline** (Thm 6) | **corollary-level but complete and tight; conditional on FKK** | exact transfer (Thm 2) + FKK 2024 upper bounds (elastic, funnel; Def 1 fit now checked against their Sections 2-3) + FKK lower bounds (Thm 5: Omega(log 1/delta) any non-reordering scheme; Thm 4: Omega(log^2 1/delta) greedy) give Theta(log 1/delta) / Theta(log^2 1/delta) for worst-case AND amortised cost under stack discipline (oscillation at the worst load makes amortisation vanish): strictly between insertion-only amortised O(1) and random-deletion delta^-Omega(1) (Tiny Pointers Thm 3, quoted). No source found stating the stack-discipline optimum |
| 5 | **Refusal probability** (Thm 7, Cor 8) | **classical content; new use** | the quantity is the tail of the unsuccessful-search cost; its exact generating function and Poisson limit are in Janson-Viola (Algorithmica 2016, Thm 11.1, Eq. 11.4) and Knuth's run-length analysis. **Not claimed as new**: the law. **New**: an elementary derivation of an explicit finite-size sum; the proof that the Chernoff-type bound used for probe limits loses a factor `Theta(L^{3/2})`; the design table (258 vs 455); validation against a real probe-limited table |
| 6 | **Key lifetime** (Props 13-15) | **small; model-based** | adaptivity against hash tables is known (Lipton-Naughton 1993; Naor-Yogev 2015); new is the exact accounting for a probe-limited table, with a fresh-key theorem and a persistent-key attack cost. No timing measurement |
| 8 | **Refusal-free fill** (Thm 10; recurrence = Aguilar-Fraga et al. Thm 3.7, OEIS A365623; the l=1 EGF is 1/(2-e^z)): exact probability that a monotone fill to `n` keys has no refusal, `n! m^-n (m/k) [z^n] Phi_L(z)^k`, with `Phi_L` the EGF of `l`-interval parking functions (`l = L-1`), a closed form `e^-Q / (1 - L int e^-Q)` from a Bernoulli ODE, and a design table | **known combinatorics, new use** | the counting sequence is that of `l`-interval parking functions (Colaric et al. 2021; Aguilar-Fraga et al. 2024, which give recursions and generating functions for specific `l`); the almost-full-table decomposition and a nonlinear ODE are in Alharbi-Banderier-Bouillaguet (AofA 2026) for a *different* process. Not found: the ring with `n<m` as a refusal-free-fill probability, the closed form, or its comparison with the union bound. Practical effect: the whole-fill probe limit is 24 % lower than the earlier `N R_max` rule at m = 4096, eps = 1e-6 (306 vs 402) and within 2 % of the sum rule |
| 9 | **Unlimited run at fixed occupancy** (Prop 11): `P(W=0)` = probability that every block has at most `L` cells = truncated-Borel coefficient ratio; `E[(1-W/m)^N]` for N push/pop pairs; extra limit ~ `ln m / ln(1/rho)` | **small; asymptotics known (Pittel 1987, largest cluster)**; exact finite-size values and the link to exact undo are ours | checked against enumeration (80 cases, exact rationals); design table 242 -> 349 at m = 4096 |
| 10 | **Bounded churn above a persistent trunk** (Prop 12): a refusal anywhere in a schedule that keeps at most `s` keys live above a never-popped trunk implies that the trunk has a window of `L` cells with at most `s-1` empty cells; so `P(refusal) <= V_s`, schedule-free, and `V_s` is the supremum (attained as the number of fresh chains grows, with an explicit rate `V_s (1 - e^(-N/m^s))`). Gap law: cyclic sums of `s` consecutive exchangeable gaps; closed-form up-crossing bound `D_s`. | **modest but new as stated; elementary proof** | `V_1` is the s=1 case of the unlimited-run law (claim 9). The general framework is classical: a scan statistic of sums of consecutive spacings (Naus; Glaz-Balakrishnan style); two web searches (2026-10-18) found no treatment of the linear-probing instance 'a window of `L` cells with at most `s-1` empties', and no source was read in full, so this is 'not found', not 'absent'. What is ours is the reduction (any refusal in a bounded-churn schedule implies vulnerability; vulnerability is the supremum) and the exchangeable-gap formulation with the closed-form up-crossing bound. The bound is conservative for short runs (the supremum needs about `m^s` chains) and vacuous for wide-band schedules. |
| 5b | **Uniform probing** (paragraph "Other probing rules") | **trivial maths; useful comparison** | refusal probability `C(n,L)/C(m,L)` for any occupied set, so probe limits about five times smaller than for linear probing (49 vs 258 at load 3/4); stated for design guidance, not as a theorem |
| 7 | **Space ledger** (Prop 16, Table 4) | **new for this design; accounting** | exact identities for five layouts; shows the earlier 16-18 % saving over the repository's baseline is a stored hash word plus packing, with interning space-neutral. Corrects an impression left by the earlier empirical paper |

## 2. What the manuscript may and may not claim

May: an elementary but previously unstated characterization of stack-ordered deletion in
open addressing (claims 1-2); a quantified cost of leaving it (3); a conditional separation (4);
the refusal probability as a design tool with a proven gap to the bound used before (5); a
precise key-lifetime rule (6); an exact space decomposition (7).

May not: that the refusal law, its Poisson limit or the tail structure are new; that the
separation is proved unconditionally; any timing result; any statement about hardware; that
the proofs are machine-checked.

## 3. Closest prior work and how it was checked

| Work | What it covers | Checked how | Overlap |
|---|---|---|---|
| Knuth, TAOCP vol. 3, 6.4 | exact finite-size analysis of linear probing, run lengths via Abel-binomial counting | lecture notes by Zwick built on it (read); book not re-read | **claim 5** (the law) |
| Janson, Viola, *A unified approach to linear probing hashing with buckets*, Algorithmica 75(4), 2016 | exact generating function of the unsuccessful-search cost (Thm 11.1), Poisson limit `(1-alpha) P(B > k)` (Eq. 11.4) | section 11 read in full (arXiv 1410.5967) | **claim 5** (the law and the limit) |
| Flajolet, Poblete, Viola 1998; Pittel 1987; Janson 2001, 2005; Viola 2005 | cost distributions and extremes of linear probing | bibliographic record verified (Crossref); not read in full | background for 5 |
| Farach-Colton, Krapivin, Kuszmaul, FOCS 2024 | insertion-only bounds for open addressing without reordering; dynamic case stated as open for linear probing | primary text read (arXiv 2501.02305) | **claim 4** |
| Bender et al., *Tiny Pointers*, TALG 2025 | the dynamic lower bound (Thm 3, tiny-pointer size `Omega(log delta^{-1})`) | primary text of Thm 3 read (arXiv 2111.12800); reduction to probe index not re-proved | claim 4 |
| Sanders, *Hashing with linear probing and referential integrity*, arXiv 2018 | tombstone-minimising, position-stable linear probing for arbitrary deletion order | full text read; no stack/LIFO/undo statement | nearest relative of claims 1-2; different problem |
| Jimenez, Martinez, ANALCO 2018; Bender, Kuszmaul, Kuszmaul, FOCS 2021 | deletion in linear probing / tombstones, arbitrary order | bibliographic level | context for 2 |
| Naor-Teague 2001; Blelloch-Golovin 2007 | history independence (layout a function of the set) | bibliographic level | weaker than claim 1 (here: function of the sequence) |
| lcc symbol table (Fraser-Hanson); Appel; LLVM `ScopedHashTable` | scoped tables with undo | lcc `sym.c` read; others by documentation | application area, no analysis of the table |
| Lipton-Naughton 1993; Naor-Yogev 2015 | timing/adaptive adversaries against hashing | bibliographic level | claim 6 |
| Alharbi, Banderier, Bouillaguet, *Bounded Linear Probing Hashing*, AofA 2026 (LIPIcs 381, art. 28) | a bounded-probe linear-probing *process* (keys exceeding `p` probes are discarded and redrawn); expected number of attempts to fill the table; lists the success probability at a given fill ratio as open | abstract, introduction, Section 3 and conclusion read | different quantity from claim 5; must be cited; our law is for the table the unlimited process would build, equal to the bounded process only up to its first refusal |
| US 9,104,678 B1 | probe-limited open-address cache (evict or refuse at the limit) | first 100 000 characters of the page read; claims not read | the idea of a probe limit; no refusal-probability analysis found |

Searches that returned nothing relevant (this shows only that these queries found nothing):
LIFO / stack-ordered / undo / rollback deletion in open-addressing hash tables; trail or undo
log for hash tables in SAT or Prolog; a probe-limited table with an analysed refusal probability.
One web note observed that deleting an entry right after inserting it does not exactly restore
a Robin Hood table, which is consistent with claims 1-2 (relocation breaks exact undo) but is
not a citable source.

## 4. Residual risks to the novelty claims

1. Claims 1-2 may be known: undo logs are routine in backtracking systems, and a reviewer may
   call the theorem trivial. The defence is the generality (any non-reordering scheme), the
   transfer of distributional results (Cor 3, Thm 6), and the converse (Thm 4).
2. The literature search is limited and several items are at bibliographic level only.
3. Claim 4 is only as strong as the quoted results; its part (i) is immediate from Thm 2.
4. Claim 5's new parts are modest by design; the law itself must be credited.
5. The attack results of claim 6 are not timing measurements.

## 5. Verdict

A correct, carefully checked, but **modest** contribution (after the second novelty pass: the strongest items are claims 2-3 and the closed-form refusal-free-fill law of claim 8, whose combinatorial core is known): an elementary yet previously
unstated characterization of stack-ordered deletion (claims 1-2: undo, the exact set of safe
deletion orders of a table as the linear extensions of a dependency relation, and stack order as
the only universally safe one), an exact law for the number of dependent keys (claim 3, the
strongest new mathematics in the manuscript) with a conditional
separation (4); a refusal-probability analysis whose law is classical but whose use, gap to the
earlier bound and validation are new (5); a precise key-lifetime rule (6); and an exact space
decomposition (7). It is not a deep technical result and the manuscript does not present it as
one. The novelty work is complete in the sense that every claim is classified, attributed
and limited as above; it cannot be strengthened further without new mathematics (candidates
that would: a trajectory-level law for refusals over a whole run, the refusal probability for
quadratic probing and double hashing, a machine-checked development).

## 5a. Second pass (2026-10-19): independent referee and prior-art search

A cold adversarial referee (a separate model run) and a prior-art search were run. Referee: no fatal error; every
formula checked by brute force matched; fixed in the manuscript: Remark 1 (Thm 4(b) needs probe sequences that start
anywhere and have a second distinct cell, and 'every assignment' means assignments that insert all keys), the
displacement definition in Prop 5, the false 'heavy tail' remark (the tail is geometric with ratio 1/z*, z = e^{a(z-1)}),
the Prop 5(b) window argument (now a monotone coupling), the 'up to the first refusal' proviso of Thm 6(i), the
elastic-hashing assumption (counters kept as functions of the occupancy), Prop 13 (schedule fixed before the key is
drawn), and several abstract overclaims. Prior art: claim 3's limit law is Janson 2005 (credited); claim 8's recurrence
is Aguilar-Fraga et al. (credited); claim 2 single-deletion test is Sanders 2018 (credited); no source found for the
LIFO level of the workload hierarchy or for the order-level characterisation. A separate independent re-implementation
(not reading the repository's checks) reproduced Thm 4(a), the finite-size orphan law and Thm 10 exactly.
Note: the referee still flags that the Theta-optimality of Thm 6 rests on FKK theorem numbering/conditions that were
read but not re-verified line by line.

## 5c. Third pass (2026-10-19): two outside suggestions checked

* **Petersson (Uppsala thesis 2009, Janson and Louchard advising): asymptotic distribution of the maximum displacement
  of linear probing**, nearly full (Paper I) and all loads in (0,1) (Paper II). A refusal-free fill with limit L is the
  event max displacement < L (keys never move), so the large-m behaviour behind claims 8 and 9 is expected to follow
  from it. Not extracted (thesis text not read). Re-tagged: exact finite-size forms and design values are ours; the
  limit regime is likely Petersson's. Credited in the manuscript.
* **Krapivin-Kuszmaul-Wang, arXiv:2607.17494 (Jul 2026, v2 Sep 2026), interlinear probing**: stable non-greedy linear
  probing, O(x log x) worst-case expected insertion for the first (1-1/x)n insertions (x <= n^0.49 known in advance),
  lower bound Omega(x sqrt(log x)) for any stable strategy. Layer chosen from layer occupancies plus a private routing
  coin, so it plausibly fits Def 1 (read in the primary text; not proved). Added as Thm 6(iv) and a table row: under
  stack discipline stable linear probing is x (log x)^Theta(1) against Theta(x^2) greedy. Also noted: Zamir,
  arXiv:2607.16390 (locality lower bound, insertions only).
* **Bounded-process success probability** (Alharbi-Banderier-Bouillaguet's open question): their conclusion asks for the
  number of successful insertions with at most p = alpha n probes, i.e. the discard-and-redraw RETRY process. That is
  a different process from our refuse-and-stop event; dropped as our problem.
* **Refusal law for arbitrary scope trees**: simulated on random depth walks (m = 256): the union bound (Prop 9) is
  3.6-7x too large; observed refusal probability is within ~2x of P(W>0) (Prop 11) at the deepest depth reached.
  A first-bad-node union bound is even looser (failures cluster on shared prefixes: a Cox-mixture structure). No
  depth-profile statistic was found; a rigorous limit theorem (Chen-Stein under strong dependence) remains open work.
  Not claimed as a result; recorded as an observation in Section 4.
  Partial result after a bounded attempt (2026-10-18): for a persistent trunk with churn of height at most `s` the
  question has an exact schedule-free answer (claim 10, Prop 12). The general wide-and-deep tree remains open.

## 5b. Directions tried and dropped (2026-10-19)

* **Uniform probing is optimal for the refusal probability among non-reordering schemes**: false. A search over
  probe-sequence distributions on m = 4, 5 found schemes whose refusal probability at high load is far below
  `C(n,L)/C(m,L)` (e.g. 0.087 against 0.25 at m = 4, n = L = 3). This agrees with Farach-Colton, Krapivin, Kuszmaul
  (funnel hashing beats uniform probing); not a new result.
* **Trajectory law for monotone fills**: derived (claim 8), but the combinatorics is known; kept as an application.
* **Success probability of the bounded process with redraws at a fill ratio** (listed as open by Alharbi et al.): not
  attempted; it is a different, hard problem.

## 6. External review of the claims (2026-10-18) and what was done with it

A reviewer who could not open the repository judged the claims from their statements alone.
Triage, after checking each point against the sources and the manuscript:

| Point raised | Verdict | Action |
|---|---|---|
| Bounded linear probing (AofA 2026) anticipates claim 5 | **wrong as stated**: that paper counts attempts to fill the table and lists the success probability at a fill ratio as open | read it; cited and positioned (related work); added to the table above |
| "Every insertion-only analysis transfers" overclaims (amortised and cumulative costs do not) | **valid** | abstract, contribution C1 and Corollary 3 now say: table state and cost of the next operation only |
| Corollary 6(i) may fail for elastic hashing if it is not occupancy-determined | **valid concern, already flagged** | Corollary 6(i) now states the proviso (scheme satisfies Definition 1) explicitly |
| The Tiny Pointers bound is a pointer-size bound, not a deletion-order bound | **already stated in the manuscript** (Section 3.2); the reduction is FKK's and is quoted | none; remains a stated limitation |
| Claim 2: backward-shift deletion handles arbitrary orders; a stored-counter scheme "breaks" the only-if | **not a counterexample**: the theorem is about clearing without moving keys, and a scheme with a stored counter is outside Definition 1 and outside greedy first-empty-stop | none |
| Claim 1 is a corollary of insertion-order invariance of the occupied set | **partly fair**: the invariance concerns the set, the undo theorem concerns the exact layout, but it is elementary | already classified "elementary" here |
| The `L^{3/2}` gap compares against a weak bound | **fair**; it corrects this repository's own earlier bound and is presented as such | wording unchanged |
| Claims 6-7 are bookkeeping | **agreed**, classified "small" / "accounting" | none |
