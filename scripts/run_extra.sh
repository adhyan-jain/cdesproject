#!/bin/bash
# Additional experiments, written into an existing run directory:
#   scripts/run_extra.sh results/raw/<run> [memory|time|all]
#
#   memory  units.csv        smallest buffer of every translation unit, STRATA and arena table
#                            (TinyCC traces and, if present, chibicc traces)
#           sweep_minbuf.csv smallest buffer for the shadowing / name-length sweep
#   time    sweep_summary.csv, sweep_replays.csv   paired replay timing on the sweep
#           chibicc_summary.csv, chibicc_replays.csv   all tables on the chibicc traces
set -e
cd "$(dirname "$0")/.."
RUN="$1"; WHAT="${2:-all}"
REPS="${REPS:-31}"; CORE="${CORE:-2}"
PIN=""; command -v taskset > /dev/null && PIN="taskset -c $CORE"
[ -d "$RUN" ] || { echo "no such run directory: $RUN"; exit 1; }
bash scripts/build.sh > /dev/null
mkdir -p build/traces build/sweep
for f in workloads/traces/*.trace.gz; do gunzip -c "$f" > "build/traces/$(basename "${f%.gz}")"; done
python3 scripts/gen_sweep.py build/sweep > /dev/null
echo "extra experiments: git $(git rev-parse --short HEAD 2>/dev/null || echo none), $(date -u +%Y-%m-%dT%H:%M:%SZ), $WHAT" >> "$RUN/environment.txt"

if [ "$WHAT" = memory ] || [ "$WHAT" = all ]; then
  rm -f "$RUN/units.csv" "$RUN/sweep_minbuf.csv"
  for f in build/traces/*.trace; do
    ./build/budget --mode units --trace "$f" --name "$(basename "$f" .trace)" --out "$RUN/units.csv"
  done
  for f in build/sweep/*.trace; do
    ./build/budget --mode minbuf --trace "$f" --name "$(basename "$f" .trace)" --out "$RUN/sweep_minbuf.csv"
  done
  echo "memory experiments done"
fi

if [ "$WHAT" = time ] || [ "$WHAT" = all ]; then
  rm -f "$RUN"/sweep_summary.csv "$RUN"/sweep_replays.csv "$RUN"/chibicc_summary.csv "$RUN"/chibicc_replays.csv
  for f in build/sweep/*.trace; do
    $PIN ./build/bench --trace "$f" --name "$(basename "$f" .trace)" --reps "$REPS" --impls strata,arena_chain,metis_x,swiss_interned \
      --summary "$RUN/sweep_summary.csv" --raw "$RUN/sweep_replays.csv"
  done
  for f in build/traces/chibicc_*.trace; do
    [ -f "$f" ] || continue
    $PIN ./build/bench --trace "$f" --name "$(basename "$f" .trace)" --reps "$REPS" --summary "$RUN/chibicc_summary.csv" --raw "$RUN/chibicc_replays.csv"
  done
  echo "timing experiments done"
fi
