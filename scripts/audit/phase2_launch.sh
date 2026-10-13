#!/bin/bash
# Audit phase 2: build everything the README documents and run it once.
# Run inside WSL/Linux from the repository root:  bash scripts/audit/phase2_launch.sh
set -u
cd "$(dirname "$0")/../.."
A=reports/artifacts
{
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "kernel: $(uname -sr)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo "cores: $(nproc)"
  echo "mem: $(free -m | awk '/Mem:/{print $2" MiB"}')"
  for t in g++ clang++-21 python3 git taskset cppcheck arm-none-eabi-g++ qemu-system-arm gdb valgrind; do
    if command -v $t >/dev/null; then echo "tool $t: $($t --version 2>&1 | head -1)"; else echo "tool $t: ABSENT"; fi
  done
  echo "git: $(git rev-parse HEAD) $(git status --short | wc -l) modified/untracked paths"
} > $A/environment.txt
cat $A/environment.txt

echo "== scripts/test.sh"
( time bash scripts/test.sh ) > $A/p2_test.log 2>&1; echo "exit=$?" | tee -a $A/p2_test.log; tail -6 $A/p2_test.log
echo "== scripts/fetch_third_party.sh"
bash scripts/fetch_third_party.sh > $A/p2_fetch.log 2>&1; echo "exit=$?" | tee -a $A/p2_fetch.log; cat $A/p2_fetch.log
echo "== scripts/build.sh"
bash scripts/build.sh > $A/p2_build.log 2>&1; echo "exit=$?" | tee -a $A/p2_build.log; tail -3 $A/p2_build.log
