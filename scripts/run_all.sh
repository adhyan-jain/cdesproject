#!/bin/bash
# Full experimental pipeline. Run from a clean checkout (Linux, g++, python3, git):
#   scripts/fetch_third_party.sh && scripts/run_all.sh [label]
# Writes results/raw/<UTC date>-<label>/ ; then run: python3 scripts/analyze.py results/raw/<run>
set -e
cd "$(dirname "$0")/.."
LABEL="${1:-full}"
REPS="${REPS:-15}"
CORE="${CORE:-2}"
RUN="results/raw/$(date -u +%Y%m%d-%H%M%S)-$LABEL"
PIN=""
command -v taskset > /dev/null && PIN="taskset -c $CORE"
bash scripts/test.sh > /dev/null
bash scripts/build.sh
mkdir -p "$RUN" build/traces build/synthetic
for f in workloads/traces/*.trace.gz; do gunzip -c "$f" > "build/traces/$(basename "${f%.gz}")"; done
python3 scripts/gen_synthetic.py build/synthetic > /dev/null

{
  echo "run: $RUN"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_commit: $(git rev-parse HEAD 2>/dev/null || echo none)"
  echo "compiler: $(${CXX:-g++} --version | head -1)"
  echo "flags: -std=c++14 -O2"
  echo "kernel: $(uname -sr)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo "libc: $(ldd --version | head -1)"
  echo "pinning: ${PIN:-none}"
  echo "repetitions: $REPS (+2 warm-up) whole-trace replays; 3 per-operation latency replays"
  echo "metis: $(git -C third_party/metis rev-parse HEAD 2>/dev/null || echo absent)"
  echo "phmap: $(git -C third_party/phmap describe --tags 2>/dev/null || echo absent)"
} > "$RUN/environment.txt"
cat "$RUN/environment.txt"

echo "== compiler traces (instrumented TinyCC)"
for f in build/traces/*.trace; do
  n=$(basename "$f" .trace); echo "  $n"
  $PIN ./build/bench --trace "$f" --name "$n" --reps "$REPS" --summary "$RUN/compiler_summary.csv" --raw "$RUN/compiler_replays.csv"
  $PIN ./build/budget --mode budget --trace "$f" --name "$n" --reps 9 --out "$RUN/budget.csv"
done

echo "== synthetic stress traces"
for f in build/synthetic/*.trace; do
  n=$(basename "$f" .trace); echo "  $n"
  $PIN ./build/bench --trace "$f" --name "$n" --reps "$REPS" --summary "$RUN/synthetic_summary.csv" --raw "$RUN/synthetic_replays.csv"
done

echo "== worst-case clustering"
$PIN ./build/budget --mode worstcase --out "$RUN/worstcase.csv"

# Supplemental: the four regex-extracted traces used in the METIS-X manuscript. The old
# arena table needs minutes per replay on the two large ones (its redeclaration check is
# a linear scan), so it is left out there; every other table runs on all four.
if [ -d third_party/metis/results ]; then
  echo "== regex-extracted traces of the earlier work (supplemental)"
  ALL="strata,strata_raw,strata_noshrink,scope_map_stack,std_undo_log,swiss_undo_log,swiss_interned,metis_x,metis_scope_maps"
  for n in FreeRTOS Arduino; do
    echo "  $n"
    $PIN ./build/bench --trace "third_party/metis/results/corpus_events_$n.txt" --name "$n" --reps 5 --summary "$RUN/legacy_summary.csv" --raw "$RUN/legacy_replays.csv"
  done
  for n in Zephyr ESP-IDF; do
    echo "  $n"
    $PIN ./build/bench --trace "third_party/metis/results/corpus_events_$n.txt" --name "$n" --reps 5 --impls "$ALL" --summary "$RUN/legacy_summary.csv" --raw "$RUN/legacy_replays.csv"
  done
fi
echo "done: $RUN"
