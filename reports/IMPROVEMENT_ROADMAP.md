# Improvement roadmap

Audit of 2026-10-13. Ordered by what most limits a credible submission. Effort estimates are
rough.

## P1: needed before any submission

| # | Item | Why | Effort |
|---|---|---|---|
| 1 | Co-authors read the code, the paper and `reports/`; decide authorship, AI-assistance disclosure and the patent question noted in `docs/ARCHITECTURE_DECISION.md` | nobody but the assistant has reviewed any of it; the repository is private for the patent reason | days, human only |
| 2 | Decide whether the bounded mode goes into the paper. If yes: add a section (threat model, construction of the colliding identifiers with credit to Aumasson and Bernstein, the two defences, their cost), regenerate `docs/RESULTS.md` and `paper/generated.tex` from a full run of the final code | the paper currently describes neither the weakness nor the fix | 2-3 days |
| 3 | Run the full pipeline (`scripts/run_all.sh`, `run_extra.sh`) on the final code and on a second machine, preferably native Linux | only the 8 TinyCC traces were re-measured; all timing is from one laptop under a hypervisor | 1 day |
| 4 | Systematic literature review with full-text access (ACM DL, IEEE Xplore): scoped symbol tables since 1979, hash-table deletion order, bounded-probe tables, on-device compilers | the audit's search was about twenty web queries; several sources are confirmed only bibliographically | 3-5 days |

## P2: strengthens the science

| # | Item | Why | Effort |
|---|---|---|---|
| 5 | Replace TinyCC's own identifier and symbol tables with STRATA (not replay), cross-compile TinyCC for a Cortex-M board with 64-256 KiB RAM, compile the test projects on the device | turns "replay under emulation" into "a compiler running in a budget on hardware"; the largest single gain in experimental strength | 2-4 weeks, needs a board |
| 6 | Analyse the probe limit: for a keyed hash at load factor 3/4, bound the probability that a table of n names refuses a declaration at limit L; compare with measured cluster lengths | the only place where a genuine theoretical contribution is within reach; replaces "0 refusals on 15 traces" by a statement that generalises | 1-3 weeks |
| 7 | Separate experimentally why STRATA is slower than `arena_chain` (query packing, open addressing, fingerprint check) with one-factor variants | the central negative result is still unexplained (`docs/LIMITATIONS.md`, "Unverified") | 2-3 days |
| 8 | Measure bounded mode against plain fixed mode on the compiler traces with the paired protocol; measure the keyed hash on the Cortex-M3 with a cycle counter | the cost of the defences is known on a PC only | 2 days plus hardware |
| 9 | Machine-check the invariants and the all-or-nothing property (a bounded model checker on the header, or a proof of the abstract algorithm) | fuzzing and bounded enumeration are evidence, not proof | 2-6 weeks |
| 10 | Workloads beyond C: a C++ front end (many `::` names take the unpacked path), a scripting-language compiler | all traces are C from two small compilers | 1-2 weeks |

## P3: engineering

| # | Item | Why | Effort |
|---|---|---|---|
| 11 | Pin trace sources by commit and SHA-256 in `tools/tcc-trace/make_traces.sh` | supply-chain finding SUP-2 | 2 hours |
| 12 | Optional run-time check of buffer alignment in the fixed constructors | INF-2 | 30 minutes |
| 13 | Fuzz `arena_chain`; give it the same keyed option so the baseline comparison stays fair in a hardened setting | SEC-3 | 1 day |
| 14 | A helper that picks `index_slots` from an expected number of names, and a way to draw the key from a caller-supplied entropy function | the bounded mode leaves both to the caller | 2 hours |
| 15 | CI: run `scripts/test.sh`, `cli_tests.sh`, `static_analysis.sh` and a 60-second fuzz on every push | none exists | 2 hours |
| 16 | Install a 32-bit multilib and add a `-m32` test run | blocked item in `TEST_RESULTS.md` | 30 minutes |
| 17 | Regenerate figures and tables from the audit run so that documents and code agree on one commit | `docs/RESULTS.md` predates the header change | 1 hour |

## Not recommended

- **Prefix sharing of stored names.** Evaluated by simulation during the audit: 0.9-10.4% memory (median 2.7%) for more lookup work. See `NOVELTY_ASSESSMENT.md` section 8.
- **Presenting the hash attack as a discovery.** It is a 2012 technique applied to a new alphabet.
- **Tuning the rubric or the baselines until the score reaches 8.** The conventional baseline being faster is the project's most useful finding.

## What a realistic outcome looks like

With P1 and items 5-8 done, an honest reviewer-style score is about 6 to 6.5: a careful
systems and evaluation paper with a security angle. That fits a workshop, a regional IEEE
conference or an artifact-oriented venue. It is not a claim about acceptance.
