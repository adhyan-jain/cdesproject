# Round 2 (2026-10-13, later the same day)

Request: raise the novelty further. This file records what was done after the first audit
round and which numbers in the other reports it supersedes. Final code state: branch `main`
after this round; final run `results/raw/20261013-125704-final`.

## 1. What was done

| # | Work | Kind | Result |
|---|---|---|---|
| 1 | Found why STRATA was slower than the conventional single-buffer table | diagnosis | Per-operation latencies showed `declare` 40-50% slower and lookups about level. Cause: (a) every buffer growth rebuilt the whole index although the index does not move; (b) each rebuild hashed every name twice; (c) each new name walked its probe path twice (search, then insert). Not the name packing and not open addressing as such. |
| 2 | Removed all three | implementation | (a) the index is rebuilt only when its size changes; (b) a rebuild swaps one word between each record and its undo entry, so each name is hashed once and no scratch memory is needed; (c) a failed search remembers the empty slot it ended at and the insertion uses it. |
| 3 | Canonical-state property | proof and test | After any sequence of operations the table's state is bit-for-bit that of a fresh table holding only the live declarations in their order. Consequence: the table does not age, and insertion-only results about linear probing apply to it at all times. |
| 4 | Probe-limit bound | proof and measurement | P(refusal) <= rho^L / (1 - rho), rho = a e^(1-a) at load a, for an ideal hash. Checked against 240 million simulated insertions using the table's own hashes: never exceeded. |

Nothing in 1-4 is a new technique. Item 2(b) and item 3 are small observations specific to
this table; item 4 is the standard interval-counting argument, which item 3 makes applicable
to a table with deletions.

## 2. Measured effect

Replay time, paired per-round ratios, 31 rounds, 8 TinyCC traces
(`artifacts/speed_comparison.md`: before = `20261013-120345-audit`, after = `20261013-125704-final`).

| Trace | STRATA vs conventional table, before | after |
|---|---|---|
| cjson | +33.8% slower | -0.2% not established |
| littlefs | +16.9% slower | +4.0% slower |
| zlib | +14.4% slower | -10.7% faster |
| lua | +31.6% slower | -0.3% not established |
| freertos | +29.8% slower | +0.0% not established |
| mbedtls | +31.6% slower | +1.7% slower |
| tinycc | +26.9% slower | +7.0% slower |
| sqlite | +11.4% slower | -4.5% faster |

- Against METIS-X: faster on 8 of 8 traces, 15.5% to 36.1% (before: 7 of 8, 3.8% to 18.0%).
- Deterministic results: 1 248 values compared between the two runs, 0 differ (correctness counters, heap peaks, bytes used inside the buffer). Minimum fixed buffers: 32 of 32 identical. The change costs no memory.
- Keyed hash against the default hash: +19.4% to +31.0% replay time (was +22.3% to +32.9% against the slower default).
- Hash flooding, default configuration: 1 248.9 ms against 4.4 ms for 32 768 names, 281-fold (ordinary input became faster, the attack did not). Keyed: 1.1-fold. Probe limit 64 alone: 2.3-fold with 32 704 names refused.
- Code on Cortex-M3: 2 715 bytes (2 557 before the audit, 2 739 after round 1). Stack 492 bytes.

Honest reading: STRATA is now **level** with the conventional design on time and 16-18%
smaller. It is not faster. The earlier headline "the compact design costs 30% in time" was an
implementation artefact, which is itself a finding worth reporting.

## 3. The probe limit, corrected

Round 1 reported that a limit of 64 refused nothing on 15 compiler traces. That is true and
remains in the data. Round 2 shows it must not be generalised: at the maximum load of 3/4,
0.77% of fresh names need more than 64 probes (measured, both hashes). Limits that the bound
supports: 512 with the default index (at most 1.1e-7 per declaration; none observed in 10
million samples; 2.0e-7 observed for a limit of 256), or 128 with `sparse_index` (at most
1.0e-10). `README.md`, `docs/PROBE_LIMIT_ANALYSIS.md` and the code example now say 512.

## 4. Tests after round 2

| Check | Result |
|---|---|
| Unit tests, `-O2` and ASan + UBSan | 2 732 358 checks, 0 failed (new: `test_canonical_state`, 360 state comparisons) |
| Exhaustive check, depth 9 | 80 621 568 sequences, 0 failures |
| Fuzzing of the round-2 code | 2 476 136 executions, no failure (total over the audit: 14.5 million) |
| Mutation check | 9 of 9 detected (three new mutants break the three round-2 changes) |
| Static analysis | 0 warnings (one analyzer false positive in new measurement code avoided) |
| Command-line cases | 41 of 41 |
| Emulated Cortex-M3 | 5 of 5 in fixed mode, 5 of 5 in bounded keyed mode |
| Clean-copy verification | 12 of 12 steps |

## 5. Novelty after round 2

| Criterion | Weight | Round 1 | Round 2 | Why it moved |
|---|---|---|---|---|
| Problem novelty | 10% | 4.5 | 4.5 | unchanged |
| Methodological novelty | 25% | 4 | 4.5 | the canonical-state property and its use to carry the insertion-only bound over to a table with deletions; still standard tools |
| Technical contribution | 20% | 6 | 6.5 | the compact table no longer costs time; one-hash rebuild without scratch memory |
| Differentiation from closest work | 15% | 5.5 | 6 | against the conventional design it is now smaller at equal speed, instead of smaller but slower |
| Experimental strength | 15% | 7 | 7.5 | the main negative result is explained by a controlled before/after with identical deterministic outputs; the limit is backed by a bound and 240 million samples |
| Reproducibility | 10% | 8.5 | 8.5 | unchanged |
| Practical significance | 5% | 5 | 5.5 | no remaining reason to prefer the conventional table when memory matters |
| **Weighted total** | | **5.5** | **6.0** | 0.45 + 1.125 + 1.30 + 0.90 + 1.125 + 0.85 + 0.275 = 6.03 |

**8/10 is still not justified.** The method is a known algorithm with careful engineering,
two small table-specific observations and a standard bound. What would move it further is
unchanged from `IMPROVEMENT_ROADMAP.md`: a real compiler on real hardware, a machine-checked
proof, a systematic literature review. Roadmap items 6 (probe-limit analysis) and 7 (explain
the slowdown) are done.

## 6. Statements in the other reports that this supersedes

| Report | Statement | Now |
|---|---|---|
| `FINAL_AUDIT_REPORT.md`, `PERFORMANCE_REPORT.md`, `NOVELTY_ASSESSMENT.md` | STRATA is 11-34% slower than the conventional table on all 8 traces | level (section 2) |
| `PERFORMANCE_REPORT.md` section 4 | flooding figures (223x, 1 925 ms against 8.6 ms) | 281x, 1 249 ms against 4.4 ms; `results/hardening/flood.csv` was regenerated |
| `PERFORMANCE_REPORT.md` section 5 | keyed hash +22.3% to +32.9%; code +182 bytes | +19.4% to +31.0%; +158 bytes |
| `TEST_RESULTS.md` | 2 706 587 checks; 6 of 6 mutants; 12 million fuzzing runs | section 4 |
| `NOVELTY_ASSESSMENT.md` | 5.5/10 | 6.0/10 (section 5) |
| all | a probe limit of 64 as the suggested setting | 512 (section 3) |
| `CHANGELOG_AUDIT.md` | "nothing was committed or pushed" | committed and pushed at the owner's request |

## 7. Files changed in round 2

`include/strata/strata.hpp` (rebuild, insertion), `tests/test_strata.cpp` (`test_canonical_state`),
`benchmarks/hardening_main.cpp` (`--mode probes`), `scripts/audit/hardening.sh`,
`scripts/audit/mutation_check.py`, `scripts/audit/final_verify.sh`, `docs/PROBE_LIMIT_ANALYSIS.md`
(new), `docs/CORRECTNESS.md`, `docs/LIMITATIONS.md`, `README.md`, `results/hardening/*`
(regenerated, plus `probes.csv`), `results/raw/20261013-125704-final/` (new),
`results/embedded/*` (regenerated), `reports/artifacts/*` (regenerated).
The paper and `docs/RESULTS.md` are still unchanged and now describe a slower table than the
code implements.
