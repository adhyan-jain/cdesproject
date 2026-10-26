#!/usr/bin/env python3
"""Analysis of the independent timing sessions (reviewer experiments R15/R16) and of the R13 memory table.

  python3 scripts/review_analyze.py [results/review]

Reads   results/review/sessions/s*/replays.csv   (trace,impl,rep,replay_ns; one row per table per round)
        results/review/r13_minbuf.csv
Writes  results/review/analysis_per_session.csv, analysis_pooled.csv, analysis.json, r13_savings.csv,
        p95_latency.csv, and prints the markdown tables used in docs/REVIEW_EXPERIMENTS_BENCH.md.

Statistic: for a pair (num, den) the ratio num/den of the two replay times of the SAME round (paired).
Per session: median of the 31 ratios, 95% percentile bootstrap CI (10 000 resamples of rounds).
"Difference established" = the 95% CI excludes 1.
TOST: equivalence margin ratio in [0.90, 1.10] (+-10 %); equivalent iff the 90% CI of the median lies
inside it (the two one-sided tests at alpha = 0.05 are equivalent to that interval-inclusion rule).
Pooled over sessions, three intervals are reported:
  t-sessions   t interval on the per-session medians of log ratio (df = sessions - 1): treats SESSION as the
               unit of replication, so it contains the between-session variability. PRIMARY verdicts.
  boot2        two-level bootstrap (resample sessions, then rounds inside each) of the median of pooled ratios
  boot-rounds  bootstrap of the pooled rounds ignoring session structure (for comparison only; too narrow)
"""
import csv, glob, json, math, os, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "review")
B = 10000
LO, HI = math.log(0.90), math.log(1.10)
TRACES = ["zlib", "cjson", "littlefs", "freertos", "lua", "mbedtls", "tinycc", "sqlite"]
PAIRS = [("strata", "arena_chain", "STRATA / arena C0"), ("strata", "arena_nohash", "STRATA / arena C1"),
         ("arena_nohash", "arena_chain", "arena C1 / arena C0"), ("strata", "metis_x", "STRATA / METIS-X"),
         ("strata_keyed", "strata", "STRATA keyed / STRATA")]
# two-sided 97.5% and 95% quantiles of Student t by df
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}
T95 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833}
rng = np.random.default_rng(20261027)

def load():
    S = {}
    for d in sorted(glob.glob(os.path.join(D, "sessions", "s*")), key=lambda p: int(p.rsplit("s", 1)[1])):
        sid = int(d.rsplit("s", 1)[1])
        R = {}
        for r in csv.DictReader(open(os.path.join(d, "replays.csv"))):
            R.setdefault((r["trace"], r["impl"]), {})[int(r["rep"])] = float(r["replay_ns"])
        S[sid] = R
    return S

def ratios(S, sid, tr, a, b):
    ra, rb = S[sid][(tr, a)], S[sid][(tr, b)]
    ks = sorted(set(ra) & set(rb))
    return np.array([ra[k] / rb[k] for k in ks])

def boot_median(x, level):
    idx = rng.integers(0, len(x), size=(B, len(x)))
    m = np.median(np.log(x)[idx], axis=1)
    a = (1 - level) / 2
    return np.quantile(m, [a, 1 - a])

def verdict(lo95, hi95, lo90, hi90):
    diff = "established" if (lo95 > 0 or hi95 < 0) else "not established"
    eq = "equivalent" if (lo90 > LO and hi90 < HI) else ("outside margin" if (lo90 > HI or hi90 < LO) else "inconclusive")
    return diff, eq

def pct(l):  # log ratio -> percent change of num relative to den
    return (math.exp(l) - 1) * 100

def main():
    S = load()
    sids = sorted(S)
    per, pooled, js = [], [], {"sessions": len(sids), "bootstrap_resamples": B, "margin_ratio": [0.90, 1.10], "pairs": {}}
    for (a, b, label) in PAIRS:
        for tr in TRACES:
            sess_med, sess_se, allr = [], [], []
            for sid in sids:
                x = ratios(S, sid, tr, a, b)
                c95 = boot_median(x, 0.95); c90 = boot_median(x, 0.90)
                m = float(np.median(np.log(x)))
                se = float(np.std(np.median(np.log(x)[rng.integers(0, len(x), size=(2000, len(x)))], axis=1), ddof=1))
                d, e = verdict(c95[0], c95[1], c90[0], c90[1])
                per.append(dict(pair=label, trace=tr, session=sid, rounds=len(x), median_ratio=math.exp(m),
                                ci95_lo=math.exp(c95[0]), ci95_hi=math.exp(c95[1]), ci90_lo=math.exp(c90[0]), ci90_hi=math.exp(c90[1]),
                                difference=d, tost=e, num_median_ns=float(np.median([S[sid][(tr, a)][k] for k in S[sid][(tr, a)]])),
                                den_median_ns=float(np.median([S[sid][(tr, b)][k] for k in S[sid][(tr, b)]]))))
                sess_med.append(m); sess_se.append(se); allr.append(x)
            k = len(sids); sm = np.array(sess_med)
            mean, sd = float(sm.mean()), float(sm.std(ddof=1))
            half95, half90 = T975[k - 1] * sd / math.sqrt(k), T95[k - 1] * sd / math.sqrt(k)
            # DerSimonian-Laird heterogeneity of the session medians
            w = 1 / np.maximum(np.array(sess_se) ** 2, 1e-12); mu = float((w * sm).sum() / w.sum())
            Q = float((w * (sm - mu) ** 2).sum()); I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 else 0.0
            # two-level bootstrap of the median pooled log ratio
            meds = np.empty(B)
            for i in range(B):
                pick = rng.integers(0, k, size=k)
                pool = np.concatenate([np.log(allr[j])[rng.integers(0, len(allr[j]), size=len(allr[j]))] for j in pick])
                meds[i] = np.median(pool)
            b95 = np.quantile(meds, [0.025, 0.975]); b90 = np.quantile(meds, [0.05, 0.95])
            flat = np.log(np.concatenate(allr)); pm = float(np.median(flat))
            idx = rng.integers(0, len(flat), size=(B, len(flat))); mr = np.median(flat[idx], axis=1)
            r95 = np.quantile(mr, [0.025, 0.975]); r90 = np.quantile(mr, [0.05, 0.95])
            dT, eT = verdict(mean - half95, mean + half95, mean - half90, mean + half90)
            d2, e2 = verdict(b95[0], b95[1], b90[0], b90[1])
            dR, eR = verdict(r95[0], r95[1], r90[0], r90[1])
            row = dict(pair=label, trace=tr, sessions=k, rounds_pooled=len(flat), pooled_median_ratio=math.exp(pm),
                       session_median_min=math.exp(sm.min()), session_median_max=math.exp(sm.max()),
                       between_session_sd_pct=(math.exp(sd) - 1) * 100, I2_pct=I2,
                       mean_of_session_medians=math.exp(mean),
                       t_ci95_lo=math.exp(mean - half95), t_ci95_hi=math.exp(mean + half95), t_ci90_lo=math.exp(mean - half90), t_ci90_hi=math.exp(mean + half90),
                       t_difference=dT, t_tost=eT,
                       boot2_ci95_lo=math.exp(b95[0]), boot2_ci95_hi=math.exp(b95[1]), boot2_ci90_lo=math.exp(b90[0]), boot2_ci90_hi=math.exp(b90[1]),
                       boot2_difference=d2, boot2_tost=e2,
                       rounds_ci95_lo=math.exp(r95[0]), rounds_ci95_hi=math.exp(r95[1]), rounds_ci90_lo=math.exp(r90[0]), rounds_ci90_hi=math.exp(r90[1]),
                       rounds_difference=dR, rounds_tost=eR)
            pooled.append(row)
    for name, rows in (("analysis_per_session.csv", per), ("analysis_pooled.csv", pooled)):
        with open(os.path.join(D, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
            for r in rows: w.writerow({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()})
    js["pooled"] = pooled
    json.dump(js, open(os.path.join(D, "analysis.json"), "w"), indent=1)

    # ---------- markdown ----------
    out = []
    for (a, b, label) in PAIRS:
        out.append("\n#### %s (ratio of replay times; < 1 means the first is faster)\n" % label)
        out.append("| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for tr in TRACES:
            sess = [p for p in per if p["pair"] == label and p["trace"] == tr]
            ps = "; ".join("%.3f [%.3f, %.3f]" % (p["median_ratio"], p["ci95_lo"], p["ci95_hi"]) for p in sess)
            r = [p for p in pooled if p["pair"] == label and p["trace"] == tr][0]
            out.append("| %s | %s | %.3f-%.3f | %.3f | [%.3f, %.3f] | %s | [%.3f, %.3f] | %s | %s / %s |" % (
                tr, ps, r["session_median_min"], r["session_median_max"], r["pooled_median_ratio"], r["t_ci95_lo"], r["t_ci95_hi"],
                r["t_difference"], r["t_ci90_lo"], r["t_ci90_hi"], r["t_tost"], r["boot2_difference"], r["boot2_tost"]))
        rs = [p for p in pooled if p["pair"] == label]
        gm = math.exp(np.mean([math.log(p["pooled_median_ratio"]) for p in rs]))
        out.append("\nGeometric mean over the 8 traces of the pooled median ratio: %.3f.  t-verdict counts: faster-established %d, slower-established %d, not established %d; TOST equivalent %d, outside margin %d, inconclusive %d." % (
            gm, sum(1 for p in rs if p["t_difference"] == "established" and p["t_ci95_hi"] < 1),
            sum(1 for p in rs if p["t_difference"] == "established" and p["t_ci95_lo"] > 1),
            sum(1 for p in rs if p["t_difference"] != "established"),
            sum(1 for p in rs if p["t_tost"] == "equivalent"), sum(1 for p in rs if p["t_tost"] == "outside margin"), sum(1 for p in rs if p["t_tost"] == "inconclusive")))
    # sessions summary: per-session per-table median ns
    out.append("\n#### Median replay time per session (ms)\n")
    impls = ["strata", "strata_keyed", "arena_chain", "arena_nohash", "metis_x"]
    out.append("| trace | session | " + " | ".join(impls) + " |"); out.append("|---|---|" + "---|" * len(impls))
    for tr in TRACES:
        for sid in sids:
            out.append("| %s | %d | " % (tr, sid) + " | ".join("%.3f" % (np.median(list(S[sid][(tr, i)].values())) / 1e6) for i in impls) + " |")
    # R13 savings
    M = {}
    for r in csv.DictReader(open(os.path.join(D, "r13_minbuf.csv"))): M[(r["trace"], r["table"])] = int(r["min_buffer_bytes"])
    rows = []
    out.append("\n#### Smallest fixed buffer (bytes, 64-byte bisection)\n")
    out.append("| trace | STRATA | STRATA raw | C0 (hash word) | C1 (no hash word) | saving vs C0 | saving vs C1 | C1 vs C0 | raw-name STRATA vs C1 |"); out.append("|---|---|---|---|---|---|---|---|---|")
    for tr in TRACES:
        s, sr, c0, c1 = (M[(tr, k)] for k in ("strata_packed", "strata_raw", "arena_C0_hash", "arena_C1_nohash"))
        rows.append(dict(trace=tr, strata=s, strata_raw=sr, c0=c0, c1=c1, saving_vs_c0_pct=(c0 - s) / c0 * 100, saving_vs_c1_pct=(c1 - s) / c1 * 100,
                         c1_vs_c0_pct=(c0 - c1) / c0 * 100, strata_raw_vs_c1_pct=(c1 - sr) / c1 * 100))
        r = rows[-1]
        out.append("| %s | %d | %d | %d | %d | %.2f%% | %.2f%% | %.2f%% | %.2f%% |" % (tr, s, sr, c0, c1, r["saving_vs_c0_pct"], r["saving_vs_c1_pct"], r["c1_vs_c0_pct"], r["strata_raw_vs_c1_pct"]))
    with open(os.path.join(D, "r13_savings.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
        for r in rows: w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    for k in ("saving_vs_c0_pct", "saving_vs_c1_pct", "c1_vs_c0_pct"):
        v = [r[k] for r in rows]; out.append("\n%s: min %.2f, median %.2f, max %.2f; pooled (sum of bytes) %.2f" % (k, min(v), float(np.median(v)), max(v),
            (1 - sum(r["strata"] for r in rows) / sum(r["c0" if "c0" in k else "c1"] for r in rows)) * 100 if k.startswith("saving") else (1 - sum(r["c1"] for r in rows) / sum(r["c0"] for r in rows)) * 100))
    # p95 latency (median over sessions of the per-session value; each is the median of 3 replays of the all-units sample)
    cols = ["lookup_p95_ns", "declare_p95_ns", "enter_p95_ns", "exit_p95_ns", "timer_overhead_ns"]
    acc = {}
    for sid in sids:
        for r in csv.DictReader(open(os.path.join(D, "sessions", "s%d" % sid, "summary.csv"))):
            acc.setdefault((r["trace"], r["impl"]), []).append([float(r[c]) for c in cols])
    with open(os.path.join(D, "p95_latency.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["trace", "impl"] + ["median_over_sessions_" + c for c in cols] + ["min_over_sessions_lookup_p95_ns", "max_over_sessions_lookup_p95_ns"])
        for (tr, im), v in sorted(acc.items()):
            v = np.array(v); w.writerow([tr, im] + ["%.1f" % x for x in np.median(v, axis=0)] + ["%.1f" % v[:, 0].min(), "%.1f" % v[:, 0].max()])
    print("\n".join(out))

main()
