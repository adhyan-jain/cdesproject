#!/bin/bash
# Fetch TinyCC at the pinned commit, apply the trace hooks and build it.
#   tools/tcc-trace/build_tcc.sh [workdir]     (default: ~/cdes)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${1:-$HOME/cdes}"
TCC_COMMIT=43c7708b85681a2fd4451c8a541af4494a8919b2
mkdir -p "$WORK" && cd "$WORK"
if [ ! -d tinycc ]; then
  git clone -q https://repo.or.cz/tinycc.git tinycc || git clone -q https://github.com/TinyCC/tinycc.git tinycc
fi
cd tinycc
git checkout -q -f "$TCC_COMMIT"
python3 "$HERE/apply_patch.py" "$PWD"
./configure --prefix="$WORK/tcc-install" > /dev/null
make -j"$(nproc)" > "$WORK/tcc-build.log" 2>&1
make install >> "$WORK/tcc-build.log" 2>&1
"$WORK/tcc-install/bin/tcc" -v
printf 'int g; int f(int a){ int b = a; { int a = b + g; b = a; } return b; }\n' > "$WORK/t.c"
rm -f "$WORK/t.trace"
CDES_TRACE="$WORK/t.trace" "$WORK/tcc-install/bin/tcc" -c "$WORK/t.c" -o /dev/null
cat "$WORK/t.trace" | tr '\n' ' '; echo
