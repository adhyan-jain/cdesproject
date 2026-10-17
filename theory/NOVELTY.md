# Novelty audit of the theory manuscript

2026-10-18. One assessor's judgment (an AI assistant, see `../docs/AI_USE_DISCLOSURE.md`) after a
limited literature check. It is meant to be attacked. Every claim below is classified by what
the evidence supports; the manuscript was edited to claim no more than this file does.

## 1. Claims and their status

| # | Claim (manuscript) | Status | Why |
|---|---|---|---|
| 1 | **Undo** (Thm 2, Cor 3): for every non-reordering open-addressing scheme, popping the newest key by clearing its cell is an exact undo; the table is always the insertion-only table of the live sequence; insertion-only laws hold at every moment | **new as a stated theorem; elementary** | no source found stating it (searches below). Likely folklore in backtracking code; the *statement for a general class of schemes, with the transfer of distributional results*, appears unpublished |
| 2 | **Exactness** (Thm 4, Remark 1): stack order is the *only* deletion order for which clearing is safe for every hash assignment (greedy schemes) | **new to our knowledge; simple** | no source found; the converse is what turns the observation into a characterization |
| 3 | **Orphans** (Prop 5): clearing a random live key orphans on average the mean displacement, `alpha/(2(1-alpha))` | **small** | a short corollary of Knuth's displacement; quantifies the cost of leaving the discipline |
| 4 | **Separation by deletion order** (Cor 6) | **observation, conditional** | combines Thm 2 with Farach-Colton, Krapivin, Kuszmaul (FOCS 2024) and the dynamic lower bound they cite from *Tiny Pointers*; part (ii) is quoted, not proved here |
| 5 | **Refusal probability** (Thm 7, Cor 8) | **classical content; new use** | the quantity is the tail of the unsuccessful-search cost; its exact generating function and Poisson limit are in Janson-Viola (Algorithmica 2016, Thm 11.1, Eq. 11.4) and Knuth's run-length analysis. **Not claimed as new**: the law. **New**: an elementary derivation of an explicit finite-size sum; the proof that the Chernoff-type bound used for probe limits loses a factor `Theta(L^{3/2})`; the design table (258 vs 455); validation against a real probe-limited table |
| 6 | **Key lifetime** (Props 10-12) | **small; model-based** | adaptivity against hash tables is known (Lipton-Naughton 1993; Naor-Yogev 2015); new is the exact accounting for a probe-limited table, with a fresh-key theorem and a persistent-key attack cost. No timing measurement |
| 5b | **Uniform probing** (paragraph "Other probing rules") | **trivial maths; useful comparison** | refusal probability `C(n,L)/C(m,L)` for any occupied set, so probe limits about five times smaller than for linear probing (49 vs 258 at load 3/4); stated for design guidance, not as a theorem |
| 7 | **Space ledger** (Prop 13, Table 4) | **new for this design; accounting** | exact identities for five layouts; shows the earlier 16-18 % saving over the repository's baseline is a stored hash word plus packing, with interning space-neutral. Corrects an impression left by the earlier empirical paper |

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
   transfer of distributional results (Cor 3, Cor 6), and the converse (Thm 4).
2. The literature search is limited and several items are at bibliographic level only.
3. Claim 4 is only as strong as the quoted results; its part (i) is immediate from Thm 2.
4. Claim 5's new parts are modest by design; the law itself must be credited.
5. The attack results of claim 6 are not timing measurements.

## 5. Verdict

A correct, carefully checked, but **modest** contribution: an elementary yet previously
unstated characterization of stack-ordered deletion (claims 1-2) with a conditional
separation (4); a refusal-probability analysis whose law is classical but whose use, gap to the
earlier bound and validation are new (5); a precise key-lifetime rule (6); and an exact space
decomposition (7). It is not a deep technical result and the manuscript does not present it as
one. The novelty work is complete in the sense that every claim is classified, attributed
and limited as above; it cannot be strengthened further without new mathematics (candidates
that would: a trajectory-level law for refusals over a whole run, the refusal probability for
quadratic probing and double hashing, a machine-checked development).

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
