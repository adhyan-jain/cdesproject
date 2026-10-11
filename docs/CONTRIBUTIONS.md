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
