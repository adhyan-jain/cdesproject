#!/bin/bash
# Hash-flooding and bounded-mode experiments -> results/hardening/
#   bash scripts/audit/hardening.sh [reps]
set -eu
cd "$(dirname "$0")/../.."
REPS=${1:-5}; CORE=${CORE:-2}
PIN=""; command -v taskset > /dev/null && PIN="taskset -c $CORE"
bash scripts/build.sh > /dev/null
mkdir -p results/hardening build/traces
for f in workloads/traces/*.trace.gz; do gunzip -c "$f" > "build/traces/$(basename "${f%.gz}")"; done
rm -f results/hardening/flood.csv results/hardening/traces.csv
{
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_commit: $(git rev-parse HEAD) (+ $(git status --short | wc -l) uncommitted paths)"
  echo "compiler: $(${CXX:-g++} --version | head -1)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo "kernel: $(uname -sr)"
  echo "pinning: ${PIN:-none}; reps: $REPS"
} > results/hardening/environment.txt
$PIN ./build/hardening --mode flood --reps "$REPS" --out results/hardening/flood.csv 2> results/hardening/flood_verification.txt
cat results/hardening/flood_verification.txt
for f in build/traces/*.trace; do
  ./build/hardening --mode traces --trace "$f" --name "$(basename "$f" .trace)" --out results/hardening/traces.csv
done
echo "done: results/hardening"
