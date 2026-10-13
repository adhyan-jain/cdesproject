#!/usr/bin/env python3
"""Copy the shared parts of the article from paper/ into the IEEE Access (Overleaf) project.

    python manuscript/tools/sync_body.py

paper/ is canonical: body.tex, abstract.tex, references.bib, generated_numbers.tex,
tables/tab_*.tex and figures/fig_*.pdf. The Overleaf project must be self-contained, so it
holds copies. Edit in paper/, then run this.
"""
import glob
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "paper")
DST = os.path.join(ROOT, "manuscript", "overleaf")
n = 0
for name in ("body.tex", "abstract.tex", "references.bib", "generated_numbers.tex"):
    shutil.copy(os.path.join(SRC, name), os.path.join(DST, name))
    n += 1
for sub, pattern in (("tables", "tab_*.tex"), ("figures", "fig_*.pdf")):
    os.makedirs(os.path.join(DST, sub), exist_ok=True)
    for f in glob.glob(os.path.join(DST, sub, pattern)):
        os.remove(f)
    for f in glob.glob(os.path.join(SRC, sub, pattern)):
        if os.path.basename(f) in ("fig_compiler_memory.pdf", "fig_compiler_time.pdf"):
            continue    # figures of the earlier draft, not used by the article
        shutil.copy(f, os.path.join(DST, sub, os.path.basename(f)))
        n += 1
print(f"synchronised {n} files into manuscript/overleaf")
