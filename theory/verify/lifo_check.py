"""Checks of the stack-discipline results by exhaustive enumeration / randomized testing.

A. Undo theorem (Thm 1): for several non-reordering open-addressing insertion rules, interleaved
   push/pop (pop = clear the newest live key's cell) leaves a table identical to the insertion-only table
   of the live sequence.
B. Exactness (Thm 2): linear probing on a ring, lookups stop at an empty cell.  Over ALL home assignments and
   ALL deletion orders of n keys, clearing is safe for every assignment only for the reverse insertion order.
C. Orphans (Prop 3): clearing a live key x makes unreachable exactly the live keys whose probe path crosses
   x's cell; summed over x this equals the sum of displacements (exact identity, all assignments).
"""
import itertools, random, sys, math

# ---------- A ----------
def probe_linear(h, m, i):      return (h + i) % m
def probe_quad(h, m, i):        return (h + i*(i+1)//2) % m                    # m power of two: permutation
def make_double(step):          return lambda h, m, i: (h + i*step) % m        # odd step, m power of two
def probe_perm(key_seed):       # uniform probing: a fixed random permutation of cells per key
    def f(h, m, i, _c={}):
        k = (key_seed, h)
        if k not in _c:
            r = random.Random(hash(k)); p = list(range(m)); r.shuffle(p); _c[k] = p
        return _c[k][i]
    return f

def insert_greedy(occ, key, m, probe):
    for i in range(m):
        c = probe(key['h'], m, i)
        if occ[c] is None: return c
    return None

def insert_window(occ, key, m, probe):
    """Non-greedy, occupancy-determined: among the first 3 free cells on the probe path choose the one
    with the fewest occupied cells among its two linear successors (a power-of-d-choices flavour)."""
    free = []
    for i in range(m):
        c = probe(key['h'], m, i)
        if occ[c] is None:
            free.append(c)
            if len(free) == 3: break
    if not free: return None
    return min(free, key=lambda c: (occ[(c+1) % m] is not None) + (occ[(c+2) % m] is not None))

def run_A(trials=3000):
    rng = random.Random(7); m = 16; bad = 0; checks = 0
    schemes = [("linear", insert_greedy, probe_linear), ("quadratic", insert_greedy, probe_quad),
               ("double-hash", insert_greedy, make_double(5)), ("uniform-probing", insert_greedy, probe_perm(1)),
               ("window-choice (non-greedy)", insert_window, probe_linear)]
    for name, ins, pr in schemes:
        b = 0
        for t in range(trials):
            occ = [None]*m; stack = []        # stack of (key, cell)
            for step in range(rng.randint(5, 60)):
                if stack and rng.random() < 0.45:
                    key, c = stack.pop(); occ[c] = None                      # pop = clear
                else:
                    key = {'id': rng.getrandbits(40), 'h': rng.randrange(m)}
                    c = ins(occ, key, m, pr)
                    if c is None: continue                                    # refusal changes nothing
                    occ[c] = key['id']; stack.append((key, c))
                ref = [None]*m
                for k2, _ in stack:
                    c2 = ins(ref, k2, m, pr); ref[c2] = k2['id']
                checks += 1
                if ref != occ: b += 1
        print(f"A  {name:28s} {'OK ' if b == 0 else 'FAIL'} ({trials} sequences)")
        bad += b
    return bad, checks

# ---------- B ----------
def lookup_ok(occ, homes, key_cell, m, probe):
    """Does a lookup scan the key's probe sequence and reach the key before an empty cell?"""
    for key, h in homes.items():
        if key not in key_cell: continue
        i = 0
        while True:
            c = probe(h, m, i)
            if occ[c] == key: break
            if occ[c] is None: return False
            i += 1
            if i > m: return False
    return True

def run_B():
    """Exactness: every assignment of homes x every deletion order, for greedy first-empty schemes.
    Linear probing (m = 4,5,6, all n <= m) and quadratic probing (m = 4,8, n <= 4)."""
    bad = 0; cases = 0
    plans = [("linear", probe_linear, [(4, range(2, 5)), (5, range(2, 6)), (6, range(2, 7))]),
             ("quadratic", probe_quad, [(4, range(2, 5)), (8, range(2, 5))])]
    for pname, probe, ms in plans:
        for m, ns in ms:
            for n in ns:
                broken_count = {}
                for sigma in itertools.permutations(range(n)):
                    broken = 0
                    for h in itertools.product(range(m), repeat=n):
                        occ = [None]*m; cell = {}
                        for k in range(n):
                            i = 0
                            while occ[probe(h[k], m, i)] is not None: i += 1
                            c = probe(h[k], m, i); occ[c] = k; cell[k] = c
                        homes = {k: h[k] for k in range(n)}
                        ok = True; live = dict(cell)
                        for k in sigma:
                            occ[live.pop(k)] = None
                            if not lookup_ok(occ, homes, live, m, probe): ok = False; break
                        broken += (not ok)
                    broken_count[sigma] = broken
                safe = [s_ for s_, b_ in broken_count.items() if b_ == 0]
                ok = safe == [tuple(reversed(range(n)))]
                bad += (not ok); cases += 1
                fifo = broken_count[tuple(range(n))]
                print(f"B  {pname:9s} m={m} n={n}: orders safe for every assignment = {len(safe)} "
                      f"(reverse insertion order only: {ok}); FIFO order breaks {fifo}/{m**n} assignments")
    return bad, cases

# ---------- C ----------
def run_C():
    bad = 0
    for (m, n) in [(5, 3), (6, 4), (7, 5), (8, 6)]:
        for h in itertools.product(range(m), repeat=n):
            occ = [None]*m; cell = {}
            for k in range(n):
                c = h[k]
                while occ[c] is not None: c = (c+1) % m
                occ[c] = k; cell[k] = c
            disp = sum((cell[k] - h[k]) % m for k in range(n))
            orphans = 0
            for x in range(n):
                occ2 = list(occ); occ2[cell[x]] = None
                live = {k: cell[k] for k in range(n) if k != x}
                homes = {k: h[k] for k in range(n)}
                for k in live:
                    c = h[k]; found = False
                    while occ2[c] is not None:
                        if occ2[c] == k: found = True; break
                        c = (c+1) % m
                    orphans += (not found)
            if orphans != disp: bad += 1
    print(f"C  orphan-sum == displacement-sum identity: {'OK' if bad == 0 else 'FAIL'}")
    # mean displacement at scale vs Knuth: (C_succ - 1) = (1/(1-a) - 1)/2
    rng = random.Random(3); m = 1 << 16
    for a in (0.5, 0.75):
        n = int(a*m); occ = bytearray(m); tot = 0
        for _ in range(n):
            h = rng.randrange(m); c = h
            while occ[c]: c = (c+1) % m
            occ[c] = 1; tot += (c - h) % m
        print(f"C  load {a}: mean displacement {tot/n:.3f}   Knuth a/(2(1-a)) = {a/(2*(1-a)):.3f}")
    return bad

if __name__ == "__main__":
    ba, ck = run_A(); bb, bcases = run_B(); bc = run_C()
    import os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "lifo_summary.tex"), "w").write(
        f"\\newcommand{{\\UndoComparisons}}{{{ck:,}}}\n".replace(",", "\\,") +
        f"\\newcommand{{\\UndoFailures}}{{{ba}}}\n\\newcommand{{\\ExactnessFailures}}{{{bb}}}\n\\newcommand{{\\ExactnessCases}}{{{bcases}}}\n\\newcommand{{\\OrphanFailures}}{{{bc}}}\n")
    print(f"A: {ck} state comparisons, {ba} failures;  B failures: {bb};  C failures: {bc}")
    sys.exit(1 if (ba or bb or bc) else 0)
