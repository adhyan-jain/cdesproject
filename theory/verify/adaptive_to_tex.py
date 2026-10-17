"""Turn adaptive_key_demo.out into a LaTeX table and macros."""
import re, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
lines = open(os.path.join(HERE, "adaptive_key_demo.out")).read().splitlines()
hdr = lines[0]
m_, L_, hon_, seeds_ = re.findall(r"m=(\d+) L=(\d+) honest names=(\d+) seeds=(\d+)", hdr)[0]
rows = []; qpc = None
for ln in lines[2:]:
    t = re.findall(r"[\d.]+", ln)
    c, q, same, smax, fresh, fmax, ctrl = t[0], t[1], t[2], t[3], t[4], t[5], t[6]
    qpc = q
    rows.append(f"{c} & {same}\\% & {smax}\\% & {fresh}\\% & {ctrl}\\% \\\\")
d = os.path.join(HERE, "../paper/tables")
open(os.path.join(d, "tab_adaptive.rows"), "w").write("\n".join(rows) + "\n")
open(os.path.join(d, "adaptive_summary.tex"), "w").write(
    f"\\newcommand{{\\AdM}}{{{m_}}}\n\\newcommand{{\\AdL}}{{{L_}}}\n\\newcommand{{\\AdHonest}}{{{hon_}}}\n"
    f"\\newcommand{{\\AdSeeds}}{{{seeds_}}}\n\\newcommand{{\\AdQueries}}{{{int(float(qpc))}}}\n")
