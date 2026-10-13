#!/bin/bash
# Audit phase 4: re-measure the eight TinyCC traces with the current code and write a new
# run directory next to the stored ones.   bash scripts/audit/repro.sh [label]
# Same protocol as scripts/run_all.sh (interleaved rounds, one pinned core); REPS defaults
# to 31 as in the reported run.
set -eu
cd "$(dirname "$0")/../.."
LABEL="${1:-audit}"; REPS="${REPS:-31}"; CORE="${CORE:-2}"
RUN="results/raw/$(date -u +%Y%m%d-%H%M%S)-$LABEL"
PIN=""; command -v taskset > /dev/null && PIN="taskset -c $CORE"
bash scripts/build.sh > /dev/null 2>&1
mkdir -p "$RUN" build/traces
for f in workloads/traces/*.trace.gz; do gunzip -c "$f" > "build/traces/$(basename "${f%.gz}")"; done
{
  echo "run: $RUN"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_commit: $(git rev-parse HEAD) (+ $(git status --short | wc -l) uncommitted paths)"
  echo "compiler: $(${CXX:-g++} --version | head -1)"
  echo "flags: -std=c++14 -O2"
  echo "kernel: $(uname -sr)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo "pinning: ${PIN:-none}"
  echo "rounds: $REPS (+2 warm-up), tables interleaved; compiler traces only"
  echo "load: $(cut -d' ' -f1-3 /proc/loadavg) at start"
} > "$RUN/environment.txt"
cat "$RUN/environment.txt"
for n in cjson littlefs zlib lua freertos mbedtls tinycc sqlite; do
  echo "  $n"
  $PIN ./build/bench --trace "build/traces/$n.trace" --name "$n" --reps "$REPS" --summary "$RUN/compiler_summary.csv" --raw "$RUN/compiler_replays.csv"
  $PIN ./build/budget --mode budget --trace "build/traces/$n.trace" --name "$n" --reps 3 --out "$RUN/budget.csv"
done
echo "done: $RUN"
