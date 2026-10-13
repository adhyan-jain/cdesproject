#!/bin/bash
# Conformance of STRATA's keyed hash with the reference HalfSipHash (1 compression round,
# 3 finalization rounds). The reference source is downloaded, not stored in the repository;
# its SHA-256 is printed so the run can be tied to an exact file.
set -eu
cd "$(dirname "$0")/../.."
mkdir -p build/halfsiphash reports/artifacts
URL=https://raw.githubusercontent.com/veorq/SipHash/master/halfsiphash.c
[ -f build/halfsiphash/halfsiphash.c ] || curl -fsSL "$URL" -o build/halfsiphash/halfsiphash.c
[ -f build/halfsiphash/halfsiphash.h ] || curl -fsSL "${URL%.c}.h" -o build/halfsiphash/halfsiphash.h
{
  echo "reference: $URL"
  echo "sha256: $(sha256sum build/halfsiphash/halfsiphash.c | cut -d' ' -f1)"
  grep -n "define cROUNDS\|define dROUNDS\|ifndef cROUNDS\|ifndef dROUNDS" build/halfsiphash/halfsiphash.c || true
  gcc -O2 -DcROUNDS=1 -DdROUNDS=3 -c build/halfsiphash/halfsiphash.c -o build/halfsiphash/ref13.o
  g++ -std=c++14 -O2 -Wall -Wextra -o build/halfsiphash/conformance tests/halfsiphash_conformance.cpp build/halfsiphash/ref13.o
  ./build/halfsiphash/conformance
} 2>&1 | tee reports/artifacts/halfsiphash_conformance.log
