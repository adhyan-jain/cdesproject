#!/usr/bin/env python3
"""Per-trace statistics of workloads/traces/*.trace.gz, computed with a minimal replay that follows the
semantics of tests/reference_model.hpp (innermost declaration wins; a second declaration in the SAME scope
replaces the first). Not part of the paper's pipeline; it documents what the traces contain.

    python3 tools/review/trace_stats.py > docs/trace_stats.txt

Columns: units, event-line counts by tag (U/E/X/D/L/G), D lines with an empty name (dropped by the replay
tools), D events that hit a name already declared in the same scope (same-scope replacement), lookups that
resolve (hit) and that do not (miss), the deepest scope nesting, and the number of '__'-prefixed names declared.
"""
import collections, glob, gzip, os

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
print("%-18s %5s %8s %8s %8s %3s %7s %7s %8s %8s %5s %7s" % (
    "trace", "units", "E", "D", "L", "G", "Dempty", "redecl", "Lhit", "Lmiss", "depth", "__names"))
for f in sorted(glob.glob(os.path.join(root, "workloads", "traces", "*.trace.gz"))):
    nm = os.path.basename(f)[:-len(".trace.gz")]
    c = collections.Counter()
    names, stacks = {}, [[]]
    depth = maxdepth = 0
    for line in gzip.open(f, "rt", errors="replace"):
        t, _, a = line.rstrip("\n").partition(" ")
        if t == "U":
            c["U"] += 1; names, stacks = {}, [[]]; depth = 0
        elif t == "E":
            c["E"] += 1; stacks.append([]); depth += 1; maxdepth = max(maxdepth, depth)
        elif t == "X":
            c["X"] += 1
            if len(stacks) > 1:
                for n in stacks.pop():
                    names[n].pop()
                depth -= 1
        elif t == "G":
            c["G"] += 1
        elif t == "D":
            c["D"] += 1
            if not a:
                c["Dempty"] += 1; continue
            if a.startswith("__"): c["dunder"] += 1
            d = len(stacks) - 1
            v = names.setdefault(a, [])
            if v and v[-1] == d: c["redecl"] += 1
            else: v.append(d); stacks[-1].append(a)
        elif t == "L":
            c["L"] += 1
            if not a: continue
            c["Lhit" if names.get(a) else "Lmiss"] += 1
    print("%-18s %5d %8d %8d %8d %3d %7d %7d %8d %8d %5d %7d" % (
        nm, c["U"], c["E"], c["D"], c["L"], c["G"], c["Dempty"], c["redecl"], c["Lhit"], c["Lmiss"], maxdepth, c["dunder"]))
