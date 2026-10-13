# Performance report

Audit of 2026-10-13. Numbers are copied from generated files; the generators are named.

## 1. Environment

| Item | Value |
|---|---|
| CPU | Intel Core Ultra 7 258V, 8 logical cores visible to WSL, 15.7 GiB |
| System | Windows 11, WSL 2, Ubuntu 22.04, kernel 6.18.33.2-microsoft-standard-WSL2 |
| Compiler | g++ 11.4.0, `-std=c++14 -O2` |
| Pinning | `taskset -c 2` |
| Stored run | `results/raw/20261011-165103-v3` (commit `8786eac`, 31 rounds) |
| New run | `results/raw/20261013-120345-audit` (commit `cd3b4cc` plus the audit's uncommitted changes, 31 rounds, load average 1.09 at start) |

A laptop under a hypervisor: absolute times move between sessions (section 3).

## 2. Method

Unchanged from the project (`docs/METHODOLOGY.md`): each trace is replayed on every table once
per round, the starting table rotating from round to round, 31 measured rounds after 2
warm-up rounds, one pinned core. Tables are compared through the per-round ratio of their
replay times (median, 95% bootstrap interval, 2000 resamples). A difference is called
"established" when the interval excludes zero. The audit re-ran the 8 TinyCC traces with all
12 stored tables plus one new variant (`strata_keyed`), and compared with the stored run by
`scripts/audit/compare_runs.py` (output: `artifacts/repro_comparison.md`).

## 3. Reproduction of the stored claims

| Claim in README / RESULTS | Stored run | New run | Reproduced? |
|---|---|---|---|
| All tables agree with the reference model | 0 wrong | 104 pairs, 0 wrong | yes |
| Minimum fixed buffer per trace | 15.8-156.5 KiB | 32 of 32 values identical | yes, exactly |
| STRATA vs METIS-X replay time | faster on 7, slower on 1 (cjson +6.0%) | faster on 7 (-3.8% to -18.0%), cjson +1.6% not established | yes on 7 of 8; the one adverse result is weaker |
| STRATA vs conventional arena table | slower on 7 of 8, sqlite not established | slower on 8 of 8 (+11.4% to +33.8%, median +28.3%) | yes; the unfavourable result is confirmed and slightly stronger |
| Arena table vs METIS-X | faster on 8 (-11% to -36%) | faster on 8 (-14.7% to -37.5%) | yes |
| Declare p95 against METIS-X | 44-64% lower | 48-63% lower | yes |
| Scope-exit p95 against METIS-X | 67-88% lower | 70-79% lower | yes |
| Lookup p95 against METIS-X | not improved | -5% to +13%, not improved | yes |

Deterministic columns: 1152 values compared, 63 differ, all in `peak_bytes` (heap peak
measured through `malloc_usable_size`), by at most 0.22%. STRATA's four variants are 32 bytes
higher on every trace because the table object itself grew (new option fields); the other
differences are in tables whose code did not change and come from allocator rounding that
depends on what was allocated before. Bytes used inside the buffer and all correctness
counters are identical. **Finding:** heap peaks are reproducible to about 0.2%, not to the
byte; the documents do not claim otherwise.

Absolute times: the new run's medians are 0.47 to 0.70 times the stored ones (median 0.64)
for the same binaries' work. The machine was faster in this session, which is why only paired
ratios within one run are compared.

## 4. Hash flooding (new measurement)

Generator and harness: `benchmarks/hardening_main.cpp`; data `results/hardening/flood.csv`;
5 repetitions, medians. The colliding input is 32 768 distinct 150-character C identifiers
that share one 32-bit hash under the built-in seed and under 8 other seeds
(`results/hardening/flood_verification.txt`). "Ordinary" names have the same length.

| Names | Configuration | Declare, ordinary (ms) | Declare, colliding (ms) | Ratio | Lookup, colliding (ms) | Refused | Longest probe |
|---|---|---|---|---|---|---|---|
| 1 024 | default | 0.35 | 2.57 | 7.3x | 0.89 | 0 | 1 024 |
| 4 096 | default | 1.27 | 34.43 | 27.1x | 14.76 | 0 | 4 096 |
| 16 384 | default | 6.77 | 614.12 | 90.8x | 237.19 | 0 | 16 384 |
| 32 768 | default | 8.63 | 1 925.13 | 223.0x | 1 059.98 | 0 | 32 768 |
| 32 768 | keyed hash | 13.56 | 14.47 | 1.1x | 3.48 | 0 | 106 |
| 32 768 | bounded (limit 64), unkeyed | 2.10 | 5.63 | 2.7x | 4.27 | 32 704 | 64 |
| 32 768 | bounded (limit 64), keyed | 3.36 | 3.49 | 1.0x | 3.44 | 0 | 26 |

- Default table: time grows 748-fold for 32 times more names (exponent 1.91: quadratic).
- Probe limit alone: 32-fold for 32 times more names (exponent 1.00), at the price of refusing every colliding name after the 64th.
- Keyed hash: no measurable difference between colliding and ordinary input.
- A side observation: with ordinary names the bounded table declares 4 times faster than the default growable one (2.10 against 8.63 ms at 32 768 names) because it never rebuilds or reallocates. That compares a pre-sized fixed buffer with a growing one and is not a like-for-like result.

## 5. Cost of the defences (new measurement)

| Cost | Measured | Source |
|---|---|---|
| Keyed hash, replay time on the 8 TinyCC traces | +22.3% to +32.9% (all established) | `artifacts/repro_comparison.md` section 5 |
| Probe limit 64 on 15 compiler traces (719 833 declarations) | 0 refused, either hash; longest probe 47 | `results/hardening/traces.csv` |
| Probe limit 32 | 51 refused (5 traces unkeyed, 4 keyed) | same |
| Probe limit 16 | 561 refused unkeyed, 571 keyed | same |
| Memory of the static index | peak bytes identical to the growing index on all 15 traces | same |
| Code size on Cortex-M3 (`-Os`) | 2 557 -> 2 739 bytes (+182) | `results/embedded/qemu_cortex_m3.txt`, git diff |
| Static RAM of the test image | +24 bytes | same |
| Default configuration | hash, layout and results unchanged; table object 24-32 bytes larger | unit test `test_keyed_hash`, section 3 |

The probe-limit rows are observations on these traces. They are not a bound on how often a
limit of 64 would refuse declarations in other programs.

## 6. Not measured

- Replay time of the bounded mode against the plain fixed mode on the compiler traces (the flooding harness measures it on synthetic names only).
- Synthetic, legacy and chibicc timing of the stored run were not repeated.
- Any timing on the emulated microcontroller (QEMU gives none) or on hardware.
- CPU counters (cache misses, branch misses); WSL 2 does not expose them reliably here.
- Throughput, startup time, API or database latency, front-end metrics: not applicable to a header library.

## 7. Reproduce

```
bash scripts/fetch_third_party.sh
bash scripts/audit/repro.sh mylabel                       # about 1 minute here
python3 scripts/audit/compare_runs.py results/raw/20261011-165103-v3 results/raw/<new run>
bash scripts/audit/hardening.sh 5                         # about 1 minute here
```
