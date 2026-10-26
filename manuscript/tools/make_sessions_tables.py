#!/usr/bin/env python3
"""Tables of the repeated-session study and the stronger-baseline memory study, from results/review/.

    python manuscript/tools/make_sessions_tables.py

Writes manuscript/ieee_access/tables/tab_sessions.tex, tab_c1.tex and sessions_numbers.tex.
Inputs are written by scripts/review_analyze.py and benchmarks/budget_main.cpp (mode r13).
"""
import csv, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RV = os.path.join(ROOT, "results", "review")
OUT = os.path.join(ROOT, "manuscript", "ieee_access", "tables")
ORDER = ["zlib", "cjson", "littlefs", "freertos", "lua", "mbedtls", "tinycc", "sqlite"]
NAME = {"zlib": "zlib", "cjson": "cJSON", "littlefs": "littlefs", "freertos": "FreeRTOS", "lua": "Lua",
        "mbedtls": "Mbed TLS", "tinycc": "TinyCC", "sqlite": "SQLite"}
pooled = {}
for r in csv.DictReader(open(os.path.join(RV, "analysis_pooled.csv"))):
    pooled[(r["pair"], r["trace"])] = r
TOST = {"equivalent": "eq", "outside margin": "out", "inconclusive": "inc"}

def cell(pair, tr):
    r = pooled[(pair, tr)]
    v = float(r["pooled_median_ratio"])
    d = r["t_difference"]
    verdict = ("slower" if v > 1 else "faster") if d == "established" else "n.e."
    return "%.3f [%.3f, %.3f] & %s & %s" % (v, float(r["t_ci95_lo"]), float(r["t_ci95_hi"]), verdict, TOST[r["t_tost"]])

pairs = ["STRATA / arena C0", "STRATA / arena C1", "arena C1 / arena C0", "STRATA / METIS-X"]
rows = []
for tr in ORDER:
    rows.append(NAME[tr] + " & " + " & ".join(cell(p, tr) for p in pairs) + r" \\")
with open(os.path.join(OUT, "tab_sessions.tex"), "w") as f:
    f.write("\n".join(rows) + "\n")

sav = {r["trace"]: r for r in csv.DictReader(open(os.path.join(RV, "r13_savings.csv")))}
rows = []
for tr in ORDER:
    r = sav[tr]
    kib = lambda k: "%.1f" % (int(r[k]) / 1024.0)
    rows.append("%s & %s & %s & %s & %s & %.1f & %.1f \\\\" % (NAME[tr], kib("strata"), kib("c0"), kib("c1"), kib("strata_raw"),
                float(r["saving_vs_c0_pct"]), float(r["saving_vs_c1_pct"])))
with open(os.path.join(OUT, "tab_c1.tex"), "w") as f:
    f.write("\n".join(rows) + "\n")

def agg(col):
    v = [float(sav[t][col]) for t in ORDER]
    return min(v), max(v)
tot = lambda k: sum(int(sav[t][k]) for t in ORDER)
m = {}
m["ConeSaveLo"], m["ConeSaveHi"] = ["%.1f" % x for x in agg("saving_vs_c1_pct")]
m["CzeroSaveLo"], m["CzeroSaveHi"] = ["%.1f" % x for x in agg("saving_vs_c0_pct")]
m["ConeSavePooled"] = "%.1f" % (100.0 * (1 - tot("strata") / tot("c1")))
m["CzeroSavePooled"] = "%.1f" % (100.0 * (1 - tot("strata") / tot("c0")))
m["ConeMemLo"], m["ConeMemHi"] = ["%.1f" % x for x in agg("c1_vs_c0_pct")]
def ratios(pair):
    return [float(pooled[(pair, t)]["pooled_median_ratio"]) for t in ORDER]
def cnt(pair, what):
    return sum(1 for t in ORDER if pooled[(pair, t)]["t_difference"] == "established" and (float(pooled[(pair, t)]["pooled_median_ratio"]) > 1) == (what == "slower"))
sc0 = ratios("STRATA / arena C0"); sc1 = ratios("STRATA / arena C1"); c1c0 = ratios("arena C1 / arena C0"); sme = ratios("STRATA / METIS-X")
m["SessSZeroLo"], m["SessSZeroHi"] = "%.0f" % ((min(sc0) - 1) * 100), "%.0f" % ((max(sc0) - 1) * 100)
m["SessSZeroSlower"] = str(cnt("STRATA / arena C0", "slower"))
m["SessSOneLo"], m["SessSOneHi"] = "%.0f" % max(0, (min(sc1) - 1) * 100), "%.0f" % ((max(sc1) - 1) * 100)
m["SessSOneSlower"] = str(cnt("STRATA / arena C1", "slower"))
m["SessSOneEq"] = str(sum(1 for t in ORDER if pooled[("STRATA / arena C1", t)]["t_tost"] == "equivalent"))
m["SessCCSlower"] = str(cnt("arena C1 / arena C0", "slower"))
m["SessCCLo"], m["SessCCHi"] = "%.0f" % ((min(c1c0) - 1) * 100), "%.0f" % ((max(c1c0) - 1) * 100)
m["SessMetisFaster"] = str(cnt("STRATA / METIS-X", "faster"))
m["SessMetisLo"], m["SessMetisHi"] = "%.0f" % ((1 - max(sme)) * 100), "%.0f" % ((1 - min(sme)) * 100)
kv = [float(pooled[("STRATA keyed / STRATA", t)]["pooled_median_ratio"]) for t in ORDER]
m["SessKeyLo"], m["SessKeyHi"] = "%.0f" % ((min(kv) - 1) * 100), "%.0f" % ((max(kv) - 1) * 100)
with open(os.path.join(OUT, "sessions_numbers.tex"), "w") as f:
    for k, v in m.items():
        f.write("\\newcommand{\\%s}{%s}\n" % (k, v))
print(m)
