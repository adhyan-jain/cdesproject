"""Checks of two refinements of the exactness and orphan results.

P. Safe deletion orders (Theorem "Safe orders"): for ONE assignment of homes, a deletion order is clear-safe
   iff it is a linear extension of the dependency order  y < x  :<=>  cell(x) lies strictly inside the probe
   path of y before cell(y).  Checked against brute-force simulation of every deletion order, every assignment.
O. Orphan law (Proposition "Orphan law"): the number orph(x) of keys orphaned by clearing x has, for a key
   chosen uniformly among the live keys, an explicit finite-size law (Lukasiewicz-path weights) and, as
   n/m -> alpha, the law of (Y - 1 | Y >= 1) for the stationary M/D/1 chain Y.  Checked by enumeration of every
   home sequence (exact rational arithmetic) and against the closed-form M/D/1 probabilities.
"""
import itertools, math, os, sys
from decimal import Decimal, getcontext
from fractions import Fraction as Fr

def build(h, m):
    occ = [None]*m; cell = []
    for i, hi in enumerate(h):
        c = hi
        while occ[c] is not None: c = (c+1) % m
        occ[c] = i; cell.append(c)
    return cell

def path(h, cell, m, i):            # cells strictly before key i's own cell on its probe path
    out = []; c = h[i]
    while c != cell[i]: out.append(c); c = (c+1) % m
    return out

def safe(h, cell, m, order):
    n = len(h); occ = {cell[i]: i for i in range(n)}; alive = set(range(n))
    for x in order:
        del occ[cell[x]]; alive.discard(x)
        for y in alive:
            c = h[y]
            while True:
                if c not in occ: return False
                if occ[c] == y: break
                c = (c+1) % m
    return True

def check_P(maxm=5):
    tot = 0
    for m in range(2, maxm+1):
        for n in range(1, m+1):
            for h in itertools.product(range(m), repeat=n):
                cell = build(h, m)
                owner = {cell[i]: i for i in range(n)}
                # dependency: y before x
                before = {x: set() for x in range(n)}      # before[x] = keys that must be deleted before x
                for y in range(n):
                    for c in path(h, cell, m, y): before[owner[c]].add(y)
                for order in itertools.permutations(range(n)):
                    pos = {k: i for i, k in enumerate(order)}
                    ext = all(pos[y] < pos[x] for x in range(n) for y in before[x])
                    s = safe(h, cell, m, order)
                    if ext != s: print("MISMATCH", m, n, h, order, ext, s); sys.exit(1)
                    tot += 1
    print("P  safe orders == linear extensions of the dependency order: %d (assignment, order) pairs, 0 mismatches" % tot)
    return tot

# ---- O ----
def orph_counts(h, m):
    n = len(h); cell = build(h, m); owner = {cell[i]: i for i in range(n)}
    o = [0]*n
    for y in range(n):
        for c in path(h, cell, m, y): o[owner[c]] += 1
    return o

def enum_law(m, n):
    """E[# keys with orph = j] exactly, by enumeration of all m^n home sequences."""
    cnt = {}
    for h in itertools.product(range(m), repeat=n):
        for v in orph_counts(h, m): cnt[v] = cnt.get(v, 0) + 1
    return {j: Fr(c, m**n) for j, c in cnt.items()}

def B(g): return Fr(g**(g-1), math.factorial(g))
def Q(j, s):
    if j == 0: return Fr(int(s == 0))
    if s < j: return Fr(0)
    return Fr(j, s) * Fr(s**(s-j), math.factorial(s-j))

def F_table(G):
    """F[u][h]: weight prod 1/y! of walks Z_0=0 -> Z_u=h, steps y-1 (y>=0), Z_t>=0 for t<=u."""
    F = [dict() for _ in range(G+1)]; F[0][0] = Fr(1)
    for u in range(G):
        for h, w in F[u].items():
            for y in range(0, G+2):
                h2 = h + y - 1
                if h2 < 0 or h2 > G: continue
                F[u+1][h2] = F[u+1].get(h2, 0) + w / math.factorial(y)
    return F

def finite_law(m, n):
    """E[# keys with orph = j] from the block decomposition."""
    k = m - n; assert k >= 1
    F = F_table(m); res = {}
    for g in range(2, n+2):
        for u in range(1, g):
            for h, w in F[u].items():
                if g-u >= h+1:
                    res[h] = res.get(h, 0) + Fr(k) * w * Q(h+1, g-u) * Q(k-1, m-g) / Q(k, m)
    return res

def check_O():
    for m, n in [(3,2),(4,3),(5,3),(5,4),(6,4),(6,5),(7,5),(7,6),(8,5),(8,7)]:
        a = enum_law(m, n); b = finite_law(m, n)
        a = {j: v for j, v in a.items() if v}; b = {j: v for j, v in b.items() if v}
        if a != b: print("MISMATCH O", m, n, a, b); sys.exit(1)
        assert sum(a.values()) == n
    print("O  finite-size orphan law == enumeration of every home sequence (10 settings, exact)")


def mdl_pmf(alpha, J, prec=80):
    """Stationary law of Y = (Y' - 1)^+ + A, A ~ Poisson(alpha) (M/D/1 in discrete time), by the exact
    balance recursion in high-precision decimals; pi_0 = 1 - alpha."""
    getcontext().prec = prec
    a = Decimal(alpha); ea = (-a).exp()
    A = [ea]
    for j in range(1, J+2): A.append(A[-1]*a/j)
    pi = [1 - a]
    pi.append(pi[0]*(1/A[0] - 1))
    for j in range(1, J):
        s = pi[0]*A[j] + sum(pi[i]*A[j-i+1] for i in range(1, j+1))
        pi.append((pi[j] - s)/A[0])
    return pi

def check_R_identity():
    """Cor 8(b) without uniform integrability: R = (k/m)[ m/k - sum_{g<=L} g pi_g - L (1 - sum_{g<=L} pi_g) ]."""
    cnt = 0
    for m in (5, 9, 14, 23, 40):
        for k in (1, 2, 3, max(2, m//4), m//2):
            if not 1 <= k < m: continue
            n = m - k; qk = Q(k, m)
            pi = {g: B(g)*Q(k-1, m-g)/qk for g in range(1, n+2)}
            assert sum(pi.values()) == 1 and sum(g*p for g, p in pi.items()) == Fr(m, k)
            for L in (1, 2, 3, 7, 12):
                direct = Fr(k, m)*sum((g-L)*p for g, p in pi.items() if g > L)
                s1 = sum(g*p for g, p in pi.items() if g <= L); s0 = sum(p for g, p in pi.items() if g <= L)
                viaid = Fr(k, m)*(Fr(m, k) - s1 - L*(1 - s0))
                assert direct == viaid; cnt += 1
    print("O  R_m(n,L) = (k/m)[m/k - sum_{g<=L} g pi_g - L(1 - sum_{g<=L} pi_g)] (finite sums only): %d exact cases" % cnt)

def Qa(j, s, a):
    if j == 0: return 1.0 if s == 0 else 0.0
    if s < j: return 0.0
    return j/s*math.exp(-a*s + (s-j)*math.log(a*s) - math.lgamma(s-j+1))

def finite_float(m, n, hmax):
    a = n/m; k = m-n
    w = [math.exp(-a + y*math.log(a) - math.lgamma(y+1)) for y in range(m+1)]
    F = [[0.0]*(m+1) for _ in range(m+1)]; F[0][0] = 1.0
    for u in range(m):
        Fu = F[u]; Fn = F[u+1]
        for h in range(m+1):
            x = Fu[h]
            if x == 0.0: continue
            for y in range(max(0, 1-h), min(m, m+1-h)+1):
                if h+y-1 > m: break
                Fn[h+y-1] += x*w[y]
    Qk = Qa(k, m, a); out = []
    for h in range(hmax+1):
        tot = 0.0
        for g in range(2, n+2):
            t = 0.0
            for u in range(1, g):
                if g-u >= h+1: t += F[u][h]*Qa(h+1, g-u, a)
            tot += t*Qa(k-1, m-g, a)
        out.append(k*tot/Qk/n)
    return out

def check_limit(write=True):
    rows = []; J = 3
    for alpha in (Fr(1, 2), Fr(3, 4)):
        pi = mdl_pmf(alpha.numerator/Decimal(alpha.denominator), 2500)
        a = float(alpha)
        tot = sum(pi); assert abs(tot-1) < Decimal("1e-12"), tot
        mean = sum((j-1)*pi[j] for j in range(1, len(pi)))/Decimal(a)
        assert abs(float(mean) - a/(2*(1-a))) < 1e-6, (float(mean), a/(2*(1-a)))
        lim = [float(pi[j+1])/a for j in range(J+1)]
        assert abs(lim[0] - (1-a)*(math.exp(a)-1)/a) < 1e-12
        errs = []
        for m in (64, 128, 256):
            fin = finite_float(m, int(a*m), J)
            errs.append(max(abs(f-l) for f, l in zip(fin, lim)))
            if a == 0.75: ZERO75[m] = fin[0]
        assert errs[0] > errs[1] > errs[2] and errs[2] < 0.02, errs
        rows.append((a, lim, errs))
    print("O  M/D/1 pmf: sums to 1, mean orphan count = alpha/(2(1-alpha)), P(orph=0) = (1-alpha)(e^alpha-1)/alpha")
    print("O  sup-distance of the finite-size law (m = 64, 128, 256) to the limit, j<=3:",
          [(a, [round(e, 4) for e in errs]) for a, _, errs in rows])
    if write:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
        # limit law for a few loads
        lines = []
        for alpha in (Fr(1, 4), Fr(1, 2), Fr(3, 4), Fr(9, 10)):
            pi = mdl_pmf(alpha.numerator/Decimal(alpha.denominator), 2500 if alpha > Fr(8, 10) else 800)
            a = float(alpha); lim = [float(pi[j+1])/a for j in range(5)]
            freeall = lim[0]
            lines.append("$%s$ & %s & %s \\\\" % (("%g" % a), " & ".join("%.3f" % x for x in lim), "%.3f" % (a/(2*(1-a)))))
        with open(os.path.join(d, "tab_orphan.tex"), "w") as f:
            f.write("\\begin{tabular}{@{}lrrrrrr@{}}\n\\toprule\n$\\alpha$ & $j{=}0$ & $1$ & $2$ & $3$ & $4$ & mean \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
        with open(os.path.join(d, "orphan_summary.tex"), "w") as f:
            f.write("\\newcommand{\\SafeOrderPairs}{%s}\n" % SAFE_PAIRS)
            f.write("\\newcommand{\\OrphZeroSmall}{%.3f}\n\\newcommand{\\OrphZeroBig}{%.3f}\n" % (ZERO75[128], ZERO75[256]))
        print("O  wrote tab_orphan.tex, orphan_summary.tex")

SAFE_PAIRS = "0"
ZERO75 = {}
if __name__ == "__main__":
    check_P_count = check_P()
    SAFE_PAIRS = "{:,}".format(check_P_count).replace(",", "\\,")
    check_O(); check_R_identity(); check_limit(); print("orphan_law: all checks passed")
