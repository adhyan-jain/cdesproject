"""Exact refusal law against the default hash on real identifiers (see law_real_names.cpp).

    python3 run_real_names.py BUILD/law_real_names TRACE_DIR OUT.csv

Names of a trace are its distinct declared identifiers. Only rows with at least four times as many
distinct names as n (pool_at_least_4n) are meaningful: when n is a large share of the pool, the subsets barely differ. One row per trace and setting:
observed rate of "the next fresh name needs more than L probes" over random subsets of the names,
against the exact law for the same m, n, L.
"""
import csv, os, subprocess, sys
from design_table import refuse
exe, tracedir, out = sys.argv[1:4]
settings = [(1024, 760, 48, 50000), (1024, 760, 96, 50000), (4096, 3071, 80, 20000), (4096, 3071, 100, 20000)]
rows = []
for fn in sorted(os.listdir(tracedir)):
    if not fn.endswith(".trace"):
        continue
    names = sorted({l.split(None, 1)[1].strip() for l in open(os.path.join(tracedir, fn)) if l.startswith("D ")})
    path = os.path.join("/tmp", "names_" + fn + ".txt")
    open(path, "w").write("\n".join(names) + "\n")
    for (m, n, L, trials) in settings:
        if len(names) <= n:
            continue
        ex, tr = [int(v) for v in subprocess.check_output([exe, path, str(m), str(n), str(L), str(trials), "7"]).split()]
        p = refuse(m, n, [L])[L]
        rows.append((fn[:-6], len(names), m, n, L, tr, ex / tr, p, n / len(names) <= 0.25))
        print(f"{fn[:-6]:9s} names {len(names):5d}  m={m:5d} n={n:5d} L={L:4d}  observed {ex/tr:.5f}  law {p:.5f}  ratio {ex/tr/p:.2f}")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["trace", "distinct_names", "m", "n", "L", "trials", "observed", "exact_law", "pool_at_least_4n"])
    w.writerows(rows)
