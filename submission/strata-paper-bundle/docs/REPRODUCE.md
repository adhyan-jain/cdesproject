# Reproducing the paper

Everything in `paper/main.pdf` and `paper/short.pdf` is regenerated from raw measurements by
the commands below. Fresh results and historical results are kept apart (section 4).

## 1. Versions

| Item | Value |
|---|---|
| Repository | https://github.com/shubhisingh1510/cdesproject |
| Starting commit of this work | `36f9f6c` (`main` on 2026-10-13) |
| Library measured | `include/strata/strata.hpp` as of `36f9f6c`; unchanged on the research branch |
| Research branch | `research/strata-paper-completion`; final commit recorded in `SUBMISSION_READINESS.md` |
| Baselines (fetched, not stored) | METIS at `7b3dacf`; parallel-hashmap v1.4.1 at `22a7f6c` |
| Trace sources | TinyCC `43c7708`, chibicc `90d1f7f`; project versions in `workloads/traces/MANIFEST.tsv` |

## 2. Environment used

| Item | Value |
|---|---|
| Machine | Intel Core Ultra 7 258V, 8 logical cores and 15.7 GiB visible to the guest |
| System | Windows 11, WSL 2, Ubuntu 22.04, kernel 6.18.33.2-microsoft-standard-WSL2, glibc 2.35 |
| Compilers | g++ 11.4.0 (`-std=c++14 -O2`); clang 21.1.8 with libFuzzer for fuzzing and static analysis |
| Embedded | arm-none-eabi-g++ 10.3.1 (`-Os`), QEMU 6.2 (`mps2-an385`, Cortex-M3, 64 KiB) |
| Python | 3.10 in WSL (pipeline); 3.12 with pandas, tabulate, matplotlib (reports, plots) |
| LaTeX | MiKTeX 25.12, pdfTeX, BibTeX |

Needs Linux on x86-64 (glibc `malloc_usable_size`, `rdtscp`, `taskset`). No paid service, no
network access beyond fetching the two baseline repositories and the reference HalfSipHash
source.

## 3. Commands

```bash
# correctness (about 15 s) and the complete audit from a clean copy (about 6 min)
bash scripts/test.sh
bash scripts/audit/final_verify.sh

# measurements
bash scripts/fetch_third_party.sh
bash scripts/run_all.sh paper                              # about 9 min; -> results/raw/<UTC>-paper
bash scripts/run_extra.sh results/raw/<UTC>-paper all      # about 2 min
PROBE_TRIALS=500 bash scripts/audit/hardening.sh 5         # about 2 min; -> results/hardening
bash tools/embedded/run.sh zlib littlefs cjson lua freertos
bash tools/embedded/bounded.sh                             # probe limit 512
bash tools/chibicc/build.sh && python3 tools/chibicc/evaluate.py   # about 12 min; needs ~/cdes/src from tools/tcc-trace/make_traces.sh

# reports and paper
python scripts/analyze.py results/raw/<UTC>-paper          # results/summary/<run>/
python scripts/make_report.py <UTC>-paper                  # docs/RESULTS.md, paper/generated.tex
python manuscript/tools/make_numbers.py results/raw/<UTC>-paper   # paper/generated_numbers.tex, paper/tables/
python manuscript/figures/source/make_plots.py             # paper/figures/fig_*.pdf
python manuscript/tools/crosscheck.py                      # the two generators must agree
(cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main)
(cd paper && pdflatex short && bibtex short && pdflatex short && pdflatex short)
python manuscript/tools/check_manuscript.py paper main
python manuscript/tools/check_manuscript.py paper short
python manuscript/tools/sync_body.py                       # copies the shared text into the IEEE Access format draft
```

## 4. Runs

| Run | Code | Role |
|---|---|---|
| `results/raw/20261013-143828-paper` | `36f9f6c` | **the run the paper reports**: full pipeline, fresh |
| `results/hardening/` (2026-10-13T16:34Z) | research branch | fresh: flooding, bounded mode on traces (limits 4-512), probe distribution |
| `results/chibicc/` (2026-10-13) | research branch | fresh: end to end in chibicc |
| `results/embedded/` (2026-10-13) | research branch | fresh: emulated Cortex-M3, both modes |
| `results/raw/20261013-125704-final` | `36f9f6c` | same code, earlier the same day, 8 TinyCC traces; cited for run-to-run variation |
| `results/raw/20261013-120345-audit` | `65db7eb` (before the rebuild change) | the "before" of the artifact comparison |
| `results/raw/20261011-*`, `results/summary/20261011-*`, `results/chibicc-20261011/` | older code | historical, superseded, kept unchanged |

## 5. What each central number is computed from

| Claim | File(s) in the reported run |
|---|---|
| smallest fixed buffer, saving, bytes per declaration | `budget.csv`, `compiler_summary.csv` |
| replay-time ratios and intervals | `compiler_replays.csv` |
| heap peaks, allocator calls, per-operation latency | `compiler_summary.csv` |
| before/after the rebuild change | `compiler_replays.csv` of `20261013-120345-audit` and of the reported run |
| synthetic traces, sweep, per-unit budgets | `synthetic_*.csv`, `sweep_*.csv`, `units.csv` |
| flooding, bounded mode, probe distribution | `results/hardening/flood.csv`, `traces.csv`, `probes.csv` |
| chibicc end to end | `results/chibicc/times.csv`, `units.csv`, `rss.csv` |
| emulated target | `results/embedded/qemu_cortex_m3.txt`, `qemu_cortex_m3_bounded.txt` |
| verification counts | `reports/artifacts/final_verification.log`, `exhaustive_small.log`, `fuzz_strata.log`, `mutation_check.log` |

## 6. Deviations and limits of reproduction

- Absolute times on this machine differ between sessions by tens of percent; only ratios within a run are meaningful, and per-trace verdicts against the conventional table changed between two runs of the same code.
- Heap peaks reproduce to about 0.2%, not to the byte (allocator rounding depends on allocation history). Bytes used inside the buffer, minimum buffers and correctness counters are exact.
- The traces depend on the host's C headers; regenerating them elsewhere changes event counts slightly. The stored traces are what the paper uses.
- The reported run measured the seven chibicc traces together with the eight TinyCC traces; the analysis keeps them apart, and `scripts/run_all.sh` now skips them.
- Not reproduced here: anything on a second machine, on hardware, or on a 32-bit host; a build on Overleaf.
