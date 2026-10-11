#!/bin/bash
# Build and run the correctness tests: plain -O2, then AddressSanitizer + UBSan.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
CXX=${CXX:-g++}
W="-std=c++14 -Wall -Wextra -Wshadow -Wconversion -Wno-sign-conversion -pedantic"
$CXX $W -O2 -o build/test_strata tests/test_strata.cpp
./build/test_strata
$CXX $W -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -o build/test_strata_san tests/test_strata.cpp
./build/test_strata_san
echo "compiler: $($CXX --version | head -1)"
