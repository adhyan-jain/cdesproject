"""Exact finite refusal law in log space; comparison with the stored simulation and the Chernoff bound."""
import csv, math, json, sys, os
from math import lgamma, log, exp

def logB(g):     return (g-1)*log(g) - lgamma(g+1)
def logQ(j, s):
    if j == 0: return 0.0 if s == 0 else -math.inf
    if s < j: return -math.inf
    return log(j) - log(s) + (s-j)*log(s) - lgamma(s-j+1) if s > j else log(j) - log(s)   # s==j: (j/j)*1 = 1 -> log 1
def logQ_(j, s):
    if j == 0: return 0.0 if s == 0 else -math.inf
    if s < j: return -math.inf
    return log(j/s) + ((s-j)*log(s) if s > j else 0.0) - lgamma(s-j+1)

def tail_terms(m, n):
    k = m - n
    lq = logQ_(k, m)
    return k, lq

def refuse(m, n, Ls):
    """P_refuse for each L in Ls (exact finite law)."""
    k = m - n
    if k == 1:
        return {L: max(m-L, 0)/m for L in Ls}
    lq = logQ_(k, m)
    gmax = m - k + 1
    w = [0.0]*(gmax+2)
    for g in range(1, gmax+1):
        lp = logB(g) + logQ_(k-1, m-g) - lq
        w[g] = exp(lp) if lp > -745 else 0.0
    out = {}
    for L in Ls:
        out[L] = (k/m) * sum((g-L)*w[g] for g in range(L+1, gmax+1))
    return out

def poisson_limit(alpha, Ls, N=20000):
    """(1-a) * sum_{g>L} (g-L) Borel(g;a), the m->infinity law."""
    lb = [0.0]+[-alpha*g + (g-1)*log(alpha*g) - lgamma(g+1) for g in range(1, N+1)]
    b = [0.0]+[exp(x) for x in lb[1:]]
    out = {}
    for L in Ls:
        out[L] = (1-alpha)*sum((g-L)*b[g] for g in range(L+1, N+1))
    return out

def chernoff(alpha, L):
    r = alpha*exp(1-alpha)
    return r**L/(1-r)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    rows = list(csv.DictReader(open(os.path.join(here, "../../results/hardening/probes.csv"))))
    Ls = [8, 16, 32, 64, 128, 256, 512]
    print("m  load hash  L   simulated  exact-finite  poisson-limit  chernoff   chernoff/exact")
    out = []
    for r in rows:
        if r["hash"] != "murmur3": continue
        m = int(r["index_slots"]); a = float(r["load"]); n = int(r["names"])
        ex = refuse(m, n, Ls); po = poisson_limit(a, Ls)
        for L in Ls:
            sim = float(r["measured_gt_%d" % L])
            ch = chernoff(a, L)
            out.append(dict(m=m, load=a, L=L, simulated=sim, exact=ex[L], poisson=po[L], chernoff=ch))
            if m == 65536 and a in (0.5, 0.75) and L >= 32:
                print(f"{m:6d} {a:5.3f} {r['hash']:7s} {L:3d}  {sim:9.2e}  {ex[L]:11.3e}  {po[L]:11.3e}  {ch:9.2e}  {ch/ex[L] if ex[L] > 0 else float('nan'):8.0f}")
    json.dump(out, open(os.path.join(here, "exact_vs_simulation.json"), "w"), indent=1)
