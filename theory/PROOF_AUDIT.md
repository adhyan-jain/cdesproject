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
| **Thm 4** Exactness | (<=) the newest key's cell lies on no older path; (=>) construction with distinct homes and `x_z` homed at `x_i` | re-derived; checked the first-deviation index `t` and that keys deleted earlier restore `Ins(x_1..x_z)` by Thm 2 | `lifo_check.py` B: every assignment x every deletion order, 18 settings (linear m<=6; quadratic m in {4,8}, n<=4), exactly one safe order each | low for linear/quadratic; **Remark 1 (all greedy schemes) is argued, not enumerated beyond quadratic** |
| **Prop 5** Orphans | pair counting; total displacement is order independent; Knuth's mean displacement | identity re-derived | `lifo_check.py` C: identity on all assignments, 4 settings; `proof_checks.py`: mean 1.502 +/- 0.008 vs 1.5 at load 3/4 (20 runs, m = 65 536) | low; the asymptotic value is Knuth's, not proved here |
| **Cor 6** Separation | Thm 2 + FKK (FOCS 2024) + the dynamic lower bound they cite | statements checked in primary text; reduction (tiny pointer <-> probe index) quoted, not re-proved; conditions on `delta` deferred to FKK | none (external results) | **medium**: conditional; elastic/funnel rules assumed to depend on occupancy counts only (our reading) |
| **Thm 7** Refusal law | block decomposition, cycle lemma, Borel-Tanner identity, exchangeability (Appendix A, 4 steps) | every step re-derived, including the pattern condition (eq. 2), the weight `B(g)`, the normalisation `(m/k) Q_k(m)` and the offset count `(g-L)^+` | `exact_law.py`: 258 `(m,n,L)` triples, exact rational arithmetic vs enumeration of every home sequence, 0 mismatches; `run_law_check.py`: real `strata::Table`, 7 settings x 400 000 trials, max abs z 1.96, bounded and unbounded tables in lockstep, 0 mismatches; agrees with the stored 240M-sample simulation; **independent derivation** by Knuth's Abel-binomial counting (`proof_checks.py`): equal in 481 cases, exact for m <= 14 and to 2e-10 relative for m up to 2^20 | low (and the law is classical: Janson-Viola Thm 11.1, Eq. 11.4) |
| **Cor 8**(a) monotone | order independence of the occupied set; superset coupling | re-derived | the table of exact limits is monotone in load | low |
| **Cor 8**(b) limit | pointwise convergence of `pi_g`, convergence of means, Scheffe-type uniform integrability | the ratio computation for `pi_g` re-derived; uniform integrability is argued, not spelled out in full | `proof_checks.py`: relative error to the Poisson limit shrinks with m at load 1/2 and 3/4 | **low-medium**: the uniform-integrability step is the least detailed argument in the paper |
| **Cor 8**(c) tail | Stirling + dominated convergence | re-derived | `proof_checks.py`: exact/asymptotic ratio 0.472, 0.772, 0.929, 0.981 at L = 64, 256, 1024, 4096 (converges at rate about `1/((1-rho) L)`) | low |
| **Prop 9** Run | Cor 3, Cor 8(a), union bound | re-derived; requires names distinct from live ones | none beyond Thm 7 | low |
| **Props 10-12** Keys | ideal-hash model; coupon collector; geometric trials | re-derived | `adaptive_key_demo.cpp`: about 2 071 queries per collider (m = 2 048), 1-5.5 % honest refusals with a persistent key, 0 % otherwise (illustration of Prop 12, idealised oracle) | low for the statements; **the model oracle is not a timing channel** |
| **Prop 13** Ledger | subtraction of the stated layout formulas | re-derived | `proof_checks.py`: the four identities hold at 848 449 instants of the eight traces; closed forms equal the independent simulation's peaks for all 5 layouts x 8 traces; `space_model.py` reproduces all 24 measured minima of the repository exactly | low |

## Places where a mistake is most likely to be found

1. Thm 7, Step 1: the bijection between home-count vectors and cyclic arrangements of blocks
   with first-passage patterns (the case `k = 1` is separate). Enumeration covers `m <= 9`.
2. Cor 8(b): the uniform-integrability step.
3. Cor 6: the quoted reduction and the exact hypotheses on `delta` in FKK.
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
uniform-integrability step of Cor 8(b); and read the quoted results behind Cor 6 for a
condition the manuscript dropped.
