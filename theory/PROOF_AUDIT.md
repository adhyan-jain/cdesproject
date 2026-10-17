# Proof audit of the theory manuscript

2026-10-18. An independent pass over every result of `paper/main.tex`, by the assistant that
wrote it (so not independent of its author's blind spots; see "How to attack this"). For each
result: what the proof relies on, what was re-derived, which program checks it, and the residual
risk. Numbering is the manuscript's. All programs are in `verify/` and run by
`bash verify/run_all.sh` (each exits non-zero on a violation).

| Result | Proof relies on | Re-derived / checked | Machine check | Residual risk |
|---|---|---|---|---|
| **Thm 2** Undo | induction; insertion changes exactly one cell, which was empty | each step re-derived; refused push and pop cases covered | `lifo_check.py` A: 488 919 state comparisons, 5 insertion rules incl. a non-greedy one, 0 failures | low |
| **Cor 3** Marginals | Thm 2 + i.i.d. probe sequences + obliviousness | needs the live names distinct and (for later moments) "up to the first refusal" | follows from Thm 2; Thm 7 check on the real table uses it | low; the "first refusal" proviso is essential |
| **Thm 4** Exactness | (a) cells before `c(y)` on `y`'s path were occupied at insertion and keys never move; (b) pair argument: for `i<j`, distinct homes for `x_1..x_{j-1}` and `h(x_j)=h(x_i)` force `x_j < x_i` | re-derived; (b) is now derived from (a) (the earlier first-deviation proof was replaced) | `orphan_law.py` P: safe orders == linear extensions of the dependency relation, 397 562 (assignment, order) pairs, linear m<=5, 0 mismatches; `lifo_check.py` B: 18 settings, exactly one universally safe order | low for linear/quadratic; **Remark 1 (all greedy schemes) is argued, not enumerated beyond quadratic** |
| **Prop 5** Orphans | (a) `Y_c` recursion and pair counting; (b) window argument + Poisson limit of home counts + M/D/1 balance equations; (c) Lukasiewicz-path weights `F_u(h)`, Borel-Tanner for the remainder | (a) re-derived; (b) the limit proof is a standard-style argument, rate not proved; (c) re-derived against the Step 1-3 machinery | `orphan_law.py` O: finite-size law == enumeration of every home sequence (10 settings, exact rationals); M/D/1 pmf sums to 1 and has mean `alpha/(2(1-alpha))`; finite law at m=64,128,256 within 0.019/0.0096/0.0048 (alpha=1/2) of the limit; `lifo_check.py` C; `proof_checks.py` mean 1.502 +/- 0.008 | **low-medium**: (b) is the least formal step (local convergence), though the numbers agree |
| **Thm 6** Probe complexity under stack discipline | (i) Thm 2 + fresh probe sequence independent of the table; oscillating workload at the worst load; (ii) FKK Thms 1, 2, 4, 5; (iii) quoted | (i) re-derived; FKK statements and the funnel/elastic algorithm descriptions read in the primary text (arXiv 2501.02305, Sections 2-5); funnel = first free cell of a fixed probe sequence, elastic = function of batch, fullness of two arrays and cell freeness | none (external results); the transfer in (i) is the checked Thm 2 | **medium**: elastic fit rests on reading that its batch/fullness state is a function of occupancy counts on reachable states; quoted bounds are FKK's with their conditions on `delta` |
| **Thm 7** Refusal law | block decomposition, cycle lemma, Borel-Tanner identity, exchangeability (Appendix A, 4 steps) | every step re-derived, including the pattern condition (eq. 2), the weight `B(g)`, the normalisation `(m/k) Q_k(m)` and the offset count `(g-L)^+` | `exact_law.py`: 258 `(m,n,L)` triples, exact rational arithmetic vs enumeration of every home sequence, 0 mismatches; `run_law_check.py`: real `strata::Table`, 7 settings x 400 000 trials, max abs z 1.96, bounded and unbounded tables in lockstep, 0 mismatches; agrees with the stored 240M-sample simulation; **independent derivation** by Knuth's Abel-binomial counting (`proof_checks.py`): equal in 481 cases, exact for m <= 14 and to 2e-10 relative for m up to 2^20 | low (and the law is classical: Janson-Viola Thm 11.1, Eq. 11.4) |
| **Cor 8**(a) monotone | order independence of the occupied set; superset coupling | re-derived | the table of exact limits is monotone in load | low |
| **Cor 8**(b) limit | pointwise convergence of `pi_g` (ratio formula written out) and the exact identity `R = (k/m)[m/k - sum_{g<=L} g pi_g - L(1 - sum_{g<=L} pi_g)]`, which involves finitely many terms | the identity replaces the earlier uniform-integrability argument | `orphan_law.py` O: the identity in exact rationals, 125 cases; `proof_checks.py`: relative error to the Poisson limit shrinks with m | low |
| **Cor 8**(c) tail | Stirling + dominated convergence | re-derived | `proof_checks.py`: exact/asymptotic ratio 0.472, 0.772, 0.929, 0.981 at L = 64, 256, 1024, 4096 (converges at rate about `1/((1-rho) L)`) | low |
| **Thm 10** Refusal-free fill | block decomposition at empty cells; last-key decomposition of a filled line (`A_L` recursion); Bernoulli ODE `Phi' = Phi (L Phi - P_L)`; union bound | re-derived; the `(m/k)` cyclic factor and the interleaving counts checked against enumeration | `fill_law.py`: equals brute force over every home sequence (135 `(m,n,L)` cases, exact rationals), the closed form equals the recursion to degree 12 for `L` in {1,2,3,4,5,7}, float and 60-digit decimal evaluations agree with the exact one, `1-P <= sum_t R_t` on test cases | low-medium: the large-`m` values (Table 2) rest on the recursion, which was verified exhaustively only for `m <= 8` |
| **Prop 9** Run | Cor 3, Cor 8(a), union bound | re-derived; requires names distinct from live ones | none beyond Thm 7 | low |
| **Props 11-13** Keys | ideal-hash model; coupon collector; geometric trials | re-derived | `adaptive_key_demo.cpp`: about 2 071 queries per collider (m = 2 048), 1-5.5 % honest refusals with a persistent key, 0 % otherwise (illustration of Prop 13, idealised oracle) | low for the statements; **the model oracle is not a timing channel** |
| **Prop 14** Ledger | subtraction of the stated layout formulas | re-derived | `proof_checks.py`: the four identities hold at 848 449 instants of the eight traces; closed forms equal the independent simulation's peaks for all 5 layouts x 8 traces; `space_model.py` reproduces all 24 measured minima of the repository exactly | low |

## Second pass (2026-10-19)

An independent cold referee and an independent re-implementation (code written without reading `verify/`) were run on
the manuscript. No fatal error; formulas matched by brute force. Corrections made are listed in NOVELTY.md section 5a.
Still unchecked by a human: the window/coupling argument of Prop 5(b), the FKK theorem numbers and conditions behind
Thm 6, and the elastic-hashing counter assumption.

## Places where a mistake is most likely to be found

1. Thm 7, Step 1: the bijection between home-count vectors and cyclic arrangements of blocks
   with first-passage patterns (the case `k = 1` is separate). Enumeration covers `m <= 9`.
2. Prop 5(b): the window/local-convergence argument for the limit of the orphan law (Cor 8(b) no longer needs a uniform-integrability step: it follows from an exact finite-sum identity).
3. Thm 6: the exact hypotheses on `delta` in FKK, and that the elastic batch index is determined by the occupancy counts.
4. Remark 1: the claim for greedy schemes other than linear and quadratic probing.
5. The scope of "non-reordering" in Definition 1 (occupancy-only rules): whether funnel and
   elastic hashing really fit it.

## What was not done

No proof assistant (none installed); no second human reader; no timing measurement for the attack model. (The independent re-derivation of Thm 7 by Knuth's
Abel-binomial route has been done: `proof_checks.py`.)

## How to attack this

The assistant already ran the obvious attack on Thm 7 (Knuth's route; it agreed). Remaining
attacks worth trying: break Thm 4 for a greedy scheme whose probe sequences cannot start at an
arbitrary cell; break Definition 1 for the funnel and elastic schemes; fault the
window argument of Prop 5(b) or the claim that orph depends only on the cell (Prop 5(a)); and read the quoted results behind Thm 6 for a
condition the manuscript dropped.
