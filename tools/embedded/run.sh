#!/bin/bash
# Build and run the bare-metal test under QEMU for one or more compiler traces.
#   tools/embedded/run.sh [trace names...]      default: zlib littlefs cjson
# Needs: arm-none-eabi-g++ (with newlib), qemu-system-arm, python3, g++.
set -e
cd "$(dirname "$0")/../.."
mkdir -p build/embedded results/embedded
OUT=results/embedded/qemu_cortex_m3.txt
ARMFLAGS="-mcpu=cortex-m3 -mthumb -Os -fno-exceptions -fno-rtti -fno-threadsafe-statics -ffunction-sections -fdata-sections"
{
  echo "compiler: $(arm-none-eabi-g++ --version | head -1)"
  echo "emulator: $(qemu-system-arm --version | head -1)"
  echo "machine: mps2-an385 (Cortex-M3); RAM limited to 64 KiB by tools/embedded/link.ld; no heap, no OS"
  echo "flags: $ARMFLAGS -Wl,--gc-sections"
  echo
} > "$OUT"
[ $# -eq 0 ] && set -- zlib littlefs cjson
for t in "$@"; do
  gunzip -c "workloads/traces/$t.trace.gz" > "build/embedded/$t.trace"
  python3 tools/embedded/gen_trace_header.py "build/embedded/$t.trace" > build/embedded/trace_data.h
  MIN=$(python3 tools/embedded/min_buffer.py "$t")
  g++ -std=c++14 -O2 -Ibuild/embedded -DBUFFER_BYTES="$MIN" -o build/embedded/host tools/embedded/main.cpp
  read -r SUM REFUSED PEAK < <(./build/embedded/host)
  arm-none-eabi-g++ -std=c++14 $ARMFLAGS -Ibuild/embedded -DBUFFER_BYTES="$MIN" -DEXPECTED_CHECKSUM="${SUM}u" \
    -c tools/embedded/main.cpp -o build/embedded/main.o
  arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -Os -c tools/embedded/startup.c -o build/embedded/startup.o
  arm-none-eabi-g++ -mcpu=cortex-m3 -mthumb -nostartfiles -T tools/embedded/link.ld -Wl,--gc-sections \
    --specs=nano.specs --specs=nosys.specs build/embedded/startup.o build/embedded/main.o \
    -o "build/embedded/$t.elf" 2> build/embedded/link.log || { cat build/embedded/link.log; exit 1; }
  {
    echo "== $t   (host run: checksum $SUM, refused $REFUSED, peak used $PEAK bytes; buffer $MIN bytes)"
    timeout 120 qemu-system-arm -M mps2-an385 -cpu cortex-m3 -nographic -semihosting -kernel "build/embedded/$t.elf" 2>&1
    echo "STRATA code size (sum of the strata:: functions in the object file, bytes):"
    arm-none-eabi-nm --size-sort -S -C build/embedded/main.o | awk '/strata::/ {n += strtonum("0x" $2)} END {print "  " n}'
    arm-none-eabi-size "build/embedded/$t.elf" | tail -1 | awk '{print "whole image: text " $1 ", data " $2 ", bss " $3 "  (text includes the embedded trace)"}'
    echo
  } | tee -a "$OUT"
done
