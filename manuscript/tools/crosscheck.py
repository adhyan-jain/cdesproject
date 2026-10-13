#!/usr/bin/env python3
"""Two generators, one data set: do they agree?

    python manuscript/tools/crosscheck.py

paper/generated.tex is written by scripts/make_report.py (pandas, written on 2026-10-11) and
paper/generated_numbers.tex by manuscript/tools/make_numbers.py (standard library, written
on 2026-10-13). They were written independently and use different bootstrap seeds, so
counts and deterministic quantities must match exactly and timing ranges to within one
percentage point. A disagreement means one of them is reading stale or wrong data.
"""
import os
import re
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "paper")


def macros(name):
    out = {}
    for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^%\n]*)\}", open(os.path.join(P, name), encoding="utf-8").read()):
        out[k] = v
    return out


def num(text):
    text = text.replace("$-$", "-").replace("$+$", "+").replace("\\,", "").replace("{,}", "")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(m.group()) if m else None


old, new = macros("generated.tex"), macros("generated_numbers.tex")
# (old macro, new macro, tolerance, sign): sign -1 when the two use opposite sign conventions
PAIRS = [
    ("RunId", "RunName", None, 1), ("Rounds", "Rounds", 0, 1), ("PairsAll", "NPairs", 0, 1), ("PairsOk", "NPairs", 0, 1),
    ("HeapRedMin", "HeapMetisLo", 0.5, 1), ("HeapRedMax", "HeapMetisHi", 0.5, 1), ("HeapRedMed", "HeapMetisMed", 0.5, 1),
    ("AllocRedMin", "AllocLo", 0.05, 1), ("AllocRedMax", "AllocHi", 0.05, 1),
    ("TimeRedMin", "MetisLo", 1.0, 1), ("TimeRedMax", "MetisHi", 1.0, 1), ("MFasterN", "MetisFaster", 0, 1), ("MSlowerN", "MetisSlower", 0, 1),
    ("DeclMin", "DeclLo", 0.5, 1), ("DeclMax", "DeclHi", 0.5, 1), ("ExitMin", "ExitLo", 0.5, 1), ("ExitMax", "ExitHi", 0.5, 1),
    ("BufMin", "MinBufLo", 0.05, 1), ("BufMax", "MinBufHi", 0.05, 1), ("BpdMin", "BytesLo", 0.5, 1), ("BpdMax", "BytesHi", 0.5, 1),
    ("FixArenaMin", "SaveLo", 0.5, 1), ("FixArenaMax", "SaveHi", 0.5, 1),
    ("ArenaVsMetisTimeMin", "AMLo", 1.0, 1), ("ArenaVsMetisTimeMax", "AMHi", 1.0, 1),
    ("ArenaSlowerN", "ArenaSlower", 0, 1), ("ArenaSlowMax", "ArenaHi", 1.0, 1), ("ArenaSlowMin", "ArenaLo", 1.0, 1),
    ("SynN", "SynCount", 0, 1), ("SynArenaFaster", "SynFasterArena", 0, 1), ("SynArenaSlower", "SynSlowerArena", 0, 1),
    ("PackMin", "PackSaveLo", 0.05, 1), ("PackMax", "PackSaveHi", 0.05, 1),
    ("SparseMemMin", "SparseBufLo", 0.5, 1), ("SparseMemMax", "SparseBufHi", 0.5, 1),
    ("DeepRefused", "MetisRefused", 0, 1), ("UnitsN", "UnitsTotal", 0, 1), ("FitBestOnly", "UnitOnlySixteen", 0, 1),
    ("SweepMemMax", "SweepBestSave", 0.5, 1),
    ("ChibiUnits", "ChibiUnitsOK", 0, 1), ("ChibiAll", "ChibiUnitsAll", 0, 1), ("ChibiSame", "ChibiIdentStrata", 0, 1),
    ("ChibiRounds", "ChibiRounds", 0, 1), ("ChibiStrataSlowN", "ChibiStrataSlower", 0, 1), ("ChibiArenaEstN", "ChibiArenaFaster", 0, 1),
    ("ChibiTimeMin", "ChibiStrataHi", 0.6, -1), ("ChibiTimeMax", "ChibiStrataLo", 0.6, -1),
    ("EmbN", "EmbPass", 0, 1), ("EmbStack", "EmbStack", 0, 1),
]
bad = 0
for a, b, tol, sign in PAIRS:
    if a not in old or b not in new:
        print(f"MISSING  {a} / {b}")
        bad += 1
        continue
    if tol is None:
        ok = old[a].replace("\\_", "_") == new[b].replace("\\_", "_")
        detail = f"{old[a]} / {new[b]}"
    else:
        x, y = num(old[a]), num(new[b])
        ok = x is not None and y is not None and abs(x - sign * y) <= tol + 1e-9
        detail = f"{x} / {sign * y if y is not None else None} (tolerance {tol})"
    bad += not ok
    print(f"{'AGREE   ' if ok else 'DISAGREE'} {a:22s} {b:18s} {detail}")
print(f"{len(PAIRS)} quantities compared, {bad} disagreements")
sys.exit(1 if bad else 0)
