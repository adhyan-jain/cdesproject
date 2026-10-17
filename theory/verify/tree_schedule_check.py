"""Re-entrant scope schedules: how loose is the union bound of Proposition 9, and is P(W>0) at the depth reached a good guide?

A push/pop schedule is a random walk of the stack depth between lo and hi (fresh names).  For each schedule the real
linear-probing process is simulated many times (fixed seeds); we report the fraction of runs with a refusal, the
union bound sum_v c_v R_m(depth(v),L) over the push-hosting nodes of the scope tree, and the exact probability P_bad
(Proposition 11) that a table at the largest depth reached has a block longer than L.
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fill_law import R_refusal
from sustain_law import p_bad_float

def schedule(rng, steps, lo, hi):
    ops = [+1]*lo; d = lo
    for _ in range(steps):
        op = -1 if d >= hi else (+1 if d <= lo else (+1 if rng.random() < 0.5 else -1))
        ops.append(op); d += op
    return ops

def simulate(m, L, ops, rng):
    occ = [0]*m; stack = []
    for op in ops:
        if op < 0:
            occ[stack.pop()] = 0; continue
        c = rng.randrange(m); d = 0
        while occ[c]:
            c = (c+1) % m; d += 1
            if d >= L: return False
        occ[c] = 1; stack.append(c)
    return True

def run(m=256, trials=2000):
    rows = []; res = []
    for (L, lo, hi, steps) in [(45, 150, 160, 2000), (55, 140, 175, 3000), (60, 100, 190, 3000)]:
        rng = random.Random(11); ops = schedule(rng, steps, lo, hi)
        nid = 0; stack = [0]; hosts = {0: 0}; depth = {0: 0}
        for op in ops:
            if op > 0:
                nid += 1; hosts[stack[-1]] += 1; stack.append(nid); hosts[nid] = 0; depth[nid] = len(stack)-1
            else: stack.pop()
        pushes = sum(1 for o in ops if o > 0)
        dmax = max(depth.values())
        union = sum(c*R_refusal(m, depth[v], L) for v, c in hosts.items() if c > 0)
        fail = sum(not simulate(m, L, ops, random.Random(1000+i)) for i in range(trials))/trials
        pb = p_bad_float(m, dmax, L)
        rows.append("%d & %d--%d & %d & %.4f & %.3f & %.4f \\\\" % (L, lo, hi, pushes, fail, union, pb))
        res.append((L, fail, union, pb))
        print("   L=%d depth %d-%d pushes=%d: refusal in %.4f of runs | union bound %.3f | P_bad(max depth %d) = %.4f" % (L, lo, hi, pushes, fail, union, dmax, pb), flush=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../paper/tables")
    with open(os.path.join(d, "tab_tree.tex"), "w") as f:
        f.write("\\begin{tabular}{@{}rrrrrr@{}}\n\\toprule\n$L$ & depth & pushes & observed & union bound & $\\Prob(W>0)$ \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    # sanity: the union bound must hold, and P_bad must be within a factor 3 of the observation in every row
    for L, fail, union, pb in res:
        assert union >= fail, (L, fail, union)
        assert fail <= 3*pb+0.01 and pb <= 3*fail+0.02, (L, fail, pb)
    print("tree_schedule_check: union bound holds; P(W>0) within a factor 3 of the observation")

if __name__ == "__main__":
    run()
