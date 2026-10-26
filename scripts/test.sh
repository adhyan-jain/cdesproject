#!/bin/bash
# Build and run the correctness tests: plain -O2, then AddressSanitizer + UBSan, then the
# bounded exhaustive check.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
CXX=${CXX:-g++}
W="-std=c++14 -Wall -Wextra -Wshadow -Wconversion -Wno-sign-conversion -pedantic"
$CXX $W -O2 -o build/test_strata tests/test_strata.cpp
./build/test_strata
$CXX $W -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -o build/test_strata_san tests/test_strata.cpp
./build/test_strata_san
# every operation sequence up to length 7 over a small alphabet, 8 configurations
$CXX $W -O2 -o build/exhaustive_small tests/exhaustive_small.cpp
./build/exhaustive_small 7 | tail -1
# reviewer-requested tests: whole-buffer equality, refusal atomicity, encodings
mkdir -p build/review_tests
$CXX $W -O2 -o build/review_tests/test_review tests/test_review.cpp
./build/review_tests/test_review | tail -1
$CXX $W -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -o build/review_tests/test_review_san tests/test_review.cpp
./build/review_tests/test_review_san | tail -1
echo "compiler: $($CXX --version | head -1)"
