# Phase 4: performance and correctness audit

Status: **complete for the 8 TinyCC traces**; the remaining workloads were not re-measured.

- New run `results/raw/20261013-120345-audit`, same protocol as the stored run (31 interleaved rounds, pinned core).
- Correctness: 104 table/trace pairs, 0 disagreements with the reference model. Minimum buffers: 32 of 32 identical.
- Timing verdicts match the stored run on 7 of 8 traces for each comparison; the conventional baseline is faster than STRATA on all 8.
- Raw times were 36% lower than in the stored run (machine state), so only paired ratios are compared.
- Machine-learning metrics do not apply.

Output: `reports/PERFORMANCE_REPORT.md`, `reports/artifacts/repro_comparison.md`.

Acceptance: met, with the stated gap.
