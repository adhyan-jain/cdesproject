"""Machine checks of the remaining claims of the manuscript.

1. Proposition 14 (ledger): the four identities hold at EVERY instant of EVERY translation unit of the eight
   traces, and the closed-form word counts reproduce the peaks of the independent simulation in space_model.py.
2. Corollary 8(b): R_m(n,L) -> R_inf(alpha,L) as m grows (differences shrink, monotone in m at fixed L).
3. Corollary 8(c): R_inf / asymptotic -> 1 as L grows.
4. Proposition 5: mean orphans per random clear (= mean displacement) against alpha/(2(1-alpha)), 20 runs.
Exits non-zero on any violation.
"""
import os, sys, math, random
from math import exp, log, lgamma
import space_model as sm
from design_table import refuse, poisson_limit
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
w4 = sm.words4; w5 = sm.words5; packable = sm.is_packable

def ledger_unit(unit, peaks):
    vis = {}; scope_names = [[]]; depth = 0
    d = 0; s = 0; m = 16; b = 16
    sum_decl_w4 = 0          # over all live declarations
    sum_vis_w4 = 0           # over visible names
    sum_vis_w = 0            # visible names, packed where packable
    hidden_w4 = 0            # over hidden declarations
    packdiff = 0             # over visible packable names: w4 - w5
    inst = 0
    def U():
        n = len(vis); h = d - n
        U0 = b + 1 + (4*d + sum_decl_w4) + s
        U1 = b + 1 + (3*d + sum_decl_w4) + s
        U2 = m + 1 + (3*d + sum_decl_w4) + s
        Sr = m + 1 + (2*n + sum_vis_w4) + n + 3*h + 2*s
        S = m + 1 + (2*n + sum_vis_w) + n + 3*h + 2*s
        return U0, U1, U2, Sr, S, n, h
    def check():
        nonlocal inst
        U0, U1, U2, Sr, S, n, h = U()
        assert U0 - U1 == d, "C0-C1"
        assert U1 - U2 == b - m, "C1-C2"
        assert U2 - Sr == hidden_w4 - s, "C2-Sraw"
        assert Sr - S == packdiff, "Sraw-S"
        for k, v in zip(("C0", "C1", "C2", "Sraw", "S"), (U0, U1, U2, Sr, S)):
            if v > peaks[k]: peaks[k] = v
        inst += 1
    check()
    for op, nm in unit:
        if op == "E":
            depth += 1; scope_names.append([]); s += 1
        elif op == "X":
            if depth == 0: continue
            for name in reversed(scope_names.pop()):
                st = vis[name]; st.pop(); l = len(name)
                d -= 1; sum_decl_w4 -= w4(l)
                if st:                                   # a hidden declaration is restored
                    hidden_w4 -= w4(l)
                else:                                    # the name stops being visible
                    del vis[name]; sum_vis_w4 -= w4(l)
                    sum_vis_w -= (w5(l) if packable(name) else w4(l))
                    if packable(name): packdiff -= (w4(l) - w5(l))
            s -= 1; depth -= 1
        else:
            st = vis.get(nm)
            if st and st[-1] == depth: check(); continue
            l = len(nm)
            d += 1; sum_decl_w4 += w4(l)
            if st is None:
                vis[nm] = [depth]; sum_vis_w4 += w4(l)
                sum_vis_w += (w5(l) if packable(nm) else w4(l))
                if packable(nm): packdiff += (w4(l) - w5(l))
            else:
                hidden_w4 += w4(len(nm)); st.append(depth)
            scope_names[-1].append(nm)
            while d > b: b *= 2
            while len(vis)*4 > m*3: m *= 2
        check()
    return inst

def check_ledger():
    total = 0
    names = ["zlib","cjson","littlefs","freertos","lua","mbedtls","tinycc","sqlite"]
    for p in names:
        units = sm.read_units(os.path.join(ROOT, "workloads/traces", p + ".trace.gz"))
        peaks = dict(C0=0, C1=0, C2=0, Sraw=0, S=0)
        for u in units: 
            pk = dict(C0=0, C1=0, C2=0, Sraw=0, S=0)
            total += ledger_unit(u, pk)
            for k in peaks: peaks[k] = max(peaks[k], pk[k])
        sim = {k: sm.trace_peak(units, d) for k, d in (("C0","arena_chain"),("C1","chain_nohash"),("C2","oa_decl"),("Sraw","strata_raw"),("S","strata"))}
        assert peaks == sim, (p, peaks, sim)
    return total

def check_limit():
    out = []
    for alpha in (0.5, 0.75):
        Ls = [16, 64]
        P = poisson_limit(alpha, Ls)
        for L in Ls:
            prev = None
            for e in (8, 10, 12, 14, 16):
                m = 1 << e; n = int(round(alpha*m))
                if L >= m: continue
                v = refuse(m, n, [L])[L]
                err = abs(v - P[L]) / P[L]
                if prev is not None: assert err <= prev*1.01 + 1e-12, ("not shrinking", alpha, L, e, err, prev)
                prev = err
            assert prev < 0.02 if L == 16 else prev < 0.15, (alpha, L, prev)
            out.append((alpha, L, prev))
    return out

def check_asym():
    alpha = 0.75; rho = alpha*exp(1-alpha); res = []
    P = poisson_limit(alpha, [64, 256, 1024, 4096], N=60000)
    last = None
    for L in (64, 256, 1024, 4096):
        asym = (1-alpha)*rho**(L+1)/((1-rho)**2*alpha*math.sqrt(2*math.pi)*L**1.5)
        r = P[L]/asym; res.append((L, r))
        if last is not None: assert abs(r-1) < abs(last-1), ("ratio not approaching 1", L, r, last)
        last = r
    assert abs(res[-1][1]-1) < 0.02, res
    return res

def check_orphans(runs=20, m=1 << 16):
    rng = random.Random(11); out = []
    for alpha in (0.5, 0.75):
        n = int(alpha*m); means = []
        for _ in range(runs):
            occ = bytearray(m); tot = 0
            for _ in range(n):
                h = rng.randrange(m); c = h
                while occ[c]: c = (c+1) % m
                occ[c] = 1; tot += (c - h) % m
            means.append(tot/n)
        mu = sum(means)/runs; sd = (sum((x-mu)**2 for x in means)/(runs-1))**0.5
        se = sd/runs**0.5; th = alpha/(2*(1-alpha))
        # finite-size bias is O(1/m); 4 standard errors plus a 1% allowance
        assert abs(mu - th) < 4*se + 0.01*th, (alpha, mu, se, th)
        out.append((alpha, mu, se, th))
    return out

def knuth_route_exact(m, n, L):
    """Independent derivation (Knuth / Abel-binomial counting): P_g = probability that a run of exactly g
    occupied cells starts at a fixed cell = C(n,g)(g+1)^(g-1) (k-1) (m-g-1)^(n-g-1) / m^n  (k = m-n >= 2);
    P(first L cells all occupied) = sum_{g>=L} (g-L+1) P_g."""
    from fractions import Fraction
    from math import comb
    k = m - n
    tot = Fraction(0)
    for g in range(L, n + 1):
        tot += (g - L + 1) * Fraction(comb(n, g) * (g + 1)**(g - 1) * (k - 1) * (m - g - 1)**(n - g - 1) if n - g - 1 >= 0
                                      else comb(n, g) * (g + 1)**(g - 1) * (k - 1), m**n * (1 if n - g - 1 >= 0 else (m - g - 1)))
    return tot

def knuth_route_float(m, n, L):
    k = m - n
    tot = 0.0
    for g in range(L, n + 1):
        lp = (lgamma(n + 1) - lgamma(g + 1) - lgamma(n - g + 1) + (g - 1)*log(g + 1) + log(k - 1)
              + (n - g - 1)*log(m - g - 1) - n*log(m))
        tot += (g - L + 1) * exp(lp) if lp > -745 else 0.0
    return tot

def check_knuth_route():
    from fractions import Fraction
    checked = 0
    for m in range(4, 15):
        for n in range(0, m - 1):                         # k >= 2
            for L in range(1, n + 2):
                a = knuth_route_exact(m, n, L)
                b = refuse(m, n, [L])[L]
                from design_table import refuse as _r
                assert abs(float(a) - b) <= 1e-12 * max(b, 1e-300) + 1e-15, ("exact small", m, n, L, float(a), b)
                checked += 1
    worst = 0.0
    for e in (10, 14, 16, 18, 20):
        m = 1 << e
        for num, den in ((1, 2), (3, 4)):
            n = m*num//den
            for L in (16, 64, 256):
                a = knuth_route_float(m, n, L); b = refuse(m, n, [L])[L]
                rel = abs(a - b)/b; worst = max(worst, rel)
                assert rel < 1e-6, ("large", m, n, L, a, b)
                checked += 1
    return checked, worst

def uniform_limits():
    """Uniform probing: P(first L probes all occupied) = prod_{i<L} (n-i)/(m-i), whatever the occupied set."""
    out = {}
    m = 1 << 16
    for num, den in ((3, 8), (1, 2), (5, 8), (3, 4)):
        n = m*num//den; acc = 0.0; L = 0; target = log(1e-6)
        while acc > target:
            acc += log(n - L) - log(m - L); L += 1
        out[(num, den)] = L
    return out

if __name__ == "__main__":
    inst = check_ledger(); print(f"ledger: 4 identities hold at {inst:,} instants; closed forms equal simulated peaks on 8 traces x 5 layouts")
    lim = check_limit(); print("limit (relative error of finite-size law vs Poisson limit at the largest m):", [(a, L, round(e, 4)) for a, L, e in lim])
    asy = check_asym(); print("tail asymptotics ratio exact/asymptotic at alpha=3/4:", [(L, round(r, 4)) for L, r in asy])
    orp = check_orphans(); print("orphans (mean displacement) vs alpha/(2(1-alpha)):", [(a, round(mu, 3), round(se, 3), th) for a, mu, se, th in orp])
    kc, kw = check_knuth_route(); print(f"Knuth-route (Abel-binomial) derivation equals Theorem 7 in {kc} cases (exact for m<=14, floats up to m=2^20, worst relative difference {kw:.1e})")
    uni = uniform_limits(); print("uniform probing, smallest L for eps=1e-6 at m=2^16:", {f"{a}/{b}": L for (a, b), L in uni.items()})
    d = os.path.join(HERE, "../paper/tables"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "proof_summary.tex"), "w") as f:
        f.write("\\newcommand{\\LedgerInstants}{%s}\n" % f"{inst:,}".replace(",", "\\,"))
        f.write("\\newcommand{\\AsymRatioFour}{%.3f}\n" % asy[-1][1])
        f.write("\\newcommand{\\KnuthCases}{%d}\n\\newcommand{\\KnuthWorst}{%.0e}\n" % (kc, kw))
        f.write("\\newcommand{\\UniLHalf}{%d}\n\\newcommand{\\UniLThreeQ}{%d}\n" % (uni[(1, 2)], uni[(3, 4)]))
        f.write("\\newcommand{\\OrphanMeasured}{%.2f}\n\\newcommand{\\OrphanTheory}{%.2f}\n" % (orp[1][1], orp[1][3]))
    print("all proof checks passed")
