#!/usr/bin/env python3
"""Admitted versus refused declarations for every configuration of the flooding experiment
(results/hardening/flood.csv, written by benchmarks/hardening_main.cpp --mode flood).

    python3 tools/review/flood_summary.py [n] > docs/flood_summary.txt      (default n = 32768; use 0 for all sizes)

'admitted' = n - refused (a refused declaration stores nothing). 'lookups ok' is the benchmark's own
correctness flag: every lookup of a stored name returned its value and every lookup of a refused name
failed, and the table's invariants held. Times are medians of 5 repetitions, in milliseconds.
"""
import csv, os, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
want = int(sys.argv[1]) if len(sys.argv) > 1 else 32768
print("%6s %-9s %-14s %9s %9s %9s %7s %11s %11s %6s" % ("n", "input", "config", "submitted", "admitted", "refused", "longest", "declare_ms", "lookup_ms", "ok"))
for r in csv.DictReader(open(os.path.join(root, "results", "hardening", "flood.csv"))):
    n = int(r["n"])
    if want and n != want: continue
    ref = int(r["refused"])
    print("%6d %-9s %-14s %9d %9d %9d %7s %11.2f %11.2f %6s" % (
        n, r["input"], r["config"], n, n - ref, ref, r["longest_probe"], float(r["declare_ns_median"]) / 1e6,
        float(r["lookup_ns_median"]) / 1e6, "yes" if r["correct"] == "1" else "NO"))
