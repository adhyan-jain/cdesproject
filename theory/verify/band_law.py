"""Bounded churn above a persistent trunk: a schedule-universal bound on the refusal probability.

Setting.  A trunk of k keys is pushed and never popped.  Afterwards the schedule pushes fresh names but never lets more
than s keys sit above the trunk (the scope tree below the trunk has height at most s).  Table: m cells, circular linear
probing, probe limit L (a key is refused iff the L cells from its home are all occupied).

Call the trunk occupancy O s-vulnerable if some window of L consecutive cells holds at most s-1 empty cells of O.

   (a) a refusal anywhere in such a schedule (trunk build included) implies that O is s-vulnerable;
   (b) with N fresh copies of an s-deep path, P(refusal) = 1 - E[(1-q(O))^N], q(O) > 0 iff O is s-vulnerable, so
       P(refusal) increases to V_s = P(O is s-vulnerable) as N grows;
   (c) cutting the ring at its e = m-k empty cells, the gaps (occupied cells between consecutive empty cells) have the
       law of e exchangeable variables with weights b_g = (g+1)^(g-1)/g! conditioned on sum k, and O is s-vulnerable iff
       some s cyclically consecutive gaps sum to at least L-s+1.  So V_s <= U_s = min(1, e P(g_1+...+g_s >= L-s+1)),
       a closed finite sum; V_1 is the one-push law of Proposition 11.

Checks:
   1. every trunk home sequence and every branch sequence through the real insertion code: (a), and q > 0 iff window rule;
   2. the gap law (c) against enumeration, in exact rationals;
   3. P(refusal after N copies) exactly: increasing in N, below V_s, and approaching V_s;
   4. U_s >= V_s exactly; at a large size U_s against Monte Carlo of V_s and V_1 against the exact one-push law.
"""
import itertools, math, os, sys
from collections import Counter
from fractions import Fraction as Fr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def b(g): return Fr((g+1)**(g-1), math.factorial(g)) if g > 0 else Fr(1)

# ------------------------------------------------------------ real insertion process
def insert(occ, m, h, L):
    """Insert with home h: the cell used, or None if the L cells from h are all occupied (refusal)."""
    c = h; d = 0
    while occ[c]:
        c = (c+1) % m; d += 1
        if d >= L: return None
    return c

def build_trunk(m, homes, L):
    occ = [0]*m
    for h in homes:
        c = insert(occ, m, h, L)
        if c is None:
            occ = [0]*m                              # refused: take the occupancy the unlimited process would give
            for g in homes:
                c = g
                while occ[c]: c = (c+1) % m
                occ[c] = 1
            return occ, True
        occ[c] = 1
    return occ, False

def branch_fail_count(m, occ, s, L):
    """Number of home sequences (h_1..h_s) of a path of s fresh keys with a refusal."""
    def rec(j):
        if j == s: return 0
        tot = 0
        for h in range(m):
            c = insert(occ, m, h, L)
            if c is None: tot += m**(s-j-1)
            else:
                occ[c] = 1; tot += rec(j+1); occ[c] = 0
        return tot
    return rec(0)

def window_vulnerable(occ, L, s):
    m = len(occ)
    return any(sum(1 for t in range(L) if not occ[(i+t) % m]) <= s-1 for i in range(m))

# ------------------------------------------------------------ exact gap law
def poly_pow(p, e, cap):
    res = [Fr(1)]+[Fr(0)]*cap
    for _ in range(e):
        new = [Fr(0)]*(cap+1)
        for i, a in enumerate(res):
            if a:
                for j, c in enumerate(p):
                    if i+j > cap: break
                    new[i+j] += a*c
        res = new
    return res

def U_exact(m, k, s, L):
    e = m-k
    G = [b(g) for g in range(k+1)]
    Gs, Ges, Ge = poly_pow(G, s, k), poly_pow(G, e-s, k), poly_pow(G, e, k)
    t = max(L-s+1, 0)
    return min(Fr(1), e*sum(Gs[j]*Ges[k-j] for j in range(t, k+1))/Ge[k])

def D_exact(m, k, s, L):
    """Declumped bound D_s = min(1, e P(S_1 >= T, S_0 < T)), T = L-s+1, S_i = g_i+...+g_{i+s-1}: count only the first
    exceedance of a run of windows (an up-crossing).  Valid because some window exceeds T and not all do."""
    e = m-k; T = max(L-s+1, 0)
    if s*k >= e*T: return Fr(1)           # all windows could exceed T at once: no up-crossing argument
    G = [b(g) for g in range(k+1)]
    X, Rest, Ge = poly_pow(G, s-1, k), poly_pow(G, e-s-1, k), poly_pow(G, e, k)
    num = Fr(0)
    for u in range(0, min(k, T-1)+1):
        if not X[u]: continue
        tau = T-u
        for a in range(0, min(tau-1, k-u)+1):
            for c in range(tau, k-u-a+1):
                num += X[u]*b(a)*b(c)*Rest[k-u-a-c]
    return min(Fr(1), e*num/Ge[k])

def V_from_gaps(m, k, s, L):
    """V_s from the gap law: all compositions of k into e = m-k parts weighted by prod b(g_i)."""
    e = m-k; t = L-s+1; num = den = Fr(0)
    def comps(rem, parts):
        if parts == 1: yield (rem,); return
        for g in range(rem+1):
            for rest in comps(rem-g, parts-1): yield (g,)+rest
    for seq in comps(k, e):
        w = Fr(1)
        for g in seq: w *= b(g)
        den += w
        if any(sum(seq[(i+j) % e] for j in range(s)) >= t for i in range(e)): num += w
    return num/den

def test_small():
    cases = [(7, 4, 3), (8, 4, 3), (8, 5, 3), (8, 4, 2), (9, 5, 4), (9, 4, 3), (8, 5, 4), (9, 6, 4)]
    n = 0
    for (m, k, L) in cases:
        weight = Counter(tuple(sorted(h)) for h in itertools.product(range(m), repeat=k))
        tot = m**k
        for s in (1, 2, 3):
            if m-k < s+1: continue
            state = {}
            for ky in weight:
                occ, refused = build_trunk(m, ky, L)
                wv = window_vulnerable(occ, L, s)
                if refused: assert wv, ("a", m, k, L, s, ky)
                q = Fr(1) if refused else Fr(branch_fail_count(m, occ, s, L), m**s)
                assert (q > 0) == wv, ("b", m, k, L, s, ky, q, wv)
                state[ky] = (wv, q)
                n += 1
            V = sum(Fr(weight[ky], tot) for ky, (wv, q) in state.items() if wv)
            assert V == V_from_gaps(m, k, s, L), ("gap law", m, k, s, L)
            U = U_exact(m, k, s, L)
            assert U >= V, ("U<V", m, k, s, L, U, V)
            D = D_exact(m, k, s, L)
            assert D >= V and (D == 1 or D <= U), ("D", m, k, s, L, D, V, U)
            prev = 0.0; P64 = None
            for N in (1, 4, 16, 64, 256, 4096, 10**6, 10**9):
                if N <= 256: Pf = float(sum(Fr(weight[ky], tot)*(1-(1-q)**N) for ky, (wv, q) in state.items()))
                else: Pf = sum(weight[ky]/tot*(1-(1-float(q))**N) for ky, (wv, q) in state.items())
                assert prev <= Pf + 1e-12 and Pf <= float(V) + 1e-12, ("monotone", m, k, s, L, N, Pf, float(V))
                prev = Pf
                if N == 64: P64 = Pf
            assert V == 0 or prev >= 0.9*float(V), ("limit", m, k, s, L, prev, float(V))
            print("  m=%d k=%d L=%d s=%d: V=%.5f D=%.5f U=%.5f  P(N=64)=%.5f  P(N=1e9)=%.5f" % (m, k, L, s, V, D, U, P64, prev), flush=True)
    print("band_law: window rule, gap law, monotone limit and U >= V verified on %d trunk multisets" % n)

def count_vectors(m, k):
    def rec(i, rem):
        if i == m-1: yield (rem,); return
        for c in range(rem+1):
            for rest in rec(i+1, rem-c): yield (c,)+rest
    return rec(0, k)

def occupancy_law(m, k):
    """Exact law of the trunk occupancy set {occ tuple: probability}: enumerate the cell-count vectors, weight k!/prod c!."""
    out = Counter(); kf = math.factorial(k)
    for cv in count_vectors(m, k):
        occ = [0]*m
        for h, c in enumerate(cv):
            for _ in range(c):
                x = h
                while occ[x]: x = (x+1) % m
                occ[x] = 1
        w = kf
        for c in cv: w //= math.factorial(c)
        out[tuple(occ)] += w
    return {o: Fr(w, m**k) for o, w in out.items()}

def test_mid():
    """Non-degenerate sizes (0 < V < 1): the window rule and q > 0 on every occupancy set, V against the gap law, U, D."""
    n = 0
    for (m, k) in [(11, 6), (12, 7), (13, 8), (12, 8)]:
        law = occupancy_law(m, k)
        assert sum(law.values()) == 1
        for L in (5, 6, 7, 8):
            for s in (1, 2, 3):
                if m-k < s+1: continue
                V = Fr(0); prev = 0.0; qs = []
                for occ, pr in law.items():
                    wv = window_vulnerable(occ, L, s)
                    q = Fr(branch_fail_count(m, list(occ), s, L), m**s)
                    assert (q > 0) == wv, ("q>0 iff window", m, k, L, s, occ, q, wv)
                    if wv: V += pr
                    qs.append((float(pr), float(q))); n += 1
                assert V == V_from_gaps(m, k, s, L), ("gap law", m, k, L, s)
                U, D = U_exact(m, k, s, L), D_exact(m, k, s, L)
                assert V <= D and (D == 1 or D <= U) and V <= U, (m, k, L, s, V, D, U)
                for N in (1, 16, 256, 4096, 10**6, 10**9):
                    Pf = sum(pr*(1-(1-q)**N) for pr, q in qs)
                    assert prev <= Pf + 1e-12 and Pf <= float(V) + 1e-12, ("monotone", m, k, L, s, N)
                    assert Pf >= float(V)*(1-math.exp(-N/m**s)) - 1e-12, ("finite-N lower bound", m, k, L, s, N)
                    prev = Pf
                assert V == 0 or prev >= 0.99*float(V), ("limit", m, k, L, s, prev, float(V))
                if 0 < V < 1: print("  m=%d k=%d L=%d s=%d: V=%.5f D=%.5f U=%.5f  limit(N=1e9)=%.5f" % (m, k, L, s, V, D, U, prev), flush=True)
    print("band_law: mid-size check passed on %d occupancy sets" % n)

# ------------------------------------------------------------ large sizes (floating point, all terms positive)
def gap_weights(k, x):
    return [math.exp(((g-1)*math.log(g+1) - math.lgamma(g+1) if g else 0.0) + g*math.log(x)) for g in range(k+1)]

def tilt(k, e):
    """x with E[gap] = k/e under weights b_g x^g (tree-function tilt); conditioning on the sum makes x irrelevant."""
    lo, hi = 1e-9, math.exp(-1.0)*(1-1e-12)
    for _ in range(100):
        x = (lo+hi)/2
        w = gap_weights(3000, x)
        if sum(g*wg for g, wg in enumerate(w))/sum(w) < k/e: lo = x
        else: hi = x
    return x

def U_float(m, k, s, L):
    """min(1, e P(S_s >= L-s+1)) with exchangeable gaps conditioned on the sum k."""
    import numpy as np
    e = m-k; t = max(L-s+1, 0)
    w = np.array(gap_weights(k, tilt(k, e)))
    def power(p):
        res = np.zeros(k+1); res[0] = 1.0; lres = 0.0; base = w.copy(); lbase = 0.0
        while p:
            if p & 1:
                res = np.convolve(res, base)[:k+1]; sc = res.max(); res /= sc; lres += math.log(sc) + lbase
            p >>= 1
            if p:
                base = np.convolve(base, base)[:k+1]; sc = base.max(); base /= sc; lbase = 2*lbase + math.log(sc)
        return res, lres
    # lres tracks log-scale of res relative to w^p: res_true = res * exp(lres)
    Gs, ls = power(s); Ges, les = power(e-s); Ge, le = power(e)
    return min(1.0, e*float(np.dot(Gs[t:], Ges[k-t::-1][:k+1-t]))/float(Ge[k])*math.exp(ls+les-le))

def D_float(m, k, s, L):
    """Declumped bound D_s in floating point (see D_exact)."""
    import numpy as np
    e = m-k; T = max(L-s+1, 0)
    if s*k >= e*T: return 1.0
    w = np.array(gap_weights(k, tilt(k, e)))
    def power(p):
        res = np.zeros(k+1); res[0] = 1.0; lres = 0.0; base = w.copy(); lbase = 0.0
        while p:
            if p & 1:
                res = np.convolve(res, base)[:k+1]; sc = res.max(); res /= sc; lres += math.log(sc) + lbase
            p >>= 1
            if p:
                base = np.convolve(base, base)[:k+1]; sc = base.max(); base /= sc; lbase = 2*lbase + math.log(sc)
        return res, lres
    X, lx = power(s-1); R, lr = power(e-s-1); Z, lz = power(e)
    num = 0.0
    for u in range(0, min(k, T-1)+1):
        if X[u] == 0.0: continue
        tau = T-u; r = k-u
        lo = w[:min(tau, r+1)]; hi = w[tau:r+1]
        if len(hi) == 0: continue
        conv = np.convolve(lo, hi)[:r+1]                 # conv[j] = sum_{a<tau, c>=tau, a+c = tau+j'}  (c offset by tau)
        # hi starts at index tau: conv index j corresponds to a + (c - tau) = j, i.e. a + c = j + tau
        for j, v in enumerate(conv):
            if v and r-(j+tau) >= 0: num += X[u]*v*R[r-(j+tau)]
    return min(1.0, e*num/float(Z[k])*math.exp(lx+lr-lz))

def mc_V(m, k, L, S, trials, seed=7):
    import numpy as np
    rng = np.random.default_rng(seed); cnt = {s: 0 for s in S}
    for _ in range(trials):
        a = np.bincount(rng.integers(0, m, size=k), minlength=m)
        y = 0; occ = np.zeros(m, bool)
        for t in range(2*m):
            c = t % m; y += a[c]
            if t >= m: occ[c] = y > 0
            if y > 0: y -= 1
        e = (~occ).astype(np.int64)
        cs = np.concatenate([[0], np.cumsum(np.concatenate([e, e[:L]]))])
        mn = (cs[L:L+m]-cs[:m]).min()
        for s in S:
            if mn <= s-1: cnt[s] += 1
    return {s: cnt[s]/trials for s in S}


def smallest_L(m, n, s, eps, lo=8, hi=900):
    """Smallest L whose declumped bound is <= eps.  V_s decreases in L, so a bound valid at L' <= L is valid at L; we
    bisect on D_s and then confirm that the five values below the answer are above eps."""
    k = m-n
    f = lambda L: D_float(m, n, s, L)
    a, c = lo, hi
    while c-a > 1:
        mid = (a+c)//2
        if f(mid) <= eps: c = mid
        else: a = mid
    assert all(f(L) > eps for L in range(max(lo, c-5), c)), ("not monotone near the crossing", m, s, eps, c)
    return c

def large_checks():
    from sustain_law import p_bad_float
    # (i) V_1 is the one-push law of Proposition 11, and D_1 bounds it from above within a hair
    for (m, n, L) in [(1024, 768, 70), (4096, 3072, 130)]:
        ex = p_bad_float(m, n, L); d1 = D_float(m, n, 1, L)
        assert ex <= d1 <= ex*1.10+1e-9, (m, n, L, ex, d1)
    # the figures quoted in the text after Proposition 12
    ex = [(L, p_bad_float(1024, 768, L), D_float(1024, 768, 1, L)) for L in (70, 100)]
    assert 1.05 < ex[0][2]/ex[0][1] < 1.07 and ex[1][2]/ex[1][1] < 1.01, ex          # ~6 % at P~0.2, <1 % once P <= 0.05
    from fill_law import R_refusal
    cross = D_float(1024, 768, 1, 259)/R_refusal(1024, 768+1, 259)
    assert 60 < cross < 80, cross                                                      # union bound wins for the first ~70 pushes
    walks = [D_float(256, lo, hi-lo, L) for (L, lo, hi) in [(45, 150, 160), (55, 140, 175), (60, 100, 190)]]
    assert 0.55 < walks[0] < 0.65 and walks[1] == 1.0 and walks[2] == 1.0, walks      # wide-band walks of the tree table
    # (ii) Monte Carlo of V_s against D_s at m=1024, load 3/4
    m, n, L = 1024, 768, 80
    S = [1, 2, 3, 4, 6]; trials = 6000
    mc = mc_V(m, n, L, S, trials)
    rows = []
    for s in S:
        d = D_float(m, n, s, L); se = (mc[s]*(1-mc[s])/trials)**0.5
        assert mc[s] <= d + 3*se + 1e-9, ("MC above the bound", s, mc[s], d)
        if s <= 3: assert d <= 1.35*mc[s] + 3*se, ("bound far above MC", s, mc[s], d)
        rows.append((s, mc[s], d))
        print("   m=%d n=%d L=%d s=%d: Monte Carlo V=%.4f (se %.4f)  D=%.4f" % (m, n, L, s, mc[s], se, d), flush=True)
    dd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
    with open(os.path.join(dd, "tab_bandmc.tex"), "w") as f:
        f.write("\\begin{tabular}{@{}rrr@{}}\n\\toprule\n$s$ & simulated $V_s$ & bound $D_s$ \\\\\n\\midrule\n" +
                "\n".join("%d & %.3f & %.3f \\\\" % r for r in rows) + "\n\\bottomrule\n\\end{tabular}\n")
    return rows

def design_band(alpha=0.75, sizes=(1024, 4096), epss=(1e-2, 1e-6), Ss=(1, 2, 4, 8)):
    from sustain_law import design_sustain
    out = {}; lines = []
    for m in sizes:
        n = int(alpha*m)
        for eps in epss:
            vals = [smallest_L(m, n, s, eps) for s in Ss]
            out[(m, eps)] = vals
            lines.append("%d & %s & %s \\\\" % (m, ("$10^{%d}$" % round(math.log10(eps)*-1) if False else "$10^{-%d}$" % round(-math.log10(eps))), " & ".join(str(v) for v in vals)))
            print("   m=%d eps=%g: L(s=%s) = %s" % (m, eps, list(Ss), vals), flush=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
    with open(os.path.join(d, "tab_band.tex"), "w") as f:
        f.write("\\begin{tabular}{@{}rr" + "r"*len(Ss) + "@{}}\n\\toprule\n$m$ & $\\varepsilon$ & " + " & ".join("$s=%d$" % s for s in Ss) + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
    return out

if __name__ == "__main__":
    test_small()
    test_mid()
    large_checks()
    design_band()
