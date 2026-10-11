#!/usr/bin/env python3
"""Parametric traces for the shadowing / name-length sweep.

    python3 scripts/gen_sweep.py OUTDIR

Each trace holds N = 4096 live declarations at its peak, built from D = N / sigma distinct
names declared in sigma nested scopes (sigma = live declarations per distinct name, the
"shadowing factor"). Names have exactly L characters. After the last declaration there
are 5 lookups per live declaration, then every scope is closed. The whole pattern is
repeated 4 times. Seeds are fixed.

File name: s<sigma x 10>_L<length>.trace     e.g. s15_L12 = sigma 1.5, 12-character names
"""
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "build/sweep"
os.makedirs(OUT, exist_ok=True)
N = 4096
ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
SIGMAS = [1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 8.0]
LENGTHS = [6, 12, 24]


def names(rng, count, length):
    seen = set()
    while len(seen) < count:
        seen.add(rng.choice(ALPHA) + "".join(rng.choice(ALPHA + "0123456789") for _ in range(length - 1)))
    return sorted(seen)


for L in LENGTHS:
    for sigma in SIGMAS:
        rng = random.Random(1000 * L + int(sigma * 100))
        D = int(round(N / sigma))
        pool = names(rng, D, L)
        lines = []
        for _ in range(4):
            left, depth = N, 0
            while left > 0:
                take = min(D, left)
                if depth:
                    lines.append("E")
                # the last, partial level redeclares a random subset: fractional sigma
                level = pool if take == D else rng.sample(pool, take)
                lines += ["D " + n for n in level]
                left -= take
                depth += 1
            lines += ["L " + rng.choice(pool) for _ in range(5 * N)]
            lines += ["X"] * (depth - 1)
            lines.append("U")
        lines.pop()
        with open(os.path.join(OUT, "s%02d_L%02d.trace" % (int(round(sigma * 10)), L)), "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
print("wrote %d traces to %s" % (len(SIGMAS) * len(LENGTHS), OUT))
