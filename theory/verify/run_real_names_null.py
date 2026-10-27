"""Spread of the real-identifier check under random keys (null distribution), see law_real_names.cpp.

    python3 run_real_names_null.py BUILD/law_real_names TRACE_DIR OUT.csv [KEYS=100] [TRIALS=20000]

For each vocabulary with at least four times as many names as stored, the same random subsets of names are inserted
under KEYS random keyed hashes (m = 1024, n = 760); one row per key with the observed frequency of "next name needs
more than L probes" for L = 48 and 96. The unkeyed (default hash) frequency of run_real_names.py is to be compared
with this spread.
"""
import csv, os, subprocess, sys
exe, tracedir, out = sys.argv[1:4]
keys = int(sys.argv[4]) if len(sys.argv) > 4 else 100
trials = int(sys.argv[5]) if len(sys.argv) > 5 else 20000
rows = []
for fn in sorted(os.listdir(tracedir)):
    if not fn.endswith(".trace"):
        continue
    names = sorted({l.split(None, 1)[1].strip() for l in open(os.path.join(tracedir, fn)) if l.startswith("D ")})
    if len(names) < 4 * 760:
        continue
    path = os.path.join("/tmp", "names_" + fn + ".txt")
    open(path, "w").write("\n".join(names) + "\n")
    for L in (48, 96):
        for k in range(keys):
            ex, tr = [int(v) for v in subprocess.check_output([exe, path, "1024", "760", str(L), str(trials), "7", str(1000 + k)]).split()]
            rows.append((fn[:-6], len(names), L, k, tr, ex / tr))
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["trace", "distinct_names", "L", "key", "trials", "observed"])
    w.writerows(rows)
