"""Final manuscript in the course template: STRATA as a system, as measured, and as proved.

It joins the empirical study (paper/, run 20261013-143828-paper) and the theory manuscript (theory/) into one article
that follows the section plan of the course template ("Paper Template-2.docx").  It reuses the template builder of
theory/template (build_docx.Doc, package) and its verified reference records; every number in a table comes from a
generated file (paper/generated_numbers.tex, paper/tables/*.tex, theory/paper/tables/*.tex) and none is typed here
except in prose that quotes those files.

Usage:  python manuscript/final/build_final.py ["/path/to/Paper Template-2.docx"]
Output: manuscript/final/build/STRATA_Final_Manuscript.docx and .pdf (PDF through Microsoft Word, else LibreOffice).
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TPL = os.path.join(ROOT, "theory", "template")
sys.path.insert(0, TPL)
import build_docx                                               # noqa: E402  (Doc, package, find_figure)
import content as theory                                         # noqa: E402  (references, related works)

OUT_DIR = os.path.join(HERE, "build")
FIGS = os.path.join(HERE, "figs")
build_docx.FIGS = FIGS                                           # look here first, then theory/template/build/figs
_orig_find = build_docx.find_figure


def find_figure(name):
    for base in (FIGS, os.path.join(TPL, "build", "figs"), os.path.join(TPL, "figures")):
        p = os.path.join(base, name)
        if os.path.exists(p): return p
    return _orig_find(name)


build_docx.find_figure = find_figure

# ---------------------------------------------------------------------------------------------------------------------
# generated numbers and tables
NUM = {}
for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(ROOT, "paper", "generated_numbers.tex"), encoding="utf8").read()):
    NUM[m.group(1)] = m.group(2).replace("\\,", " ").replace("$-$", "−").replace("$+$", "+").replace("$", "")


def n(key):
    v = NUM[key]
    v = re.sub(r"(\d(?:\.\d)?)\\!\\times\\!10\^\{(-?\d+)\}", lambda m: "%s×10{sup:%s}" % (m.group(1), m.group(2).replace("-", "−")), v)
    return v


def cell(c):
    """One LaTeX table cell to template markup: superscripts as real superscripts, not Unicode digits."""
    c = c.strip().replace("\\,", " ").replace("$-$", "−").replace("$+$", "+").replace("\\%", "%").replace("{=}", " = ")
    c = c.replace("\\varepsilon", "ε").replace("\\alpha", "α").replace("\\infty", "∞").replace("\\to", "→").replace("\\mathrm", "")
    c = re.sub(r"\^\{?(-?\d+)\}?", lambda m: "{sup:%s}" % m.group(1).replace("-", "−"), c)
    c = c.replace("$", "").replace("{", "{").strip()
    c = re.sub(r"(?<!sup:)\{([^{}:]*)\}", r"\1", c)               # drop grouping braces, keep {sup:..}
    return {"1e-06": "10{sup:−6}", "1e-6": "10{sup:−6}", "0.0001": "10{sup:−4}", "0.01": "10{sup:−2}", "n.e.": "n.e."}.get(c, c)


def rows_paper(name):
    """Rows of a generated table of the empirical paper (lines with & ... \\\\ before \\hline)."""
    out = []
    for l in open(os.path.join(ROOT, "paper", "tables", name), encoding="utf8"):
        if l.startswith("%") or "&" not in l: continue
        out.append([cell(c) for c in l.replace("\\\\", "").split("&")])
    return out


def rows_theory(name):
    out, on = [], False
    for l in open(os.path.join(ROOT, "theory", "paper", "tables", name), encoding="utf8"):
        if "\\midrule" in l: on = True; continue
        if "\\bottomrule" in l: break
        if on and "&" in l and "\\\\" in l: out.append([cell(c) for c in l.replace("\\\\", "").split("&")])
    return out


# the frontend's recorded figures (frontend/web/src/data/recorded.json, generated from results/ by make-results.mjs)
import json, math                                                # noqa: E402
REC = json.load(open(os.path.join(ROOT, "frontend", "web", "src", "data", "recorded.json"), encoding="utf8"))
REC_STRATA = next(c for c in REC["correctness"] if c["impl"] == "strata")
REC_STD = next(v for v in REC["vsAll"] if v["impl"] == "std_undo_log")
_cut = [100 * (1 - t["strataAllocs"] / t["stdAllocs"]) for t in REC["perTrace"]]
ALLOC_STD = (math.floor(min(_cut) * 10) / 10, math.floor(max(_cut) * 10) / 10)
fmt_int = lambda v: "{:,}".format(v).replace(",", " ")

# ---------------------------------------------------------------------------------------------------------------------
# references: the theory manuscript's verified records, plus the tools of the empirical study
EXTRA_REFS = {
    "strata": "Singh, Shubhi, and Adhyan Jain. (2026) “STRATA: a scoped symbol table in one caller-supplied buffer.” Public repository cdesproject (https://github.com/shubhisingh1510/cdesproject); paper/, theory/ and frontend/ hold the sources of this article, its proofs, its measurements and the interactive tool.",
    "tcc": "Bellard, Fabrice, and TinyCC contributors. (2026) “Tiny C Compiler, commit 43c7708.” https://repo.or.cz/tinycc.git. Accessed October 2026.",
    "chibicc": "Ueyama, Rui. (2026) “chibicc: a small C compiler, commit 90d1f7f.” https://github.com/rui314/chibicc. Accessed October 2026.",
    "phmap": "Popovitch, Gregory. (2023) “The Parallel Hashmap, version 1.4.1.” https://github.com/greg7mdp/parallel-hashmap. Accessed October 2026.",
}
_orig_text = theory.R.text


def ref_text(key):
    return EXTRA_REFS[key] if key in EXTRA_REFS else _orig_text(key)


theory.R.text = ref_text


def pretty(text):
    """ASCII math of the reference summaries to symbols; unlike the original, a ^ never swallows a closing parenthesis."""
    for a, b in [("Omega~", "Ω̃"), ("O~", "Õ"), ("Theta", "Θ"), ("Omega", "Ω"), ("delta", "δ"), ("epsilon", "ε"), ("eps", "ε"),
                 ("<=", "≤"), (">=", "≥"), ("sqrt(", "√(")]:
        text = text.replace(a, b)
    text = re.sub(r"\^\((-?[0-9]+(?:\.[0-9]+)?)\)", lambda m: "{sup:%s}" % m.group(1).replace("-", "−"), text)
    text = re.sub(r"\^(-?[0-9]+(?:\.[0-9]+)?)", lambda m: "{sup:%s}" % m.group(1).replace("-", "−"), text)
    text = re.sub(r"\^(Θ\(1\))", r"{sup:\1}", text)
    return text


theory.pretty = pretty                                           # used by theory.related()

# ---------------------------------------------------------------------------------------------------------------------
TITLE = "One Buffer, Every Scope: A Fixed-Memory Symbol Table for Embedded Compilers, Measured on Real Compiler Traces and Analysed Exactly"
AUTHORS = theory.AUTHORS
AFFIL = theory.AFFIL
KEYWORDS = "bounded memory, embedded compilers, linear probing, open addressing, scoped symbol tables, stack discipline"

ABSTRACT = (
    "Every compiler keeps a scoped symbol table that binds names to declarations and forgets them when a block ends, and compilers increasingly run on "
    "microcontrollers, in boot loaders and under fixed memory budgets. "
    "There, the table must live in one fixed buffer, refuse a request cleanly when the buffer is full, and bound the work of every call even on hostile source text. "
    "Textbook and production designs, such as a hash map with an undo log or one map per scope, rely on a general-purpose allocator, "
    "and the analysis of open addressing covers insertions, not the last-in-first-out deletions of scopes. "
    "So their memory is unbounded in advance, their behaviour at the limit is undefined, and their probe limits are set with loose bounds. "
    "We present STRATA, which keeps an open-addressing index, packed identifier records and an undo stack in one caller-supplied buffer and refuses any call that does not fit without changing a single bit. "
    "We prove that popping the newest name is an exact undo, so the table always equals a fresh table of its live names, and that stack order is the only deletion order safe for every table; "
    "we compute the refusal probability of a probe-limited table exactly. "
    "On symbol-table events recorded from a C compiler building eight open-source projects, STRATA answered all " + fmt_int(REC_STRATA["checked"]) + " checked operations correctly, needed a fixed buffer "
    + n("SaveLo") + "–" + n("SaveHi") + "% smaller than a conventional single-buffer table at statistically indistinguishable speed on six of eight traces, made " + n("AllocLo") + "–" + n("AllocHi") + "% fewer allocator calls than its multi-allocation predecessor, "
    "and ran on an emulated 64 KiB Cortex-M3. The exact law cuts the probe limit for a failure probability of 10{sup:−6} at load 3/4 from 455 to 258. "
    "Future work is a refusal law for wide scope trees, real hardware and C++ workloads."
)

INTRO_KEYS = theory.INTRO_KEYS


def front(d):
    d.para(TITLE, jc="center", b=True, sz=28, after=60, line=300)
    d.para(AUTHORS, jc="center", sz=24, after=0, line=300)
    d.para("{i:%s}" % AFFIL, jc="center", sz=22, after=200, line=300)
    d.heading("Abstract")
    d.para(ABSTRACT)
    d.para("{b:Keywords} – %s" % KEYWORDS, before=80)


def intro(d):
    d.heading("1. Introduction")
    d.para("Compilers, interpreters and virtual machines are moving onto small devices. Run-time systems for Arduino-class microcontrollers execute WebAssembly with live code updates {cite:GurdeepSingh2019WARDuino}, and name resolution has become a subject of its own in mainstream language tooling, where the scheduling of name queries and their safety under parallel checking are characterised with scope graphs {cite:Rouvoet2020Knowing,vanAntwerpen2021ScopeStates}. Whatever the language, one data structure sits at the centre of name resolution: a {i:scoped symbol table} that binds identifiers to declarations, forgets the declarations of a block when the block ends, and is consulted at every use of a name.")
    d.para("{b:Problem and motivation.} When the compiler runs on a microcontroller, in a boot loader or under a fixed allocation, three requirements appear. The table must live in {i:one fixed buffer}, because the allocator is absent or must not be called. It must {i:refuse} a request that does not fit and stay usable afterwards, because running out of memory is an expected event, not a crash. And the {i:work} of one call must be bounded, even when the source text comes from someone else: algorithmic denial of service against hash-based structures is a demonstrated attack class, and low-rate adversarial traffic reduced a software packet classifier to about 12% of its capacity {cite:csikor2019tse}.")
    d.para("{b:Existing methodologies.} The textbook implementation, also used by LLVM, is a hash table from names to their innermost declaration together with an undo log that restores what a scope hid {cite:appel1998,graham1979,llvmsht}; the other classical design keeps one hash map per scope. Both obtain memory from the allocator one node at a time. On the analytical side, open addressing has a long tradition, from Knuth's analysis of linear probing {cite:knuth3} to exact distributional results {cite:janson2016}, and recent years have been productive: iceberg hashing achieves constant time at load 1 − o(1) {cite:BenderEtAl2023Iceberg}, the time/space trade-off of hash tables has been determined for a large class of structures {cite:BenderEtAl2022TimeSpace}, two-way probing makes the worst unsuccessful search O(log log n) {cite:dalal2023twoway}, and quadratic probing has been analysed in a smoothed model {cite:HuKuszmaulLiangWalzerYuZhou2026}.")
    d.para("Keyed hash functions such as SipHash are the standard defence against chosen collisions, and reduced-round variants have been cryptanalysed {cite:he2023siphash}. The combinatorics of the event that every key finds a place are those of parking functions, whose probabilistic properties are now understood in detail {cite:KenyonYin2023}.")
    d.para("{b:Shortfall.} None of these designs gives a table whose memory is fixed in advance, whose behaviour at the limit is defined, and whose cost per call is bounded. Allocator-based tables have none of the three properties; their memory is spread over thousands of small allocations, so even measuring the space a compilation needs is indirect.")
    d.para("The analysis does not cover the case either. It concerns insertions, or deletions in random order; the deletion order of a scoped table is last-in-first-out, and for that order the state of an open-addressing table, its safe deletion orders and its refusal probabilities had not been stated exactly. Probe limits are chosen with Chernoff-type bounds that lose a factor growing with the limit, and whether a probe-limited table refuses an honest name is usually answered by simulation, although tables of a few hundred to a few thousand cells are exactly where asymptotic formulas are inaccurate.")
    d.para("{b:Proposed work.} We present STRATA, a scoped symbol table that keeps its open-addressing index, one packed record per visible name and its undo stack in one caller-supplied buffer of 32-bit words, never calls the allocator after it is created, and refuses any call that does not fit without changing a single bit {cite:strata}. We measure it against five other tables on symbol-table events recorded from a real C compiler compiling eight open-source projects, on a second compiler, under hash flooding and on an emulated microcontroller, and check every answer against an independent reference model.")
    d.para("We then analyse why the design works and how to configure it. Popping the newest key by clearing its cell is an {i:exact undo} for every open-addressing scheme that does not move keys, so the table always equals the insertion-only table of its live names, and stack order is the only deletion order safe for every table. On that basis the refusal probability of a probe-limited table is exactly computable, which turns the probe limit and the buffer size into design values instead of guesses. Finally, an interactive tool lets a reader paste a C program, see every name, scope and use, and run the program's symbol-table calls on the real table.")
    d.para("{b:Structure.} Section 2 reviews fifteen recent works and their research gaps. Section 3 presents the system: the problem, the architecture, the buffer layout, the exact undo and refusal laws with their equations, the modules, the flow and three algorithms. Section 4 describes the implementation and tools and analyses eight performance metrics with a comparison against related work. Section 5 concludes, Section 6 lists the references and the declarations follow.")


def section3(d):
    d.heading("3. Proposed work/system")
    d.heading("3.1 Problem formulation", 2)
    d.para("A scoped symbol table receives a sequence of four calls from the compiler's front end: {code:declare(x, v)} binds name {i:x} to value and type {i:v} in the current scope, {code:lookup(x)} returns the innermost visible binding of {i:x}, {code:enter_scope()} opens a block and {code:exit_scope()} closes it, after which every binding made in the block is gone and every binding it hid is visible again. A redeclaration in the same scope is reported. The deletion order is therefore fixed by the program: the bindings of a scope disappear together and newest first.")
    d.para("We require (R1) that all state lives in one buffer of {i:C} bytes supplied by the caller, with no allocator call after creation; (R2) that a call which does not fit is refused with a status code and leaves the table bit-for-bit unchanged; (R3) that, in bounded mode, every call examines at most {i:L} index slots whatever the names are; and (R4) that every answer equals that of a reference model of scoped binding. The questions are how small {i:C} can be on real programs, what the design costs in time against allocator-based and allocator-free alternatives, and how {i:L} and {i:C} should be chosen so that an honest program is refused with a stated, small probability.")

    d.heading("3.2 System architecture", 2)
    d.figure("fig_d1.png", "Architecture. The compiler front end issues four calls to a STRATA table that keeps its open-addressing index, packed identifier records and undo stack in one fixed buffer. The analysis layer models the index and produces design rules for the probe limit, the buffer size and the key policy.", 16.4)
    d.para("Figure 1 shows the system. The compiler front end issues the four calls. STRATA keeps the index, one packed record per visible name and the undo stack of the open scopes in one caller-provided buffer. A declaration that hides an outer name saves the old binding on the undo stack, and leaving a scope pops the entries in reverse order. Space for the record and the undo entry is reserved before anything is written, so a request that does not fit returns {code:kNoMemory} and leaves the table unchanged; in bounded mode a request whose probe sequence meets {i:L} occupied slots returns {code:kProbeLimit}, also without change.")
    d.para("Below the table, the analysis layer mirrors the requirements: exact undo and safe deletion orders explain why scope exit needs no tombstones (R2, R4), the refusal laws give the probability of {code:kProbeLimit} (R3), the key-lifetime results say when the laws hold against chosen names, and the space ledger explains the buffer size (R1). The dashed arrow marks the modelling step: the index of the table is a ring of cells, and everything proved about the ring is a statement about the index. Around both sits the measurement harness of Section 4, which replays recorded compiler traces on STRATA and five other tables.")

    d.heading("3.3 Detailed methodology", 2)
    d.heading("3.3.1 One buffer, four regions", 2)
    d.figure("fig_layout.png", "Layout of the buffer and of the three kinds of undo entries. The index and the identifier records grow from the start of the buffer, the undo stack from its end; the free space between them is shared.", 15.0)
    d.para("All state lives in one array of 32-bit words (Figure 2). The {i:index} occupies the first {i:m} words, {i:m} a power of two; a slot is zero when empty and otherwise holds an 8-bit fingerprint and a 24-bit reference to an identifier record. Collisions are resolved by linear probing, and the index is kept at most three quarters full. The {i:identifier records} follow the index and grow upward, one per distinct visible name; a record holds the value of the name's innermost declaration, a metadata word and the name, packed five characters to a word when it consists of letters, digits and underscores. A lookup therefore ends in the record it finds, whatever the depth of shadowing. The {i:undo stack} grows downward from the end of the buffer: a new name pushes one word (its index slot), a declaration that hides an outer one pushes three (the record reference and the overwritten value, type and depth), and entering a scope pushes a two-word mark. With {i:n} distinct visible names, {i:d} live declarations and {i:s} open scopes, the buffer is used up to")
    d.equation(r"M=m+1+\sum_{x}\left(2+w(x)\right)+n+3\,(d-n)+2\,s")
    d.para("words, where {i:w}({i:x}) is the number of name words. A declaration is accepted only if the words it needs fit between the two growing ends:")
    d.equation(r"\mathrm{accept}\;\Leftrightarrow\;M+\Delta M\le\frac{C}{4}")
    d.para("with Δ{i:M} = 3 + {i:w}({i:x}) words for a new name and 3 words for a declaration that hides an outer one. Otherwise the call returns {code:kNoMemory} before writing anything (all-or-nothing refusal). The conventional allocator-free table used as the fair baseline stores, per declaration, a chain link, the hash, the value, a length-and-depth word and the unpacked name; the difference between the two layouts is quantified exactly by the space ledger of Metric 4.")

    d.heading("3.3.2 Exact undo and safe deletion orders", 2)
    d.para("Write Ins({i:a}{sub:1},…,{i:a}{sub:n}) for the table obtained by inserting keys in this order into an empty table. {b:Theorem 2 (undo).} For every open-addressing rule that never moves a key and chooses a cell from the occupied set and the key's own probe sequence, after any sequence of pushes and pops the table at time {i:t} is the insertion-only table of the live keys in push order:")
    d.equation(r"T_t=\mathrm{Ins}\left(a_1,\dots,a_{n_t}\right)")
    d.figure("fig_d2.png", "Exact undo. Pushing {i:x} writes one empty cell; popping {i:x} clears it, and the table is identical in every cell to the table before the push.", 15.0)
    d.para("The proof is by induction: an insertion changes exactly one empty cell, chosen from the occupied set alone, so clearing that cell restores the previous table (Figure 3). This is why STRATA's scope exit needs no tombstones and no rehashing: the newest key lies on no other key's probe path. A key {i:y} {i:depends on} {i:x}, written {i:y} ◁ {i:x}, if the cell of {i:x} lies strictly before the cell of {i:y} on the probe path of {i:y}:")
    d.equation(r"y\lhd x\;\Leftrightarrow\;c(x)\in\{h(y),\,h(y)+1,\,\dots,\,c(y)-1\}")
    d.figure("fig_d3.png", "Dependency and orphans. Key {i:y} probed cells 2, 3 and 4 before it was stored in cell 5, so it depends on {i:u}, {i:v} and {i:w}. Clearing {i:w} first leaves a hole on its path and orphans {i:y}; clearing the newest key never does.", 14.2)
    d.para("{b:Theorem 4.} For a given table, the safe orders of clearing cells are exactly the linear extensions of ◁, and stack order is the only order safe for every hash assignment. The number of keys that depend on a key is a queue length minus one; its mean and the limiting fraction of keys with no dependents at load α = {i:n}/{i:m} are")
    d.equation(r"\mathbb{E}[\mathrm{orph}]=\frac{\alpha}{2(1-\alpha)},\qquad \mathbb{P}(\mathrm{orph}=0)\to\frac{(1-\alpha)(e^{\alpha}-1)}{\alpha}")
    d.para("At load 3/4 the mean is 1.5 and only 37% of keys could be removed out of order without harm, so a table that did not follow stack order would need tombstones. The limit law is Janson's {cite:janson2005} and the single-deletion test Sanders' {cite:sanders2018}; the characterisation of safe orders, the finite-size law and the reading as orphans are new as stated.")

    d.heading("3.3.3 The exact refusal law and the probe limit", 2)
    d.para("In bounded mode the index is static and a declaration that finds no empty slot within {i:L} probes is refused. Let {i:n} = {i:m} − {i:k} keys occupy the ring with independent uniform homes (the model for a keyed hash). {b:Theorem 7.} The probability that a new key finds its first {i:L} cells occupied is")
    d.equation(r"R_m(n,L)=\frac{k}{m}\sum_{g=L+1}^{n+1}(g-L)\,\pi_g,\qquad \pi_g=\frac{B(g)\,Q_{k-1}(m-g)}{Q_k(m)}")
    d.equation(r"B(g)=\frac{g^{g-1}}{g!},\qquad Q_j(x)=\frac{j\,x^{x-j-1}}{(x-j)!}")
    d.para("The ring is cut at its {i:k} empty cells into blocks whose sizes are Borel distributed; a block of {i:g} cells contains ({i:g} − {i:L}){sup:+} homes that would be refused. The tail is of order ρ{sup:L} L{sup:−3/2} with ρ = α e{sup:1−α}, so the Chernoff-type bound previously used to choose {i:L} is loose by a factor growing like L{sup:3/2}. The law is classical as a quantity (Knuth {cite:knuth3}; Janson and Viola {cite:janson2016}); the elementary derivation, the finite-size sum, its validation on the real table and its use for design are the contribution. Because of Theorem 2, the same law holds after any number of push/pop pairs on a fixed set of persistent names, and Adhyan Jain's manuscript extends it to a whole fill, an unlimited run and bounded churn above a persistent trunk.")

    d.heading("3.3.4 Keyed hash and hash flooding", 2)
    d.para("With the default hash, identifiers can be crafted to collide for every seed, which makes each declaration walk a long probe sequence. STRATA offers a keyed HalfSipHash-1-3 and the probe limit. The law above assumes independent homes, which a key provides only if it is independent of everything the adversary has seen: with a fresh key per table the law holds against arbitrary names, while one persistent key combined with a probe-length oracle lets an adversary plant names that make the limit refuse honest ones (Propositions 13–15 of the theory manuscript). The design rule is therefore a new key per translation unit, derived from a device secret and a counter.")

    d.heading("3.4 Modules and their functions", 2)
    d.table([["Module", "Function", "Where", "Checked by"],
             ["Table core", "declare, lookup, enter, exit in one buffer; all-or-nothing refusal", "include/strata/strata.hpp (C++14, header only)", "unit, differential and exhaustive tests"],
             ["Bounded mode", "static index, probe limit L, keyed hash", "strata.hpp", "fuzzing; QEMU bounded runs"],
             ["Trace recorder", "logs every symbol-table call of a real compiler", "tools/tcc-trace, tools/chibicc", "identical assembly output"],
             ["Replay harness", "replays traces on six tables; heap, allocator calls, time, smallest buffer", "benchmarks/", "reference model on every answer"],
             ["Exact undo and orders", "Theorem 2, Theorem 4, orphan law", "theory/verify", "enumeration in exact rationals"],
             ["Refusal law and design", "R{sub:m}(n, L); smallest L for a target ε", "theory/verify", "enumeration; real table (z-scores)"],
             ["Space ledger", "exact word accounting of five layouts", "theory/verify/space_model.py", "reproduces 24 measured buffers"],
             ["Interactive tool", "Analyse your code, Live lab, results and theory pages", "frontend/", "npm test (37 checks)"]],
            [3.0, 5.6, 4.4, 3.3], "Modules of the work, what each does, where it lives in the repository and how it is checked.", sz=19)

    d.heading("3.5 Flow of the operations", 2)
    d.figure("fig_d4.png", "Flow of a declaration and of a scope exit. A declaration is refused, with the table unchanged, when no empty cell is found within {i:L} probes or when the record and its undo entry do not fit; a scope exit pops the undo entries in reverse order.", 14.6)
    d.para("Figure 5 gives the flow. A declaration computes the home slot and probes at most {i:L} slots. If no empty slot is found it answers {code:kProbeLimit}; if the record and the undo entry do not fit it answers {code:kNoMemory}; in both cases nothing has been written. Otherwise it writes the record, sets the index slot and, if the name hides an outer one, pushes an undo entry. Leaving a scope pops the entries of that scope newest first: a new name has its slot cleared, a hidden name has its binding restored, and the record stack is reset to the scope's mark. By Theorem 2 the table then equals the table that existed before the scope was entered.")
    d.para("The two refusal exits are exactly what the analysis quantifies: {code:kProbeLimit} is the event of the refusal law, and {code:kNoMemory} is governed by the space ledger and the measured smallest buffers. Both are all-or-nothing, which is what makes the exact undo meaningful: a refused call never leaves a half-written state.")

    d.heading("3.6 Algorithms", 2)
    d.algorithm("Declaration and scope exit (all-or-nothing)", [
        (0, "{b:procedure} DECLARE({i:x}, {i:v})"),
        (1, "{i:k} ← PackAndHash({i:x}); ({i:r}, {i:e}) ← Find({i:k}, {i:L})      ▹ record, or first empty slot within {i:L} probes"),
        (1, "{b:if} {i:r} exists {b:and} depth({i:r}) = current depth {b:then} overwrite value; {b:return} kRedeclared"),
        (1, "{b:if} {i:r} exists {b:then}  {b:if} fewer than 3 free words {b:then return} kNoMemory"),
        (2, "push ({i:r}, value, type, depth) on the undo stack; overwrite the binding; {b:return} kOk"),
        (1, "{b:if} fewer than 3 + {i:w}({i:x}) free words {b:then return} kNoMemory      ▹ nothing written"),
        (1, "{b:if} {i:e} = nil {b:then return} kProbeLimit      ▹ nothing written"),
        (1, "append the record; store fingerprint and reference in slot {i:e}; push {i:e} on the undo stack; {b:return} kOk"),
        (0, "{b:procedure} EXIT_SCOPE()"),
        (1, "{b:while} the top undo entry is not the scope's mark {b:do}"),
        (2, "{b:if} it names a slot {b:then} clear the slot {b:else} restore the saved binding"),
        (1, "reset the record stack to the mark; pop the mark"),
    ], caption="Algorithm 1 has the form search, reserve, write: nothing is written before the last point at which the call can be refused. EXIT_SCOPE clears exactly the slots DECLARE wrote, newest first, so Theorem 2 applies and no tombstone is needed.")
    d.algorithm("Smallest fixed buffer of a trace (64-byte resolution)", [
        (0, "{b:input} trace {i:T}, table variant; {b:output} the smallest buffer with which {i:T} replays without a refusal"),
        (1, "{i:lo} ← 128; {i:hi} ← 64 MiB      ▹ {i:hi} must pass, else report “does not fit”"),
        (1, "{b:while} {i:hi} − {i:lo} > 64 {b:do}"),
        (2, "{i:mid} ← ⌊({i:lo} + {i:hi})/2⌋ rounded down to a multiple of 64"),
        (2, "{b:if} Replay({i:T}, {i:mid}) refuses nothing {b:then} {i:hi} ← {i:mid} {b:else} {i:lo} ← {i:mid}"),
        (1, "{b:return} {i:hi}      ▹ the same search runs for STRATA and the conventional table"),
    ], caption="Algorithm 2 is benchmarks/budget_main.cpp. Because sizing is not perfectly monotone, the harness re-checks the result at 1×, 1.25×, 2× and 4× the buffer and reports any refusal.")
    d.algorithm("Design rule: smallest probe limit for a target failure probability", [
        (0, "{b:input} {i:m}, {i:n}, target ε; {b:output} the smallest {i:L} with R{sub:m}({i:n}, {i:L}) ≤ ε"),
        (1, "{i:lo} ← 2; {i:hi} ← {i:m}"),
        (1, "{b:while} {i:lo} < {i:hi} {b:do}"),
        (2, "{i:mid} ← ⌊({i:lo} + {i:hi})/2⌋"),
        (2, "{b:if} R{sub:m}({i:n}, {i:mid}) ≤ ε {b:then} {i:hi} ← {i:mid} {b:else} {i:lo} ← {i:mid} + 1"),
        (1, "{b:return} {i:lo}"),
    ], caption="Algorithm 3 turns the exact law (Equation 6) into a design value; R{sub:m} decreases in {i:L}, so bisection applies.")
    d.para("{b:Contribution of the team.} (C1) The STRATA table: one buffer, all-or-nothing refusal, exact scope exit, bounded mode. (C2) A measurement method on recorded compiler traces with a reference model, a fair allocator-free baseline and paired, interleaved timing. (C3) Exact undo, safe deletion orders and the exact refusal law used as design rules, with a space ledger that explains the measured buffer saving. (C4) An interactive tool that runs any pasted C program's symbol-table calls on the real table.")


def section4(d):
    d.heading("4. Implementation and result analysis")
    d.heading("4.1 Tools, configuration and commands", 2)
    d.para("STRATA is a header-only C++14 library ({code:include/strata/strata.hpp}, " + n("HeaderLines") + " lines) compiled with " + n("EnvCompiler") + " at {code:-O2} {cite:ISO14882_2014}. Workloads were recorded by adding logging to the Tiny C Compiler {cite:tcc} at the points where it looks up an identifier, pushes a symbol and opens or closes a scope, and compiling eight open-source C projects at pinned versions; a second set of traces comes from an instrumented chibicc {cite:chibicc}. The harness replays each trace on STRATA, the conventional allocator-free single-buffer table, an undo-log table on std::unordered_map (the algorithm of LLVM's ScopedHashTable {cite:llvmsht}), the same on a Swiss-table map {cite:phmap}, one map per scope, and an interned Swiss flat map. Timing used " + n("Rounds") + " paired, interleaved rounds per trace on an " + n("EnvCPU") + " under WSL 2, with 95% bootstrap intervals; heap peak and allocator calls are counted by a replacement allocator.")
    d.para("The bare-metal run cross-compiles the same header with arm-none-eabi-g++ for the mps2-an385 board (Cortex-M3) and runs it under QEMU {cite:Bellard2005QEMU,QEMUDocsMPS2} with RAM limited to 64 KiB, no heap and no operating system. The commands are {code:bash scripts/test.sh} (unit and differential tests), {code:bash scripts/run_all.sh <label>} (all measurements), {code:python scripts/analyze.py} and {code:manuscript/tools/make_numbers.py} (every number of this article) and {code:bash theory/verify/run_all.sh} (every check of the theory). The interactive tool is a React {cite:ReactDocs} and Vite {cite:ViteDocs} application whose local server runs a C++ engine linked with the real table ({code:cd frontend/web; npm start}); Figure 6 shows its Analyse page.")
    d.figure("screenshot_analyse.png", "The implementation tool: “Analyse your code”. A pasted C program is translated into the calls a compiler makes on its symbol table, which run on the real strata::Table in the local engine; the page lists every name with its type, scope, line and uses, the names it hides, problems such as unused names, and the smallest buffer that holds the program.", 16.0)

    d.heading("4.2 Parameter setup", 2)
    d.table([["Parameter", "Values", "Used for"],
             ["Compiler traces", "8 projects (cJSON, littlefs, zlib, Lua, FreeRTOS, Mbed TLS, TinyCC, SQLite), " + n("NTracesAll") + " traces in all with chibicc", "all metrics"],
             ["Tables compared", "STRATA, conventional single-buffer table, std map + undo log, Swiss map + undo log, map per scope, interned Swiss map", "memory, time"],
             ["Timing", n("Rounds") + " paired interleaved rounds; median ratio, 95% bootstrap interval", "replay time"],
             ["Buffer search", "128 B to 64 MiB, 64-byte resolution (Algorithm 2)", "smallest buffer"],
             ["Index load (bounded mode)", "at most 3/4; probe limit L = 512 in the library documentation", "probe limit"],
             ["Exact law", "m = 2{sup:8}…2{sup:16} and m → ∞; ε = 10{sup:−6}, 10{sup:−9}; load 3/8 … 3/4", "design table"],
             ["Real-table trials", "400 000 per setting, 7 settings, keyed hash, fresh key per trial", "law validation"],
             ["Hash flooding", "1 024 to " + n("FloodN") + " names of 150 characters, median of 5 runs", "robustness"],
             ["Embedded target", "Cortex-M3 (mps2-an385) in QEMU, 64 KiB RAM", "fit, code size"],
             ["Machine", n("EnvCPU") + ", " + n("EnvCompiler") + ", WSL 2", "all timings"]],
            [3.6, 9.2, 3.4], "Parameters of the experiments.", sz=19)

    d.heading("4.3 Performance analysis", 2)
    d.para("Eight metrics are reported, each with a table or figure and the reason for the result. The workloads are summarised in Table 4.")
    wl = rows_paper("tab_workloads.tex")
    d.table([["Project", "Units", "Events", "Declares", "Lookups", "Names", "Peak live", "Depth"]] + wl,
            [2.4, 1.4, 2.2, 2.1, 2.1, 1.8, 2.0, 1.6], "The eight compiler traces. “Names” counts distinct identifiers; “Peak live” is the largest number of simultaneously live declarations.", align=["left"] + ["right"] * 7, sz=19)

    d.heading("Metric 1: correctness", 2)
    d.table([["Check", "Size", "Result"],
             ["Answers on the eight compiler traces, against the reference model", fmt_int(REC_STRATA["checked"]) + " lookups and declarations", "%d wrong" % REC_STRATA["wrong"]],
             ["Unit and differential tests", "2 732 358 checks", "0 failed"],
             ["Exhaustive enumeration of short operation sequences", n("ExhSeq") + " sequences, " + n("ExhOps") + " operations", "0 failures"],
             ["Refused calls leave the state unchanged (digest compared)", n("ExhRefusals") + " refusals in the enumeration", "all unchanged"],
             ["chibicc with STRATA inside, assembly compared with the original", n("ChibiUnitsOK") + " of " + n("ChibiUnitsOK") + " compiled units", "byte-identical"],
             ["Bare-metal runs, checksum against the desktop run", n("EmbPass") + " default + " + n("EmbBoundedPass") + " bounded", "all pass"]],
            [8.0, 5.0, 3.2], "Correctness evidence. Every answer of every replay is compared with an independent reference model of scoped binding.", sz=19)
    d.para("STRATA gave no wrong answer and no check failed. The enumeration matters most for requirement R2: it covers every short sequence of calls on small buffers, including every way a call can be refused, and compares the table's digest before and after each refusal.")

    d.heading("Metric 2: smallest fixed buffer", 2)
    d.figure("fig_minbuffer.png", "Smallest fixed buffer that replays each trace without a refusal, for STRATA and the conventional single-buffer table (Algorithm 2).", 13.6)
    mem = rows_paper("tab_memory.tex")
    d.table([["Project", "STRATA (KiB)", "Conventional (KiB)", "Saving (%)", "Bytes per live decl."]] + [[r[0], r[1], r[2], r[3], r[4]] for r in mem],
            [3.0, 3.0, 3.6, 2.8, 3.8], "Smallest fixed buffer on the eight compiler traces.", align=["left"] + ["right"] * 4, sz=19)
    d.para("STRATA needs a buffer " + n("SaveLo") + "–" + n("SaveHi") + "% smaller than the conventional allocator-free table on every trace, from " + n("MinBufLo") + " KiB (zlib) to " + n("MinBufHi") + " KiB (TinyCC). The saving is nearly constant because it is a per-declaration difference in layout; Metric 4 decomposes it exactly.")

    d.heading("Metric 3: heap peak and allocator calls", 2)
    d.table([["Project", "STRATA", "Conventional", "METIS-X", "Map per scope", "Undo log", "Interned map"]] + [[r[0]] + r[5:11] for r in mem],
            [2.5, 2.0, 2.4, 2.1, 2.5, 2.1, 2.5], "Heap peak in growable mode (KiB).", align=["left"] + ["right"] * 6, sz=19)
    d.para("Against tables that allocate node by node the difference is large: STRATA's heap peak is " + n("HeapMetisLo") + "–" + n("HeapMetisHi") + "% (median " + n("HeapMetisMed") + "%) below that of METIS-X, its multi-allocation predecessor, and it makes " + n("AllocLo") + "–" + n("AllocHi") + "% fewer allocator calls. The conventional single-buffer table reaches the same heap peak as STRATA on " + n("HeapSameArena") + " of 8 traces in growable mode, because both grow one block in steps; most of the gain over allocator-based tables therefore comes from keeping everything in one allocation-free buffer, not from the compact layout.")

    d.heading("Metric 4: where the buffer saving comes from (space ledger)", 2)
    d.figure("fig_p6.png", "Saving of the compact layout over the conventional single-buffer layout on the eight traces, split into the stored hash word and name packing (space ledger).", 15.0)
    lad = rows_theory("tab_ladder.tex")
    d.table([["trace", "C{sub:0} (KiB)", "C{sub:1}", "S", "hash %", "pack %", "total %"]] + [[r[0], r[1], r[2], r[5], r[6], r[7], r[8]] for r in lad],
            [2.6, 2.3, 2.0, 2.0, 2.2, 2.2, 2.3], "Smallest buffer for the conventional layout (C{sub:0}), the same without a stored hash word (C{sub:1}) and STRATA (S), with the savings of dropping the hash, of packing names, and in total.", align=["left"] + ["right"] * 6, sz=19)
    d.para("The exact word accounting reproduces all 24 measured minimum buffers to the 64-byte resolution of the measurement. Of the 16.4–17.9% saving, 9.2–12.2% comes from not storing a hash word and 5.3–9.0% from packing names; interning with the undo log changes the footprint by between −0.38% and 0.00%. Against a conventional table that does not store the hash, STRATA would be only 5–9% smaller. This corrects the earlier impression that interning was the source of the compactness.")

    d.heading("Metric 5: replay time", 2)
    d.figure("fig_time.png", "Replay time of STRATA relative to the conventional single-buffer table: median paired difference with 95% interval over " + n("Rounds") + " rounds (final code), and the same before an index-rebuild defect was fixed.", 13.6)
    tt = rows_paper("tab_time.tex")
    d.table([["Project", "STRATA vs conventional (%)", "", "STRATA vs METIS-X (%)", ""]] + [[r[0], r[1], r[2], r[3], r[4]] for r in tt],
            [2.4, 5.0, 1.8, 5.0, 1.8], "Replay time: median ratio in percent with 95% bootstrap interval; negative means STRATA is faster; “n.e.” means not established.", align=["left", "left", "center", "left", "center"], sz=18)
    d.para("Against the conventional table STRATA is faster on " + n("ArenaFaster") + " traces, slower on " + n("ArenaSlower") + " and not established on " + n("ArenaNE") + "; where a difference is established it is at most " + n("ArenaAbsMax") + "%. Against METIS-X it is faster on " + n("MetisFaster") + " of 8 traces, by " + n("MetisLo") + "–" + n("MetisHi") + "%. The compact table is therefore not faster than a well-built allocator-free table; its contribution is memory that is fixed, smaller and refusable, at comparable speed. The grey series shows why the method matters: an earlier version rebuilt the index on every buffer growth and appeared 11–34% slower, an artefact the paired design exposed.")

    d.heading("Metric 6: accuracy and tightness of the exact refusal law", 2)
    d.figure("fig_p1.png", "Probability that an insertion needs more than {i:L} probes ({i:m} = 65 536, load 3/4): exact law, Chernoff-type bound and the stored simulation (10 million samples from 500 tables).", 14.6)
    lc = rows_theory("tab_lawcheck.tex")
    d.table([["m", "n", "L", "observed", "exact", "z", "clean trials", "mismatches"]] + lc,
            [1.4, 1.4, 1.2, 2.3, 2.3, 1.5, 3.0, 2.3], "Exact law against the real probe-limited table in 400 000 trials per setting.", align=["right"] * 8, sz=19)
    ds = rows_theory("tab_design.tex")
    d.table([["load", "ε", "m=2{sup:8}", "2{sup:10}", "2{sup:12}", "2{sup:14}", "2{sup:16}", "m→∞", "Chernoff"]] + ds,
            [1.4, 1.6, 1.7, 1.5, 1.5, 1.5, 1.5, 1.6, 2.1], "Smallest probe limit with per-insertion refusal probability at most ε: exact law against the Chernoff-type rule.", align=["center", "center"] + ["right"] * 7, sz=19)
    d.para("All seven z-scores lie within ±1.96 and the lock-step comparison found no mismatch, so the law describes the implementation, not only the model. At load 3/4 and ε = 10{sup:−6} the exact limit is 258 for 2{sup:16} slots against 455 for the Chernoff-type rule, 43% fewer probes allowed per call; the library's documented limit of 512 corresponds to a refusal probability of about 2.4×10{sup:−11} per declaration at that size and is safe but conservative. A smaller limit bounds the work on hostile input more tightly at a stated failure probability.")

    d.heading("Metric 7: robustness under hash flooding", 2)
    d.figure("fig_flood.png", "Time to declare all names: ordinary names and names crafted to collide in the default hash, with the default hash, the keyed hash and a probe limit (median of 5 runs, log scale).", 12.6)
    fl = rows_paper("tab_flood_scale.tex")
    d.table([["Names", "Ordinary (ms)", "Colliding (ms)", "Slowdown (×)", "Colliding lookups (ms)"]] + fl,
            [2.4, 3.0, 3.0, 2.8, 4.2], "Declaration time with the default hash: ordinary against colliding identifiers.", align=["right"] * 5, sz=19)
    d.para("Identifiers that collide for every seed slow declarations by a factor of " + n("FloodRatio") + " at " + n("FloodN") + " names (" + n("FloodCol") + " ms against " + n("FloodOrd") + " ms), growing roughly quadratically. The keyed hash brings colliding names back to " + n("FloodKeyedRatio") + "× the ordinary time, at a cost of " + n("KeyedLo") + "–" + n("KeyedHi") + "% replay time on ordinary traces, and the probe limit alone refuses colliding names instead of slowing down. Requirement R3 therefore needs the bounded mode.")

    d.heading("Metric 8: fit on a 64 KiB microcontroller", 2)
    d.table([["Quantity", "Value"],
             ["Bare-metal runs passed (default build)", n("EmbPass") + " of 5, checksum equal to the desktop run"],
             ["Bare-metal runs passed (bounded build)", n("EmbBoundedPass") + " of 5"],
             ["STRATA code size", n("EmbCode") + " bytes"],
             ["Stack used", n("EmbStack") + " bytes (default build); 484 bytes (bounded build)"],
             ["Workloads that fit only with STRATA at the same buffer", "3 (FreeRTOS at 48 KiB, Lua at 40 KiB, cJSON at 32 KiB)"]],
            [8.0, 8.0], "Cortex-M3 (mps2-an385) under QEMU, 64 KiB RAM, no heap, no operating system. Emulated, not real hardware.", sz=19)
    d.para("The same header runs unchanged without a heap or an operating system. At the same buffer, STRATA fits three workloads that the conventional table refuses (for example FreeRTOS in 48 KiB, where the conventional table refuses 420 operations), which is the practical meaning of a 16–18% smaller buffer on a device whose RAM is fixed.")

    d.heading("4.4 Comparison with related work", 2)
    d.para("Three works are used for comparison. {b:(1) LLVM's ScopedHashTable} {cite:llvmsht}, measured here as the undo-log table on std::unordered_map: STRATA's heap peak is " + "%.0f" % REC_STD["heapMedian"] + "% lower in median (" + "%.0f–%.0f" % (REC_STD["heapMin"], REC_STD["heapMax"]) + "%), it makes " + "%.1f–%.1f" % ALLOC_STD + "% fewer allocator calls, and it is " + "%.0f–%.0f" % (REC_STD["timeMin"], REC_STD["timeMax"]) + "% faster on all eight traces, while offering a fixed buffer and defined refusal, which the map design does not. {b:(2) Optimal open addressing without reordering} {cite:FarachColtonKrapivinKuszmaul2024}: their bounds cover insertions only; Theorem 2 transfers them to every push of a stack-disciplined workload. {b:(3) Bounded linear probing} {cite:AlharbiBanderierBouillaguet2026} analyses a process in which a key that exceeds the probe cap is discarded and redrawn; our event, refuse and stop, with stack-order deletions, is different, and the exact law gives its probability at finite size.")
    d.table([["Aspect", "LLVM ScopedHashTable design", "Insertion-only bounds (FKK)", "Bounded linear probing (ABB)", "STRATA (this work)"],
             ["Memory", "allocator, node per declaration", "—", "—", "one caller buffer, no allocator"],
             ["At the limit", "undefined (allocation failure)", "—", "key discarded and redrawn", "refused, state unchanged"],
             ["Deletions", "undo log", "not treated", "not treated", "exact undo; stack order only safe order"],
             ["Probe limit", "none", "not a design rule", "asymptotic results", "exact law; 258 at load 3/4, 10{sup:−6}"],
             ["Evidence", "production use", "proofs", "proofs", "8 compiler traces, proofs, real-table validation"]],
            [2.4, 3.4, 3.2, 3.4, 3.8], "Comparison with the related work used for evaluation.", sz=18)


def section5(d):
    d.heading("5. Conclusion and scope for future work")
    d.bullets([
        "{b:The proposed work.} STRATA is a scoped symbol table for compilers under a fixed memory budget: one caller-supplied buffer, no allocator calls, refusal that changes nothing, and an optional bound on the work of every call.",
        "{b:Existing methodology.} Textbook and production tables (an undo log on a hash map, one map per scope) depend on the allocator, and the analysis of open addressing covers insertions, so probe limits were set with loose Chernoff-type bounds.",
        "{b:Proposed methodology and its advantage.} Keeping index, records and undo stack in one buffer makes memory fixed and measurable; exact undo explains why scope exit needs no tombstones, and the exact refusal law turns the probe limit into a design value.",
        "{b:Tools.} A recording Tiny C Compiler and chibicc, a C++14 replay harness with a reference model, QEMU for the Cortex-M3, exact-arithmetic verification programs and a React tool linked to the real table.",
        "{b:Results.} No wrong answer in " + fmt_int(REC_STRATA["checked"]) + " checked operations; a fixed buffer " + n("SaveLo") + "–" + n("SaveHi") + "% smaller than a conventional single-buffer table, explained exactly as a stored hash word plus name packing; speed not distinguishable on six of eight traces and at most " + n("ArenaAbsMax") + "% slower where it differs; " + n("AllocLo") + "–" + n("AllocHi") + "% fewer allocator calls than the predecessor; a probe limit of 258 instead of 455 at load 3/4 for 10{sup:−6}; three workloads that fit a 64 KiB microcontroller only with STRATA.",
        "{b:Scope for future work.} A limit law for refusals on wide and deep scope trees is open. The measurements cover C only, one machine and an emulated microcontroller; C++ workloads, real hardware and a compiler that keeps several scopes alive at once are next. A machine-checked version of the proofs and a measured timing channel for the key-lifetime results would strengthen the claims, and the authors still have to review every proof in full.",
    ])


def declarations(d):
    d.heading("Author Contributions")
    d.para("Shubhi Singh designed and implemented STRATA, its tests, the trace recorder, the benchmarks and the interactive tool, and wrote the empirical study. Adhyan Jain wrote the earlier METIS-X table that STRATA follows, directed the theoretical work (the adversarial review, the theorems and proofs, the verification programs and the Theory pages) and produced the course-template manuscript this version extends. Both authors are responsible for the content; roles follow docs/CONTRIBUTIONS.md.")
    d.heading("Acknowledgements")
    d.para("The authors thank their guide, Prof. Bhuvaneshwari M, School of Computer Science and Engineering, VIT Vellore, and the maintainers of the open-source tools used: GCC, QEMU, Python, TeX, React and Vite.")
    d.heading("Funding")
    d.para("This research received no external funding.")
    d.heading("Competing interests")
    d.para("The authors declare no competing interests.")
    d.heading("Data and code availability")
    d.para("All sources, traces, raw results and programs are in the public repository {cite:strata}. {code:manuscript/tools/make_numbers.py} regenerates every measured number, {code:bash theory/verify/run_all.sh} every theoretical one, and {code:python manuscript/final/build_final.py} this document.")


def build(d):
    front(d)
    intro(d)
    theory.related(d)
    section3(d)
    section4(d)
    section5(d)
    declarations(d)
    refs = list(d.cite_order)
    saved, d.body = d.body, []
    d.heading("6. References")
    d.references([theory.R.text(k) for k in refs])
    refs_xml, d.body = d.body, saved
    idx = next(i for i, x in enumerate(d.body) if "Author Contributions" in x)
    d.body = d.body[:idx] + refs_xml + d.body[idx:]


def to_pdf(docx):
    pdf = docx[:-5] + ".pdf"
    ps = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          "$d = $w.Documents.Open('%s'); $d.Fields.Update() | Out-Null; $d.SaveAs([ref]'%s', [ref]17); $d.Close(); $w.Quit()") % (docx, pdf)
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True, timeout=300)
    except Exception:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(docx), docx], check=True, capture_output=True, timeout=300)
    return pdf


if __name__ == "__main__":
    if len(sys.argv) > 1: build_docx.TEMPLATE = sys.argv[1]
    d = build_docx.Doc()
    build(d)
    os.makedirs(OUT_DIR, exist_ok=True)
    docx = build_docx.package(d, os.path.join(OUT_DIR, "STRATA_Final_Manuscript.docx"))
    pdf = to_pdf(os.path.abspath(docx))
    print("docx:", docx, "\npdf:", pdf)
    print("figures %d, tables %d, equations %d, algorithms %d, references %d" % (d.fig, d.tab, d.eq, d.alg, len(d.cite_order)))
