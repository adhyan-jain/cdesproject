"""Copy the theory tables (theory/paper/tables, written by theory/verify/run_all.sh) into tables/th_*.tex
in the ruled style of the other tables of this article (vertical rules, \\hline instead of booktabs).
Only the rules change; every cell is copied unchanged.  Run from the repository root:
    python manuscript/ieee_access/tools/theory_tables.py
"""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "theory", "paper", "tables")
DST = os.path.join(ROOT, "manuscript", "ieee_access", "tables")

for name in ("tab_design", "tab_lawcheck", "tab_lawproc", "tab_ladder", "tab_orphan", "tab_adaptive"):
    t = open(os.path.join(SRC, name + ".tex"), encoding="utf8").read()
    t = re.sub(r"\\begin\{tabular\}\{@\{\}([a-z]+)@\{\}\}", lambda m: "\\begin{tabular}{|" + "|".join(m.group(1)) + "|}", t)
    t = t.replace("\\toprule", "\\hline").replace("\\midrule", "\\hline").replace("\\bottomrule", "\\hline")
    open(os.path.join(DST, "th_" + name + ".tex"), "w", encoding="utf8").write(t)
    print("th_" + name + ".tex")
