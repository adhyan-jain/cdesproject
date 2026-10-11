#!/bin/bash
# "Does it fit?" on the emulated Cortex-M3: the same trace and the same static buffer for
# STRATA and for the conventional arena table.
#   tools/embedded/fit.sh TRACE BUFFER_KIB [TRACE BUFFER_KIB ...]
# Writes results/embedded/fit_cortex_m3.txt. Needs the same tools as run.sh.
set -e
cd "$(dirname "$0")/../.."
mkdir -p build/embedded results/embedded
OUT=results/embedded/fit_cortex_m3.txt
ARMFLAGS="-mcpu=cortex-m3 -mthumb -Os -fno-exceptions -fno-rtti -fno-threadsafe-statics -ffunction-sections -fdata-sections"
{
  echo "compiler: $(arm-none-eabi-g++ --version | head -1)"
  echo "emulator: $(qemu-system-arm --version | head -1)"
  echo "machine: mps2-an385 (Cortex-M3); RAM limited to 64 KiB; no heap, no OS"
  echo
} > "$OUT"
while [ $# -ge 2 ]; do
  t="$1"; BYTES=$(( $2 * 1024 )); shift 2
  gunzip -c "workloads/traces/$t.trace.gz" > "build/embedded/$t.trace"
  python3 tools/embedded/gen_trace_header.py "build/embedded/$t.trace" > build/embedded/trace_data.h
  # expected checksum: host run of STRATA with a buffer that is certainly large enough
  g++ -std=c++14 -O2 -Ibuild/embedded -DBUFFER_BYTES=4194304 -o build/embedded/host tools/embedded/main.cpp
  read -r SUM REFUSED PEAK < <(./build/embedded/host)
  arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -Os -c tools/embedded/startup.c -o build/embedded/startup.o
  for table in STRATA ARENA; do
    D=""; [ "$table" = ARENA ] && D="-DTABLE_ARENA"
    arm-none-eabi-g++ -std=c++14 $ARMFLAGS $D -Ibuild/embedded -DBUFFER_BYTES="$BYTES" -DEXPECTED_CHECKSUM="${SUM}u" \
      -c tools/embedded/main.cpp -o build/embedded/main.o
    arm-none-eabi-g++ -mcpu=cortex-m3 -mthumb -nostartfiles -T tools/embedded/link.ld -Wl,--gc-sections \
      --specs=nano.specs --specs=nosys.specs build/embedded/startup.o build/embedded/main.o -o build/embedded/fit.elf 2> build/embedded/link.log || { cat build/embedded/link.log; exit 1; }
    {
      echo "== $t  buffer $BYTES bytes  table $table"
      timeout 120 qemu-system-arm -M mps2-an385 -cpu cortex-m3 -nographic -semihosting -kernel build/embedded/fit.elf 2>&1 | grep -E "refused|peak used|RESULT"
      echo
    } | tee -a "$OUT"
  done
done
