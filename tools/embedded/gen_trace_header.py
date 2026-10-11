#!/usr/bin/env python3
"""Turn a compact trace (U/E/X/D/L) into a C header for the bare-metal test.

    python3 gen_trace_header.py TRACE > trace_data.h
"""
import sys

names, ids, ops = [], {}, []
for line in open(sys.argv[1]):
    p = line.split()
    if not p or p[0] == "G":
        continue
    k = "UEXDL".index(p[0])
    i = 0
    if k >= 3:
        if p[1] not in ids:
            ids[p[1]] = len(names)
            names.append(p[1])
        i = ids[p[1]]
    ops.append((k, i))
if ops and ops[0][0] == 0:
    ops = ops[1:]          # the first unit needs no reset
assert len(names) < 65536
print("/* generated from %s: %d operations, %d distinct names */" % (sys.argv[1].split("/")[-1], len(ops), len(names)))
print("static const char *const kNames[] = {")
for n in names:
    print('    "%s",' % n)
print("};")
print("static const unsigned char kKind[] = {%s};" % ",".join(str(k) for k, _ in ops))
print("static const unsigned short kName[] = {%s};" % ",".join(str(i) for _, i in ops))
print("enum { kOps = %d };" % len(ops))
