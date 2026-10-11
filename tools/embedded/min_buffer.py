#!/usr/bin/env python3
"""Print the measured minimum STRATA buffer for a trace, rounded up to a whole KiB.

    python3 min_buffer.py TRACE_NAME      (reads the newest results/raw/*/budget.csv)
"""
import csv
import glob
import sys

best = None
for f in sorted(glob.glob("results/raw/*/budget.csv")):
    for r in csv.DictReader(open(f)):
        if r["trace"] == sys.argv[1] and r["names"] == "packed" and r["budget_factor"] == "1.00":
            best = int(r["min_buffer_bytes"])
print(((best or 32768) + 1023) // 1024 * 1024)
