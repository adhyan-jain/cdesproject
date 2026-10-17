"""Trajectory-level law: probability that a fill of n pushes into a ring of m cells (probe limit L) has no refusal.

Decomposition (cut the ring at its k = m-n empty cells; blocks are independent lines):
    A(0) = 1,  A(j) = sum_{s=1}^{j} C(j-1,s-1) A(s-1) A(j-s) min(L,s)         (line, all j cells filled, displacement < L)
    P_fill(m,n,L) = n! m^{-n} (m/k) [z^n] Phi(z)^k,   Phi(z) = sum_j A(j) z^j / j!.
Equivalent: the A(j) count the l-interval parking functions with l = L-1 (Colaric-DeMori-Fox; Aguilar-Fraga et al.);
the block decomposition is that of Alharbi-Banderier-Bouillaguet (AofA 2026).  Checked against brute force below.
"""
import itertools, math, sys
from fractions import Fraction as Fr

def line_counts(J, L):
    A = [1]
    for j in range(1, J+1):
        A.append(sum(math.comb(j-1, s-1)*A[s-1]*A[j-s]*min(L, s) for s in range(1, j+1)))
    return A

def fill_prob_exact(m, n, L):
    k = m-n; assert k >= 1
    A = line_counts(n, L); phi = [Fr(A[j], math.factorial(j)) for j in range(n+1)]
    g = [Fr(1)]
    for j in range(1, n+1):                                  # coefficients of phi^k
        g.append(sum((k*i-(j-i))*phi[i]*g[j-i] for i in range(1, j+1))/j)
    return Fr(math.factorial(n), m**n)*Fr(m, k)*g[n]

def fill_prob_float(m, n, L):
    """Same quantity in floating point with the scaling phi_j e^{-j} (no overflow); returns log-safe float."""
    k = m-n; A = [1]; 
    # A(j)/j! scaled by e^{-j}, computed from the recursion in the scaled variables
    lf = [math.lgamma(j+1) for j in range(n+1)]
    f = [1.0]                                                  # f_j = A(j)/j! * e^{-j}
    for j in range(1, n+1):
        # A(j)/j! = (1/j) sum_s min(L,s) * [A(s-1)/(s-1)!] [A(j-s)/(j-s)!]   (from C(j-1,s-1)/j!)
        t = 0.0
        for s in range(1, j+1): t += min(L, s)*f[s-1]*f[j-s]
        f.append(t/j*math.exp(-1.0))
    g = [1.0]
    for j in range(1, n+1):
        g.append(sum((k*i-(j-i))*f[i]*g[j-i] for i in range(1, j+1))/j)
    logP = lf[n] - n*math.log(m) + n + math.log(m/k) + math.log(g[n]) if g[n] > 0 else float("-inf")
    return math.exp(logP)

def fill_prob_dec(m, n, L, prec=60):
    """Same quantity in 60-digit decimals, using phi_j = A(j)/j! directly:
    phi_j = (1/j) sum_s min(L,s) phi_{s-1} phi_{j-s}   (no overflow, no big integers)."""
    from decimal import Decimal, getcontext
    getcontext().prec = prec
    k = m-n
    phi = [Decimal(1)]
    for j in range(1, n+1):
        phi.append(sum(min(L, s)*phi[s-1]*phi[j-s] for s in range(1, j+1))/j)
    g = [Decimal(1)]
    for j in range(1, n+1):
        g.append(sum((k*i-(j-i))*phi[i]*g[j-i] for i in range(1, j+1))/j)
    fact = Decimal(1)
    for j in range(1, n+1): fact *= j
    return fact/(Decimal(m)**n)*(Decimal(m)/k)*g[n]

def brute(m, n, L):
    ok = tot = 0
    for h in itertools.product(range(m), repeat=n):
        occ = [0]*m; good = True
        for hi in h:
            d = 0; c = hi
            while occ[c]: c = (c+1) % m; d += 1
            if d >= L: good = False; break
            occ[c] = 1
        ok += good; tot += 1
    return Fr(ok, tot)

def series_closed_form(L, N):
    """Phi(z) = e^{-Q}/(1 - L int_0^z e^{-Q}),  Q(z) = sum_{i=0}^{L-2} (L-1-i) Phi_i z^{i+1}/(i+1),
    Phi_i = (i+1)^{i-1}/i! for i <= L-2 (parking functions): Taylor coefficients up to z^N, exact."""
    Q = [Fr(0)]*(N+2)
    for i in range(0, L-1):
        if i+1 <= N+1: Q[i+1] += Fr(L-1-i)*Fr(i+1)**(i-1)/math.factorial(i)/(i+1)
    # e^{-Q}: E' = -Q' E
    E = [Fr(1)]
    for j in range(1, N+2):
        E.append(-sum(i*Q[i]*E[j-i] for i in range(1, j+1))/j)
    I = [Fr(0)] + [L*E[j-1]/j for j in range(1, N+2)]        # L * int e^{-Q}
    den = [Fr(1)-I[0]] + [-I[j] for j in range(1, N+2)]      # 1 - L int e^{-Q}
    inv = [1/den[0]]
    for j in range(1, N+1):
        inv.append(-sum(den[i]*inv[j-i] for i in range(1, j+1))/den[0])
    return [sum(E[i]*inv[j-i] for i in range(j+1)) for j in range(N+1)]

def logQ(j, s): return math.log(j/s) + (s-j)*math.log(s) - math.lgamma(s-j+1)
def R_refusal(m, n, L):
    """Theorem (refusal law) as a float, via logarithms."""
    k = m-n
    if k == 1: return max(m-L, 0)/m
    lq = logQ(k, m); tot = 0.0
    for g in range(L+1, n+2):
        if m-g < k-1: break
        lp = (g-1)*math.log(g) - math.lgamma(g+1) + logQ(k-1, m-g) - lq
        tot += (g-L)*math.exp(lp)
    return k/m*tot

def smallest(pred, lo, hi):
    while lo < hi:
        mid = (lo+hi)//2
        if pred(mid): hi = mid
        else: lo = mid+1
    return lo

def design_fill(sizes=(256, 1024, 4096), alpha=0.75, epss=(1e-2, 1e-4, 1e-6)):
    import os
    rows = []; out = {}
    for m in sizes:
        n = int(alpha*m)
        for eps in epss:
            sumR = lambda L: sum(R_refusal(m, t, L) for t in range(n))
            Ls = smallest(lambda L: sumR(L) <= eps, 2, m)
            Lu = smallest(lambda L: n*R_refusal(m, n-1, L) <= eps, 2, m)
            Le = smallest(lambda L: 1-float(fill_prob_dec(m, n, L)) <= eps, max(2, Ls-40), Ls)
            ratio = (1-float(fill_prob_dec(m, n, Le)))/sumR(Le)
            rows.append("%d & %g & %d & %d & %d & %.2f \\\\" % (m, eps, Le, Ls, Lu, ratio))
            out[(m, eps)] = (Le, Ls, Lu, ratio)
            print("   m=%d eps=%g  exact L=%d  sum_t R_t L=%d  N*R(n) L=%d   P_exact/Lambda at exact L = %.2f" % (m, eps, Le, Ls, Lu, ratio), flush=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
    with open(os.path.join(d, "tab_fill.tex"), "w") as f:
        f.write("\\begin{tabular}{@{}rrrrrr@{}}\n\\toprule\n$m$ & $\\varepsilon'$ & exact & $\\sum_t R_t$ & $N R_{\\max}$ & $\\Prob/\\Lambda$ \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    Le, Ls, Lu, ratio = out[(4096, 1e-6)]
    with open(os.path.join(d, "fill_summary.tex"), "w") as f:
        f.write("\\newcommand{\\FillExactBig}{%d}\n\\newcommand{\\FillUnionBig}{%d}\n\\newcommand{\\FillSaving}{%d}\n" % (Le, Lu, round(100*(Lu-Le)/Lu)))
    return out

if __name__ == "__main__":
    cnt = 0
    for m in range(2, 9):
        for n in range(1, m):
            if m**n > 300000: continue
            for L in (1, 2, 3, 4, 6):
                assert brute(m, n, L) == fill_prob_exact(m, n, L), (m, n, L); cnt += 1
    print("fill law == brute force over every home sequence: %d (m,n,L) cases, 0 mismatches" % cnt)
    for (m, n, L) in [(9, 7, 3), (10, 7, 4), (12, 9, 5)]:
        assert abs(float(fill_prob_exact(m, n, L)) - fill_prob_float(m, n, L)) < 1e-9
    for (m, n, L) in [(40, 30, 12), (64, 48, 20)]:
        assert abs(float(fill_prob_exact(m, n, L)) - float(fill_prob_dec(m, n, L))) < 1e-12
    print("float and decimal evaluations agree with the exact one")
    cf = 0
    for L in (1, 2, 3, 4, 5, 7):
        A = line_counts(12, L); ser = series_closed_form(L, 12)
        assert all(ser[j] == Fr(A[j], math.factorial(j)) for j in range(13)), L; cf += 1
    print("closed form Phi = e^{-Q}/(1 - L int e^{-Q}) equals the recursion to degree 12 for L = 1,2,3,4,5,7")
    # the probability of no refusal never exceeds 1 - (Lambda - pair terms); Lambda is an upper bound on refusal prob
    for (m, n, L) in [(64, 48, 20), (128, 96, 30)]:
        lam = sum(R_refusal(m, t, L) for t in range(n)); pe = 1-float(fill_prob_dec(m, n, L))
        assert pe <= lam + 1e-12 and pe >= lam/2 - 1e-12
    print("1 - P_fill <= sum_t R_t (union bound) on test cases")
    design_fill()
    print("fill_law: all checks passed")
