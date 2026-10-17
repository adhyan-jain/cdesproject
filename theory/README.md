# theory/: a theory manuscript on stack-disciplined open addressing

`paper/main.tex` is a self-contained article (about 19 pages, standard `article` class):
**Stack-Disciplined Open Addressing: Exact Undo, an Exact Refusal Law, and Key-Lifetime Rules for
Bounded-Memory Scoped Tables.** It is a theory/analysis paper; it contains no new benchmark. The
earlier empirical paper is in `../paper/`.

## What it proves

| Result | Statement (manuscript numbering) |
|---|---|
| Theorem 2, Corollary 3 | for every non-reordering open-addressing scheme, popping the newest key by clearing its cell is an exact undo, so the table always equals the insertion-only table of the live sequence |
| Theorem 4, Remark 1 | (a) for a given table the deletion orders for which clearing is safe are exactly the linear extensions of the dependency relation "`y`'s probe path passes through `x`'s cell"; (b) stack order is the *only* order safe for every hash assignment (greedy schemes: linear, quadratic, double hashing, uniform probing) |
| Proposition 5 | the number of keys that depend on a key is a queue length minus one: exact finite-size law, limit law of a discrete M/D/1 queue (mean `alpha / (2 (1 - alpha))`; fraction of keys removable out of order `(1-alpha)(e^alpha-1)/alpha`) |
| Corollary 6 | separation by deletion order, combining Theorem 2 with published results on open addressing without reordering (conditional on them) |
| Theorem 7, Corollary 8 | refusal probability of a probe-limited linear-probing table (the tail of the classical unsuccessful-search cost): an elementary derivation of the explicit finite-size sum, its tail `C rho^L L^{-3/2}`, and the proof that the Chernoff-type bound used earlier is loose by a factor growing like `L^{3/2}`; the law itself is classical (Knuth; Janson-Viola) |
| Propositions 10-12 | with an independent key per table the exact law holds against arbitrary adversarial names; with a persistent key and a probe oracle it does not; costs of the attack |
| Proposition 13 | exact space-ledger identities; on the eight traces the compact layout's saving is a stored hash word plus packing, and interning is space-neutral |

## Reproduce everything

Needs `g++` (C++14), `python3` (standard library only), `pdflatex` + `latexmk` + `pgfplots`.
No network, no paid tool.

```bash
bash theory/verify/run_all.sh      # about 9 minutes; writes tables/ and data/, builds paper/main.pdf
```

| Program | Checks |
|---|---|
| `verify/exact_law.py` | the exact refusal law against brute-force enumeration of every home sequence, in exact rational arithmetic (258 triples) |
| `verify/orphan_law.py` | Theorem 4(a) (397 562 assignment-order pairs), the finite-size orphan law against enumeration of every home sequence (exact rationals), the identity behind Corollary 8(b), and the M/D/1 limit |
| `verify/lifo_check.py` | Theorem 2 (488 919 state comparisons, five insertion rules), Theorem 4 (every assignment x every deletion order, 18 settings), Proposition 5 |
| `verify/design_table.py` | the law against the repository's stored 240-million-sample simulation |
| `verify/law_vs_table.cpp`, `run_law_check.py` | the law against the real `strata::Table` (keyed hash, static index, probe limit): 7 settings x 400 000 trials, z-scores, and bounded/unbounded tables in lockstep |
| `verify/proof_checks.py` | the remaining proofs: the ledger identities at 848 449 instants of the traces, the limit and tail-asymptotic corollaries, the orphan mean, an independent re-derivation of Theorem 7 by Knuth's Abel-binomial route (481 cases), and the uniform-probing limits |
| `verify/design_rule.py` | the design table of smallest probe limits |
| `verify/space_model.py` | the ledger; it reproduces all 24 measured minimum buffers of the repository exactly before predicting the new layouts |
| `verify/adaptive_key_demo.cpp` | the persistent-key illustration (idealised oracle, not a timing attack) |
| `verify/make_figdata.py`, `wrap_tables.py` | figure data, numeric macros and the complete tables the manuscript inputs |

Every number in the manuscript is written by these programs into `paper/tables/` and
`paper/data/`; none is typed by hand. A program that finds a mismatch exits non-zero and
`run_all.sh` stops.

## Audit documents

* `NOVELTY.md`: every claim classified (new / classical / small), with the closest prior work and how it was checked.
* `PROOF_AUDIT.md`: each result, its proof's dependencies, the programs that check it, and where an attack is most likely to succeed.

## What is and is not established

* Proofs are pen-and-paper. They are supported by exhaustive and statistical checks, not by a
  proof assistant (none is installed here).
* The attack results use a model oracle; no timing was measured.
* The separation corollary quotes two published results (primary text read, not re-proved).
* No author has recorded a reading of the proofs: see `../docs/AI_USE_DISCLOSURE.md`.
