#!/usr/bin/env python3
"""Mechanical checks of manuscript/overleaf/main.tex against the IEEE Access rules.

    python manuscript/tools/check_manuscript.py

Abstract length (150-250 words), keyword count (3-10) and order, unresolved references and
citations in the log, uncited bibliography entries, duplicate labels, author markers left.
"""
import os
import re
import sys

D = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "paper")
MAIN = sys.argv[2] if len(sys.argv) > 2 else "main"
tex = open(os.path.join(D, MAIN + ".tex"), encoding="utf-8").read()
for part in ("body", "abstract"):
    if "\\input{" + part + "}" in tex:
        tex = tex.replace("\\input{" + part + "}", open(os.path.join(D, part + ".tex"), encoding="utf-8").read())
tex = "\n".join(l for l in tex.splitlines() if not l.lstrip().startswith("%"))    # comments are not text
gen = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(D, "generated_numbers.tex"), encoding="utf-8").read()))
ok = True


def report(name, good, detail):
    global ok
    ok = ok and good
    print(f"{'PASS' if good else 'FAIL'}  {name}: {detail}")


abstract = tex[tex.index("\\begin{abstract}") + 16:tex.index("\\end{abstract}")]
plain = re.sub(r"\\(\w+)\\?", lambda m: gen.get(m.group(1), ""), abstract)
plain = re.sub(r"[$\\{}]", " ", plain)
n = len(plain.split())
LO, HI = (0, 150) if MAIN == "short" else (150, 250)
report("abstract length", LO <= n <= HI, f"{n} words (limit {LO}-{HI})")
report("abstract has no citation or footnote", "\\cite" not in abstract and "\\footnote" not in abstract, "checked")

km = re.search(r"\\begin\{(?:IEEE)?keywords\}(.*?)\\end\{(?:IEEE)?keywords\}", tex, re.S)
kw = [k.strip().rstrip(".") for k in km.group(1).split(",")]
KMAX = 6 if MAIN == "short" else 10
report("keyword count", 3 <= len(kw) <= KMAX, f"{len(kw)} (limit 3-{KMAX})")
report("keywords alphabetical", [k.lower() for k in kw] == sorted(k.lower() for k in kw), "; ".join(kw))

log = open(os.path.join(D, MAIN + ".log"), encoding="utf-8", errors="replace").read()
undefined = re.findall(r"(?:Reference|Citation) `([^']+)' on page", log)
report("references and citations resolve", not undefined, f"{len(undefined)} unresolved {sorted(set(undefined))[:5]}")
report("no LaTeX errors", "\n!" not in log, "main.log")
over = [m for m in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log) if float(m) > 1 and m not in ("505.12177", "9.2679")]
report("no overfull boxes beyond those of the unmodified template", not over, f"{over}")

cited = set()
for group in re.findall(r"\\cite\{([^}]+)\}", tex):
    cited.update(k.strip() for k in group.split(","))
bib = open(os.path.join(D, "references.bib"), encoding="utf-8").read()
keys = re.findall(r"@\w+\{(\w+),", bib)
if MAIN != "short":    # the four-page version cites a subset of the shared bibliography
    report("every bibliography entry is cited", set(keys) <= cited, f"uncited: {sorted(set(keys) - cited)}")
report("every citation has an entry", cited <= set(keys), f"missing: {sorted(cited - set(keys))}")
report("no duplicate bibliography keys", len(keys) == len(set(keys)), f"{len(keys)} entries")

labels = re.findall(r"\\label\{([^}]+)\}", tex)
report("no duplicate labels", len(labels) == len(set(labels)), f"{len(labels)} labels")
refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", tex))
floats = [l for l in labels if l.startswith(("fig:", "tab:", "alg:"))]
report("every figure, table and algorithm is referenced", all(l in refs for l in floats), f"unreferenced: {[l for l in floats if l not in refs]}")

markers = tex.count("\\authorfill{")
print(f"INFO  author markers remaining: {markers} (must be 0 before submission)")
pages = re.search(r"Output written on \w+\.pdf \((\d+) pages", log)
print(f"INFO  pages: {pages.group(1) if pages else '?'} ")
sys.exit(0 if ok else 1)
