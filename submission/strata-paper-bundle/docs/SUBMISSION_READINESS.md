# Submission readiness

2026-10-13. Research-completion work on STRATA (`cdesproject`).

**Verdict: the paper and its artifact are technically complete; the paper is NOT ready to
submit, because every human approval is still missing (section 10). After those sign-offs it
is ready for a work-in-progress or student-research track. It is not a strong candidate for a
full research track.**

## 1. Starting state

| Item | Value |
|---|---|
| Directory | the existing clone of https://github.com/shubhisingh1510/cdesproject (public) |
| Integration branch | `main` (the remote's default branch; there is no `master`) |
| Starting commit | `36f9f6c` on `main`, equal to `origin/main` |
| Working tree at start | three uncommitted items from earlier work the same day: `.gitignore`, `manuscript/` (IEEE Access format draft), `results/raw/20261013-143828-paper/` (full run). Preserved: they are the first commit of the branch (`2382cb5`). Nothing was reset, stashed or discarded |

## 2. Branch

| Item | Value |
|---|---|
| Research branch | `research/strata-paper-completion`, created from `36f9f6c` |
| Commits | `2382cb5` carry-over; `cddcb25` results, probe limit, chibicc; `73de39d` paper; `149c5d8` gate and documents; then the commit that adds this file and the bundle (the branch head) |
| Library version measured | `include/strata/strata.hpp` of `36f9f6c`; `git diff 36f9f6c -- include tests benchmarks/baselines` is empty on the branch |
| Remote | **nothing was pushed** |
| Merge | see section 13 |

## 3. Files materially changed on the branch

| Area | Files |
|---|---|
| Paper | `paper/main.tex` (rewritten), new `paper/short.tex`, `paper/body.tex`, `paper/abstract.tex`, `paper/references.bib`, `paper/generated_numbers.tex`, `paper/tables/`, `paper/figures/fig_*.pdf`, `paper/main.pdf`, `paper/short.pdf` |
| Journal-format draft | `manuscript/` (carried over; its body, numbers and bibliography are now copies of `paper/`) |
| Generators and checks | `manuscript/tools/make_numbers.py`, `crosscheck.py`, `sync_body.py`, `check_manuscript.py`, `make_bundle.py`; `manuscript/figures/source/make_plots.py` |
| Pipeline fixes | `scripts/analyze.py`, `scripts/make_report.py`, `scripts/run_all.sh` |
| Experiments | `tools/embedded/bounded.sh` (limit 512 by default), `benchmarks/hardening_main.cpp` (limits up to 512 on traces) |
| Results | `results/raw/20261013-143828-paper/`, `results/summary/20261013-143828-paper/`, `results/hardening/`, `results/chibicc/` (old copy in `results/chibicc-20261011/`), `results/embedded/`, `docs/RESULTS.md`, `paper/generated.tex` |
| Documents | `README.md`, `docs/LIMITATIONS.md`, `docs/CONTRIBUTIONS.md`, `docs/ARCHITECTURE_DECISION.md`, `docs/REPRODUCIBILITY.md`, `NOVELTY_GATE.md`, this file, `submission/` |
| Not changed | `include/`, `tests/`, `benchmarks/baselines/`, the traces, every earlier run under `results/raw/2026101*` |

## 4. Experiments executed, with outcomes

All on 2026-10-13, on the library of `36f9f6c`. Environment: `submission/REPRODUCE.md`.

| Experiment | Outcome | Data |
|---|---|---|
| Full pipeline (`run_all.sh`, `run_extra.sh`): 15 compiler traces x 13 tables x 31 rounds, 9 synthetic, 4 legacy, budgets, sweep, per-unit budgets | completed; 195 compiler pairs agree with the reference model; one known synthetic disagreement (METIS-X refuses 149 of 400 declarations) | `results/raw/20261013-143828-paper/` |
| Hardening (`hardening.sh 5`, 500 probe trials) | completed; 48 flooding rows correct; 270 bounded-mode rows, 0 wrong lookups, 0 rebuilds; bound never exceeded in 168 cells | `results/hardening/` |
| chibicc end to end (3 builds, 21 rounds) | completed; 158 of 158 units identical for both tables | `results/chibicc/` |
| Emulated Cortex-M3, fixed mode | 5 of 5 pass | `results/embedded/qemu_cortex_m3.txt` |
| Emulated Cortex-M3, bounded mode, limit 512, keyed | 5 of 5 pass, no refusal | `results/embedded/qemu_cortex_m3_bounded.txt` |
| Clean-copy verification, 12 steps | 12 passed, 0 failed | `reports/artifacts/final_verification.log` |
| Fuzzing of the final library | 2 476 136 executions, no failure | `reports/artifacts/fuzz_strata.log` |
| Exhaustive enumeration, depth 9 | 80 621 568 sequences, no failure | `reports/artifacts/exhaustive_small.log` |
| Mutation check | 9 of 9 detected | `reports/artifacts/mutation_check.log` |
| Generator cross-check | 49 quantities, 0 disagreements | `python manuscript/tools/crosscheck.py` |

Earlier the same day, on the same library and used in the paper for comparison only:
`results/raw/20261013-125704-final` (8 traces) and `results/raw/20261013-120345-audit` (the
code before the rebuild change).

## 5. Not run, and why

| Item | Reason |
|---|---|
| Unit tests on a 32-bit host | no `-m32` multilib installed; not installed to leave the system toolchain alone. 32-bit evidence is the emulator |
| Any physical microcontroller | none available |
| A second machine | none available |
| valgrind, cppcheck | not installed; sanitizers and two static analyzers were used |
| A build on Overleaf | no account access; built locally from a clean directory |
| Trace regeneration from the compilers | stored traces used; regeneration depends on host headers |
| A conventional baseline without a stored hash | would test a competing explanation for the memory saving (see `NOVELTY_GATE.md` section 8); not built to keep the scope controlled |
| Systematic literature review | about twenty-five web queries with Crossref verification; no library access |

## 6. Main results and where they come from

Run `20261013-143828-paper` unless stated. Sign: positive = STRATA slower.

| Result | Value | Raw data |
|---|---|---|
| Smallest fixed buffer, STRATA | 15.8 to 156.5 KiB; 27 to 36 bytes per live declaration | `budget.csv` |
| Saving against the conventional single-buffer table | 16.4% to 17.9% on all 8 traces | `budget.csv` |
| Replay time against the conventional table | faster on 0, slower on 2 (+7.2%, +10.7%), not established on 6; range -10.6% to +10.7% | `compiler_replays.csv` |
| Same comparison, earlier run of the same code | faster on 2, slower on 3, not established on 3; -10.7% to +7.0% | `20261013-125704-final/compiler_replays.csv` |
| Replay time against METIS-X | faster on 8 of 8, 15.9% to 36.7% | `compiler_replays.csv` |
| Conventional table against METIS-X | faster on 8 of 8, 14.6% to 34.8% | `compiler_replays.csv` |
| Heap peak against METIS-X | 23% to 76% lower (median 58%); 98.7% to 99.9% fewer allocator calls | `compiler_summary.csv` |
| Before the rebuild change, against the conventional table | +11.4% to +33.8% slower on every trace | `20261013-120345-audit/compiler_replays.csv` |
| Keyed hash cost | +20.2% to +32.2% replay time | `compiler_replays.csv` |
| Flooding, default configuration, 32 768 names | about 300-fold slower than ordinary names; exponent about 2 | `results/hardening/flood.csv` |
| Bounded mode on 15 traces, 719 833 declarations | refused: 561/571 at limit 16, 51/51 at 32, 0 at 64 to 512 (default/keyed hash) | `results/hardening/traces.csv` |
| Probe distribution, load 3/4 | 0.77% of fresh names exceed 64 probes; 2.0e-7 exceed 256; none of 10 million exceed 512; bound never exceeded | `results/hardening/probes.csv` |
| chibicc end to end | STRATA -3.7% to +2.2% (slower on 1 of 7, faster on 0); arena table -3.1% to +4.3% (faster on 3) | `results/chibicc/times.csv` |
| Emulated Cortex-M3 | 5 of 5 in both modes; 2 715 bytes of code; 492 bytes of stack | `results/embedded/` |

## 7. Literature and novelty

Summary of `NOVELTY_GATE.md`: the algorithm is Appel's undo-stack scheme (also LLVM's); the
attack is Aumasson and Bernstein's; the bound uses the standard interval argument; bounded-probe
dictionaries exist (cuckoo, hopscotch) but move keys. What is specific: the measured
decomposition against a strong single-buffer baseline with the diagnosis of a rebuild
artifact; the canonical-state property and its use; the combination of budget, refusal
guarantee and probe limit. Verdict PASS for these narrowed claims.

Risks: (1) a closer precedent may exist that the limited search missed; (2) reviewers may judge
the contribution too incremental; (3) the baselines are the authors' own; (4) one machine and
no hardware; (5) the per-trace timing verdicts are unstable, which the paper states.

## 8. Manuscript build and visual review

| Item | Result |
|---|---|
| `paper/main.tex` | builds with pdfLaTeX + BibTeX, 14 pages, no errors, no unresolved references, no overfull boxes; all 14 pages inspected: title, authors, abstract, 6 figures, 15 tables, 2 propositions, algorithm, 27 references render correctly |
| `paper/short.tex` | builds, 3 pages (limit 4); all pages inspected; abstract 147 words, 6 keywords |
| `manuscript/overleaf/main.tex` (IEEE Access format) | builds, 14 pages; ZIP rebuilt (78 files) |
| Mechanical checks | `check_manuscript.py` passes for all three |
| Problems found in the visual pass and fixed | missing space after the opening letter in the conference format; one table wider than its column; labels overlapping data in one figure |
| Remaining visible placeholders | 3 `[AUTHOR: ...]` markers in `main.tex`, 2 in `short.tex`, 9 in the journal draft |

## 9. Venues

Details, sources and compliance checklists: `submission/VENUES.md`.

| Rank | Venue | Verified | Unverified |
|---|---|---|---|
| Primary | COMPSAC 2027 Student Research Symposium (IEEE; Tokyo, 13-16 July 2027) | conference dates and place; that the symposium exists and publishes in the proceedings (https://ieeecompsac.computer.org/2027/); 2026 rules: 4 pages IEEE format, 150-word abstract, 6 keywords, double-blind, first author a student (https://ieeecompsac.computer.org/2026/srs-2026/) | the 2027 deadline and rules; fees; AI policy |
| Alternative A | LCTES 2027 work-in-progress paper (ACM SIGPLAN/SIGBED, with PLDI) | 2026 categories and dates (https://www.sigarch.org/call-contributions/lctes-2026/) | everything about 2027: no call is published |
| Alternative B | COMPSAC 2027 main symposium | full papers due 31 January 2027, notification 7 April 2027 (https://ieeecompsac.computer.org/2027/) | page limit, template details, fees, AI policy |

## 10. Human-only blockers

None of these can be resolved by an agent. Full list: `submission/SIGNOFF_CHECKLIST.md`.

1. **No author other than the first has seen the work.** Review and approval by Adhyan Jain, Akshith Venkatataramana and Arjuman are not recorded.
2. **Authorship is unjustified in the record** for two of the four names; the guide's role (acknowledged, not an author) needs her agreement.
3. **AI assistance.** Implementation, experiments, analysis and text were produced by an AI assistant. The venue's policy must be read and the disclosure approved; the authors must be able to defend the content themselves.
4. **Patent/IP.** The advisory recorded for the predecessor project is unresolved, and the repository was made public on 2026-10-13 by its owner without a recorded agreement of the co-author or institution.
5. **Author details**: spelling of one name, affiliations, e-mails, corresponding author.
6. **Venue decision** (including travel and registration cost) and a fresh check of the 2027 call.
7. **Authorisation to push** the branch or the merged result.

## 11. Status

| Area | Status | Note |
|---|---|---|
| Git safety and branch discipline | PASS | existing work preserved; all work on the research branch |
| Repository state inspected and inconsistencies resolved | PASS | stale results regenerated; limit 64/512 reconciled; visibility conflict recorded, not decided |
| Implementation and guarantees reviewed | PASS | no defect found; library unchanged; evidence is tests, enumeration, fuzzing, not proof |
| Literature review and novelty reassessment | PARTIAL | done and documented; limited search, several sources at abstract level |
| Experimental program on the final code | PASS | full pipeline, hardening, chibicc, emulator |
| Second machine / hardware | BLOCKED | not available |
| Manuscript | PASS | builds, inspected, numbers generated |
| Artifact chain regenerated and cross-checked | PASS | two generators agree on 49 quantities |
| Venue research | PARTIAL | three candidates; 2027 student-track and LCTES dates not yet published |
| Submission materials and bundle | PASS | `submission/` |
| Novelty gate | PASS | for narrowed claims and an incremental-work venue |
| Human approvals | BLOCKED | section 10 |
| Push / public release of this work | BLOCKED | not authorised |

## 12. Final verdict

**Not ready for submission.** Exact reasons: items 1 to 6 of section 10. Technically, the
three-page work-in-progress paper (`paper/short.pdf`) and the full paper (`paper/main.pdf`)
are complete, reproducible from the repository, and consistent with the data. Once the
authors have reviewed, verified and signed off, `paper/short.tex` can be submitted to the
primary venue after a fresh check of its 2027 call. Acceptance is not predictable and is not
promised.

## 13. Merge record

To be completed after the gate decision (see the end of this file).
