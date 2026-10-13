#!/bin/bash
# Final verification from a clean copy of the working tree (tracked files and new,
# non-ignored files; no build/ or third_party/ carried over).
#   bash scripts/audit/final_verify.sh        -> reports/artifacts/final_verification.log
set -u
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
CLEAN=${CLEAN_DIR:-/opt/strata_clean}
LOG="$SRC/reports/artifacts/final_verification.log"
rm -rf "$CLEAN"; mkdir -p "$CLEAN"
(cd "$SRC" && git ls-files -co --exclude-standard -z | tar --null -T - -cf - 2>/dev/null) | tar -xf - -C "$CLEAN"
cd "$CLEAN"
: > "$LOG"
pass=0; fail=0
step() {   # id "description" command...
  local id=$1 what=$2; shift 2
  local t0=$(date +%s)
  "$@" > "step_$id.out" 2>&1
  local rc=$?
  if [ $rc -eq 0 ]; then pass=$((pass + 1)); v=PASS; else fail=$((fail + 1)); v=FAIL; fi
  printf '%s | %s | %s | exit %s | %ss | %s\n' "$id" "$v" "$what" "$rc" "$(( $(date +%s) - t0 ))" "$(grep -E "checks, |depth 7:|passed [0-9]+, failed|mismatches|detected [0-9]|RESULT|warnings in log|replayed" "step_$id.out" | sort | uniq -c | tr '\n' ';' | cut -c1-330)" | tee -a "$LOG"
}
echo "clean copy: $CLEAN ($(find . -type f | wc -l) files), source commit $(git -C "$SRC" rev-parse --short HEAD) + uncommitted changes, $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
step V01 "unit tests -O2, ASan+UBSan, exhaustive depth 7 (scripts/test.sh)" bash scripts/test.sh
step V02 "fetch pinned baselines" bash scripts/fetch_third_party.sh
step V03 "build benchmark tools" bash scripts/build.sh
step V04 "command-line robustness tests under sanitizers" bash scripts/audit/cli_tests.sh
step V05 "warnings, static analyzers, ARM header build, clang sanitizers" bash -c 'bash scripts/audit/static_analysis.sh > sa.out; cat sa.out; ! grep -q -E "^exit=[1-9]" reports/artifacts/static_analysis.log && grep -q "warnings in log: 0" sa.out'
step V06 "keyed hash against reference HalfSipHash" bash scripts/audit/halfsiphash_check.sh
step V07 "differential fuzzing, 2 workers x 90 s on the saved corpus" bash scripts/audit/fuzz.sh 90 2
step V08 "fuzzer detects injected defects" bash -c 'python3 scripts/audit/mutation_check.py 30 | tee m.out; grep -q "detected 9 of 9" m.out'
step V09 "hardening experiments run and verify the collisions" bash -c 'bash scripts/audit/hardening.sh 1 && python3 -c "
import csv,sys
r=list(csv.DictReader(open(\"results/hardening/flood.csv\")))
t=list(csv.DictReader(open(\"results/hardening/traces.csv\")))
ok=all(x[\"correct\"]==\"1\" for x in r) and sum(int(x[\"wrong_lookups\"]) for x in t)==0 and sum(int(x[\"rebuilds\"]) for x in t)==0 and all(int(x[\"refused_probe_limit\"])==0 for x in t if x[\"max_probe\"]==\"64\")
print(\"hardening rows\",len(r),len(t),\"ok\",ok); sys.exit(0 if ok else 1)"'
step V10 "emulated Cortex-M3, fixed mode, 5 traces" bash -c 'bash tools/embedded/run.sh zlib littlefs cjson lua freertos > e.out 2>&1; cat e.out; [ "$(grep -c "RESULT: PASS" e.out)" = 5 ]'
step V11 "emulated Cortex-M3, bounded keyed mode, 5 traces" bash -c 'bash tools/embedded/bounded.sh > b.out 2>&1; cat b.out; [ "$(grep -c "RESULT: PASS" b.out)" = 5 ]'
step V12 "short benchmark run agrees with the reference model" bash -c 'REPS=2 bash scripts/audit/repro.sh verify > r.out 2>&1; cat r.out; python3 -c "
import csv,glob,sys
f=sorted(glob.glob(\"results/raw/*-verify/compiler_summary.csv\"))[-1]
r=list(csv.DictReader(open(f)))
bad=[(x[\"trace\"],x[\"impl\"]) for x in r if int(x[\"wrong_lookups\"]) or int(x[\"wrong_declares\"]) or int(x[\"refused_declares\"])]
print(\"pairs\",len(r),\"bad\",bad); sys.exit(1 if bad or len(r)!=104 else 0)"'
echo "steps passed $pass, failed $fail" | tee -a "$LOG"
[ $fail -eq 0 ]
