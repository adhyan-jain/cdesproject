#!/usr/bin/env python3
"""Plots for the manuscript, from the data_*.csv files written by make_numbers.py.

    python manuscript/figures/source/make_plots.py

Vector PDF, one column wide (3.5 in), 8 pt Times-like text as the IEEE figure guidelines
ask. Series are distinguished by marker and line style or hatch as well as by colour, so
the figures survive greyscale printing. Colours: a four-slot categorical palette checked
with the colour-vision-deficiency validator (all adjacent pairs pass).
"""
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTS = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "..", "..", "paper", "figures")]
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7d", "#eda100"
INK, MUTED = "#222222", "#888888"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "grid.color": "#dddddd", "grid.linewidth": 0.5, "pdf.fonttype": 42, "ps.fonttype": 42,
    "legend.frameon": False, "hatch.linewidth": 0.5,
})


def read(name):
    with open(os.path.join(HERE, name), newline="") as fh:
        return list(csv.DictReader(fh))


def save(fig, name):
    for d in OUTS:
        fig.savefig(os.path.join(d, name), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ---- Fig.: smallest fixed buffer per trace --------------------------------------------------
rows = read("data_minbuffer.csv")
fig, ax = plt.subplots(figsize=(3.5, 2.05))
x = range(len(rows))
w = 0.38
a = [int(r["strata"]) / 1024 for r in rows]
b = [int(r["arena_chain"]) / 1024 for r in rows]
ax.bar([i - w / 2 - 0.01 for i in x], a, w, color=BLUE, label="STRATA", zorder=2)
ax.bar([i + w / 2 + 0.01 for i in x], b, w, color=ORANGE, hatch="////", edgecolor="white", linewidth=0, label="Conventional table", zorder=2)
for i, (u, v) in enumerate(zip(a, b)):
    ax.text(i, max(u, v) + 4, f"$-${(1 - u / v) * 100:.0f}%", ha="center", va="bottom", fontsize=6.5, color=INK)
ax.set_xticks(list(x))
ax.set_xticklabels([r["label"] for r in rows], rotation=30, ha="right")
ax.set_ylabel("Smallest fixed buffer (KiB)")
ax.set_ylim(0, max(b) * 1.14)
ax.yaxis.grid(True, zorder=0)
ax.set_axisbelow(True)
ax.legend(loc="upper left", handlelength=1.4)
save(fig, "fig_minbuffer.pdf")

# ---- Fig.: replay time against the conventional table, before and after ----------------------
rows = read("data_time.csv")
fig, ax = plt.subplots(figsize=(3.5, 2.25))
ys = list(range(len(rows)))[::-1]
for y, r in zip(ys, rows):
    for key, col, mk, dy in (("before", MUTED, "s", 0.16), ("after", BLUE, "o", -0.16)):
        p, lo, hi = float(r[key]), float(r[key + "_lo"]), float(r[key + "_hi"])
        ax.plot([lo, hi], [y + dy, y + dy], color=col, linewidth=1.2, solid_capstyle="butt", zorder=2)
        ax.plot([p], [y + dy], marker=mk, color=col, markersize=4.2, markeredgecolor="white", markeredgewidth=0.5, zorder=3,
                label=("Before the rebuild change" if key == "before" else "Final code") if y == ys[0] else None)
ax.axvline(0, color=INK, linewidth=0.6, zorder=1)
ax.set_yticks(ys)
ax.set_yticklabels([r["label"] for r in rows])
ax.set_xlabel("Replay time of STRATA relative to the conventional table\n(%; negative: STRATA is faster)")
ax.xaxis.grid(True, zorder=0)
ax.set_axisbelow(True)
ax.set_ylim(-0.6, len(rows) - 0.4)
ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, handlelength=1.2, columnspacing=1.2)
save(fig, "fig_time.pdf")

# ---- Fig.: hash flooding ----------------------------------------------------------------------
rows = read("data_flood.csv")
n = [int(r["n"]) for r in rows]
fig, ax = plt.subplots(figsize=(3.5, 2.3))
series = [("colliding_default", "Colliding names, default", ORANGE, "o", "-"),
          ("colliding_bounded", "Colliding, probe limit 64", YELLOW, "^", "--"),
          ("colliding_keyed", "Colliding, keyed hash", AQUA, "s", "-."),
          ("ordinary_default", "Ordinary names, default", BLUE, "D", ":")]
for key, label, col, mk, ls in series:
    ax.plot(n, [float(r[key]) for r in rows], color=col, marker=mk, linestyle=ls, linewidth=1.3, markersize=4,
            markeredgecolor="white", markeredgewidth=0.5, label=label, zorder=3)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(n)
ax.set_xticklabels([f"{v // 1024}k" for v in n])
ax.set_xlabel("Distinct names declared")
ax.set_ylabel("Time to declare all names (ms)")
ax.grid(True, which="major", zorder=0)
ax.set_axisbelow(True)
ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, handlelength=2.4, labelspacing=0.25, columnspacing=1.0)
save(fig, "fig_flood.pdf")

# ---- Fig.: probability of exceeding a probe limit ---------------------------------------------
rows = [r for r in read("data_probe.csv") if r["hash"] == "halfsiphash13"]
limits = [8, 16, 32, 64, 128, 256, 512]
fig, ax = plt.subplots(figsize=(3.5, 2.45))
style = {"0.375": (AQUA, "s"), "0.500": (BLUE, "o"), "0.625": (YELLOW, "^"), "0.750": (ORANGE, "D")}
for r in rows:
    col, mk = style[r["load"]]
    m = [(L, float(r[f"m{L}"])) for L in limits if float(r[f"m{L}"]) > 0]
    b = [(L, float(r[f"b{L}"])) for L in limits if 1e-12 < float(r[f"b{L}"]) <= 1]
    ax.plot([p[0] for p in b], [p[1] for p in b], color=col, linestyle="--", linewidth=1.0, zorder=2)
    ax.plot([p[0] for p in m], [p[1] for p in m], color=col, marker=mk, linestyle="-", linewidth=1.3, markersize=4,
            markeredgecolor="white", markeredgewidth=0.5, label=f"load {float(r['load']):.3f}".rstrip("0"), zorder=3)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(limits)
ax.set_xticklabels([str(v) for v in limits])
ax.set_ylim(3e-8, 2)
ax.set_xlabel("Probe limit $L$")
ax.set_ylabel("Probability that a new name needs more than $L$ probes")
ax.grid(True, which="major", zorder=0)
ax.set_axisbelow(True)
h, lab = ax.get_legend_handles_labels()
from matplotlib.lines import Line2D
h += [Line2D([0], [0], color=INK, linewidth=1.3), Line2D([0], [0], color=INK, linewidth=1.0, linestyle="--")]
lab += ["measured", "bound"]
ax.legend(h, lab, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, handlelength=2.0, columnspacing=1.0, labelspacing=0.25)
save(fig, "fig_probe.pdf")
print("wrote fig_minbuffer.pdf fig_time.pdf fig_flood.pdf fig_probe.pdf")
