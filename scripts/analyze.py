#!/usr/bin/env python3
"""Turn the raw CSV files of one run into tables (Markdown + CSV) and figures.

    python3 scripts/analyze.py results/raw/<run>

Writes results/summary/<run>/ : tables.md, *.csv, fig_*.png and fig_*.pdf.
Every number in docs/RESULTS.md and in the paper comes from these outputs.

Percentage reduction is always ((baseline - new) / baseline) x 100; a negative value
means the new table is worse.
"""
import os
import random
import sys

import pandas as pd

run = sys.argv[1].rstrip("/\\")
out = os.path.join("results", "summary", os.path.basename(run))
os.makedirs(out, exist_ok=True)
NEW = "strata"
ORDER = ["strata", "strata_raw", "strata_noshrink", "strata_sparse", "metis_x", "metis_arena_lp", "metis_scope_maps",
         "scope_map_stack", "std_undo_log", "swiss_undo_log", "swiss_interned"]
LABEL = {"strata": "STRATA", "strata_raw": "STRATA (raw names)", "strata_noshrink": "STRATA (no shrink)",
         "strata_sparse": "STRATA (sparse index)",
         "metis_x": "METIS-X (previous)", "metis_arena_lp": "old arena table", "metis_scope_maps": "old scope maps",
         "scope_map_stack": "map per scope", "std_undo_log": "std map + undo log",
         "swiss_undo_log": "Swiss node map + undo log", "swiss_interned": "Swiss flat map, interned"}
md = []


def reduction(base, new):
    return (base - new) / base * 100.0 if base else float("nan")


def bootstrap_ci(values, n=2000, seed=7):
    """95% percentile-bootstrap interval of the median."""
    rng = random.Random(seed)
    v = list(values)
    meds = sorted(pd.Series([rng.choice(v) for _ in v]).median() for _ in range(n))
    return meds[int(0.025 * n)], meds[int(0.975 * n) - 1]


def table(df, title, note=""):
    md.append("### %s\n" % title)
    if note:
        md.append(note + "\n")
    md.append(df.to_markdown(index=False, floatfmt=".1f"))
    md.append("")


def load(name):
    p = os.path.join(run, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def section(tag, heading):
    s, raw = load(tag + "_summary.csv"), load(tag + "_replays.csv")
    if s is None:
        return None
    md.append("## %s\n" % heading)
    s["impl"] = pd.Categorical(s["impl"], [i for i in ORDER if i in set(s["impl"])], ordered=True)
    s = s.sort_values(["trace", "impl"])
    traces = list(dict.fromkeys(s["trace"]))

    # workloads
    w = s.drop_duplicates("trace")[["trace", "units", "ops", "declares", "lookups", "enters", "distinct_names",
                                    "peak_live_decls", "peak_live_distinct", "max_depth"]]
    table(w, "Workloads", "`peak_live_decls`: largest number of simultaneously live declarations in one translation unit.")
    w.to_csv(os.path.join(out, tag + "_workloads.csv"), index=False)

    # correctness
    c = s[["trace", "impl", "wrong_lookups", "wrong_declares", "refused_declares"]]
    bad = c[(c.wrong_lookups > 0) | (c.wrong_declares > 0) | (c.refused_declares > 0)]
    md.append("### Correctness\n")
    md.append("%d table/trace pairs were checked against the reference model; %d had no wrong or refused result.\n"
              % (len(c), len(c) - len(bad)))
    if len(bad):
        md.append(bad.to_markdown(index=False))
        md.append("")

    # memory
    mem = s.pivot(index="trace", columns="impl", values="peak_bytes").loc[traces]
    mem.to_csv(os.path.join(out, tag + "_peak_heap_bytes.csv"))
    t = (mem / 1024).round(1).reset_index()
    t.columns = ["trace"] + [LABEL[c] for c in mem.columns]
    table(t, "Peak heap (KiB)", "Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; "
          "a realloc that moves a block is charged for both copies).")
    per = s.assign(bpd=s.peak_bytes / s.peak_live_decls).pivot(index="trace", columns="impl", values="bpd").loc[traces]
    t = per.round(1).reset_index()
    t.columns = ["trace"] + [LABEL[c] for c in per.columns]
    table(t, "Peak heap bytes per live declaration (at the peak)")
    al = s.pivot(index="trace", columns="impl", values="allocs").loc[traces].reset_index()
    al.columns = ["trace"] + [LABEL[c] for c in al.columns[1:]]
    table(al, "Allocator calls during the whole replay")

    # replay time with bootstrap CI
    rows = []
    for (tr, im), g in raw.groupby(["trace", "impl"]):
        lo, hi = bootstrap_ci(g.replay_ns)
        ops = int(s[(s.trace == tr) & (s.impl == im)].ops.iloc[0])
        rows.append({"trace": tr, "impl": im, "median_ms": g.replay_ns.median() / 1e6, "ci_lo_ms": lo / 1e6, "ci_hi_ms": hi / 1e6,
                     "iqr_pct_of_median": (g.replay_ns.quantile(0.75) - g.replay_ns.quantile(0.25)) / g.replay_ns.median() * 100,
                     "min_ms": g.replay_ns.min() / 1e6, "max_ms": g.replay_ns.max() / 1e6, "reps": len(g),
                     "ns_per_op": g.replay_ns.median() / ops, "mops_per_s": ops / g.replay_ns.median() * 1e3})
    rt = pd.DataFrame(rows)
    rt["impl"] = pd.Categorical(rt["impl"], [i for i in ORDER if i in set(rt["impl"])], ordered=True)
    rt = rt.sort_values(["trace", "impl"])
    rt.to_csv(os.path.join(out, tag + "_replay_time.csv"), index=False)
    tp = rt.pivot(index="trace", columns="impl", values="ns_per_op").loc[traces]
    t = tp.round(1).reset_index()
    t.columns = ["trace"] + [LABEL[c] for c in tp.columns]
    table(t, "Whole-trace replay time (ns per trace operation, median)",
          "One timer around each complete replay, table construction and destruction included. "
          "Per-table 95%% bootstrap intervals of the median are in `%s_replay_time.csv`." % tag)

    # per-operation latency
    for op in ("lookup", "declare", "exit"):
        cols = ["%s_p50_ns" % op, "%s_p95_ns" % op, "%s_p99_ns" % op]
        lat = s[["trace", "impl"] + cols].copy()
        lat["impl"] = lat["impl"].map(LABEL)
        wide = lat.pivot(index="trace", columns="impl", values=cols[1]).loc[traces]
        wide = wide[[LABEL[i] for i in ORDER if LABEL[i] in wide.columns]].round(1).reset_index()
        table(wide, "%s latency, p95 (ns)" % op.capitalize(),
              "Per-call TSC timing; the calibrated cost of one timed interval (%.0f ns here) is subtracted. "
              "p50 and p99 are in the summary CSV." % s.timer_overhead_ns.median())

    # old versus new
    base = "metis_x"
    if base in set(s["impl"]):
        rows = []
        for tr in traces:
            a = s[(s.trace == tr) & (s.impl == base)].iloc[0]
            b = s[(s.trace == tr) & (s.impl == NEW)].iloc[0]
            ta = rt[(rt.trace == tr) & (rt.impl == base)].iloc[0]
            tb = rt[(rt.trace == tr) & (rt.impl == NEW)].iloc[0]
            rows.append({"trace": tr,
                         "peak heap KiB old": a.peak_bytes / 1024, "new": b.peak_bytes / 1024, "peak heap red. %": reduction(a.peak_bytes, b.peak_bytes),
                         "allocs old": a.allocs, "allocs new": b.allocs, "allocs red. %": reduction(a.allocs, b.allocs),
                         "replay ms old": ta.median_ms, "replay ms new": tb.median_ms, "replay red. %": reduction(ta.median_ms, tb.median_ms),
                         "intervals overlap": "yes" if not (tb.ci_hi_ms < ta.ci_lo_ms or ta.ci_hi_ms < tb.ci_lo_ms) else "no",
                         "lookup p95 old": a.lookup_p95_ns, "lookup p95 new": b.lookup_p95_ns, "lookup p95 red. %": reduction(a.lookup_p95_ns, b.lookup_p95_ns),
                         "declare p95 red. %": reduction(a.declare_p95_ns, b.declare_p95_ns),
                         "exit p95 red. %": reduction(a.exit_p95_ns, b.exit_p95_ns),
                         "old refused": int(a.refused_declares)})
        ovn = pd.DataFrame(rows)
        ovn.to_csv(os.path.join(out, tag + "_old_vs_new.csv"), index=False)
        table(ovn, "Previous implementation (METIS-X) versus STRATA",
              "Reduction = (old - new) / old x 100; negative means STRATA is worse. 'intervals overlap = yes' means the "
              "95% intervals of the two replay-time medians overlap, so the time difference is not established.")
        others = [i for i in ORDER if i in set(s["impl"]) and not i.startswith("strata")]
        rows = []
        for im in others:
            r = {"baseline": LABEL[im]}
            have = [tr for tr in traces if len(s[(s.trace == tr) & (s.impl == im)])]   # a baseline may be absent on some traces
            heap = [reduction(s[(s.trace == tr) & (s.impl == im)].peak_bytes.iloc[0], s[(s.trace == tr) & (s.impl == NEW)].peak_bytes.iloc[0]) for tr in have]
            tim = [reduction(rt[(rt.trace == tr) & (rt.impl == im)].median_ms.iloc[0], rt[(rt.trace == tr) & (rt.impl == NEW)].median_ms.iloc[0]) for tr in have]
            r.update({"traces": len(have),"peak heap red. % min": min(heap), "median": pd.Series(heap).median(), "max": max(heap),
                      "replay time red. % min": min(tim), "median ": pd.Series(tim).median(), "max ": max(tim)})
            rows.append(r)
        allb = pd.DataFrame(rows)
        allb.to_csv(os.path.join(out, tag + "_strata_vs_all.csv"), index=False)
        table(allb, "STRATA against every baseline (range over the traces of this section)")
    return s, rt


def figures(s, rt, tag):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        md.append("_matplotlib is not installed: figures were not generated._\n")
        return
    impls = [i for i in ORDER if i in set(s["impl"]) and i not in ("strata_raw", "strata_noshrink", "strata_sparse")]
    traces = list(dict.fromkeys(s["trace"]))
    grey = {"strata": "black"}
    shades = ["0.25", "0.4", "0.55", "0.68", "0.78", "0.86", "0.93"]
    colors = [grey.get(i, shades[k % len(shades)]) for k, i in enumerate(impls)]
    for metric, ylabel, fname, src in (("bpd", "peak heap bytes per live declaration", "memory", s.assign(bpd=s.peak_bytes / s.peak_live_decls)),
                                       ("ns_per_op", "replay time (ns per operation)", "time", rt)):
        fig, ax = plt.subplots(figsize=(7.2, 3.0))
        width = 0.8 / len(impls)
        for k, im in enumerate(impls):
            d = src[src.impl == im].set_index("trace")[metric].reindex(traces)
            ax.bar([x + k * width for x in range(len(traces))], d.values, width, label=LABEL[im], color=colors[k], edgecolor="black", linewidth=0.3)
        ax.set_xticks([x + width * (len(impls) - 1) / 2 for x in range(len(traces))])
        ax.set_xticklabels(traces, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", linewidth=0.3, alpha=0.6)
        ax.set_axisbelow(True)
        ax.legend(fontsize=6.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.22), frameon=False)
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(os.path.join(out, "fig_%s_%s.%s" % (tag, fname, ext)), dpi=200)
        plt.close(fig)


md.append("# Result tables for run `%s`\n" % os.path.basename(run))
env = os.path.join(run, "environment.txt")
if os.path.exists(env):
    md.append("```\n" + open(env).read().strip() + "\n```\n")

got = section("compiler", "A. Compiler traces (instrumented TinyCC)")
if got:
    figures(got[0], got[1], "compiler")

b = load("budget.csv")
if b is not None and got:
    md.append("## B. Fixed-buffer mode\n")
    s = got[0]
    first = b[b.budget_factor == 1.0]
    rows = []
    for tr in dict.fromkeys(first.trace):
        p = first[(first.trace == tr) & (first.names == "packed")].iloc[0]
        r = first[(first.trace == tr) & (first.names == "raw")].iloc[0]
        sp = first[(first.trace == tr) & (first.names == "packed_sparse")]
        row = {"trace": tr, "min buffer KiB (packed)": p.min_buffer_bytes / 1024, "min buffer KiB (raw)": r.min_buffer_bytes / 1024,
               "min buffer KiB (sparse index)": sp.min_buffer_bytes.iloc[0] / 1024 if len(sp) else float("nan"),
               "packing saves %": reduction(r.min_buffer_bytes, p.min_buffer_bytes),
               "bytes per live decl": p.min_buffer_bytes / s[s.trace == tr].peak_live_decls.iloc[0]}
        for im in ("metis_x", "scope_map_stack", "std_undo_log", "swiss_interned"):
            if im in set(s["impl"]):
                row["vs %s peak heap, red. %%" % LABEL[im]] = reduction(s[(s.trace == tr) & (s.impl == im)].peak_bytes.iloc[0], p.min_buffer_bytes)
        rows.append(row)
    bt = pd.DataFrame(rows)
    bt.to_csv(os.path.join(out, "budget_min_buffer.csv"), index=False)
    table(bt, "Smallest fixed buffer that replays the whole trace without a refused operation",
          "Found by bisection to 64 bytes. The baselines have no fixed-memory mode; the comparison is with their peak heap.")
    bp = b[b.names == "packed"].copy()
    bp["replay_ms"] = pd.to_numeric(bp.replay_ns_median, errors="coerce") / 1e6
    sp = bp.pivot(index="trace", columns="budget_factor", values="replay_ms").reset_index()
    sp.columns = ["trace"] + ["%.2fx" % c for c in sp.columns[1:]]
    table(sp, "Replay time (ms) with a buffer of 1x, 1.25x, 2x and 4x the minimum", "Median of 9 replays. Blank: that size was refused (sizing is not perfectly monotonic).")

syn = section("synthetic", "C. Synthetic stress traces")
if syn:
    figures(syn[0], syn[1], "synthetic")

wc = load("worstcase.csv")
if wc is not None:
    md.append("## D. Worst-case clustering\n")
    table(wc, "STRATA lookup cost when every key is forced into one probe cluster",
          "Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.")

leg = section("legacy", "E. Regex-extracted traces of the earlier work (supplemental)")
if leg:
    figures(leg[0], leg[1], "legacy")

with open(os.path.join(out, "tables.md"), "w", newline="\n") as f:
    f.write("\n".join(md) + "\n")
print("wrote", out)
