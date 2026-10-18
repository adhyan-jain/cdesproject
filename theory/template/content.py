"""Text of the manuscript in the institution's template order.

build(d) fills a build_docx.Doc.  Numbers in tables are read from the paper's generated tables (theory/paper/tables) so
that none is typed by hand; references come from refs/*.json (verified records) and theory/paper/refs.bib.
Theorem and proposition numbers follow the full manuscript (theory/paper/main.pdf), which contains every proof.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(HERE, "..", "paper", "tables")

# ---------------------------------------------------------------------------------------------------------------------
# generated tables
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def clean(c):
    c = c.replace("\\,", "").replace("$", "").replace("\\%", "%").replace("{=}", "=").replace("\\varepsilon", "ε").replace("\\alpha", "α")
    c = re.sub(r"\^\{?(-?\d+)\}?", lambda m: m.group(1).translate(SUP), c)
    c = c.replace("{", "").replace("}", "").replace("\\mathrm", "").replace("\\infty", "∞").replace("\\to", "→").replace("\\sum", "Σ")
    c = c.strip()
    return {"1e-06": "10⁻⁶", "1e-6": "10⁻⁶", "0.0001": "10⁻⁴", "0.01": "10⁻²"}.get(c, c)


def pretty(text):
    """ASCII math of the reference summaries to symbols and markup."""
    for a, b in [("Theta", "Θ"), ("Omega", "Ω"), ("delta", "δ"), ("epsilon", "ε"), ("eps", "ε"), ("O~", "Õ"), ("Omega~", "Ω̃")]:
        text = text.replace(a, b)
    text = re.sub(r"\^\(?(-?[0-9]+(?:\.[0-9]+)?)\)?", lambda m: "{sup:%s}" % m.group(1).replace("-", "−"), text)
    return text.replace("{sup:−1}", "{sup:−1}")


def table_rows(name):
    out, on = [], False
    for l in open(os.path.join(TABLES, name), encoding="utf8"):
        if "\\midrule" in l: on = True; continue
        if "\\bottomrule" in l: break
        if on and "&" in l and "\\\\" in l: out.append([clean(c) for c in l.replace("\\\\", "").split("&")])
    return out


# ---------------------------------------------------------------------------------------------------------------------
# references
LATEX_CHARS = {"{\\'\\i}": "í", "{\\'e}": "é", "{\\'a}": "á", "{\\AA}": "Å", "{\\\"o}": "ö", "{\\'o}": "ó", "\\&": "&", "--": "–",
               "{\\'\\i}n": "ín", "{\\\"u}": "ü", "$\\ell$": "ℓ", "\\texttt": ""}


def unlatex(s):
    for k, v in LATEX_CHARS.items(): s = s.replace(k, v)
    s = re.sub(r"\{\\[`'^\"~=.]\\?(\w)\}", lambda m: m.group(1), s)
    return s.replace("{", "").replace("}", "").strip()


def parse_bib():
    out = {}
    txt = open(os.path.join(HERE, "..", "paper", "refs.bib"), encoding="utf8").read()
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", txt, flags=re.S):
        kind, key, body = m.groups()
        fields = {k.lower(): v.strip() for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", body)}
        fields["kind"] = kind
        out[key] = fields
    return out


def name_list(authors):
    """Template style: first author inverted, the rest in natural order, 'and' before the last."""
    def natural(a):
        if "," in a:
            fam, giv = [x.strip() for x in a.split(",", 1)]
            return "%s %s" % (giv, fam)
        return a
    if isinstance(authors, str): return authors
    if len(authors) > 6: authors = authors[:3] + ["et al."]
    first = authors[0]
    if "," not in first and first != "et al.":
        parts = first.split(); first = "%s, %s" % (parts[-1], " ".join(parts[:-1]))
    rest = [natural(a) if a != "et al." else a for a in authors[1:]]
    names = [first] + rest
    if len(names) == 1: return names[0]
    if names[-1] == "et al.": return ", ".join(names[:-1]) + ", et al."
    return ", ".join(names[:-1]) + (", and " if len(names) > 2 else " and ") + names[-1]


def fmt_ref(authors, year, title, venue=None, volume=None, issue=None, pages=None, doi=None, url=None, note=None):
    s = "%s. (%s) “%s.”" % (name_list(authors).rstrip("."), year if year else "n.d.", title.rstrip("."))
    if venue:
        s += " " + venue
        if volume: s += " " + str(volume)
        if issue: s += " (%s)" % issue
        if pages: s += ": " + re.sub(r"-+", "–", str(pages))
        s += "."
    if doi: s += " doi:%s." % doi
    elif url: s += " %s." % url
    if note: s += " " + note
    return s


class Refs:
    def __init__(self):
        self.rec = {}
        refdir = os.path.join(HERE, "refs")
        if os.path.isdir(refdir):
            for fn in sorted(os.listdir(refdir)):
                if fn.endswith(".json"):
                    for e in json.load(open(os.path.join(refdir, fn), encoding="utf8")): self.rec[e["key"]] = e
        self.bib = parse_bib()

    def text(self, key):
        if key == "strata":
            return ("Singh, Shubhi, and Adhyan Jain. (2026) “STRATA: a budgeted, stack-disciplined scoped symbol table.” Public repository cdesproject "
                    "(https://github.com/adhyan-jain/cdesproject); the directory theory/ holds this article's sources and verification programs.")
        if key == "sanders2018":
            return "Sanders, Peter. (2018) “Hashing with Linear Probing and Referential Integrity.” arXiv preprint arXiv:1808.04602."
        if key in self.rec:
            e = self.rec[key]
            if e.get("kind") == "tool":
                authors = re.sub(r"\s*\(site footer.*$", "", e["authors"]) if isinstance(e["authors"], str) else e["authors"]
                return fmt_ref(authors, e["year"], e["title"], e.get("venue"), url=e.get("url"), note="Accessed October 2026." if e.get("url") else None)
            return fmt_ref(e["authors"], e["year"], e["title"], e.get("venue"), e.get("volume"), e.get("issue"), e.get("pages"), e.get("doi"), e.get("url"))
        b = self.bib[key]
        authors = [a.strip() for a in unlatex(b.get("author", "")).replace("\n", " ").split(" and ")]
        authors = [", ".join([a.split()[-1], " ".join(a.split()[:-1])]) if "," not in a and len(a.split()) > 1 else a for a in authors]
        venue = b.get("journal") or b.get("booktitle") or b.get("publisher") or b.get("school")
        if b["kind"] == "phdthesis" and venue: venue = "PhD thesis, " + venue
        return fmt_ref(authors, b.get("year", ""), unlatex(b.get("title", "")), unlatex(venue) if venue else None, b.get("volume"), b.get("number"),
                       b.get("pages"), b.get("doi"))


R = Refs()

# ---------------------------------------------------------------------------------------------------------------------
INCLUDE_AI_DISCLOSURE = False
TITLE = "Stack-Disciplined Open Addressing: Exact Undo, Exact Refusal Probabilities, and Key-Lifetime Rules for Bounded-Memory Scoped Tables"
AUTHORS = "Shubhi Singh and Adhyan Jain"
AFFIL = "Vellore Institute of Technology, Vellore, India"

ABSTRACT = (
    "Compilers and interpreters keep a scoped symbol table that binds names to declarations and forgets them in last-in-first-out order when a block ends; "
    "on microcontrollers and in boot loaders the table must live in one fixed buffer, refuse a request cleanly when it is full, and bound the work of every call. "
    "Open addressing is the natural structure, but its analysis covers insertions, deletions are known to be difficult, and probe limits have been set with loose Chernoff-type bounds. "
    "We ask what the stack discipline itself gives such a table. We prove that, for every non-reordering scheme, popping the newest key by clearing its cell is an exact undo, so that every insertion-only analysis transfers; "
    "that stack order is the only deletion order safe for every table, and that the safe orders of a given table are the linear extensions of a dependency relation whose size is a queue length; "
    "that the refusal probability of a probe-limited table is exactly computable for one push, for a whole fill, for an unlimited run, and, through a schedule-free bound, for a persistent set of names with bounded churn above it; "
    "and that a fresh key per table keeps the exact law valid against adversarial names. "
    "Exhaustive enumeration in exact arithmetic and a real probe-limited table agree with every formula; at load 3/4 the exact probe limit for a failure probability of 10⁻⁶ is 258 against 455 for the Chernoff-type rule, "
    "and the whole-fill rule is 24% smaller than the union bound. "
    "Open problems are a limit law for refusals on wide and deep scope trees and an unconditional probe-complexity separation."
)
KEYWORDS = "bounded memory, exact analysis, linear probing, open addressing, scoped symbol tables, stack discipline"


# ---------------------------------------------------------------------------------------------------------------------
def abstract(d):
    d.para(TITLE, jc="center", b=True, sz=28, after=60, line=300)
    d.para("%s" % AUTHORS, jc="center", sz=24, after=0, line=300)
    d.para("{i:%s}" % AFFIL, jc="center", sz=22, after=200, line=300)
    d.heading("Abstract")
    d.para(ABSTRACT)
    d.para("{b:Keywords} – %s" % KEYWORDS, before=80)


INTRO_KEYS = ["GurdeepSingh2019WARDuino", "Rouvoet2020Knowing", "vanAntwerpen2021ScopeStates", "BenderEtAl2023Iceberg", "BenderEtAl2022TimeSpace",
              "dalal2023twoway", "HuKuszmaulLiangWalzerYuZhou2026", "he2023siphash", "csikor2019tse", "KenyonYin2023"]
RELATED = [
    ("BenderKuszmaulKuszmaul2021", "Bender, Kuszmaul and Kuszmaul (2021): linear probing with tombstones"),
    ("BravermanKuszmaul2024", "Braverman and Kuszmaul (2024): tight analyses of linear probing"),
    ("FarachColtonKrapivinKuszmaul2024", "Farach-Colton, Krapivin and Kuszmaul (2024): elastic and funnel hashing"),
    ("KrapivinKuszmaulWang2026", "Krapivin, Kuszmaul and Wang (2026): interlinear probing"),
    ("AlharbiBanderierBouillaguet2026", "Alharbi, Banderier and Bouillaguet (2026): bounded linear probing"),
    ("BenderKuszmaulZhou2025", "Bender, Kuszmaul and Zhou (2025): non-oblivious open addressing"),
    ("BenderEtAl2023TinyPointers", "Bender et al. (2023): tiny pointers"),
    ("AguilarFragaEtAl2024", "Aguilar-Fraga et al. (2024): ℓ-interval parking functions"),
    ("vanAntwerpen2018Scopes", "van Antwerpen et al. (2018): scopes as types"),
    ("Zwaan2022Incremental", "Zwaan et al. (2022): incremental type checking from scope graphs"),
    ("Ball2019StaticTypeScript", "Ball, de Halleux and Moskal (2019): Static TypeScript"),
    ("Mochizuki2025BlueScript", "Mochizuki and Yamazaki (2025): BlueScript"),
    ("naor2019bloom", "Naor and Yogev (2019): Bloom filters in adversarial environments"),
    ("clayton2019pds", "Clayton, Patton and Shrimpton (2019): probabilistic data structures in adversarial environments"),
    ("blair2020hotfuzz", "Blair et al. (2020): HotFuzz"),
]
GAP_OVERRIDE = {
    "AlharbiBanderierBouillaguet2026": "(Our assessment) The closest prior work on probe-limited linear probing, but for insertions in which a failed key is discarded and redrawn until the table is full; it has no deletions, no stack discipline, and no refuse-and-stop event with a refusal probability at a fixed load.",
}


def intro(d):
    d.heading("1. Introduction")
    d.para("Compilers, interpreters and virtual machines for small devices are moving onto the device. Run-time systems for Arduino-class microcontrollers now execute WebAssembly with live code updates {cite:GurdeepSingh2019WARDuino}, and the tooling of mainstream languages treats name resolution as a subject of its own: the scheduling of name and type queries in type checkers, and their safety under parallel checking, have been characterised with scope graphs {cite:Rouvoet2020Knowing,vanAntwerpen2021ScopeStates}. Whatever the language, the same data structure sits at the centre of name resolution: a symbol table that binds identifiers to declarations, forgets the declarations of a block when the block ends, and is consulted at every use of a name. The textbook implementation is a hash table from names to their innermost declaration together with an undo stack that restores what a scope hid {cite:appel1998,graham1979}.")
    d.para("When the program that owns the table runs on a microcontroller, in a boot loader or under a fixed allocation, three requirements appear. The table must live in {i:one fixed buffer}, because the allocator is absent or must not be called. It must {i:refuse} a request that does not fit and stay usable afterwards, because running out of memory is an expected event and not a crash. And the {i:work} of one call must be bounded, even when the source text is supplied by someone else. We study a table that meets these requirements, STRATA {cite:strata}: one buffer holds an open-addressing index, one packed record per visible name and the undo stack, and an operation that does not fit changes nothing. The question is what the last-in-first-out discipline of scopes, a very special deletion order, gives such a table that a general hash table does not have.")
    d.para("Open addressing has a long analytical tradition, from Knuth's analysis of linear probing {cite:knuth3} to exact distributional results {cite:janson2016}, and recent years have been unusually productive. Iceberg hashing gives a stable table with constant-time operations at load 1 − o(1) and strong space, cache and failure-probability guarantees {cite:BenderEtAl2023Iceberg}, and the time/space trade-off of hash tables has been determined for a large class of structures {cite:BenderEtAl2022TimeSpace}. For the simple schemes used in practice, a second probe sequence makes the worst unsuccessful search of linear probing O(log log n) almost surely at constant load {cite:dalal2023twoway}, and quadratic probing has been analysed in a smoothed model, with a separation between Robin Hood and anti-Robin Hood orderings {cite:HuKuszmaulLiangWalzerYuZhou2026}.")
    d.para("The combinatorics we use comes from parking functions, which describe exactly the event that every key finds a place: bijections with spanning forests and the probabilistic properties of a uniform parking function are now understood in detail {cite:KenyonYin2023}, and the ℓ-interval variants count the cases in which every key stays within ℓ cells of its home {cite:AguilarFragaEtAl2024,ColaricDeMuseMartinYin2021}. Nothing in this literature concerns the discipline of a scoped table; the related work of Section 2 makes this precise.")
    d.para("All of this concerns insertions, or deletions drawn at random. The deletion order of a scoped table is neither: it is last-in-first-out, and for that order the state of an open-addressing table, its safe deletion orders and its refusal probabilities have not, to our knowledge, been stated exactly. Probe limits are chosen with Chernoff-type bounds that lose a factor growing with the limit, and whether a probe-limited table refuses an honest name is usually answered by simulation. Exact finite-size laws matter here because the tables have hundreds to thousands of cells, where asymptotic formulas are not accurate.")
    d.para("The second shortfall concerns adversarial input. A table that must bound the work of every call has to withstand names chosen to collide, and algorithmic denial of service against hash-based structures is a demonstrated attack class: low-rate adversarial traffic reduced an Open vSwitch packet classifier built on tuple space search to about 12% of its capacity {cite:csikor2019tse}. Keyed hash functions such as SipHash are the standard defence, and reduced-round variants have been cryptanalysed {cite:he2023siphash}. Whether one key may be reused across tables, and what an adversary with a probe oracle then gains against a probe-limited table, has not been quantified.")
    d.para("We prove that, for every non-reordering open-addressing scheme, popping the newest key by clearing its cell is an {i:exact undo}, so that every insertion-only analysis of the table transfers to push/pop workloads. We characterise the deletion orders that are safe for a given table, show that stack order is the only order safe for every table, and give the exact law of the number of keys orphaned by a deletion. These statements are elementary; their value lies in what follows from them.")
    d.para("On this basis we derive the refusal probability of a probe-limited table exactly, for one push, for a whole fill, for an unlimited run on a fixed table and, through a schedule-free bound, for a persistent set of names with bounded churn above it. We show that a fresh key per table keeps the law exact against adversarial names while a persistent key does not, and we give an exact space ledger. Every formula is checked by exhaustive enumeration in exact arithmetic, against the real table and by an independent derivation, and all numbers are regenerated by one script. The refusal law and the limit law of the orphan count are classical as quantities and are credited as such.")
    d.para("Section 2 reviews fifteen recent works on hash tables, on scoped name resolution on constrained devices and on adversarial robustness, with their research gaps. Section 3 presents the proposed work: the problem, the architecture, the methods with their equations, the modules, the flow and three algorithms. Section 4 describes the implementation and analyses eight performance metrics and a comparison with related work. Section 5 concludes and Section 6 lists the references; the declarations follow. The full proofs are in the accompanying manuscript.")


def related(d):
    d.heading("2. Related works")
    d.para("Fifteen recent works are reviewed in three groups: hash tables and open addressing (2.1–2.8), scoped name resolution and compilation on constrained devices (2.9–2.12) and adversarial robustness (2.13–2.15). Each summary was written from the abstract of the paper and, for some, its introduction or overview, as recorded with the reference; proofs were not read, and the research gaps are our assessment relative to this work.", before=40)
    for n, (key, label) in enumerate(RELATED, 1):
        e = R.rec[key]
        d.heading("2.%d %s %s" % (n, label, d.cite(key)), 2)
        d.para("{b:Solution proposed.} " + pretty(e["solution"]))
        meth = [x.strip() for x in e["methodology"].split("\n") if x.strip()]
        d.para("{b:Methodology and tools.} " + pretty(meth[0]))
        for extra in meth[1:]: d.para(pretty(extra))
        d.para("{b:Result and effectiveness.} " + pretty(e["results"]))
        gap = GAP_OVERRIDE.get(key, e["gap"])
        d.para("{b:Research gap.} " + pretty(gap))


def build(d):
    abstract(d)
    intro(d)
    related(d)
    section3(d)
    section4(d)
    section5(d)
    # the reference list is built from the citations, in order of first appearance; the declarations cite one more entry
    declarations(d)
    d.page_break_before_refs = len(d.body)
    order = list(d.cite_order)
    refs_body = Doc_refs(d, order)


def Doc_refs(d, order):
    # references are inserted before the declarations: build them separately, then splice
    saved = d.body
    d.body = []
    references_section(d, order)
    refs_xml = d.body
    d.body = saved
    # the declarations were the last block appended; find where they start (first heading "Author Contributions")
    idx = next(i for i, x in enumerate(saved) if "Author Contributions" in x)
    d.body = saved[:idx] + refs_xml + saved[idx:]
    return refs_xml


def section3(d):
    d.heading("3. Proposed work/system")
    d.para("The work is a theory of what the last-in-first-out discipline of scopes gives an open-addressing index. The statements below follow the numbering of the full manuscript, which contains every proof and the programs that check them; the text here explains the system, the method and the results.", before=40)

    # --- 3.1
    d.heading("3.1 Problem formulation", 2)
    d.para("Let a table consist of {i:m} cells arranged on a ring. A key {i:x} has a home {i:h}({i:x}) in {0,…,{i:m}−1}, drawn independently and uniformly (the random-function model for a keyed hash function), and an insertion rule places {i:x} in the first empty cell found by probing {i:h}({i:x}), {i:h}({i:x})+1, and so on. A rule is {i:non-reordering} if a key never moves after it is placed and the cell chosen for an insertion depends only on the set of occupied cells and on the key's own probe sequence. A scoped symbol table receives an oblivious schedule of {i:push} (declare a name) and {i:pop} (leave a scope) operations; pops remove the newest live keys, so the live keys form a stack. A {i:probe limit} {i:L} makes the table refuse a push whose first {i:L} probed cells are all occupied, and a refusal changes nothing.")
    d.para("Four questions follow. {b:Q1 (state):} is the table after a pop distributed like an insertion-only table? {b:Q2 (order):} which orders of clearing cells keep every lookup correct, and is stack order special? {b:Q3 (refusal):} how large must {i:L} be so that an honest push is refused with probability at most ε, for one push, for a whole fill, for an unlimited run on a fixed table, and for a persistent set of names with bounded churn above it? {b:Q4 (keys):} what changes when an adversary can query the hash? The answers have to be exact at finite {i:m}, because the tables of interest have a few hundred to a few thousand cells, where asymptotic formulas are not accurate.")

    # --- 3.2
    d.heading("3.2 System architecture", 2)
    d.figure("fig_d1.png", "Architecture. The compiler front end issues four calls to a STRATA table that keeps its open-addressing index, packed identifier records and undo stack in one fixed buffer. The analysis layer models the index and produces design rules for the probe limit, the buffer size and the key policy.", 16.4)
    d.para("Figure 1 shows the system. The compiler front end issues four calls: declare, lookup, enter scope and exit scope. STRATA keeps the index, one packed record per visible name and the undo stack of the open scopes in one caller-provided buffer. A declaration that hides an outer name saves the old record on the undo stack, and leaving a scope pops the entries in reverse order. Space for the record and the undo entry is reserved before anything is written, so a request that does not fit returns {code:kNoMemory} and leaves the table unchanged; a request whose probe sequence meets {i:L} occupied cells returns {code:kProbeLimit}, also without change.")
    d.para("The analysis layer below the table has four parts that mirror the four questions: exact undo and deletion orders (Theorems 2 and 4, Proposition 5), the refusal laws (Theorems 7 and 10, Propositions 11 and 12), the key-lifetime results (Propositions 13–15) and the space ledger (Proposition 16). The dashed arrow in Figure 1 marks the modelling step: the index of the table is the ring of cells, and everything proved about the ring is a statement about that index. The design rules at the bottom are the product: a probe limit, a buffer size and a key policy chosen from exact numbers instead of loose bounds.")

    # --- 3.3
    d.heading("3.3 Detailed methodology", 2)
    d.heading("3.3.1 Exact undo", 2)
    d.para("Write Ins({i:a}{sub:1},…,{i:a}{sub:n}) for the table obtained by inserting the keys in this order into an empty table. {b:Theorem 2 (undo).} For every non-reordering rule, after any sequence of pushes and pops the table at time {i:t} is the insertion-only table of the live keys, in the order in which they were pushed:")
    d.equation(r"T_t=\mathrm{Ins}\left(a_1,\dots,a_{n_t}\right)")
    d.para("The proof is by induction. An insertion changes exactly one empty cell, chosen from the set of occupied cells alone, so clearing that cell restores the table that existed before the insertion (Figure 2). Consequently the table has, at every moment, the law of an insertion-only table, and every insertion-only result about the table's state or the cost of the next operation transfers to push/pop workloads, up to the first refusal (Corollary 3).")
    d.figure("fig_d2.png", "Exact undo. Pushing {i:x} writes one empty cell; popping {i:x} clears it, and the table is identical in every cell to the table before the push.", 15.0)

    d.heading("3.3.2 Safe deletion orders and the orphan law", 2)
    d.para("Let {i:c}({i:x}) be the cell of key {i:x}. A key {i:y} {i:depends on} {i:x}, written {i:y} ◁ {i:x}, if the cell of {i:x} lies strictly before the cell of {i:y} on the probe path of {i:y}:")
    d.equation(r"y\lhd x\;\Leftrightarrow\;c(x)\in\{h(y),\,h(y)+1,\,\dots,\,c(y)-1\}")
    d.para("{b:Theorem 4.} (a) For a given table, the orders of clearing cells that keep every lookup correct are exactly the linear extensions of ◁: every key is cleared before the keys it depends on. (b) Reverse insertion order, that is stack order, is the only order that is safe for every hash assignment, for greedy schemes with probe sequences that start anywhere and have a second distinct cell. The newest key has no dependents, because a key's path crosses only cells that were filled before it (Figure 3).")
    d.figure("fig_d3.png", "Dependency and orphans. Key {i:y} probed cells 2, 3 and 4 before it was stored in cell 5, so it depends on {i:u}, {i:v} and {i:w}. Clearing {i:w} first leaves a hole on its path and orphans {i:y}.", 14.2)
    d.para("The number of keys that depend on a key is the length of a queue minus one. Linear probing is a queue: cell {i:c} receives {i:A}{sub:c} keys whose home it is, one key is served per cell, and the queue length {i:Y}{sub:c} obeys a Lindley recursion. With {i:α} = {i:n}/{i:m} the mean number of dependents and the limiting fraction of keys with none are")
    d.equation(r"\mathrm{orph}(x)=Y_c-1,\qquad Y_c=\left(Y_{c-1}-1\right)^{+}+A_c")
    d.equation(r"\mathbb{E}[\mathrm{orph}]=\frac{\alpha}{2(1-\alpha)},\qquad \mathbb{P}(\mathrm{orph}=0)\to\frac{(1-\alpha)(e^{\alpha}-1)}{\alpha}")
    d.para("At load 1/2 the mean is 0.5 and 65% of keys have no dependents; at load 3/4 the mean is 1.5 and only 37% have none. Out-of-order deletion is therefore a gamble that gets worse as the table fills. The queue representation of linear probing and the limit law are due to Janson {cite:janson2005}, and the single-deletion form of the safe-order test to Sanders {cite:sanders2018}; the exact finite-size law, the reading as orphans, the characterisation of safe orders and the converse are new as stated.")

    d.heading("3.3.3 The exact refusal law", 2)
    d.para("Let {i:n} = {i:m} − {i:k} keys sit on the ring with independent uniform homes. {b:Theorem 7.} The probability that a new key with an independent uniform home finds its first {i:L} cells occupied is")
    d.equation(r"R_m(n,L)=\frac{k}{m}\sum_{g=L+1}^{n+1}(g-L)\,\pi_g,\qquad \pi_g=\frac{B(g)\,Q_{k-1}(m-g)}{Q_k(m)}")
    d.equation(r"B(g)=\frac{g^{g-1}}{g!},\qquad Q_j(x)=\frac{j\,x^{x-j-1}}{(x-j)!}")
    d.para("The proof cuts the ring at its {i:k} empty cells (Figure 4). Each empty cell and the run of occupied cells after it form a block whose size is Borel distributed, by the cycle lemma, and the blocks, conditioned on filling the ring, are exchangeable. A new key is refused exactly when its home starts a window of {i:L} occupied cells, and a block of {i:g} cells contains (g − L)⁺ such homes; summing gives Equation (5). The tail is of order ρ{sup:L} L{sup:−3/2} with ρ = α e{sup:1−α}, so the Chernoff-type bound used for probe limits is loose by a factor that grows like L{sup:3/2}. The law is classical as a quantity (it is the tail of the unsuccessful-search cost, Knuth {cite:knuth3}, Janson and Viola {cite:janson2016}); what is new is the elementary derivation, the explicit finite-size sum and its use for design.")
    d.figure("fig_d5.png", "Block decomposition used to prove the refusal law. The ring is cut at its {i:k} empty cells; a block is an empty cell and the run after it. A window of {i:L} occupied cells inside a block of {i:g} cells has {i:g} − {i:L} bad homes.", 15.4)

    d.heading("3.3.4 Whole fill and unlimited run", 2)
    d.para("Two further questions have exact answers. For a monotone fill of {i:n} pushes, the probability that no push is refused is the probability that the maximum displacement stays below {i:L}; the counts are those of the ℓ-interval parking functions {cite:AguilarFragaEtAl2024,ColaricDeMuseMartinYin2021} and have a closed generating function (Theorem 10). For a table that holds {i:n} keys and is then used for any number of push/pop pairs of fresh names, the table returns to the same state after every pop (Theorem 2), so the pushes are independent given the table, and no push is ever refused exactly when every block has at most {i:L} cells (Proposition 11):")
    d.equation(r"\mathbb{P}(W=0)=\frac{[z^m]\left(\sum_{g=1}^{L}B(g)z^g\right)^{k}}{[z^m]\left(\sum_{g\ge1}B(g)z^g\right)^{k}}")
    d.equation(r"P_{\mathrm{fill}}=\frac{n!}{m^{n}}\cdot\frac{m}{k}\,[z^n]\,\Phi_L(z)^{k}")
    d.para("The large-size behaviour of both events is that of the maximum displacement of linear probing, studied by Pittel and by Petersson {cite:pittel1987,petersson2009}; the exact finite-size forms and the design values are ours.")

    d.heading("3.3.5 Persistent names with bounded churn", 2)
    d.para("A real program has global names that are never popped and local scopes that come and go. Call the global names the {i:trunk} and let at most {i:s} further names be live above it, counting the one being pushed. Call a table {i:s-vulnerable} if some window of {i:L} consecutive cells contains at most {i:s} − 1 empty cells. {b:Proposition 12.} (a) Any refusal in any such schedule, however long, implies that the trunk is {i:s}-vulnerable. (b) This is the supremum: a chain of at most {i:s} pushes fills the empty cells of the window and pushes at its start, which is refused, so the refusal probability after {i:N} fresh chains increases to the vulnerability probability. (c) Cutting the ring at its empty cells, vulnerability is the event that some {i:s} consecutive gaps sum to at least {i:L} − {i:s} + 1, which gives a closed-form bound ({i:D}{sub:s}):")
    d.equation(r"V_s=\mathbb{P}\left(\exists\, i:\; g_i+g_{i+1}+\dots+g_{i+s-1}\ge L-s+1\right)\le D_s=\min\left(1,\,k\,\Pi_s\right)")
    d.equation(r"\mathbb{P}\left(\text{refusal after }N\text{ chains}\right)\ge V_s\left(1-e^{-N/m^{s}}\right)")
    d.figure("fig_d6.png", "Persistent trunk with bounded churn. Scope trees whose branches above the persistent names have height at most {i:s}; a refusal needs a window of {i:L} cells with at most {i:s} − 1 empty cells in the persistent part.", 15.4)
    d.para("Figure 5 shows the situation. The bound depends on neither the length of the run nor the order of the calls, so it is a guarantee that holds for the whole life of the table. It is conservative for short runs and uninformative for schedules that swing over a wide band; a limit law for such scope trees remains open.")

    d.heading("3.3.6 Probe complexity, keys and space", 2)
    d.para("Because the table is the insertion-only table of its live keys (Theorem 2), the worst-case and the amortised cost of a push under any oblivious stack-disciplined workload both equal the worst-case cost of the insertion-only table (Theorem 6):")
    d.equation(r"\text{cost}=\max_{j\le(1-\delta)m}q_j")
    d.para("Combined with the published insertion bounds {cite:FarachColtonKrapivinKuszmaul2024,KrapivinKuszmaulWang2026}, the optimum under stack discipline is Θ(log 1/δ) for non-greedy and Θ(log² 1/δ) for greedy schemes, strictly between the insertion-only amortised optimum and the cost of random deletions. For keys, an independent key per table keeps the exact law valid against arbitrary adversarial names (Proposition 13); with one persistent key and a probe oracle, after about {i:m} ln {i:m} queries an adversary knows a name for every cell and can build a run of occupied cells that exceeds the law (Propositions 14 and 15). The space ledger (Proposition 16) gives exact identities for the words used by five single-buffer layouts at every instant.")

    # --- 3.4
    d.heading("3.4 Modules and their functions", 2)
    d.table([["Module", "Function", "Result", "Checked by"],
             ["Exact undo", "pop = clear one cell; table = insertion of the live keys", "Thm 2, Cor 3", "lifo_check.py"],
             ["Dependency and orphans", "safe deletion orders; orphan law", "Thm 4, Prop 5", "orphan_law.py"],
             ["Refusal law", "exact R{sub:m}(n, L), tail, probe-limit design", "Thm 7, Cor 8", "exact_law.py, design_table.py, law_vs_table.cpp"],
             ["Fill and unlimited run", "whole-fill and unlimited-run probabilities", "Thm 10, Prop 11", "fill_law.py, sustain_law.py"],
             ["Bounded churn", "schedule-free bound D{sub:s}", "Prop 12", "band_law.py"],
             ["Probe complexity", "cost under stack discipline", "Thm 6", "derivation; published bounds"],
             ["Key lifetime", "fresh versus persistent key", "Props 13–15", "adaptive_key_demo.cpp"],
             ["Space ledger", "exact space identities", "Prop 16", "space_model.py, proof_checks.py"],
             ["Interactive page", "calculators and models of the results", "all of the above", "npm test (33 checks)"]],
            [3.2, 5.9, 2.4, 4.6], "Modules of the proposed work, the result each one provides and the program that checks it.", sz=19)

    # --- 3.5
    d.heading("3.5 Flow of the operations", 2)
    d.figure("fig_d4.png", "Flow of a declaration and of a scope exit. A declaration is refused, with the table unchanged, when no empty cell is found within {i:L} probes or when the record and its undo entry do not fit; a scope exit pops the undo entries in reverse order.", 14.6)
    d.para("Figure 6 gives the flow. A declaration computes the home with a keyed hash and probes at most {i:L} cells. If no empty cell is found, the table answers {code:kProbeLimit}; if the record and the undo entry do not fit in the buffer, it answers {code:kNoMemory}; in both cases nothing has been written. Otherwise it writes the record, sets the index cell and, if the name hides an outer one, pushes an undo entry. Leaving a scope pops the undo entries of that scope in reverse order: a new name has its cell cleared, a hidden name has its record restored. By Theorem 2 the table then equals the table that existed before the scope was entered.")
    d.para("The two exits of the flow are what the analysis quantifies. {code:kProbeLimit} is the event whose probability the refusal laws compute; {code:kNoMemory} is governed by the space ledger. Both are all-or-nothing, which is what makes the exact undo meaningful: a refused push never leaves a half-written state to undo.")

    # --- 3.6
    d.heading("3.6 Algorithms", 2)
    d.algorithm("Push with probe limit and scope exit (all-or-nothing)", [
        (0, "{b:procedure} PUSH(name)"),
        (1, "{i:h} ← F{sub:K}(name) mod {i:m}; {i:c} ← {i:h}"),
        (1, "{b:for} {i:t} = 0 {b:to} {i:L} − 1 {b:do}  {b:if} cell {i:c} is empty {b:then break}; {i:c} ← ({i:c} + 1) mod {i:m}"),
        (1, "{b:if} no empty cell was found {b:then return} kProbeLimit   ▹ table unchanged"),
        (1, "{b:if} the record and the undo entry do not fit {b:then return} kNoMemory   ▹ table unchanged"),
        (1, "write the record; set the index cell {i:c}; {b:if} name hides an outer name {b:then} push the saved record on the undo stack"),
        (1, "{b:return} kOk"),
        (0, "{b:procedure} EXIT_SCOPE()"),
        (1, "{b:for each} undo entry of this scope, newest first {b:do}"),
        (2, "{b:if} the entry marks a new name {b:then} clear its index cell {b:else} restore the saved record"),
    ], caption="Algorithm 1 is the table's behaviour. Because {i:c} is decided by the occupied cells alone and EXIT_SCOPE clears exactly the cells that PUSH wrote, Theorem 2 applies.")
    d.algorithm("Design rule: smallest probe limit for a target failure probability", [
        (0, "{b:input} {i:m}, {i:n}, target ε, and the event ∈ {one push, unlimited run, churn depth {i:s}}"),
        (0, "{b:output} the smallest {i:L} whose failure probability is at most ε"),
        (1, "{i:lo} ← 2; {i:hi} ← {i:m}"),
        (1, "{b:while} {i:lo} < {i:hi} {b:do}"),
        (2, "{i:mid} ← ⌊({i:lo} + {i:hi})/2⌋"),
        (2, "{b:if} FAIL({i:mid}) ≤ ε {b:then} {i:hi} ← {i:mid} {b:else} {i:lo} ← {i:mid} + 1"),
        (1, "{b:return} {i:lo}      ▹ FAIL is R{sub:m}(n, L) of Eq. (5), P(W>0) of Eq. (7) or D{sub:s} of Eq. (9)"),
    ], caption="Algorithm 2 turns the exact laws into design values; FAIL is decreasing in {i:L}, so bisection applies. For D{sub:s} the five values below the answer are also checked.")
    d.algorithm("Test for {i:s}-vulnerability and the refusing chain", [
        (0, "{b:input} occupancy {i:O} of the persistent names, probe limit {i:L}, churn depth {i:s}"),
        (1, "compute {i:e}({i:i}) = number of empty cells in the window of {i:L} cells starting at cell {i:i}, for all {i:i} (sliding sum)"),
        (1, "{i:i}* ← the start of a window with the fewest empty cells"),
        (1, "{b:if} {i:e}({i:i}*) > {i:s} − 1 {b:then return} “not {i:s}-vulnerable: no such schedule can be refused”"),
        (1, "{b:for each} empty cell {i:c} in the window {b:do} push a name whose home is {i:c}      ▹ it is stored in {i:c}"),
        (1, "push a name whose home is {i:i}*      ▹ all {i:L} cells from its home are occupied: refused"),
        (1, "{b:return} the chain (at most {i:s} pushes)"),
    ], caption="Algorithm 3 is the constructive half of Proposition 12(b) and is what the interactive page replays.")
    d.para("Algorithm 1 is the behaviour of the table, Algorithm 2 is the way the laws are used, and Algorithm 3 is the proof of the sharpness of the churn bound turned into a procedure. All three are implemented: the first in the C++ library, the second in the Python programs that generate the tables of Section 4, and the third in the verification program for Proposition 12 and in the interactive page.")
    d.para("{b:Contribution of this work.} (C1) Exact undo and its converse: safe deletion orders and the orphan law. (C2) Exact refusal probabilities for probe-limited tables: one push, a whole fill, an unlimited run, and bounded churn above a persistent trunk. (C3) Key-lifetime rules against adaptive adversaries. (C4) An exact space ledger. The refusal law and the orphan limit law are classical as quantities and are credited as such; the characterisation of safe orders, the exact finite-size forms, the use of the laws for design and the churn bound are the contribution.")


def section4(d):
    d.heading("4. Implementation and result analysis")
    d.heading("4.1 Tools, configuration and commands", 2)
    d.para("All laws are implemented twice and checked against each other and against the real table. The table itself is the header-only C++14 library of the STRATA repository {cite:strata}, compiled with {code:g++ -std=c++14 -O2} {cite:ISO14882_2014}. The exact formulas, the enumerations and the design tables are Python 3 programs that use exact rational arithmetic (the {code:fractions} module) for every check on small rings and floating point with logarithms for the large-size tables; the figures are drawn with LaTeX (TikZ and PGFPlots). One script, {code:bash theory/verify/run_all.sh}, runs every program, stops on the first mismatch and rebuilds the tables, figures and the manuscript; it takes about ten minutes on a laptop-class machine. The interactive page is a React {cite:ReactDocs} application built with Vite {cite:ViteDocs}; {code:npm start} serves it and {code:npm test} runs 33 checks, among them every formula against the Python reference values and the model's claims by brute force.")
    d.para("Two further components were used for validation. A C++ program drives the real probe-limited table, with a keyed hash and a random key per trial, and compares the observed frequency of a refused push with the exact law (400 000 trials per setting) and compares a table with the probe limit set against an unlimited one in lock step. The repository's earlier simulation of fresh insertions into tables of 65 536 slots (10 million samples per row) provides an independent empirical reference for the law. Figure 7 summarises the verification method, and Figure 8 shows the interactive page used to explore the results.")
    d.figure("fig_d7.png", "Verification method. Each result is proved on paper, checked by exhaustive enumeration in exact arithmetic, compared with the real table, re-derived independently, and every number in the tables is written by the programs.", 15.4)
    d.figure("screenshot_theory.png", "The interactive Theory page (React, Vite). The cards show, for {i:m} = 1024, load 3/4 and {i:L} = 130, the refusal probability of one push, the probability that some fresh name can ever be refused, and the schedule-free bound for churn depth 2; the lower panel finds the smallest probe limit for a target of 10⁻⁴ (131, 195 and 204).", 15.8)

    d.heading("4.2 Parameter setup", 2)
    d.table([["Parameter", "Values", "Used for"],
             ["Index slots {i:m}", "2⁸, 2¹⁰, 2¹², 2¹⁴, 2¹⁶ and {i:m} → ∞", "exact law, design tables"],
             ["Load α = {i:n}/{i:m}", "3/8, 1/2, 5/8, 3/4 (0.25–0.9 for the orphan law)", "all results"],
             ["Target failure probability ε", "10⁻², 10⁻⁴, 10⁻⁶, 10⁻⁹", "probe limits"],
             ["Probe limit {i:L}", "8–600 (curves); smallest meeting ε (tables)", "refusal law"],
             ["Churn depth {i:s}", "1, 2, 4, 8", "Proposition 12"],
             ["Homes", "independent uniform (model); keyed HalfSipHash-1-3 (real table); murmur3 (stored simulation)", "model and validation"],
             ["Enumeration", "every home sequence on rings with {i:m} ≤ 9 (258 triples)", "exact law"],
             ["Real-table trials", "400 000 per setting, 7 settings", "agreement of law and table"],
             ["Stored simulation", "10 million samples per row, 500 tables per row", "empirical reference"],
             ["Monte Carlo for Prop. 12", "6000 trunks, {i:m} = 1024, {i:n} = 768, {i:L} = 80", "tightness of {i:D}{sub:s}"],
             ["Software", "g++ (C++14), Python 3, TeX Live, Node.js 18+", "all programs"]],
            [4.2, 8.6, 3.5], "Parameters of the experiments and of the exact computations.", sz=19)

    d.heading("4.3 Performance analysis", 2)
    d.para("Eight metrics are reported. Each has a figure or a table and a short justification. All numbers are written by the programs of the repository.")

    d.heading("Metric 1: accuracy of the exact refusal law", 2)
    d.figure("fig_p1.png", "Probability that an insertion needs more than {i:L} probes ({i:m} = 65 536 cells, load 3/4): exact law, Chernoff-type bound, and the stored simulation (10 million samples from 500 tables). The simulated point at {i:L} = 256 rests on two events and is shown for completeness.", 15.4)
    d.para("The exact law follows the simulation at every probe limit where the simulation observes enough events and lies below the Chernoff-type bound by a factor that grows with {i:L}: the uncapped bound (the plotted curve is cut at 1) is 315 times the exact value at {i:L} = 64 and 4637 times at {i:L} = 512. The point at {i:L} = 256 comes from two observed events in 10 million samples of 500 tables and cannot resolve a probability of the order of 10⁻⁶; it is not evidence for or against the law. The next metric tests the law against the real implementation with 400 000 independent trials per setting.")
    d.heading("Metric 2: agreement with the real table (z-score)", 2)
    rows = table_rows("tab_lawcheck.tex")
    d.table([["m", "n", "L", "observed", "exact", "z", "clean trials", "mismatches"]] + [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]] for r in rows],
            [1.4, 1.4, 1.2, 2.3, 2.3, 1.5, 3.0, 2.3], "Exact law against the real probe-limited table: observed frequency of a refused push in 400 000 trials, the exact value and the z-score. “Clean” trials are those in which no earlier push exceeded the limit; in them the limited table and the unlimited table stayed in lock step.", align=["right"] * 8, sz=19)
    d.figure("fig_p7.png", "z-scores of the exact law against the real table. All seven settings lie inside ±1.96; the largest |z| is 1.96.", 14.2)
    d.para("All seven z-scores lie within ±1.96, and the lock-step comparison found no mismatch. The law is therefore a statement about the implementation and not only about the model.")

    d.heading("Metric 3: tightness of the probe limit", 2)
    rows = table_rows("tab_design.tex")
    d.table([["load", "ε", "m=2⁸", "2¹⁰", "2¹²", "2¹⁴", "2¹⁶", "m→∞", "Chernoff", "saving"]] +
            [r + ["%d%%" % round(100 * (float(r[8]) - float(r[6])) / float(r[8]))] for r in rows],
            [1.3, 1.5, 1.6, 1.4, 1.4, 1.4, 1.4, 1.5, 2.0, 1.7], "Smallest probe limit {i:L} such that a push is refused with probability at most ε, from the exact law for several ring sizes and in the limit, against the Chernoff-type rule. The last column is the saving at {i:m} = 2¹⁶.", align=["center", "center"] + ["right"] * 8, sz=19)
    d.figure("fig_p2.png", "Smallest probe limit for ε = 10⁻⁶ against the load.", 14.4)
    d.para("At load 3/4 and ε = 10⁻⁶ the exact limit is 258 at 2¹⁶ cells and 260 in the limit, against 455 for the Chernoff-type rule, a saving of 43% of the probes allowed per call; at load 3/8 the saving is 33%. The gap widens with the load because the Chernoff-type bound loses a factor that grows like {i:L}{sup:3/2}. A smaller limit means less work on a hostile input, and the exact numbers state what failure probability that limit buys.")

    d.heading("Metric 4: probe limit for a whole fill", 2)
    d.figure("fig_p3.png", "Smallest probe limit for a whole monotone fill to load 3/4 ({i:m} = 4096) to be refusal-free with probability at least 1 − ε′: exact (Theorem 10), the sum of the per-push bounds, and {i:n} times the maximum per-push bound.", 14.6)
    rows = [r for r in table_rows("tab_fill.tex") if r[0] == "4096"]
    d.table([["m", "ε′", "exact", "sum of per-push bounds", "n·R{sub:max}", "true / sum"]] + rows, [1.6, 1.8, 2.0, 4.6, 2.4, 2.4],
            "Whole-fill probe limits at {i:m} = 4096 and load 3/4. The last column is the true failure probability divided by the sum at the exact limit.", align=["right"] * 6, sz=19)
    d.para("The exact limit is close to the one given by summing the per-push bounds and well below the limit given by {i:n} times the largest one: at ε′ = 10⁻⁶ it is 306 against 402, a saving of 24% in the probes allowed per call. The sum is not exact because refusals cluster: once a window of occupied cells exists, several pushes can hit it, and the true probability is 61%–76% of the sum in the table (and up to 93% for smaller rings).")

    d.heading("Metric 5: safety of out-of-order deletion (orphan law)", 2)
    d.figure("fig_p4.png", "Probability that a key has {i:j} dependents, for four loads.", 14.0)
    rows = table_rows("tab_orphan.tex")
    d.table([["α", "j = 0", "1", "2", "3", "4", "mean"]] + rows, [1.8, 2.2, 1.9, 1.9, 1.9, 1.9, 2.0],
            "Distribution of the number of keys that depend on a key (limit law) and its mean.", align=["center"] + ["right"] * 6, sz=19)
    d.para("The fraction of keys that could be removed out of order without harm falls from 85% at load 1/4 to 37% at 3/4 and 16% at 9/10, and the mean number of orphans created grows as α/(2(1−α)): 0.17 at load 1/4, 1.5 at 3/4 and 4.5 at 9/10. The finite-size law was checked against enumeration of every home sequence. Stack order is the one order with no orphans at any load.")

    d.heading("Metric 6: price of persistent names with churn", 2)
    d.figure("fig_p5.png", "Smallest probe limit with {i:D}{sub:s} ≤ ε against the churn depth {i:s}, at load 3/4.", 14.4)
    rows = table_rows("tab_band.tex")
    d.table([["m", "ε", "s = 1", "s = 2", "s = 4", "s = 8"]] + rows, [1.8, 1.8, 2.4, 2.4, 2.4, 2.4],
            "Smallest probe limit for which no schedule keeping at most {i:s} names above a persistent set is refused with probability above ε (Proposition 12). The column {i:s} = 1 is the unlimited-run limit.", align=["right", "center"] + ["right"] * 4, sz=19)
    d.table([["s", "simulated V{sub:s}", "bound D{sub:s}"]] + table_rows("tab_bandmc.tex"), [2.0, 3.6, 3.6],
            "Closeness of the closed-form bound: {i:m} = 1024, {i:n} = 768, {i:L} = 80; V{sub:s} estimated from 6000 simulated trunks.", align=["center", "right", "right"], sz=19)
    d.para("A guarantee against every schedule with eight names of churn above a persistent set costs 410 probes at {i:m} = 4096 and ε = 10⁻⁶, against 349 for one level, about 17% more, and each level costs roughly eight more probes. The closed form is within 5% of the simulated vulnerability at {i:s} = 1 and 2, within 11% at {i:s} = 3 and 17% at {i:s} = 4, and is conservative as {i:s} grows.")

    d.heading("Metric 7: memory overhead of the compact layout (space ledger)", 2)
    d.figure("fig_p6.png", "Saving of the compact layout over the baseline single-buffer layout on eight compiler traces, split into the stored hash word and packing.", 15.6)
    rows = table_rows("tab_ladder.tex")
    d.table([["trace", "C₀ (KiB)", "C₁", "C₂", "S_raw", "S", "hash %", "pack %", "total %"]] + rows, [2.4, 1.9, 1.7, 1.7, 1.8, 1.7, 1.8, 1.8, 1.9],
            "Smallest fixed buffer in KiB for the five layouts and the savings: dropping the stored hash (C₀ → C₁), packing (C₁ → S) and in total (C₀ → S).", align=["left"] + ["right"] * 8, sz=19)
    d.para("The identities reproduce all 24 measured minimum buffers of the repository exactly (to the 64-byte resolution of the measurement). The compact layout saves 16.4%–17.9% of the buffer: 9.2%–12.2% from not storing the hash and 5.3%–9.0% from packing, and interning contributes between −0.38% and 0.00%. The saving therefore comes from design choices that the ledger isolates, not from the probe limit.")

    d.heading("Metric 8: effect of the key policy under attack", 2)
    d.figure("fig_p8.png", "Fraction of honest names refused after an adversary has found colliding names ({i:m} = 2048, idealised oracle).", 14.0)
    rows = table_rows("tab_adaptive.tex")
    d.table([["colliders", "persistent key (mean)", "(max)", "fresh key", "random names"]] + rows, [2.6, 4.2, 2.4, 2.6, 3.2],
            "Honest names refused after the attack, by key policy.", align=["right"] * 5, sz=19)
    d.para("With a persistent key the adversary makes 1%–6% of honest names fail; with a fresh key per table, or with random names, none does, as Proposition 13 states. The attack uses an idealised oracle: no timing was measured, and the result is a statement about the model.")

    d.heading("Verification coverage", 2)
    d.table([["Check", "Size", "Result"],
             ["Exact law against enumeration of every home sequence (exact rationals)", "258 triples (m, n, L)", "0 mismatches"],
             ["Exact undo, five insertion rules", "488 919 state comparisons", "0 failures"],
             ["Safe orders (Theorem 4a)", "397 562 assignment–order pairs", "0 failures"],
             ["Exactness of safe orders and orphan law", "18 settings; every assignment × every order", "0 failures"],
             ["Independent derivation of Theorem 7 (Abel binomial route)", "481 cases", "agree to 2·10⁻¹⁰"],
             ["Space ledger", "848 449 instants of eight traces", "identities hold"],
             ["Proposition 12 (real insertion code)", "16 920 trunks and 36 432 occupancy sets", "0 failures"]],
            [8.6, 5.0, 2.7], "Coverage of the exhaustive checks.", sz=19)

    d.heading("4.4 Comparison with related work", 2)
    _sav = [100 * (float(r[8]) - float(r[6])) / float(r[8]) for r in table_rows("tab_design.tex")]
    _lo, _hi = round(min(_sav)), round(max(_sav))
    d.para("Three works are used for comparison. {b:(1) The earlier probe-limit rule.} The earlier analysis of the same table {cite:strata} and common practice set the probe limit with a Chernoff-type bound. The design table and figure of Metric 3 show that the exact law needs @@LO@@%–@@HI@@% fewer probes at the same failure probability, and the real-table test shows that the exact law is the correct one. {b:(2) Optimal open addressing without reordering.} Farach-Colton, Krapivin and Kuszmaul {cite:FarachColtonKrapivinKuszmaul2024} give insertion bounds for elastic and funnel hashing, and Krapivin, Kuszmaul and Wang {cite:KrapivinKuszmaulWang2026} give interlinear probing. They bound the cost of insertions only; Theorem 6 shows that, under stack discipline, the same bounds hold for every push of every oblivious schedule, which no insertion-only analysis states. {b:(3) Bounded linear probing.} Alharbi, Banderier and Bouillaguet {cite:AlharbiBanderierBouillaguet2026} analyse linear probing with at most {i:p} probes per insertion, for insertions in which a key that fails is discarded and redrawn; our event, refusal and stop, with deletions in stack order, is a different process, and their results do not give the refusal probabilities above.".replace("@@LO@@", str(_lo)).replace("@@HI@@", str(_hi)))
    d.table([["Aspect", "Chernoff-type rule (earlier STRATA analysis)", "Insertion-only bounds (FKK; KKW)", "Bounded linear probing (ABB)", "This work"],
             ["Operations", "insertions", "insertions", "insertions", "pushes and pops in stack order"],
             ["Quantity", "probe limit from a tail bound", "expected probe index at load 1 − δ", "successful insertions under a probe cap", "exact refusal probabilities; safe orders"],
             ["Exact at finite m", "no (loose by Θ(L{sup:3/2}))", "no (orders of magnitude)", "asymptotic and finite-size results", "yes, and validated on the real table"],
             ["Deletions", "not treated", "not treated", "not treated", "exact undo; only stack order is safe for every table"],
             ["Probe limit", "455 (load 3/4, 10⁻⁶)", "not a design rule", "not a design rule", "258 (load 3/4, 10⁻⁶, m = 2¹⁶)"]],
            [2.3, 3.4, 3.4, 3.4, 3.8], "Comparison with the related work used for evaluation.", sz=18)
    d.table([["scheme", "insertion-only: worst / amortised", "stack discipline: worst = amortised"]] + [["linear probing", "δ⁻² / δ⁻¹", "δ⁻²"], ["uniform probing", "δ⁻¹ / log δ⁻¹", "δ⁻¹"], ["funnel hashing (greedy)", "log² δ⁻¹ / log δ⁻¹", "log² δ⁻¹"], ["elastic hashing (non-greedy)", "log δ⁻¹ / 1", "log δ⁻¹"], ["interlinear probing (stable)", "δ⁻¹ log δ⁻¹ / δ⁻¹", "δ⁻¹ log δ⁻¹"]], [5.0, 5.6, 5.6],
            "Expected probe index at load 1 − δ (orders of magnitude, δ → 0). Under stack discipline the worst push equals the average over the worst oblivious schedule (Theorem 6). Linear and uniform probing: Knuth {cite:knuth3} and Yao {cite:yao1985}; funnel and elastic hashing: {cite:FarachColtonKrapivinKuszmaul2024}; interlinear probing: {cite:KrapivinKuszmaulWang2026} (upper bounds).", sz=19)


def section5(d):
    d.heading("5. Conclusion and scope for future work")
    d.bullets([
        "{b:The proposed work.} We asked what the last-in-first-out discipline of scopes gives an open-addressing table that must live in one fixed buffer, and answered with exact statements: popping the newest key is an exact undo, stack order is the only universally safe order, and the refusal probability of a probe-limited table is exactly computable.",
        "{b:Existing methodology.} Analyses of open addressing cover insertions, deletions are known to be difficult, and probe limits were set with Chernoff-type bounds that are loose by a factor growing like {i:L}{sup:3/2}.",
        "{b:Proposed methodology and its advantage.} Reducing a push/pop workload to an insertion-only table (Theorem 2) transfers every insertion-only result; the exact laws replace loose bounds, and the schedule-free bound covers a persistent set of names with bounded churn for the whole life of the table.",
        "{b:Tools.} Exact rational arithmetic, exhaustive enumeration, the real C++ table and an independent derivation were used, and one script regenerates every number, table and figure.",
        "{b:Results.} At load 3/4 and failure probability 10⁻⁶ the exact probe limit is 258 against 455 for the Chernoff-type rule; the whole-fill limit is 306 against 402; guarding against any schedule with eight names of churn costs 410 against 349 for one level. The law agrees with the real table (all |z| ≤ 1.96, no mismatch), and 16.4%–17.9% of the buffer is saved by the compact layout.",
        "{b:Scope for future work.} A limit law for refusal probabilities on wide and deep scope trees is open: simulations show that failures cluster on shared prefixes, a mixture structure for which we found no clean statistic. An unconditional version of the probe-complexity separation needs a lower bound for stable schemes under stack discipline. Compilers that keep several scopes alive at once, a measured timing channel for the key results, and a machine-checked version of the proofs are further directions.",
    ])


def references_section(d, order):
    d.heading("6. References")
    entries = [R.text(k) for k in order]
    d.references(entries)


def declarations(d):
    d.heading("Author Contributions")
    d.para("Shubhi Singh designed and implemented STRATA, its tests and benchmarks and wrote the earlier empirical study this work extends. Adhyan Jain directed the theoretical work: the adversarial review of the earlier study, the statements and proofs of the theory, the verification programs and the interactive page. Both authors are responsible for the content. Contribution roles follow the repository record (docs/CONTRIBUTIONS.md and docs/AI_USE_DISCLOSURE.md).")
    d.heading("Acknowledgements")
    d.para("The authors thank the maintainers of the open-source tools used: GCC, Python, TeX Live, LibreOffice, React and Vite.")
    d.heading("Funding")
    d.para("This research received no external funding.")
    d.heading("Competing interests")
    d.para("The authors declare no competing interests.")
    if INCLUDE_AI_DISCLOSURE:   # off in the version for the course; switch on if a venue requires the statement
        d.heading("Use of AI assistance")
        d.para("The software, tests, benchmarks and the earlier empirical manuscript that this article extends were produced by an AI coding assistant working in the environment of the first author, under the authors' direction, as recorded in the repository. This article was developed with the same kind of tool: Anthropic's Claude (model Sonnet 5.5, through the Claude Code command-line tool) was used, at one author's direction, to review the earlier work adversarially, to propose and derive the theorems and proofs, to write the verification programs, to build the interactive page and to draft the text. Every number in the article is produced by those programs, which can be re-run. The tool is not an author; the listed authors are responsible for the content. The proofs are pen-and-paper and were checked by exhaustive and statistical programs, not by a proof assistant.")
    d.heading("Data and code availability")
    d.para("All sources, programs, traces and raw results are in the public repository {cite:strata}; the directory {code:theory/} holds the full manuscript with every proof, the verification programs and the interactive page, and {code:bash theory/verify/run_all.sh} regenerates every number, table and figure of this article.")
