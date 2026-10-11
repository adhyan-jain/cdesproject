#!/bin/bash
# Compile pinned open-source C projects with the instrumented TinyCC and collect one
# trace per project (translation units are separated by "U" lines).
#   tools/tcc-trace/make_traces.sh [workdir] [outdir]
# Requires build_tcc.sh to have been run. A translation unit that TinyCC cannot
# compile is skipped and counted; its partial trace is discarded.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${1:-$HOME/cdes}"
OUT="${2:-$HERE/../../workloads/traces}"
TCC="$WORK/tcc-install/bin/tcc"
SRC="$WORK/src"
mkdir -p "$SRC" "$OUT"
MANIFEST="$OUT/MANIFEST.tsv"
printf 'project\tversion\tsource\tunits_ok\tunits_failed\tevents\n' > "$MANIFEST"

fetch_git() {   # name url ref
  if [ ! -d "$SRC/$1" ]; then
    git clone -q --depth 1 --branch "$3" "$2" "$SRC/$1" || return 1
  fi
}
fetch_tar() {   # name url
  if [ ! -d "$SRC/$1" ]; then
    mkdir -p "$SRC/$1" && curl -sL "$2" -o "$SRC/$1.pkg" || return 1
    case "$2" in
      *.zip) (cd "$SRC/$1" && python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall('.')" "$SRC/$1.pkg") ;;
      *) tar xf "$SRC/$1.pkg" -C "$SRC/$1" --strip-components=1 ;;
    esac
  fi
}
trace() {       # project version source flags... -- files...
  local name="$1" ver="$2" src="$3"; shift 3
  local flags=()
  while [ "$1" != "--" ]; do flags+=("$1"); shift; done
  shift
  local out="$OUT/$name.trace" ok=0 bad=0 tmp="$WORK/unit.trace"
  : > "$out"
  for f in "$@"; do
    rm -f "$tmp"
    if CDES_TRACE="$tmp" "$TCC" -c "${flags[@]}" "$f" -o /dev/null 2> "$WORK/unit.err"; then
      cat "$tmp" >> "$out"; ok=$((ok + 1))
    else
      bad=$((bad + 1)); echo "  skipped $(basename "$f"): $(head -1 "$WORK/unit.err")"
    fi
  done
  local n; n=$(wc -l < "$out")
  printf '%s\t%s\t%s\t%d\t%d\t%d\n' "$name" "$ver" "$src" "$ok" "$bad" "$n" >> "$MANIFEST"
  echo "$name: $ok units, $bad skipped, $n events"
}

fetch_git cjson https://github.com/DaveGamble/cJSON v1.7.18 &&
  trace cjson v1.7.18 https://github.com/DaveGamble/cJSON -- "$SRC"/cjson/cJSON.c "$SRC"/cjson/cJSON_Utils.c

fetch_git littlefs https://github.com/littlefs-project/littlefs v2.9.3 &&
  trace littlefs v2.9.3 https://github.com/littlefs-project/littlefs -- "$SRC"/littlefs/lfs.c "$SRC"/littlefs/lfs_util.c

fetch_git zlib https://github.com/madler/zlib v1.3.1 &&
  trace zlib v1.3.1 https://github.com/madler/zlib -I"$SRC/zlib" -- "$SRC"/zlib/*.c

fetch_tar lua https://www.lua.org/ftp/lua-5.4.7.tar.gz &&
  trace lua 5.4.7 https://www.lua.org/ftp/lua-5.4.7.tar.gz -DLUA_USE_POSIX -- "$SRC"/lua/src/*.c

fetch_git freertos https://github.com/FreeRTOS/FreeRTOS-Kernel V11.1.0 &&
  trace freertos V11.1.0 https://github.com/FreeRTOS/FreeRTOS-Kernel \
    -I"$SRC/freertos/include" -I"$SRC/freertos/portable/ThirdParty/GCC/Posix" \
    -I"$SRC/freertos/portable/ThirdParty/GCC/Posix/utils" -I"$HERE/freertos-config" -- \
    "$SRC"/freertos/tasks.c "$SRC"/freertos/queue.c "$SRC"/freertos/list.c "$SRC"/freertos/timers.c \
    "$SRC"/freertos/event_groups.c "$SRC"/freertos/stream_buffer.c "$SRC"/freertos/croutine.c \
    "$SRC"/freertos/portable/MemMang/heap_4.c "$SRC"/freertos/portable/ThirdParty/GCC/Posix/port.c

fetch_git mbedtls https://github.com/Mbed-TLS/mbedtls v3.6.2 &&
  trace mbedtls v3.6.2 https://github.com/Mbed-TLS/mbedtls -I"$SRC/mbedtls/include" -I"$SRC/mbedtls/library" -- "$SRC"/mbedtls/library/*.c

if [ ! -d "$SRC/tinycc" ]; then git -C "$WORK/tinycc" worktree add -q "$SRC/tinycc" 43c7708b85681a2fd4451c8a541af4494a8919b2; fi
[ -f "$SRC/tinycc/tccdefs_.h" ] || (cd "$SRC/tinycc" && ./configure > /dev/null && make -s tccdefs_.h > /dev/null)
trace tinycc 43c7708 https://repo.or.cz/tinycc.git -I"$SRC/tinycc" -- "$SRC"/tinycc/tcc.c

fetch_tar sqlite https://www.sqlite.org/2024/sqlite-amalgamation-3460000.zip &&
  trace sqlite 3.46.0 https://www.sqlite.org/2024/sqlite-amalgamation-3460000.zip -- "$SRC"/sqlite/*/sqlite3.c

{ echo "tcc: $($TCC -v)"; echo "libc headers: $(ldd --version | head -1)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$OUT/ENVIRONMENT.txt"
cat "$MANIFEST"
ls -l "$OUT"
