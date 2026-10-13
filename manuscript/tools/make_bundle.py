#!/usr/bin/env python3
"""Assemble the clean submission bundle and its ZIP.

    python manuscript/tools/make_bundle.py

Writes submission/strata-paper-bundle/ and submission/strata-paper-bundle.zip with the two
PDFs, the LaTeX sources needed to rebuild them, and the submission documents. No raw
measurements (they are in the repository), no build products, no machine paths.
"""
import glob
import os
import shutil
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "submission", "strata-paper-bundle")
FIGS = ["fig_layout", "fig_pipeline", "fig_minbuffer", "fig_time", "fig_flood", "fig_probe"]

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "paper", "tables"))
os.makedirs(os.path.join(OUT, "paper", "figures"))
os.makedirs(os.path.join(OUT, "docs"))


def put(src, dst):
    shutil.copy(os.path.join(ROOT, src), os.path.join(OUT, dst))


for f in ("main.pdf", "short.pdf", "main.tex", "short.tex", "body.tex", "abstract.tex", "references.bib", "generated_numbers.tex"):
    put("paper/" + f, "paper/" + f)
for f in sorted(glob.glob(os.path.join(ROOT, "paper", "tables", "tab_*.tex"))):
    shutil.copy(f, os.path.join(OUT, "paper", "tables"))
for f in FIGS:
    put(f"paper/figures/{f}.pdf", f"paper/figures/{f}.pdf")
for f in ("REPRODUCE.md", "CONTRIBUTION_SUMMARY.md", "COVER_LETTER.md", "VENUES.md", "SIGNOFF_CHECKLIST.md"):
    put("submission/" + f, "docs/" + f)
for f in ("NOVELTY_GATE.md", "SUBMISSION_READINESS.md"):
    put(f, "docs/" + f)
with open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("""STRATA paper bundle

paper/main.pdf    full paper, IEEE conference format
paper/short.pdf   four-page-limit version for work-in-progress and student-research tracks
paper/            LaTeX sources of both; build with
                    pdflatex main && bibtex main && pdflatex main && pdflatex main
                  (and the same for short). The numbers in generated_numbers.tex and tables/
                  are generated from the measurements in the repository; see docs/REPRODUCE.md.
docs/             reproduction guide, contribution summary, draft cover letter, venue
                  assessment, sign-off checklist, novelty gate, readiness report

NOT READY TO SUBMIT until docs/SIGNOFF_CHECKLIST.md is complete. The sources contain visible
[AUTHOR: ...] markers for information only the authors can supply.

Repository with code, traces and raw data: https://github.com/shubhisingh1510/cdesproject
""")
zpath = OUT + ".zip"
if os.path.exists(zpath):
    os.remove(zpath)
n = 0
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk(OUT):
        for f in sorted(files):
            full = os.path.join(base, f)
            z.write(full, os.path.join("strata-paper-bundle", os.path.relpath(full, OUT)))
            n += 1
print(f"bundle: {n} files, {os.path.getsize(zpath) // 1024} KiB zip")
