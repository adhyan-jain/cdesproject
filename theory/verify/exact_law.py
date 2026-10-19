"""Exact refusal law for probe-limited linear probing on a ring, and its brute-force check.

Ring of m cells, n = m-k keys with independent uniform home cells, linear probing.
A new key with an independent uniform home is refused at probe limit L iff the L cells
starting at its home are all occupied.  Claim (Theorem 4 of the paper):

    P_refuse(m,n,L) = (k/m) * sum_{g>L} (g-L) * P(gamma_1 = g | gamma_1+...+gamma_k = m)

where gamma_i are i.i.d. Borel variables; the conditional law does not depend on the Borel
parameter:   P(gamma_1=g | S_k=m) = B(g) Q_{k-1}(m-g) / Q_k(m),
B(g) = g^{g-1}/g!,  Q_j(s) = (j/s) s^{s-j}/(s-j)!  (Borel-Tanner, parameter-free form), Q_0(s)=[s==0].
"""
from fractions import Fraction
from math import factorial
import itertools, sys

def B(g):  return Fraction(g**(g-1), factorial(g))
def Q(j, s):
    if j == 0: return Fraction(1 if s == 0 else 0)
    if s < j: return Fraction(0)
    return Fraction(j, s) * Fraction(s**(s-j), factorial(s-j))

def refuse_exact(m, n, L):
    k = m - n
    assert k >= 1
    tot = Fraction(0)
    for g in range(L+1, m-k+2):          # a gap has g cells: 1 empty + g-1 occupied, so g <= m-k+1
        p = B(g) * Q(k-1, m-g) / Q(k, m)
        tot += (g - L) * p
    return Fraction(k, m) * tot

def refuse_brute(m, n, L):
    hits = 0
    for homes in itertools.product(range(m), repeat=n):
        occ = [False]*m
        for h in homes:
            i = h
            while occ[i]: i = (i+1) % m
            occ[i] = True
        for h in range(m):
            if all(occ[(h+t) % m] for t in range(L)): hits += 1
    return Fraction(hits, m**n * m)

if __name__ == "__main__":
    bad = 0; cnt = 0
    for m in range(2, 10):
        for n in range(0, m):
            if m**n > 2_000_000: continue
            for L in range(1, m+1):
                a, b = refuse_exact(m, n, L), refuse_brute(m, n, L)
                cnt += 1
                if a != b: bad += 1; print("MISMATCH", m, n, L, a, b)
    print(f"checked {cnt} (m,n,L) triples exactly (rational arithmetic): {bad} mismatches")
    import os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "exact_summary.tex"), "w").write(f"\\newcommand{{\\ExactTriples}}{{{cnt}}}\n\\newcommand{{\\ExactMismatch}}{{{bad}}}\n")
    sys.exit(1 if bad else 0)
