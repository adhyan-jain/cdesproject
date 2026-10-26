# Use of AI assistance: full account

Written 2026-10-17. This file records, for every part of this repository, what an AI system did
and what humans did, so that the disclosure required by a publisher or an institution can be
written from facts. It states what is known from the repository and from the 2026-10-17
session; it does not state anything about what the authors have or have not read beyond what
the repository itself records.

## 1. Tools used

| Phase | Tool | Operated by / at whose direction |
|---|---|---|
| Creation of the repository, library, tests, benchmarks, traces, first paper (2026-10-11 to 2026-10-13) | Anthropic Claude, through an AI coding assistant, in Shubhi Singh's development environment | Shubhi Singh, following a written brief (`docs/CONTRIBUTIONS.md`) |
| Adversarial review, theory, verification programs and the theory manuscript in `theory/` (2026-10-17) | Anthropic Claude (model Sonnet 5.5) through the Claude Code command-line tool | Adhyan Jain |
| The predecessor METIS / METIS-X repository (`adhyan-jain/Metis`, 2026-09-01 to 2026-10-10) | not covered by this file; see that repository's history | Adhyan Jain, Shubhi Singh |

The tool is not an author. The AI system produced text and code; it did not verify its own
output except by running the programs listed below, and it can be wrong.

## 2. What the AI did in the 2026-10-17 session

A later session (October 2026, Claude Code, model Sonnet 5.5, with subagents) revised the IEEE Access manuscript in response to an instructor's reviewer report: it extended the refusal-law experiment, wrote `tests/test_review.cpp`, the stronger baseline `benchmarks/baselines/arena_chain_nohash.hpp`, the timing-session scripts, `docs/EVIDENCE.md` and `docs/REVIEW_MANIFEST.md`, rewrote parts of the article, and cleaned the repository. Each result was produced by a program that can be re-run; the authors must read and verify the text before submission.

| Output | What the AI did | How it was checked, by running programs (not by reading) |
|---|---|---|
| adversarial review report (removed in the repository cleanup; git tag `pre-cleanup`) | read the paper, library, correctness and probe documents; re-ran the test suite; wrote the findings | `bash scripts/test.sh`: 2 732 358 checks, 0 failed; the scripts in `review/` |
| novelty and proof-audit notes (removed in the repository cleanup; git tag `pre-cleanup`) | assessed novelty and audited the proofs (by the same assistant that wrote them, so not independent of its blind spots) | the programs in `theory/verify/`, including an independent re-derivation of Theorem 7 |
| `theory/verify/*` (Python, C++) | wrote every verification program | each program fails (non-zero exit) on a mismatch; all pass; `bash theory/verify/run_all.sh` |
| Theorems and proofs in `theory/paper/main.tex` | proposed the statements, derived the proofs, wrote the text | exhaustive enumeration in exact rational arithmetic (258 triples), 488 919 state comparisons for five insertion rules, exhaustive check of the exactness theorem, a z-test of the law against the real table, an independent reproduction of 24 measured buffer sizes |
| Literature checks | ran web searches; read primary text where stated in `theory/paper/refs.bib`; verified every DOI-backed entry against Crossref | the `note` fields in `refs.bib` say what was and was not read |
| Documents under `docs/`, `theory/`, `review/`, and the README additions of 2026-10-17 | drafted | none beyond reading |

## 3. What the AI did not do

* It did not read anything on behalf of an author. No author has recorded a reading of the
  theory manuscript, its proofs, or the review.
* It made no timing measurement of an attack. The attack results use an idealised oracle.
* It did not install or use a proof assistant; the proofs are on paper.
* It did not contact any publisher, venue, institution or third party, and it did not
  submit anything.
* It did not decide authorship, author order, affiliations, the licence, or release.

## 4. Known limitations of the AI's work (so reviewers can look in the right places)

* The proofs of Theorem 2 (undo), Theorem 4 (exactness) and Proposition 5 (orphans) are short; the proof of the exact refusal law (Theorem 7, proved in Appendix A of the
  manuscript) is the longest and the one most worth reading line by line. It is validated
  numerically, which is strong evidence but not a proof.
* The probe-complexity theorem (Theorem 6) quotes published results. The AI read the
  relevant statements in the primary text of Farach-Colton, Krapivin, Kuszmaul (arXiv
  2501.02305) and of Bender et al., *Tiny Pointers* (arXiv 2111.12800), and did not re-prove them or
  the reduction between them.
* Several references were checked at bibliographic level only (`note` fields).
* The literature search was limited; a closer precedent may exist.

## 5. Suggested statement for the manuscript

The manuscript (`theory/paper/main.tex`, section "Declarations") already contains this
statement:

> The software, tests, benchmarks and the earlier empirical manuscript that this article extends
> were produced by an AI coding assistant working in the environment of the first author, under
> the authors' direction, as recorded in the repository. This article was developed with the same
> kind of tool: Anthropic's Claude (model Sonnet 5.5, through the Claude Code command-line tool)
> was used, at one author's direction, to review the earlier work adversarially, to propose and
> derive the theorems and proofs, to write the verification programs, and to draft the text.
> Every number in the article is produced by those programs, which can be re-run. The tool is
> not an author; the listed authors are responsible for the content.

The final sentence is a commitment by the authors. It is true in the sense that matters only
if the authors read the manuscript and its proofs and can defend them. A venue's own wording and
form (some require a field in the submission system, some a specific heading) replace the
heading above; the facts in sections 1-3 are what the form needs.

## 6. Items only a human can complete

The sign-off checklist of the earlier empirical paper was removed in the repository cleanup (git tag `pre-cleanup`). For the IEEE Access manuscript the one that matters most: each author reads and can explain the proofs.
