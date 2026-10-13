#!/bin/bash
# Build the benchmark binaries. Baselines that have not been fetched are left out.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
CXX=${CXX:-g++}
FLAGS="-std=c++14 -O2 -Wall -Wextra"
DEFS=""
[ -d third_party/phmap/parallel_hashmap ] && DEFS="$DEFS -DCDES_HAVE_PHMAP -Ithird_party/phmap"
[ -f third_party/metis/include/metis_x.hpp ] && DEFS="$DEFS -DCDES_HAVE_METIS -Ithird_party/metis/include"
$CXX $FLAGS $DEFS -o build/bench benchmarks/bench_main.cpp
[ -f benchmarks/budget_main.cpp ] && $CXX $FLAGS -DSTRATA_TEST_HOOKS $DEFS -o build/budget benchmarks/budget_main.cpp
[ -f benchmarks/hardening_main.cpp ] && $CXX $FLAGS -o build/hardening benchmarks/hardening_main.cpp
echo "built with $($CXX --version | head -1); baselines:$DEFS"
