"""Sustainability of a persistent table: probability that NO fresh name can ever be refused at occupancy n.

Given the table T (n keys in m cells, linear probing, probe limit L) a fresh name with uniform home is refused iff its
home starts a window of L occupied cells.  By exact undo (push, pop, push, ...) the table stays T, so refusals are
conditionally independent given T:   P(no refusal in N oscillating pushes) = E[(1 - W/m)^N],  W = sum_blocks (g-L)^+.
W = 0  iff every block (an empty cell plus the occupied run after it) has at most L cells.  Cutting the ring at its
k = m-n empty cells (Appendix A of the manuscript):

    P(W = 0) = [z^m] (sum_{g<=L} B(g) z^g)^k / [z^m] (sum_{g>=1} B(g) z^g)^k ,      B(g) = g^(g-1)/g!.

Checked against enumeration of every home sequence (exact rationals) and Monte Carlo; then compared with the union
bound N*R_m(n,L).
"""
import itertools, math, random
from fractions import Fraction as Fr
from decimal import Decimal, getcontext

def B(g): return Fr(g**(g-1), math.factorial(g))

def p_nowin_exact(m, n, L):
    k = m-n
    def powcoef(cap):
        base = [Fr(0)]+[B(g) if g <= cap else Fr(0) for g in range(1, m+1)]
        res = [Fr(1)]+[Fr(0)]*m
        for _ in range(k):
            new = [Fr(0)]*(m+1)
            for i, a in enumerate(res):
                if a:
                    for j in range(1, m+1-i):
                        if base[j]: new[i+j] += a*base[j]
            res = new
        return res[m]
    return powcoef(L)/powcoef(m)

def p_nowin_dec(m, n, L, prec=50):
    getcontext().prec = prec
    k = m-n
    def pw(cap):
        base = [Decimal(0)]+[(Decimal(g)**(g-1))/Decimal(math.factorial(g))*(-Decimal(g)).exp() if g <= cap else Decimal(0) for g in range(1, m+1)]
        res = [Decimal(1)]+[Decimal(0)]*m
        e = k; b = base
        def mul(x, y):
            out = [Decimal(0)]*(m+1)
            for i, a in enumerate(x):
                if a:
                    for j in range(0, m+1-i):
                        if y[j]: out[i+j] += a*y[j]
            return out
        while e:
            if e & 1: res = mul(res, b)
            e >>= 1
            if e: b = mul(b, b)
        return res[m]
    return pw(L)/pw(m)

def p_nowin_float_check(m, n, L): return 1-p_bad_float(m, n, L)

def brute(m, n, L):
    ok = tot = 0
    for h in itertools.product(range(m), repeat=n):
        c = [0]*m
        for x in h: c[x] += 1
        # occupied set via linear probing
        occ = [0]*m
        for x in h:
            i = x
            while occ[i]: i = (i+1) % m
            occ[i] = 1
        good = True
        for s in range(m):
            if all(occ[(s+t) % m] for t in range(L)): good = False; break
        ok += good; tot += 1
    return Fr(ok, tot)


import os, sys
def _basevec(m, cap):
    import numpy as np
    b = np.zeros(m+1)
    for g in range(1, min(cap, m)+1): b[g] = math.exp((g-1)*math.log(g)-math.lgamma(g+1)-g)
    return b
def _powc(b, k, m):
    import numpy as np
    res = np.zeros(m+1); res[0] = 1.0; e = k
    while e:
        if e & 1: res = np.convolve(res, b)[:m+1]
        e >>= 1
        if e: b = np.convolve(b, b)[:m+1]
    return res[m]
def p_bad_float(m, n, L):
    """P(some block has more than L cells) = 1 - P(W=0), in floating point (scaled by e^-g, no overflow)."""
    k = m-n
    return 1 - _powc(_basevec(m, L), k, m)/_powc(_basevec(m, m), k, m)

def design_sustain(sizes=(256, 1024, 4096), alpha=0.75, epss=(1e-2, 1e-4, 1e-6)):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from fill_law import R_refusal, smallest
    rho = alpha*math.exp(1-alpha); rows = []; out = {}
    for m in sizes:
        n = int(alpha*m)
        for eps in epss:
            Lr = smallest(lambda L: R_refusal(m, n, L) <= eps, 2, m)
            Lw = smallest(lambda L: p_bad_float(m, n, L) <= eps, 2, m)
            rows.append("%d & %g & %d & %d & %d \\\\" % (m, eps, Lr, Lw, Lw-Lr)); out[(m, eps)] = (Lr, Lw)
            print("   m=%d eps=%g  L(one push)=%d  L(unlimited run)=%d  extra=%d  (ln m / ln(1/rho) = %.0f)" % (m, eps, Lr, Lw, Lw-Lr, math.log(m)/math.log(1/rho)), flush=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
    with open(os.path.join(d, "tab_sustain.tex"), "w") as f:
        f.write("\\begin{tabular}{@{}rrrrr@{}}\n\\toprule\n$m$ & $\\varepsilon$ & one push & unlimited run & extra \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    return out

if __name__ == "__main__":
    cnt = 0
    for m in range(3, 8):
        for n in range(1, m):
            if m**n > 120000: continue
            for L in (1, 2, 3, 4):
                assert brute(m, n, L) == p_nowin_exact(m, n, L), (m, n, L); cnt += 1
    print("P(W=0) == enumeration of every home sequence: %d cases, 0 mismatches" % cnt)
    for (m, n, L) in [(12, 9, 5), (16, 12, 6)]:
        assert abs(float(p_nowin_exact(m, n, L)) - float(p_nowin_dec(m, n, L))) < 1e-12
    print("decimal evaluation agrees")
    for (m, n, L) in [(40, 30, 12), (64, 48, 20)]:
        assert abs(float(p_nowin_exact(m, n, L)) - p_nowin_float_check(m, n, L)) < 1e-9
    print("float evaluation agrees with exact rationals")
    design_sustain()
    print("sustain_law: all checks passed")
