#!/bin/bash
# Bounded exhaustive check (tests/exhaustive_small.cpp).  bash scripts/audit/exhaustive.sh [depth]
set -eu
cd "$(dirname "$0")/../.."
mkdir -p build reports/artifacts
g++ -std=c++14 -O2 -Wall -Wextra -o build/exhaustive_small tests/exhaustive_small.cpp
( time ./build/exhaustive_small "${1:-9}" ) 2>&1 | tee reports/artifacts/exhaustive_small.log
