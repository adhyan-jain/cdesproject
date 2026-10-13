#!/bin/bash
# Differential fuzzing of strata::Table under AddressSanitizer + UBSan (libFuzzer).
#   bash scripts/audit/fuzz.sh [seconds per job] [jobs]
# Needs clang with libFuzzer (tested: clang++-21). Corpus and binary live outside the
# repository ($FUZZ_DIR, default /opt/strata_fuzz); the log is copied to reports/artifacts/.
set -u
cd "$(dirname "$0")/../.."
SECS=${1:-240}; JOBS=${2:-4}
CXX=${FUZZ_CXX:-clang++-21}
D=${FUZZ_DIR:-/opt/strata_fuzz}
mkdir -p "$D/corpus" reports/artifacts
$CXX -std=c++14 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all \
     -o "$D/fuzz_strata" tests/fuzz_strata.cpp || exit 1
cd "$D"
./fuzz_strata -max_len=4096 -max_total_time="$SECS" -jobs="$JOBS" -workers="$JOBS" -print_final_stats=1 corpus > fuzz_driver.log 2>&1
rc=$?
cd - > /dev/null
{
  echo "compiler: $($CXX --version | head -1)"
  echo "seconds per job: $SECS, jobs: $JOBS, exit status: $rc"
  echo "corpus files: $(ls "$D/corpus" | wc -l)"
  for f in "$D"/fuzz-*.log; do echo "--- $(basename "$f")"; grep -E "stat::|ERROR|FUZZ FAILURE|SUMMARY|DONE" "$f" | tail -8; done
  ls "$D"/crash-* "$D"/leak-* "$D"/timeout-* "$D"/oom-* 2>/dev/null | sed 's/^/artifact: /'
} > reports/artifacts/fuzz_strata.log
cat reports/artifacts/fuzz_strata.log
exit $rc
