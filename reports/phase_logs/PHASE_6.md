# Phase 6: improvement and re-testing

Status: **complete**.

- Bug fixes: `budget --reps 0`; baseline pinned by commit. Regression tests added.
- Research modification, documented separately: bounded mode (static index, probe limit with `kProbeLimit`) and keyed hash (HalfSipHash-1-3, verified against the reference source).
- Re-tested after the change: unit tests (2 706 587 checks), fuzzing of all modes (2.2 million runs), exhaustive check to depth 9, emulated Cortex-M3 in both modes, benchmark correctness.
- Measured cost: keyed hash +22 to +33% replay time; probe limit 64 refuses nothing on 15 traces; +182 bytes of code.
- No evaluation criterion was changed after seeing results; the default configuration and the stored results are untouched.

Output: `reports/CHANGELOG_AUDIT.md`.

Acceptance: met.
