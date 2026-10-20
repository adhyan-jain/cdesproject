"""references.bib for the IEEE Access manuscript: the empirical paper's bibliography plus the
entries of the theory manuscript (theory/paper/refs.bib) whose keys it does not already have.
Run from the repository root:  python manuscript/ieee_access/tools/merge_bib.py
"""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
A = open(os.path.join(ROOT, "manuscript", "overleaf", "references.bib"), encoding="utf8").read()
B = open(os.path.join(ROOT, "theory", "paper", "refs.bib"), encoding="utf8").read()


def entries(txt):
    out = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", txt, flags=re.S):
        out[m.group(2)] = m.group(0)
    return out


# Tools of the interactive page and the emulator (records as in theory/template/refs/compilers.json).
TOOLS = r"""@misc{react,
  author       = {{Meta Open Source}},
  title        = {React},
  note         = {[Online]. Available: \url{https://react.dev}. Accessed: Oct. 20, 2026}
}

@misc{vite,
  author       = {{Vite contributors}},
  title        = {Vite: Next Generation Frontend Tooling},
  note         = {[Online]. Available: \url{https://vite.dev/guide/}. Accessed: Oct. 20, 2026}
}

@inproceedings{bellard2005qemu,
  author       = {Fabrice Bellard},
  title        = {{QEMU}, a Fast and Portable Dynamic Translator},
  booktitle    = {Proc. USENIX Annual Technical Conference, FREENIX Track},
  pages        = {41--46},
  year         = {2005}
}
"""
B = B + "\n" + TOOLS
ea, eb = entries(A), entries(B)
extra = [v for k, v in eb.items() if k not in ea]
with open(os.path.join(ROOT, "manuscript", "ieee_access", "references.bib"), "w", encoding="utf8") as f:
    f.write("% Merged by tools/merge_bib.py: manuscript/overleaf/references.bib + theory/paper/refs.bib (new keys only).\n\n")
    f.write(A.strip() + "\n\n% ---- from theory/paper/refs.bib ----\n\n" + "\n\n".join(extra) + "\n")
print("empirical %d, theory %d, added %d: %s" % (len(ea), len(eb), len(extra), ", ".join(k for k in eb if k not in ea)))
