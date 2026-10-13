#!/bin/bash
# Static checks and portability builds -> reports/artifacts/static_analysis.log
set -u
cd "$(dirname "$0")/../.."
A=reports/artifacts; mkdir -p $A build
L=$A/static_analysis.log; : > $L
run() { echo "== $*" >> $L; "$@" >> $L 2>&1; echo "exit=$?" >> $L; }
SRC="tests/test_strata.cpp tests/exhaustive_small.cpp tests/fuzz_strata.cpp"
# 1. strict warnings, two compilers, three language levels
for std in c++14 c++17 c++20; do
  run g++ -std=$std -fsyntax-only -Wall -Wextra -Wshadow -Wconversion -Wno-sign-conversion -Wcast-align -Wundef -Wformat=2 -pedantic -DFUZZ_STANDALONE $SRC
  run clang++-21 -std=$std -fsyntax-only -Weverything -Wno-c++98-compat -Wno-c++98-compat-pedantic -Wno-padded -Wno-sign-conversion \
      -Wno-old-style-cast -Wno-zero-as-null-pointer-constant -Wno-unsafe-buffer-usage -Wno-global-constructors -Wno-exit-time-destructors \
      -Wno-missing-prototypes -Wno-missing-variable-declarations -Wno-covered-switch-default -Wno-switch-default -Wno-weak-vtables \
      -Wno-unsafe-buffer-usage-in-libc-call -Wno-nrvo -DFUZZ_STANDALONE $SRC
done
# 2. path-sensitive analyzers
run clang++-21 -std=c++14 --analyze -Xclang -analyzer-output=text -DSTRATA_TEST_HOOKS -x c++ include/strata/strata.hpp
run clang++-21 -std=c++14 --analyze -Xclang -analyzer-output=text tests/exhaustive_small.cpp
run g++ -std=c++14 -fanalyzer -fsyntax-only -x c++ include/strata/strata.hpp
run g++ -std=c++14 -fanalyzer -O1 -c -o /dev/null benchmarks/hardening_main.cpp
# 3. the header on its own, freestanding-ish, no exceptions / RTTI (as on the embedded target)
echo '#include "../include/strata/strata.hpp"' > build/hdr_only.cpp
run g++ -std=c++14 -fno-exceptions -fno-rtti -Wall -Wextra -Werror -c -o /dev/null build/hdr_only.cpp
run arm-none-eabi-g++ -std=c++14 -mcpu=cortex-m3 -mthumb -fno-exceptions -fno-rtti -Os -Wall -Wextra -Werror -c -o build/hdr_m3.o build/hdr_only.cpp
# 4. 32-bit host build of the tests (pointer size, size_t arithmetic)
if echo 'int main(){}' | g++ -m32 -x c++ - -o /dev/null 2>/dev/null; then
  run g++ -m32 -std=c++14 -O2 -o build/test_strata_m32 tests/test_strata.cpp
  run ./build/test_strata_m32
else
  echo "== 32-bit host build: NOT RUN (g++ -m32 multilib not installed)" >> $L
fi
# 5. undefined behaviour and memory errors with a second compiler
run clang++-21 -std=c++14 -O1 -g -fsanitize=address,undefined,integer -fno-sanitize=unsigned-integer-overflow,unsigned-shift-base,implicit-conversion -fno-sanitize-recover=all -o build/test_strata_clang_san tests/test_strata.cpp
run ./build/test_strata_clang_san
grep -c "warning:" $L | sed 's/^/warnings in log: /'
grep -E "^== |^exit=|checks, |warning:|error:" $L | cut -c1-260
