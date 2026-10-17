"""Data files (CSV) for the pgfplots figures and the numeric macros used in the paper."""
import csv, os, math, json
from math import exp, log
from design_rule import tail_array_finite, tail_array_poisson, chernoff_L
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "../paper/data"); os.makedirs(D, exist_ok=True)
T = os.path.join(HERE, "../paper/tables"); os.makedirs(T, exist_ok=True)

# Figure 1: refusal probability against the probe limit, m = 65536, load 3/4
m = 65536; n = 3*m//4; alpha = 0.75; rho = alpha*exp(1-alpha)
tf = tail_array_finite(m, n)
with open(os.path.join(D, "fig_law.csv"), "w") as f:
    f.write("L,exact,chernoff\n")
    for L in range(8, 601, 4):
        ch = rho**L/(1-rho)
        f.write(f"{L},{tf[L]:.6e},{min(ch,1.0):.6e}\n")
sim = [r for r in csv.DictReader(open(os.path.join(HERE, "../../results/hardening/probes.csv")))
       if r["hash"] == "murmur3" and r["index_slots"] == "65536" and float(r["load"]) == 0.75]
with open(os.path.join(D, "fig_sim.csv"), "w") as f:
    f.write("L,simulated\n")
    for L in (8, 16, 32, 64, 128, 256):
        v = float(sim[0]["measured_gt_%d" % L])
        if v > 0: f.write(f"{L},{v:.6e}\n")

# Figure 2: smallest limit for eps = 1e-6 against the load, m = 4096 and m -> infinity, with the Chernoff rule
with open(os.path.join(D, "fig_design.csv"), "w") as f:
    f.write("load,finite4096,poisson,chernoff\n")
    for a100 in range(20, 86, 5):
        a = a100/100.0
        mm = 4096; nn = int(round(a*mm))
        def minL(Tarr, eps=1e-6):
            for L in range(1, len(Tarr)):
                if Tarr[L] <= eps: return L
        f.write(f"{a:.2f},{minL(tail_array_finite(mm, nn))},{minL(tail_array_poisson(a, 20000))},{chernoff_L(a, 1e-6)}\n")

# numeric macros
def tf_at(mm, nn, L): return tail_array_finite(mm, nn)[L]
vals = {
 "ExactAtFiveTwelve": tf[512], "ChernoffAtFiveTwelve": rho**512/(1-rho), "ExactAtTwoFiftySix": tf[256],
 "ExactAtSixtyFour": tf[64], "SimAtSixtyFour": float(sim[0]["measured_gt_64"]),
}
def sci(x): 
    e = int(math.floor(math.log10(x))); mant = x/10**e
    return f"{mant:.2f}\\times 10^{{{e}}}"
with open(os.path.join(T, "numbers.tex"), "w") as f:
    for k, v in vals.items(): f.write(f"\\newcommand{{\\{k}}}{{${sci(v)}$}}\n")
    f.write(f"\\newcommand{{\\GapAtFiveTwelve}}{{{vals['ChernoffAtFiveTwelve']/vals['ExactAtFiveTwelve']:,.0f}}}\n".replace(",", "\\,"))
    f.write(f"\\newcommand{{\\GapAtSixtyFour}}{{{(rho**64/(1-rho))/tf[64]:,.0f}}}\n".replace(",", "\\,"))
    asym = lambda L: (1-alpha)*rho**(L+1)/((1-rho)**2*alpha*math.sqrt(2*math.pi)*L**1.5)
    f.write(f"\\newcommand{{\\AsymAtFiveTwelve}}{{${sci(asym(512))}$}}\n")
    f.write(f"\\newcommand{{\\PoissonAtFiveTwelve}}{{${sci(tail_array_poisson(alpha)[512])}$}}\n")
print("figure data written")

# Table: the layout ladder on the eight compiler traces (needs space_ladder.json from space_model.py)
lad = json.load(open(os.path.join(HERE, "space_ladder.json")))
names = {"zlib": "zlib", "cjson": "cJSON", "littlefs": "littlefs", "freertos": "FreeRTOS", "lua": "Lua", "mbedtls": "Mbed TLS", "tinycc": "TinyCC", "sqlite": "SQLite"}
rows = []; agg = {"hash": [], "pack": [], "total": [], "intern": []}
for p in ["zlib", "cjson", "littlefs", "freertos", "lua", "mbedtls", "tinycc", "sqlite"]:
    r = lad[p]; k = lambda d: r[d]/1024.0
    h = 100*(r["arena_chain"]-r["chain_nohash"])/r["arena_chain"]
    pk = 100*(r["chain_nohash"]-r["strata"])/r["chain_nohash"]
    tot = 100*(r["arena_chain"]-r["strata"])/r["arena_chain"]
    it = 100*(r["oa_decl"]-r["strata_raw"])/r["oa_decl"]
    for key, v in (("hash", h), ("pack", pk), ("total", tot), ("intern", it)): agg[key].append(v)
    rows.append(f"{names[p]} & {k('arena_chain'):.1f} & {k('chain_nohash'):.1f} & {k('oa_decl'):.1f} & {k('strata_raw'):.1f} & {k('strata'):.1f} & {h:.1f} & {pk:.1f} & {tot:.1f} \\\\")
open(os.path.join(T, "tab_ladder.rows"), "w").write("\n".join(rows) + "\n")
with open(os.path.join(T, "ladder_summary.tex"), "w") as f:
    f.write(f"\\newcommand{{\\HashSaveLo}}{{{min(agg['hash']):.1f}}}\n\\newcommand{{\\HashSaveHi}}{{{max(agg['hash']):.1f}}}\n")
    f.write(f"\\newcommand{{\\PackSaveLo}}{{{min(agg['pack']):.1f}}}\n\\newcommand{{\\PackSaveHi}}{{{max(agg['pack']):.1f}}}\n")
    f.write(f"\\newcommand{{\\TotSaveLo}}{{{min(agg['total']):.1f}}}\n\\newcommand{{\\TotSaveHi}}{{{max(agg['total']):.1f}}}\n")
    f.write(f"\\newcommand{{\\InternLo}}{{{min(agg['intern']):.2f}}}\n\\newcommand{{\\InternHi}}{{{max(agg['intern']):.2f}}}\n")
print("ladder table written", {k: (round(min(v),2), round(max(v),2)) for k, v in agg.items()})
