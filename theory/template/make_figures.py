"""Figures for the template manuscript.

Reads the paper's generated tables (theory/paper/tables) and data (theory/paper/data), writes the small CSV files the plots
use into build/data, compiles figures/diagrams.tex and figures/plots.tex with pdflatex (one page per picture) and converts
the pages to PNG: build/figs/fig_d1..d7.png (diagrams) and fig_p1..p8.png (plots).  Nothing is typed by hand.

Run:  python3 theory/template/make_figures.py
"""
import csv, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.join(HERE, "..", "paper")
BUILD = os.path.join(HERE, "build")
DATA = os.path.join(BUILD, "data")
FIGS = os.path.join(BUILD, "figs")
for d in (BUILD, DATA, FIGS): os.makedirs(d, exist_ok=True)


def cells(line):
    """Cells of one tabular row with the LaTeX markup removed."""
    out = []
    for c in line.replace("\\\\", "").split("&"):
        c = c.replace("\\,", "").replace("$", "").replace("{", "").replace("}", "").replace("\\%", "").replace("%", "").strip()
        out.append(c)
    return out


def rows(table):
    """Data rows of a generated tabular: the lines between \\midrule and \\bottomrule."""
    path = os.path.join(PAPER, "tables", table)
    out, on = [], False
    for l in open(path, encoding="utf8"):
        if "\\midrule" in l: on = True; continue
        if "\\bottomrule" in l: break
        if on and "&" in l and "\\\\" in l: out.append(cells(l))
    return out


def write(name, header, data):
    with open(os.path.join(DATA, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(data)


# ---- data files -------------------------------------------------------------------------------------------------------
for f in ("fig_law.csv", "fig_sim.csv", "fig_design.csv"):
    shutil.copy(os.path.join(PAPER, "data", f), os.path.join(DATA, f))

fill = [r for r in rows("tab_fill.tex") if r[0] == "4096"]
write("fill.csv", ["eps", "exact", "sum", "union"], [(k, r[2], r[3], r[4]) for k, r in zip("abc", fill)])

band = rows("tab_band.tex")                       # m, eps, L(s=1), L(s=2), L(s=4), L(s=8)
key = {("1024", "10-2"): "m1024e2", ("1024", "10-6"): "m1024e6", ("4096", "10-2"): "m4096e2", ("4096", "10-6"): "m4096e6"}
cols = {key[(r[0], r[1].replace("^", ""))]: r[2:] for r in band}
write("band.csv", ["s", "m1024e2", "m1024e6", "m4096e2", "m4096e6"],
      [(s, cols["m1024e2"][i], cols["m1024e6"][i], cols["m4096e2"][i], cols["m4096e6"][i]) for i, s in enumerate((1, 2, 4, 8))])

orph = rows("tab_orphan.tex")                     # alpha, j=0..4, mean
write("orphan.csv", ["j", "a25", "a50", "a75", "a90"], [(j, *[orph[a][1 + j] for a in range(4)]) for j in range(5)])

lad = rows("tab_ladder.tex")                      # trace, C0, C1, C2, Sraw, S, hash, pack, total
write("ladder.csv", ["trace", "hash", "pack", "total"], [(r[0], r[6], r[7], r[8]) for r in lad])

lc = rows("tab_lawcheck.tex")                     # m, n, L, observed, exact, z, clean, mismatches
write("lawcheck.csv", ["setting", "z"], [("s%d" % (i + 1), r[5].replace("+", "")) for i, r in enumerate(lc)])

ad = rows("tab_adaptive.tex")                     # colliders, persistent mean, max, fresh, random
write("adaptive.csv", ["colliders", "persistent", "fresh", "random"], [(r[0], r[1], r[3], r[4]) for r in ad])


# ---- compile ----------------------------------------------------------------------------------------------------------
def build(tex, prefix):
    shutil.copy(os.path.join(HERE, "figures", tex), os.path.join(BUILD, tex))
    p = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex], cwd=BUILD, capture_output=True, text=True)
    pdf = os.path.join(BUILD, tex.replace(".tex", ".pdf"))
    if not os.path.exists(pdf) or "\n!" in p.stdout:
        print(p.stdout[-2500:]); sys.exit("pdflatex failed on " + tex)
    base = os.path.join(FIGS, prefix)
    subprocess.run(["pdftoppm", "-r", "230", "-png", pdf, base], check=True)
    # pdftoppm names pages prefix-1.png, prefix-2.png, ...; make them fig_d1.png style
    for name in sorted(os.listdir(FIGS)):
        m = re.fullmatch(re.escape(prefix) + r"-0*(\d+)\.png", name)
        if m: os.replace(os.path.join(FIGS, name), os.path.join(FIGS, "%s%s.png" % (prefix, m.group(1))))


build("diagrams.tex", "fig_d")
build("plots.tex", "fig_p")
print("figures:", sorted(os.listdir(FIGS)))
