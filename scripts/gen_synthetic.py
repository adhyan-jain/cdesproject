#!/usr/bin/env python3
"""Deterministic synthetic stress traces (compact format: E / X / D name / L name).

    python3 scripts/gen_synthetic.py OUTDIR

Each trace isolates one property. Seeds are fixed, so the files are reproducible.
"""
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "workloads/synthetic"
os.makedirs(OUT, exist_ok=True)
ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"


def ident(rng, lo, hi):
    n = rng.randint(lo, hi)
    return rng.choice(ALPHA) + "".join(rng.choice(ALPHA + "0123456789") for _ in range(n - 1))


def pool(rng, count, lo, hi):
    seen = set()
    while len(seen) < count:
        seen.add(ident(rng, lo, hi))
    return sorted(seen)


def write(name, lines):
    with open(os.path.join(OUT, name + ".trace"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("%-18s %8d events" % (name, len(lines)))


def mixed(seed, names, steps, max_depth, p_scope, p_decl):
    """Random walk over scopes; lookups pick names with a bias to recent ones."""
    rng = random.Random(seed)
    out, depth = [], 0
    for _ in range(steps):
        r = rng.random()
        if r < p_scope:
            if depth < max_depth and (depth == 0 or rng.random() < 0.5):
                out.append("E"); depth += 1
            elif depth:
                out.append("X"); depth -= 1
        elif r < p_scope + p_decl:
            out.append("D " + rng.choice(names))
        else:
            out.append("L " + rng.choice(names))
    out += ["X"] * depth
    return out


rng = random.Random(1)
write("short_ids", mixed(11, pool(rng, 2000, 1, 3), 300000, 10, 0.10, 0.30))
write("long_ids", mixed(12, pool(rng, 2000, 40, 80), 300000, 10, 0.10, 0.30))
write("deep_nesting", mixed(13, pool(rng, 3000, 6, 16), 300000, 200, 0.30, 0.30))
write("shadow_heavy", mixed(14, pool(rng, 24, 4, 10), 300000, 40, 0.20, 0.45))
write("lookup_heavy", mixed(15, pool(rng, 3000, 6, 16), 300000, 10, 0.05, 0.05))

# high declaration density: 50 000 live names in one scope, then lookups
names = pool(rng, 50000, 6, 20)
r2 = random.Random(16)
write("dense_50k", ["D " + n for n in names] + ["L " + r2.choice(names) for _ in range(200000)])

# scope churn: many small scopes created and destroyed
names = pool(rng, 500, 4, 12)
r3 = random.Random(17)
lines = ["D " + n for n in names[:50]]
for _ in range(30000):
    lines.append("E")
    lines += ["D " + r3.choice(names) for _ in range(5)]
    lines += ["L " + r3.choice(names) for _ in range(4)]
    lines.append("X")
write("scope_churn", lines)

# one very large scope entered and left repeatedly: scope-exit cost per declaration
names = pool(rng, 10000, 6, 20)
lines = ["D outer_%d" % i for i in range(100)]
for _ in range(20):
    lines.append("E")
    lines += ["D " + n for n in names]
    lines.append("X")
write("big_scope_exit", lines)

# the same identifier declared in 400 nested scopes (METIS-X stores at most 251 keys with one hash)
lines = []
for d in range(400):
    lines += ["D x", "L x", "E"]
lines += ["X", "L x"] * 400
write("deep_shadow_400", lines)
