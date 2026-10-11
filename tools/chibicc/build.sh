#!/bin/bash
# Fetch chibicc at the pinned commit, patch it, and build three compilers:
#   chibicc-orig     original per-scope hash maps (plus the trace hook)
#   chibicc-strata   variable scopes on STRATA
#   chibicc-arena    variable scopes on the conventional arena + chains table
#   tools/chibicc/build.sh [workdir]        (default ~/cdes)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/../.."
WORK="${1:-$HOME/cdes}"
COMMIT=90d1f7f199cc55b13c7fdb5839d1409806633fdb
mkdir -p "$WORK" && cd "$WORK"
[ -d chibicc ] || git clone -q https://github.com/rui314/chibicc.git chibicc
cd chibicc
git checkout -q -f "$COMMIT"
git clean -q -fdx
python3 "$HERE/apply_patch.py" "$PWD"
C="-std=c11 -O2 -fno-common -w"
for v in orig strata arena; do
  rm -f ./*.o
  D=""
  [ "$v" != orig ] && D="-DCDES_BACKEND"
  for f in *.c; do cc $C $D -c "$f" -o "${f%.c}.o"; done
  if [ "$v" = orig ]; then
    cc -o "$WORK/chibicc-orig" ./*.o
  else
    B=BACKEND_STRATA; [ "$v" = arena ] && B=BACKEND_ARENA
    g++ -std=c++14 -O2 -fno-exceptions -fno-rtti -D$B -I"$ROOT/include" -I"$ROOT/benchmarks/baselines" -c "$HERE/cdes_backend.cpp" -o cdes_backend.o
    g++ -o "$WORK/chibicc-$v" ./*.o
  fi
done
rm -f ./*.o
# chibicc looks for its own headers next to the binary
for v in orig strata arena; do mkdir -p "$WORK/cc-$v" && cp "$WORK/chibicc-$v" "$WORK/cc-$v/chibicc" && rm -rf "$WORK/cc-$v/include" && cp -r include "$WORK/cc-$v/include"; done
printf 'int g = 5;\nint f(int a) { int b = a; { int a = b + g; b = a; } return b; }\nint main(void) { return f(37) - 42; }\n' > "$WORK/t.c"
for v in orig strata arena; do
  "$WORK/cc-$v/chibicc" -o "$WORK/t-$v" "$WORK/t.c" && "$WORK/t-$v" && echo "chibicc-$v: test program compiled and returned 0"
done
