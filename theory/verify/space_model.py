"""Exact word accounting of single-buffer scoped tables on the stored compiler traces.

Each design is a deterministic layout rule; the minimum fixed buffer is the peak of the words in
use (plus the 64-byte bisection resolution used by benchmarks/budget_main.cpp).  The two designs
that exist in the repository (STRATA packed/raw, arena_chain) are checked against the measured
minima in results/raw/*/budget.csv; the others are layout rules only (no code was written).

Designs (words per live declaration, name of l bytes, wc = ceil(l/4), wp = ceil(l/5)):
  arena_chain  chain table, one entry per declaration  [next|hash|value|len,depth|name] = 4+wc ; buckets b >= live decls
  chain_nohash same, stored hash removed                                                  = 3+wc
  oa_decl      open-addressed index (<=3/4 load, one slot per distinct visible name) over
               one entry per declaration [prev|value|meta|name]                           = 3+wc
  strata_raw   interned: record [value|meta|name] once per visible name, undo word 1,
               shadow entry 3 words (no name)                                              = (2+wc)+1 fresh, 3 shadow
  strata       as strata_raw with names of [A-Za-z0-9_] packed 5 per word (wp)
"""
import gzip, os, sys, csv, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
PACK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

def read_units(path):
    """-> list of units, each a list of ('E',) ('X',) ('D',name) ops; lookups and G are irrelevant to space."""
    units, cur = [], []
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line: continue
            sp = line.find(" "); tag = line if sp < 0 else line[:sp]; arg = "" if sp < 0 else line[sp+1:]
            if tag == "U":
                if cur: units.append(cur)
                cur = []
            elif tag == "E": cur.append(("E", None))
            elif tag == "X": cur.append(("X", None))
            elif tag == "D":
                e = arg.find(" ")
                if e >= 0: arg = arg[:e]
                if arg and len(arg) <= 255: cur.append(("D", arg))
    if cur: units.append(cur)
    return units

def words4(l): return (l + 3) // 4
def words5(l): return (l + 4) // 5
def is_packable(nm): return all(c in PACK for c in nm)

def simulate(unit, design):
    """Peak words in use over one translation unit."""
    vis = {}                    # name -> list of depths of live declarations (innermost last)
    scope_names = [[]]          # per scope: names declared (in order), for exit
    depth = 0
    live = 0                    # live declarations
    idx = 16; nb = 16           # index slots / buckets
    itop = 1; undo = 0; etop = 1; marks = 0
    peak = 0
    def used():
        if design == "arena_chain" or design == "chain_nohash": return nb + etop + marks
        if design == "oa_decl": return idx + etop + marks
        return idx + itop + undo
    for op, nm in unit:
        if op == "E":
            depth += 1; scope_names.append([])
            if design in ("arena_chain", "chain_nohash", "oa_decl"): marks += 1
            else: undo += 2
        elif op == "X":
            if depth == 0: continue
            for n in reversed(scope_names.pop()):
                st = vis[n]; st.pop()
                l = len(n)
                if design == "arena_chain": etop -= 4 + words4(l)
                elif design == "chain_nohash" or design == "oa_decl": etop -= 3 + words4(l)
                else:
                    if st: undo -= 3
                    else:
                        undo -= 1
                        itop -= 2 + (words5(l) if design == "strata" and is_packable(n) else words4(l))
                if not st: del vis[n]
                live -= 1
            if design in ("arena_chain", "chain_nohash", "oa_decl"): marks -= 1
            else: undo -= 2
            depth -= 1
        else:
            st = vis.get(nm)
            if st and st[-1] == depth: continue                # redeclared in this scope
            l = len(nm)
            if design == "arena_chain": etop += 4 + words4(l)
            elif design == "chain_nohash": etop += 3 + words4(l)
            elif design == "oa_decl": etop += 3 + words4(l)
            else:
                if st: undo += 3
                else:
                    undo += 1
                    itop += 2 + (words5(l) if design == "strata" and is_packable(nm) else words4(l))
            if st is None: vis[nm] = [depth]
            else: st.append(depth)
            scope_names[-1].append(nm)
            live += 1
            nvis = len(vis)
            if design in ("arena_chain", "chain_nohash"):
                while live > nb: nb *= 2                      # buckets double when load would exceed 1
            else:
                while nvis * 4 > idx * 3: idx *= 2             # index doubles above 3/4
            if design == "oa_decl": pass
        u = used()
        if u > peak: peak = u
    return peak

def trace_peak(units, design):
    return max(simulate(u, design) for u in units)

def bytes_min(words):
    b = max(words, 32) * 4
    return -(-b // 64) * 64         # bisection resolution of the repository's tool

if __name__ == "__main__":
    run = sys.argv[1] if len(sys.argv) > 1 else "20261013-143828-paper"
    meas = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "results/raw", run, "budget.csv"))):
        if r["budget_factor"] == "1.00": meas[(r["trace"], r["names"])] = int(r["min_buffer_bytes"])
    projects = ["zlib","cjson","littlefs","freertos","lua","mbedtls","tinycc","sqlite"]
    designs = ["arena_chain","chain_nohash","oa_decl","strata_raw","strata"]
    out = {}
    print(f"{'trace':9s}" + "".join(f"{d:>13s}" for d in designs) + "   | measured: arena strata_raw strata | model==measured?")
    for p in projects:
        units = read_units(os.path.join(ROOT, "workloads/traces", p + ".trace.gz"))
        res = {d: bytes_min(trace_peak(units, d)) for d in designs}
        out[p] = res
        m = (meas[(p, "arena_chain")], meas[(p, "raw")], meas[(p, "packed")])
        ok = (res["arena_chain"], res["strata_raw"], res["strata"]) == m
        print(f"{p:9s}" + "".join(f"{res[d]:13d}" for d in designs) + f"   | {m[0]:6d} {m[1]:6d} {m[2]:6d} | {'yes' if ok else 'NO'}")
    import json; json.dump(out, open(os.path.join(HERE, "space_ladder.json"), "w"), indent=1)
