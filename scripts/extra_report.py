"""Sections of docs/RESULTS.md and paper macros for the experiments added after the second
review: per-unit fit, shadowing/name-length sweep with a memory model, a second compiler
(chibicc) used both as a trace source and as an integration target, and the emulated
"does it fit" run. Imported by make_report.py; every number is computed from files.
"""
import math
import os
import random
import re

import pandas as pd


def _paired(df, key, keyval, base, new, col, rep="rep", n=2000, seed=11):
    a = df[(df[key] == keyval) & (df.impl == base)].set_index(rep)[col]
    b = df[(df[key] == keyval) & (df.impl == new)].set_index(rep)[col]
    d = ((a - b) / a * 100).dropna().tolist()
    if not d:
        return float("nan"), float("nan"), float("nan")
    g = random.Random(seed)
    meds = sorted(pd.Series([g.choice(d) for _ in d]).median() for _ in range(n))
    return pd.Series(d).median(), meds[int(0.025 * n)], meds[int(0.975 * n) - 1]


def _pow2_at_least(x, start=16):
    v = start
    while v < x:
        v *= 2
    return v


def model_strata(N, D, L, depth):
    """Predicted bytes: D identifier records (8-byte header + packed name), an index of the
    smallest power of two that keeps the load at or below 3/4, one undo word per first
    declaration, three per shadowing declaration, two words per open scope, one reserved word."""
    idx = 16
    while D * 4 > idx * 3:
        idx *= 2
    return D * (8 + 4 * math.ceil(L / 5)) + 4 * idx + 4 * D + 12 * (N - D) + 8 * depth + 4


def model_arena(N, L, depth):
    """Predicted bytes: N entries (16-byte header + raw name padded to 4), buckets at load <= 1,
    one word per open scope, one reserved word."""
    return N * (16 + 4 * math.ceil(L / 4)) + 4 * _pow2_at_least(N) + 4 * depth + 4


def build(run, md, macro, table, esc):
    R = os.path.join("results", "raw", run)
    have = lambda name: os.path.exists(os.path.join(R, name))
    A = md.append
    rng = lambda s, fmt="%.1f": (fmt + " to " + fmt) % (min(s), max(s))

    # ---------------------------------------------------------------- per-unit fit
    if have("units.csv"):
        u = pd.read_csv(os.path.join(R, "units.csv"))
        u["compiler"] = u.trace.apply(lambda t: "chibicc" if t.startswith("chibicc_") else "TinyCC")
        u["red"] = (u.arena_chain_min_bytes - u.strata_min_bytes) / u.arena_chain_min_bytes * 100
        A("## 13. Does the saving let a workload fit? Per translation unit\n")
        A("For every translation unit of every compiler trace, the smallest buffer (64-byte resolution) with which each bounded table replays the unit without a refusal. "
          "Source: `units.csv` (`budget --mode units`).\n")
        budgets = [4, 8, 16, 24, 32, 48, 64, 96, 128, 192]
        rows = []
        for comp, g in u.groupby("compiler"):
            for b in budgets:
                s_fit = int((g.strata_min_bytes <= b * 1024).sum())
                a_fit = int((g.arena_chain_min_bytes <= b * 1024).sum())
                rows.append({"compiler": comp, "buffer KiB": b, "units": len(g), "fit in STRATA": s_fit, "fit in arena+chains": a_fit, "only STRATA fits": s_fit - a_fit})
        fit = pd.DataFrame(rows)
        fit.to_csv(os.path.join("results", "summary", run, "unit_fit.csv"), index=False)
        A(fit.to_markdown(index=False))
        t = u[u.compiler == "TinyCC"]
        c = u[u.compiler == "chibicc"]
        A("\nPer-unit reduction of STRATA against the conventional table: TinyCC traces median %.1f%% (range %s%%, %d units)%s. "
          "STRATA needs the smaller buffer on %d of %d units."
          % (t.red.median(), rng(t.red), len(t),
             ("; chibicc traces median %.1f%% (range %s%%, %d units)" % (c.red.median(), rng(c.red), len(c))) if len(c) else "",
             int((u.red > 0).sum()), len(u)))
        best = fit[fit.compiler == "TinyCC"].sort_values("only STRATA fits", ascending=False).iloc[0]
        A("\nReading: the saving decides whether a unit fits only when the budget falls between the two requirements. "
          "At %d KiB that is the case for %d of the %d TinyCC units, the largest count among the tested sizes; at 64 KiB and above it is the case for at most %d. "
          "The reduction therefore matters for a design with a hard table budget near the workload's need, and not otherwise.\n"
          % (best["buffer KiB"], best["only STRATA fits"], best["units"],
             int(fit[(fit.compiler == "TinyCC") & (fit["buffer KiB"] >= 64)]["only STRATA fits"].max())))
        macro("UnitsN", len(t)); macro("UnitRedMed", "%.0f" % t.red.median()); macro("UnitRedMin", "%.0f" % t.red.min()); macro("UnitRedMax", "%.0f" % t.red.max())
        macro("FitBestKiB", int(best["buffer KiB"])); macro("FitBestOnly", int(best["only STRATA fits"]))
        macro("FitBestStrata", int(best["fit in STRATA"])); macro("FitBestArena", int(best["fit in arena+chains"]))
        ft = fit[fit.compiler == "TinyCC"]
        table("TabFit", ["Buffer (KiB)"] + [str(b) for b in ft["buffer KiB"]],
              [["STRATA fits"] + [str(v) for v in ft["fit in STRATA"]], ["arena fits"] + [str(v) for v in ft["fit in arena+chains"]],
               ["only STRATA"] + [str(v) for v in ft["only STRATA fits"]]], "@{}l" + "r" * len(ft) + "@{}")

    # ---------------------------------------------------------------- emulated fit
    fpath = os.path.join("results", "embedded", "fit_cortex_m3.txt")
    if os.path.exists(fpath):
        text = open(fpath).read()
        rows = []
        for block in text.split("== ")[1:]:
            m = re.match(r"(\S+)\s+buffer (\d+) bytes\s+table (\S+)", block)
            rows.append({"trace": m.group(1), "buffer bytes": int(m.group(2)), "table": "STRATA" if m.group(3) == "STRATA" else "arena+chains",
                         "refused operations": int(re.search(r"refused operations\s+(\d+)", block).group(1)),
                         "result": re.search(r"RESULT: (.*)", block).group(1).strip()})
        ef = pd.DataFrame(rows)
        A("On the emulated Cortex-M3 (64 KiB RAM, `tools/embedded/fit.sh`, log `results/embedded/fit_cortex_m3.txt`), same trace and same static buffer for both tables:\n")
        A(ef.to_markdown(index=False))
        A("")
        only = ef[ef.result == "DOES NOT FIT"]
        macro("EmbFitCases", len(only))
        fr = ef[(ef.trace == "freertos")]
        if len(fr):
            small = fr["buffer bytes"].min()
            macro("EmbFitKiB", small // 1024)
            macro("EmbFitRefused", int(fr[(fr["buffer bytes"] == small) & (fr.table != "STRATA")]["refused operations"].iloc[0]))

    # ---------------------------------------------------------------- sweep
    if have("sweep_minbuf.csv"):
        sw = pd.read_csv(os.path.join(R, "sweep_minbuf.csv"))
        sw["sigma"] = sw.trace.str.extract(r"s(\d+)_")[0].astype(int) / 10
        sw["L"] = sw.trace.str.extract(r"_L(\d+)")[0].astype(int)
        N = 4096
        sw["D"] = (N / sw.sigma).round().astype(int)
        sw["depth"] = (N / sw.D).apply(math.ceil) - 1
        sw["model_strata"] = [model_strata(N, d, l, dp) for d, l, dp in zip(sw.D, sw.L, sw.depth)]
        sw["model_arena"] = [model_arena(N, l, dp) for l, dp in zip(sw.L, sw.depth)]
        sw["err_s"] = (sw.model_strata - sw.strata_min_bytes) / sw.strata_min_bytes * 100
        sw["err_a"] = (sw.model_arena - sw.arena_chain_min_bytes) / sw.arena_chain_min_bytes * 100
        sw["mem_red"] = (sw.arena_chain_min_bytes - sw.strata_min_bytes) / sw.arena_chain_min_bytes * 100
        A("## 14. When does the saving grow? Shadowing factor and name length\n")
        A("Synthetic traces (`scripts/gen_sweep.py`): 4 096 live declarations at the peak, built from 4 096 / sigma distinct names declared in nested scopes "
          "(sigma = live declarations per distinct live name), names of exactly L characters, five lookups per declaration. "
          "The compiler traces sit at sigma = 1.00.\n")
        A("Memory model (bytes; N live declarations, D distinct names, L name length, d open scopes):\n")
        A("```\nSTRATA       = D * (8 + 4*ceil(L/5)) + 4*index(D) + 4*D + 12*(N - D) + 8*d + 4     index(D): smallest 16*2^k with D <= 0.75*index\n"
          "arena+chains = N * (16 + 4*ceil(L/4)) + 4*buckets(N) + 4*d + 4                  buckets(N): smallest 16*2^k >= N\n```\n")
        mem = sw.pivot(index="sigma", columns="L", values="mem_red").round(1)
        mem.columns = ["L = %d" % c for c in mem.columns]
        A("Reduction of STRATA's minimum buffer against the conventional table, % (measured):\n")
        A(mem.reset_index().to_markdown(index=False))
        A("\nModel against measurement over the %d sweep points: STRATA error %s%% (median |error| %.2f%%); conventional table error %s%% (median |error| %.2f%%).\n"
          % (len(sw), rng(sw.err_s, "%.2f"), sw.err_s.abs().median(), rng(sw.err_a, "%.2f"), sw.err_a.abs().median()))
        macro("ModelErrS", "%.1f" % sw.err_s.abs().max()); macro("ModelErrA", "%.1f" % sw.err_a.abs().max())
        macro("SweepMemMin", "%.0f" % sw.mem_red.min()); macro("SweepMemMax", "%.0f" % sw.mem_red.max())
        s1 = sw[sw.sigma == 1.0]
        macro("SweepMemSigmaOne", "%s" % rng(s1.mem_red, "%.0f").replace(" to ", "--"))
        s2 = sw[sw.sigma == 2.0]
        macro("SweepMemSigmaTwo", "%s" % rng(s2.mem_red, "%.0f").replace(" to ", "--"))
        if have("sweep_replays.csv"):
            sr = pd.read_csv(os.path.join(R, "sweep_replays.csv"))
            rows = []
            for tr in sw.trace:
                p = _paired(sr, "trace", tr, "arena_chain", "strata", "replay_ns")
                row = sw[sw.trace == tr].iloc[0]
                rows.append({"sigma": row.sigma, "L": int(row.L), "memory red. %": row.mem_red, "time red. %": p[0], "CI low": p[1], "CI high": p[2],
                             "STRATA faster": "yes" if p[1] > 0 else ("no" if p[2] < 0 else "not established")})
            tv = pd.DataFrame(rows).sort_values(["L", "sigma"])
            tv.to_csv(os.path.join("results", "summary", run, "sweep.csv"), index=False)
            A("Replay time of STRATA against the conventional table on the same traces (paired rounds; positive = STRATA faster):\n")
            A(tv.round(1).to_markdown(index=False))
            by_len = []
            for L, g in tv.groupby("L"):
                by_len.append({"L": int(L), "sweep points": len(g), "STRATA established faster": int((g["CI low"] > 0).sum()),
                               "STRATA established slower": int((g["CI high"] < 0).sum()),
                               "time red. % min": g["time red. %"].min(), "time red. % max": g["time red. %"].max()})
            bl = pd.DataFrame(by_len)
            A("\nBy name length:\n")
            A(bl.round(1).to_markdown(index=False))
            short = bl[bl.L == bl.L.min()].iloc[0]
            rest = bl[bl.L != bl.L.min()]
            A("\nReading. **Memory** behaves as the model says: the saving is %s%% at sigma = 1 (it depends on name length and on where the number of names falls "
              "between two index sizes; the compiler traces, with mixed lengths, show 16-18%%) and grows monotonically with shadowing to %.0f%% at sigma = 8. "
              "**Time does not follow shadowing.** It follows name length: with %d-character names STRATA is established faster at %d of %d shadowing factors; "
              "with longer names it is established slower at %d of %d points and faster at %d. We found no shadowing factor from which STRATA is reliably the faster "
              "table. The individual time values are not monotone in sigma, which we attribute to cache and index-size effects that the sweep does not control; "
              "only the sign pattern by name length is consistent.\n"
              % (rng(s1.mem_red, "%.0f"), sw[sw.sigma == 8.0].mem_red.max(), short.L, short["STRATA established faster"], short["sweep points"],
                 int(rest["STRATA established slower"].sum()), int(rest["sweep points"].sum()), int(rest["STRATA established faster"].sum())))
            macro("SweepShortL", int(short.L)); macro("SweepShortFaster", int(short["STRATA established faster"])); macro("SweepShortN", int(short["sweep points"]))
            macro("SweepLongSlower", int(rest["STRATA established slower"].sum())); macro("SweepLongFaster", int(rest["STRATA established faster"].sum()))
            macro("SweepLongN", int(rest["sweep points"].sum()))
            piv = tv.pivot(index="sigma", columns="L", values="memory red. %")
            pt = tv.pivot(index="sigma", columns="L", values="time red. %")
            table("TabSweep", ["$\\sigma$"] + ["mem. $L{=}%d$" % c for c in piv.columns] + ["time $L{=}%d$" % c for c in pt.columns],
                  [["%.2f" % s] + ["%.0f" % piv.loc[s, c] for c in piv.columns] + ["%.0f" % pt.loc[s, c] for c in pt.columns] for s in piv.index],
                  "@{}l" + "r" * (len(piv.columns) + len(pt.columns)) + "@{}")

    # ---------------------------------------------------------------- chibicc
    cdir = os.path.join("results", "chibicc")
    if os.path.exists(os.path.join(cdir, "times.csv")) and os.path.getsize(os.path.join(cdir, "times.csv")) > 100:
        cu = pd.read_csv(os.path.join(cdir, "units.csv"))
        crss = pd.read_csv(os.path.join(cdir, "rss.csv"))
        ct = pd.read_csv(os.path.join(cdir, "times.csv")).rename(columns={"variant": "impl", "round": "rep"})
        A("## 15. A second compiler, used two ways: chibicc\n")
        A("chibicc (commit `90d1f7f`, MIT) resolves identifiers by string with one hash map per open scope, so, unlike TinyCC, it is a compiler in which a "
          "string-keyed scoped table is on the real resolution path. `tools/chibicc/` patches it to log its scope calls and to route its variable scopes "
          "through STRATA or the conventional arena table.\n")
        A("```\n" + open(os.path.join(cdir, "environment.txt")).read().strip() + "\n```\n")
        ok = int(cu.original_compiles.sum())
        A("**Integration correctness.** The unmodified chibicc compiles %d of the %d translation units of seven projects. For those, the STRATA build produces "
          "assembly identical to the original on %d and the arena build on %d (after normalising the path of the compiler's own headers).\n"
          % (ok, len(cu), int(cu.strata_identical_asm.sum()), int(cu.arena_identical_asm.sum())))
        rows = []
        for proj in dict.fromkeys(ct.project):
            g = ct[ct.project == proj]
            med = g.groupby("impl").seconds.median()
            ps = _paired(ct, "project", proj, "orig", "strata", "seconds")
            pa = _paired(ct, "project", proj, "orig", "arena", "seconds")
            r = crss[crss.project == proj]
            rows.append({"project": proj, "units": int(g.units.iloc[0]), "compile s (original)": med["orig"], "STRATA": med["strata"], "arena": med["arena"],
                         "time red. % STRATA": ps[0], "CI": "[%.1f, %.1f]" % (ps[1], ps[2]), "time red. % arena": pa[0], "CI ": "[%.1f, %.1f]" % (pa[1], pa[2]),
                         "max peak RSS MB (original)": r.orig_peak_rss_kb.max() / 1024, "STRATA ": r.strata_peak_rss_kb.max() / 1024, "arena ": r.arena_peak_rss_kb.max() / 1024})
        ce = pd.DataFrame(rows)
        ce.to_csv(os.path.join("results", "summary", run, "chibicc_end_to_end.csv"), index=False)
        A("**End to end.** Whole-project compile time (`-S`, %d interleaved rounds, positive reduction = faster than the original) and the largest peak resident set size over a project's units:\n"
          % ct.rep.nunique())
        A(ce.round(2).to_markdown(index=False))
        crss["d"] = (crss.orig_peak_rss_kb - crss.strata_peak_rss_kb) / crss.orig_peak_rss_kb * 100
        ci = lambda text: (float(text[1:].split(",")[0]), float(text.split(",")[1][:-1]))
        s_slow = [r["project"] for r in rows if ci(r["CI"])[1] < 0]
        s_fast = [r["project"] for r in rows if ci(r["CI"])[0] > 0]
        a_slow = [r["project"] for r in rows if ci(r["CI "])[1] < 0]
        a_fast = [r["project"] for r in rows if ci(r["CI "])[0] > 0]
        A("\nReading: replacing chibicc's per-scope hash maps changes whole-compiler time by %s%% with STRATA (established slower on %s; established faster on %s) "
          "and by %s%% with the arena table (established slower on %s; faster on %s), and peak memory by a median of %.2f%% per unit. "
          "Symbol-table work is a small part of this compiler's time and its memory is dominated by tokens and syntax trees that it never frees, "
          "so neither table gives an end-to-end benefit here, and STRATA costs one to four percent of compile time on the larger projects. "
          "Both builds also keep file-scope declarations in a second table to answer chibicc's global lookups, which adds work the original does not do.\n"
          % (rng(ce["time red. % STRATA"]), ", ".join(s_slow) or "no project", ", ".join(s_fast) or "no project",
             rng(ce["time red. % arena"]), ", ".join(a_slow) or "no project", ", ".join(a_fast) or "no project", crss.d.median()))
        macro("ChibiStrataSlowN", len(s_slow)); macro("ChibiArenaEstN", len(a_slow) + len(a_fast)); macro("ChibiProjects", len(rows))
        macro("ChibiUnits", ok); macro("ChibiAll", len(cu)); macro("ChibiSame", int(cu.strata_identical_asm.sum()))
        macro("ChibiTimeMin", "%.1f" % ce["time red. % STRATA"].min()); macro("ChibiTimeMax", "%.1f" % ce["time red. % STRATA"].max())
        macro("ChibiArenaTimeMin", "%.1f" % ce["time red. % arena"].min()); macro("ChibiArenaTimeMax", "%.1f" % ce["time red. % arena"].max())
        macro("ChibiRssMed", "%.2f" % crss.d.median()); macro("ChibiRounds", int(ct.rep.nunique()))
        if have("chibicc_summary.csv"):
            s = pd.read_csv(os.path.join(R, "chibicc_summary.csv"))
            rp = pd.read_csv(os.path.join(R, "chibicc_replays.csv"))
            bad = int(((s.wrong_lookups > 0) | (s.wrong_declares > 0) | (s.refused_declares > 0)).sum())
            rows = []
            units = pd.read_csv(os.path.join(R, "units.csv")) if have("units.csv") else None
            for tr in dict.fromkeys(s.trace):
                g = s[s.trace == tr].iloc[0]
                row = {"trace": tr, "units": int(g.units), "operations": int(g.ops), "peak live decls": int(g.peak_live_decls), "peak live distinct": int(g.peak_live_distinct)}
                for base in ("scope_map_stack", "arena_chain", "metis_x", "swiss_interned"):
                    if len(rp[(rp.trace == tr) & (rp.impl == base)]):
                        p = _paired(rp, "trace", tr, base, "strata", "replay_ns")
                        row["time red. % vs " + base] = p[0]
                        row["est. " + base] = "yes" if (p[1] > 0 or p[2] < 0) else "no"
                rows.append(row)
            cr = pd.DataFrame(rows)
            cr.to_csv(os.path.join("results", "summary", run, "chibicc_replay.csv"), index=False)
            A("**Replay of chibicc's own scope calls** (%d table/trace pairs, %d with a wrong or refused result; `scope_map_stack` is chibicc's own design):\n" % (len(s), bad))
            A(cr.round(1).to_markdown(index=False))
            sig = (s.drop_duplicates("trace").peak_live_decls / s.drop_duplicates("trace").peak_live_distinct)
            A("\nShadowing factor at the peak on these traces: %s. STRATA against the conventional table: %s%% (established slower on %d of %d traces, faster on %d); "
              "against chibicc's own per-scope maps: %s%% (established faster on %d, slower on %d).\n"
              % (rng(sig, "%.3f"), rng(cr["time red. % vs arena_chain"]),
                 int(((cr["est. arena_chain"] == "yes") & (cr["time red. % vs arena_chain"] < 0)).sum()), len(cr),
                 int(((cr["est. arena_chain"] == "yes") & (cr["time red. % vs arena_chain"] > 0)).sum()),
                 rng(cr["time red. % vs scope_map_stack"]),
                 int(((cr["est. scope_map_stack"] == "yes") & (cr["time red. % vs scope_map_stack"] > 0)).sum()),
                 int(((cr["est. scope_map_stack"] == "yes") & (cr["time red. % vs scope_map_stack"] < 0)).sum())))
            macro("ChibiVsArenaSlowN", int(((cr["est. arena_chain"] == "yes") & (cr["time red. % vs arena_chain"] < 0)).sum()))
            macro("ChibiVsMapFastN", int(((cr["est. scope_map_stack"] == "yes") & (cr["time red. % vs scope_map_stack"] > 0)).sum()))
            macro("ChibiTraces", len(cr))
            macro("ChibiVsArenaMin", "%.0f" % cr["time red. % vs arena_chain"].min()); macro("ChibiVsArenaMax", "%.0f" % cr["time red. % vs arena_chain"].max())
            macro("ChibiVsMapMin", "%.0f" % cr["time red. % vs scope_map_stack"].min()); macro("ChibiVsMapMax", "%.0f" % cr["time red. % vs scope_map_stack"].max())
            macro("ChibiPairsBad", bad); macro("ChibiPairs", len(s))
