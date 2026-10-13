#!/bin/bash
# Bounded mode (static index, probe limit 64, HalfSipHash-1-3) on the bare-metal Cortex-M3
# under QEMU. The index size per trace comes from results/hardening/traces.csv
# (scripts/audit/hardening.sh). The expected checksum is the one of the ordinary
# fixed-buffer host run, so a PASS also shows that the bounded table refused nothing and
# answered every lookup identically.
#   tools/embedded/bounded.sh [trace names...]      default: zlib littlefs cjson lua freertos
set -e
cd "$(dirname "$0")/../.."
mkdir -p build/embedded results/embedded
OUT=results/embedded/qemu_cortex_m3_bounded.txt
ARMFLAGS="-mcpu=cortex-m3 -mthumb -Os -fno-exceptions -fno-rtti -fno-threadsafe-statics -ffunction-sections -fdata-sections"
{
  echo "compiler: $(arm-none-eabi-g++ --version | head -1)"
  echo "emulator: $(qemu-system-arm --version | head -1)"
  echo "machine: mps2-an385 (Cortex-M3); RAM limited to 64 KiB by tools/embedded/link.ld; no heap, no OS"
  echo
} > "$OUT"
[ $# -eq 0 ] && set -- zlib littlefs cjson lua freertos
for t in "$@"; do
  gunzip -c "workloads/traces/$t.trace.gz" > "build/embedded/$t.trace"
  python3 tools/embedded/gen_trace_header.py "build/embedded/$t.trace" > build/embedded/trace_data.h
  MIN=$(python3 tools/embedded/min_buffer.py "$t")
  SLOTS=$(awk -F, -v t="$t" '$1 == t { print $3; exit }' results/hardening/traces.csv)
  DEFS="-DBUFFER_BYTES=$MIN -DTABLE_BOUNDED -DINDEX_SLOTS=$SLOTS -DMAX_PROBE=64"
  g++ -std=c++14 -O2 -Ibuild/embedded -DBUFFER_BYTES="$MIN" -o build/embedded/host tools/embedded/main.cpp
  read -r SUM REFUSED PEAK < <(./build/embedded/host)
  arm-none-eabi-g++ -std=c++14 $ARMFLAGS -Ibuild/embedded $DEFS -DEXPECTED_CHECKSUM="${SUM}u" -c tools/embedded/main.cpp -o build/embedded/main_b.o
  arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -Os -c tools/embedded/startup.c -o build/embedded/startup.o
  arm-none-eabi-g++ -mcpu=cortex-m3 -mthumb -nostartfiles -T tools/embedded/link.ld -Wl,--gc-sections \
    --specs=nano.specs --specs=nosys.specs build/embedded/startup.o build/embedded/main_b.o \
    -o "build/embedded/${t}_bounded.elf" 2> build/embedded/link.log || { cat build/embedded/link.log; exit 1; }
  {
    echo "== $t   (ordinary fixed-buffer host run: checksum $SUM, refused $REFUSED; buffer $MIN bytes, index $SLOTS slots, probe limit 64)"
    timeout 120 qemu-system-arm -M mps2-an385 -cpu cortex-m3 -nographic -semihosting -kernel "build/embedded/${t}_bounded.elf" 2>&1
    echo "STRATA code size (sum of the strata:: functions in the object file, bytes):"
    arm-none-eabi-nm --size-sort -S -C build/embedded/main_b.o | awk '/strata::/ {n += strtonum("0x" $2)} END {print "  " n}'
    echo
  } | tee -a "$OUT"
done
