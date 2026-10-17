"""Smallest probe limit L with refusal probability <= eps: exact finite law, Poisson limit, and the
Chernoff bound of the earlier analysis.  Writes design_rule.csv and ../paper/tables/tab_design.rows"""
import csv, math, os
from math import exp, log, lgamma
from design_table import logB, logQ_

HERE = os.path.dirname(os.path.abspath(__file__))

def tail_array_finite(m, n):
    """T[L] = P_refuse(m,n,L) for L = 0..gmax, via suffix sums of positive terms only (no cancellation)."""
    k = m - n; gmax = m - k + 1
    lq = logQ_(k, m)
    w = [0.0]*(gmax+2)
    for g in range(1, gmax+1):
        lp = logB(g) + logQ_(k-1, m-g) - lq if k > 1 else (0.0 if g == m else -math.inf)
        w[g] = exp(lp) if lp > -745 else 0.0
    S0 = [0.0]*(gmax+3)                     # S0[j] = sum_{g>j} w[g]
    acc = 0.0
    for g in range(gmax, 0, -1):
        acc += w[g]; S0[g-1] = acc
    T = [0.0]*(gmax+2); acc = 0.0
    for L in range(gmax, -1, -1):
        acc += S0[L]; T[L] = (k/m)*acc      # sum_{j>=L} S0[j]
    return T

def tail_array_poisson(alpha, N=40000):
    w = [0.0]*(N+2)
    for g in range(1, N+1):
        lp = -alpha*g + (g-1)*log(alpha*g) - lgamma(g+1)
        w[g] = exp(lp) if lp > -745 else 0.0
    S0 = [0.0]*(N+3); acc = 0.0
    for g in range(N, 0, -1):
        acc += w[g]; S0[g-1] = acc
    T = [0.0]*(N+2); acc = 0.0
    for L in range(N, -1, -1):
        acc += S0[L]; T[L] = (1-alpha)*acc
    return T

def min_L(T, eps):
    for L in range(1, len(T)):
        if T[L] <= eps: return L
    return None

def chernoff_L(alpha, eps):
    r = alpha*exp(1-alpha)
    L = 1
    while r**L/(1-r) > eps: L += 1
    return L

def selftest():
    from design_table import refuse
    for (m, n, L) in [(65536, 49152, 512), (65536, 49152, 64), (1024, 512, 30), (256, 190, 24)]:
        a = tail_array_finite(m, n)[L]; b = refuse(m, n, [L])[L]
        assert abs(a - b) <= 1e-9*b, (m, n, L, a, b)

if __name__ == "__main__":
    selftest()
    loads = [(3, 8), (1, 2), (5, 8), (3, 4)]
    ms = [1 << 8, 1 << 10, 1 << 12, 1 << 14, 1 << 16]
    rows = []
    for (a_n, a_d) in loads:
        alpha = a_n/a_d
        TP = tail_array_poisson(alpha)
        for eps in (1e-6, 1e-9):
            rec = dict(load=f"{a_n}/{a_d}", eps=eps, chernoff=chernoff_L(alpha, eps), poisson=min_L(TP, eps))
            for m in ms:
                n = m*a_n//a_d
                rec[f"m={m}"] = min_L(tail_array_finite(m, n), eps)
            rows.append(rec)
    with open(os.path.join(HERE, "design_rule.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    os.makedirs(os.path.join(HERE, "../paper/tables"), exist_ok=True)
    with open(os.path.join(HERE, "../paper/tables/tab_design.rows"), "w") as f:
        for r in rows:
            e = "10^{-6}" if r["eps"] == 1e-6 else "10^{-9}"
            cells = " & ".join(str(r[f"m={m}"]) for m in ms)
            f.write(f"${r['load']}$ & ${e}$ & {cells} & {r['poisson']} & {r['chernoff']} \\\\\n")
    for r in rows: print(r)
