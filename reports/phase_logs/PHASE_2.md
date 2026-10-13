# Phase 2: launch

Status: **complete for what exists; browser part not applicable**.

- `scripts/test.sh`: 1 856 579 checks, 0 failed, at -O2 and under ASan + UBSan (8 s).
- `scripts/fetch_third_party.sh`: METIS at `7b3dacf`, parallel-hashmap v1.4.1 at `22a7f6c`.
- `scripts/build.sh`: `build/bench`, `build/budget` built with all baselines.
- No backend, frontend, worker or database exists; nothing was started that needs shutting down. No browser was opened.

Logs: `reports/artifacts/environment.txt`, `p2_test.log`, `p2_fetch.log`, `p2_build.log`.

Acceptance: met for the command-line project; the browser criterion is not applicable.
