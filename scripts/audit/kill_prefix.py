"""Kill test: how much would LIFO-safe prefix sharing of packed names save?

    python3 scripts/audit/kill_prefix.py workloads/traces/cjson.trace.gz ...

Simulates STRATA's fixed-buffer layout (index + identifier stack + undo stack) on a
trace and reports the peak, with and without storing a new name as
(reference to an older live record, number of shared leading words, remaining words).
"""
import gzip, sys, re
IDENT = re.compile(r'^[A-Za-z0-9_]+$')
def words(name):
    if IDENT.match(name):
        return tuple(name[i:i+5] for i in range(0, len(name), 5))
    b = name.encode('utf-8', 'replace')
    return tuple(b[i:i+4] for i in range(0, len(b), 4))
def common(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y: break
        n += 1
    return n
def simulate(path, K):
    """K = 0: no sharing; K > 0: best of the previous K records; K < 0: best of all live records."""
    recs = []            # (name, words, stored_words)
    live = {}            # name -> [record index, declaration count]
    scopes = [[]]        # per scope: list of (name, first?)
    marks = 0
    itop, undo, idx = 1, 0, 16
    peak = (0, 0, 0, 0)
    saved_words = total_words = shared_recs = 0
    trie = {}
    def trie_add(w, sign):
        node = trie
        for x in w:
            nxt = node.setdefault(x, [0, {}])
            nxt[0] += sign
            node = nxt[1]
    def trie_best(w):
        node, n = trie, 0
        for x in w:
            nxt = node.get(x)
            if not nxt or nxt[0] <= 0: break
            n += 1; node = nxt[1]
        return n
    op = gzip.open(path, 'rt', errors='replace')
    for line in op:
        line = line.rstrip('\n')
        t = line[:1]
        if t == 'U':
            recs, live, scopes = [], {}, [[]]
            itop, undo, idx = 1, 0, 16
            trie = {}
            continue
        if t == 'E':
            scopes.append([]); undo += 2
        elif t == 'X':
            if len(scopes) == 1: continue
            for name, first in reversed(scopes.pop()):
                if first:
                    _, w, st = recs.pop()
                    itop -= 2 + st; undo -= 1
                    del live[name]
                    if K < 0: trie_add(w, -1)
                else:
                    undo -= 3
            undo -= 2
        elif t == 'D':
            name = line[2:].split(' ')[0]
            if not name or len(name) > 255: continue
            depth = len(scopes) - 1
            if name in live:
                if live[name] == depth: continue
                scopes[-1].append((name, False)); undo += 3
                prev = live[name]; live[name] = depth
                restore.setdefault(len(scopes) - 1, []).append((name, prev))
            else:
                w = words(name)
                best = 0
                if K > 0:
                    for _, cw, _ in recs[-K:]:
                        best = max(best, common(w, cw))
                elif K < 0:
                    best = trie_best(w)
                st = len(w)
                if best >= 2:
                    st = 1 + len(w) - best
                    saved_words += best - 1; shared_recs += 1
                total_words += len(w)
                recs.append((name, w, st)); itop += 2 + st; undo += 1
                live[name] = depth
                scopes[-1].append((name, True))
                if K < 0: trie_add(w, +1)
                while len(recs) * 4 > idx * 3: idx *= 2
        else:
            continue
        if t == 'X':
            for name, prev in restore.pop(len(scopes), []):
                if name in live: live[name] = prev
        tot = idx + itop + undo
        if tot > peak[0]: peak = (tot, idx, itop, undo)
    return peak, saved_words, total_words, shared_recs
restore = {}
for path in sys.argv[1:]:
    base = None
    out = []
    for K in (0, 1, 4, 16, -1):
        restore.clear()
        peak, sw, tw, sr = simulate(path, K)
        if K == 0: base = peak
        out.append(f"K={K}: peak {peak[0]*4}B ({100*(1-peak[0]/base[0]):.1f}% less; idx {peak[1]*4} ident {peak[2]*4} undo {peak[3]*4})")
    print(path.split('/')[-1]); print('  ' + '\n  '.join(out))
