# Contributions and Work History

## Earlier work: METIS / METIS-X (repository `adhyan-jain/Metis`)

87 commits between 1 September and 10 October 2026.

| Author | Commits | Main work (from the commit history) |
|---|---|---|
| Adhyan Jain (`adhyan-jain`) | 77 | SymTab V2-V4, METIS-X (`include/metis_x.hpp`), benchmark drivers, corpus extraction, the nine research phases and the project-closure note, the manuscript |
| Shubhi Singh (`shubhisingh1510`) | 10 | BUDGET-SYM adaptive prototype (the project's starting point), Robin Hood / trie comparison and LRU-cache benchmark, fix of a shadowing bug in the lookup cache, the dashboard backend, Review-3 paper updates |

The guide for the course project was Prof. Bhuvaneshwari M (VIT Vellore).

## This repository (`cdesproject`)

Created on 11 October 2026 from Shubhi Singh's account.

**How the work was done, stated plainly:** the audit, the design, the code, the tests, the
benchmark runs and the documents in this repository were produced in one working session by
an AI coding assistant (Claude, Anthropic) operating in Shubhi Singh's development
environment at her direction, following a written brief. All commits carry a
`Co-Authored-By` line to that effect. Human review of the code and of the claims is still
to be done by the authors.

| Part | Origin |
|---|---|
| `include/strata/` | written for this repository |
| `tests/`, `benchmarks/`, `scripts/`, `tools/tcc-trace/` | written for this repository |
| `workloads/traces/*.trace.gz` | generated here by the patched Tiny C Compiler from the pinned projects listed in `workloads/traces/MANIFEST.tsv` |
| METIS tables used as baselines | Adhyan Jain's code, fetched at commit `7b3dacf`, not stored here |
| parallel-hashmap | Gregory Popovitch, Apache-2.0, fetched at v1.4.1, not stored here |
| Ideas carried over from METIS | the trace-replay method, heap accounting by allocator hook, the list of limitations, the phase-2 and phase-8 findings (see `INITIAL_AUDIT.md`, section 3) |

Adhyan Jain did not take part in this session and has not reviewed the result. He is
listed as a co-author of the draft paper because the work builds directly on METIS-X and on
his findings; that listing needs his agreement.

## Before anything is submitted

* Both authors read the code and re-run `scripts/test.sh` and `scripts/run_all.sh`.
* The authors decide how the AI assistance is disclosed, following the venue's policy.
* The guide's role and affiliation lines are confirmed.
* The patent question noted in `ARCHITECTURE_DECISION.md` is settled before the repository
  is made public.

## Status on 2026-10-13 (recorded by the research-completion branch; nothing here is a decision)

* The work of 2026-10-13 (audit, bounded mode, rebuild change, probe-limit analysis, the
  re-run of every experiment, the rewritten paper in `paper/` and the IEEE Access format draft
  in `manuscript/`) was again produced by an AI coding assistant at Shubhi Singh's direction.
* The paper now lists four authors in the order Shubhi Singh, Adhyan Jain, Akshith
  Venkatataramana, Arjuman, as instructed by Shubhi Singh, and thanks the guide
  (Bhuvaneswari M.) in the Acknowledgment. The earlier draft listed five authors in a different
  order with the guide as an author. **No record exists in this repository that any of the
  other three authors or the guide has read or approved either version.**
* The contributions of Akshith Venkatataramana and Arjuman to this repository are not
  recorded anywhere in it. Their authorship has to be justified by the authors themselves.
* The four items under "Before anything is submitted" above are all still open. They are
  tracked in `SUBMISSION_READINESS.md` and `submission/SIGNOFF_CHECKLIST.md`.
