#!/bin/bash
# Robustness tests of the command-line tools with valid, invalid, empty and boundary input.
# The tools are built with AddressSanitizer + UBSan, so a memory error or undefined
# behaviour fails the test even when the exit status looks normal.
#   bash scripts/audit/cli_tests.sh        -> reports/artifacts/cli_tests.log, exit 1 on any FAIL
set -u
cd "$(dirname "$0")/../.."
A=reports/artifacts; T=build/cli; mkdir -p $A $T
SAN="-std=c++14 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
DEFS=""
[ -d third_party/phmap/parallel_hashmap ] && DEFS="$DEFS -DCDES_HAVE_PHMAP -Ithird_party/phmap"
g++ $SAN $DEFS -o $T/bench benchmarks/bench_main.cpp 2> $T/build.log || { cat $T/build.log; exit 2; }
g++ $SAN -DSTRATA_TEST_HOOKS -o $T/budget benchmarks/budget_main.cpp 2>> $T/build.log || { cat $T/build.log; exit 2; }
g++ $SAN -o $T/hardening benchmarks/hardening_main.cpp 2>> $T/build.log || { cat $T/build.log; exit 2; }
export ASAN_OPTIONS=detect_leaks=1:abort_on_error=0 UBSAN_OPTIONS=print_stacktrace=1

# input files
printf 'E\nD alpha\nL alpha\nE\nD alpha\nL alpha\nX\nL alpha\nX\n' > $T/ok.trace
: > $T/empty.trace
printf '\n\n\n' > $T/blank.trace
printf 'X\nX\nX\nL never\nX\n' > $T/unbalanced.trace
printf 'Q what\nZZ\nD\nL\nD  \n' > $T/garbage_tags.trace
head -c 20000 /dev/urandom > $T/random.trace
python3 -c "print('D ' + 'a' * 300); print('D ' + 'b' * 255); print('L ' + 'b' * 255); print('D ' + 'c' * 256)" > $T/long_names.trace
python3 -c "
import sys
sys.stdout.buffer.write(b'D caf\xc3\xa9\nD a\x00b\nL caf\xc3\xa9\nD tab\there\nD ns::name\nL ns::name\n')" > $T/odd_bytes.trace
python3 -c "
print('\n'.join(['E'] * 20000 + ['D x'] + ['L x'] + ['X'] * 20000))" > $T/deep.trace
printf 'E\r\nD crlf\r\nL crlf\r\nX\r\n' > $T/crlf.trace
python3 -c "print('D ' + 'x' * 5000000)" > $T/huge_line.trace
printf 'D a\nU\nU\nU\nD a\nL a\n' > $T/units.trace

pass=0; fail=0
: > $A/cli_tests.log
# t ID "purpose" expected-exit-status command...     (expected "any" = any status below 128)
t() {
  local id=$1 purpose=$2 want=$3; shift 3
  timeout 120 "$@" > $T/out.txt 2> $T/err.txt
  local rc=$? verdict=PASS
  if grep -q -E "AddressSanitizer|runtime error|LeakSanitizer" $T/err.txt; then verdict=FAIL
  elif [ "$want" = any ]; then [ $rc -lt 124 ] || verdict=FAIL
  elif [ "$rc" != "$want" ]; then verdict=FAIL; fi
  if [ $verdict = PASS ]; then pass=$((pass + 1)); else fail=$((fail + 1)); fi
  printf '%s | %s | %s | expected exit %s | actual exit %s | %s\n' "$id" "$verdict" "$purpose" "$want" "$rc" "$(head -c 160 $T/err.txt | tr '\n' ' ')" >> $A/cli_tests.log
}

I="--impls strata,arena_chain,scope_map_stack"
t C01 "bench: valid small trace" 0 $T/bench --trace $T/ok.trace --name ok --reps 3 $I
t C02 "bench: no arguments" 2 $T/bench
t C03 "bench: missing file" 2 $T/bench --trace $T/does_not_exist.trace
t C04 "bench: empty file" 2 $T/bench --trace $T/empty.trace
t C05 "bench: blank lines only" 2 $T/bench --trace $T/blank.trace
t C06 "bench: exits without enters" 0 $T/bench --trace $T/unbalanced.trace --reps 2 $I
t C07 "bench: unknown tags and missing names" any $T/bench --trace $T/garbage_tags.trace --reps 2 $I
t C08 "bench: random bytes" any $T/bench --trace $T/random.trace --reps 2 $I
t C09 "bench: names of 255, 256 and 300 bytes" 0 $T/bench --trace $T/long_names.trace --reps 2 $I
t C10 "bench: non-ASCII, NUL, tab, '::' in names" 0 $T/bench --trace $T/odd_bytes.trace --reps 2 $I
t C11 "bench: 20000 nested scopes (past STRATA's depth limit)" 0 $T/bench --trace $T/deep.trace --reps 2 $I
t C12 "bench: CRLF line ends" 0 $T/bench --trace $T/crlf.trace --reps 2 $I
t C13 "bench: one 5 MB line" any $T/bench --trace $T/huge_line.trace --reps 2 $I
t C14 "bench: consecutive unit separators" 0 $T/bench --trace $T/units.trace --reps 2 $I
t C15 "bench: unknown option" 2 $T/bench --bogus 1
t C16 "bench: --reps 0" 0 $T/bench --trace $T/ok.trace --reps 0 $I
t C17 "bench: --reps -5" 0 $T/bench --trace $T/ok.trace --reps -5 $I
t C18 "bench: --reps not a number" 0 $T/bench --trace $T/ok.trace --reps abc $I
t C19 "bench: --warmup -3" 0 $T/bench --trace $T/ok.trace --reps 2 --warmup -3 $I
t C20 "bench: --impls names nothing" 0 $T/bench --trace $T/ok.trace --reps 2 --impls nosuchtable
t C21 "bench: summary path in a missing directory" 3 $T/bench --trace $T/ok.trace --reps 1 $I --summary $T/no/such/dir/s.csv
t C22 "bench: option without a value" any $T/bench --trace
t C23 "budget: valid, budget mode" 0 $T/budget --mode budget --trace $T/ok.trace --name ok --reps 1 --out $T/b.csv
t C24 "budget: units mode" 0 $T/budget --mode units --trace $T/units.trace --name u --out $T/u.csv
t C25 "budget: minbuf mode" 0 $T/budget --mode minbuf --trace $T/ok.trace --name ok --out $T/m.csv
t C26 "budget: missing trace" any $T/budget --mode budget --trace $T/does_not_exist.trace --out $T/b.csv
t C27 "budget: unknown mode" any $T/budget --mode nonsense --out $T/b.csv
t C28 "budget: deep nesting trace" any $T/budget --mode minbuf --trace $T/deep.trace --name deep --out $T/m.csv
t C29 "budget: random bytes" any $T/budget --mode minbuf --trace $T/random.trace --name r --out $T/m.csv
t C30 "budget: --reps 0 (regression: indexed an empty vector)" 0 $T/budget --mode budget --trace $T/ok.trace --name ok --reps 0 --out $T/b.csv
t C30b "budget: --reps -3" 0 $T/budget --mode budget --trace $T/ok.trace --name ok --reps -3 --out $T/b.csv
t C31 "hardening: no mode" 2 $T/hardening
t C32 "hardening: names, valid" 0 $T/hardening --mode names --count 8 --words 6
t C33 "hardening: names, odd word count" 2 $T/hardening --mode names --count 8 --words 5
t C34 "hardening: names, more than exist" 2 $T/hardening --mode names --count 100 --words 4
t C35 "hardening: names, zero count" 2 $T/hardening --mode names --count 0 --words 4
t C36 "hardening: traces, valid" 0 $T/hardening --mode traces --trace $T/ok.trace --name ok
t C37 "hardening: traces, missing file" 2 $T/hardening --mode traces --trace $T/does_not_exist.trace
t C38 "hardening: traces, random bytes" any $T/hardening --mode traces --trace $T/random.trace --name r
t C39 "hardening: traces, deep nesting" 0 $T/hardening --mode traces --trace $T/deep.trace --name deep
t C40 "hardening: unknown option" 2 $T/hardening --what 1

echo "passed $pass, failed $fail" >> $A/cli_tests.log
cat $A/cli_tests.log | cut -c1-230
[ $fail -eq 0 ]
