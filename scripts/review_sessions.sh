#!/bin/bash
# Reviewer experiments R15/R16: independent timing sessions (separate process launches,
# separated in time), rotating start order, pinned to one core.
#   scripts/review_sessions.sh [SESSIONS=5] [GAP_SECONDS=300] [CORE=4] [REPS=31]
# Needs build/review_bench/bench (see docs/REVIEW_EXPERIMENTS_BENCH.md for the build commands)
# and build/review_bench/traces/*.trace. Writes results/review/sessions/sN/.
set -e
cd "$(dirname "$0")/.."
NS="${1:-5}"; GAP="${2:-300}"; CORE="${3:-4}"; REPS="${4:-31}"
SIB=$(cut -d, -f1-2 /sys/devices/system/cpu/cpu$CORE/topology/thread_siblings_list | tr ',-' '  ' | tr ' ' '\n' | grep -vx "$CORE" | head -1)
TRACES=(zlib cjson littlefs freertos lua mbedtls tinycc sqlite)
IMPLS=(strata strata_keyed arena_chain arena_nohash metis_x)
busy() { awk -v c="cpu$1" '$1==c {t=0; for(i=2;i<=NF;i++) t+=$i; print t-$5-$6, t}' /proc/stat; }   # busy ticks, total ticks
for ((s=1; s<=NS; s++)); do
  D=results/review/sessions/s$s; mkdir -p "$D"; rm -f "$D"/summary.csv "$D"/replays.csv
  ROT=$(( (s-1) % ${#IMPLS[@]} ))
  {
    echo "session: $s of $NS"; echo "start_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "core: $CORE (sibling hardware thread: ${SIB:-none})"
    echo "rotation_offset (--rot): $ROT"
    echo "loadavg_start: $(cat /proc/loadavg)"
    echo "governor: $(cat /sys/devices/system/cpu/cpu$CORE/cpufreq/scaling_governor)  epp: $(cat /sys/devices/system/cpu/cpu$CORE/cpufreq/energy_performance_preference)  no_turbo: $(cat /sys/devices/system/cpu/intel_pstate/no_turbo)"
    echo "cur_freq_khz_start: $(cat /sys/devices/system/cpu/cpu$CORE/cpufreq/scaling_cur_freq)"
    echo "busy_processes_start (>=20% cpu, excluding this script):"; ps -eo pid,psr,pcpu,comm --sort=-pcpu | awk 'NR>1 && $3>=20' | head -8
  } > "$D/context.txt"
  read B0 T0 < <(busy $CORE); [ -n "$SIB" ] && read SB0 ST0 < <(busy $SIB)
  # trace order rotates with the session; table start order rotates with --rot and, within a run, every round
  for ((i=0; i<${#TRACES[@]}; i++)); do
    t=${TRACES[$(( (i + s - 1) % ${#TRACES[@]} ))]}
    taskset -c $CORE ./build/review_bench/bench --trace build/review_bench/traces/$t.trace --name $t --reps $REPS --rot $ROT \
      --impls "$(IFS=,; echo "${IMPLS[*]}")" --summary "$D/summary.csv" --raw "$D/replays.csv"
  done
  read B1 T1 < <(busy $CORE); [ -n "$SIB" ] && read SB1 ST1 < <(busy $SIB)
  {
    echo "end_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "loadavg_end: $(cat /proc/loadavg)"
    echo "cur_freq_khz_end: $(cat /sys/devices/system/cpu/cpu$CORE/cpufreq/scaling_cur_freq)"
    echo "pinned_cpu${CORE}_busy_fraction_over_session: $(awk -v b=$((B1-B0)) -v t=$((T1-T0)) 'BEGIN{printf "%.3f", b/t}')"
    [ -n "$SIB" ] && echo "sibling_cpu${SIB}_busy_fraction_over_session: $(awk -v b=$((SB1-SB0)) -v t=$((ST1-ST0)) 'BEGIN{printf "%.3f", b/t}')"
  } >> "$D/context.txt"
  echo "session $s done $(date -u +%H:%M:%S)"
  [ $s -lt $NS ] && sleep "$GAP"
done
