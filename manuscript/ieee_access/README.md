# IEEE Access manuscript (final): STRATA measured and analyzed

Main file: `main.tex`. Compiler: **pdfLaTeX**. Bibliography: **BibTeX** with `IEEEtran.bst`.
On Overleaf: *New Project > Upload Project* with `strata_ieee_access_final_overleaf.zip`, main document `main.tex`.

```
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

This version joins the empirical study (`../overleaf/`, `paper/`) and the theory manuscript (`theory/`):
exact undo and safe deletion orders (Section V), the exact refusal law and design table (Section VI),
the key-lifetime rule, the space ledger (Section IX-C), the validation of the law against the real
table, and the interactive tool (Section X). It applies the corrections of `docs/ADDENDUM_2026-10-17.md`
(the Chernoff-type bound is loose by a factor growing like L^{3/2}; the buffer saving is a stored hash
word plus packing; the refusal law holds against chosen names only with a fresh key).

| File | Origin | Edit? |
|---|---|---|
| `main.tex`, `abstract.tex`, `body.tex` | the manuscript | yes |
| `generated_numbers.tex`, `tables/tab_*.tex` | `../tools/make_numbers.py` from run `20261013-143828-paper` | no: regenerate |
| `tables/th_*.tex` | `theory/verify/run_all.sh`, restyled to this article's ruled tables by `tools/theory_tables.py` (cells unchanged) | no: regenerate |
| `figures/fig_{arch,undo,dep,flow,law,design,ledger,lawz}.pdf` | pages of `theory/template/build/{diagrams,plots}.pdf` (`theory/template/make_figures.py`) | regenerate |
| other `figures/*.pdf` | `../figures/source/` | regenerate |
| `figures/screenshot_analyse.png` | the frontend's Analyse page | — |
| `references.bib` | `tools/merge_bib.py` (empirical bibliography + theory entries + tools) | via the script |
| class, fonts, logos | official IEEE Access LaTeX template of 2026-05-13, unmodified | no |

## Before submission

* Authors and the guide follow the authors' earlier instruction (four authors; the guide in the
  Acknowledgment). The course-template version (`../final/`) lists two authors: decide which is right.
* No e-mail addresses are included, by the authors' decision. ORCID iDs and photographs are not in the file.
  The biographies are minimal; each author should check and extend their own.
* The AI-disclosure paragraph in the Acknowledgment follows the journal's policy; the authors must review it.
* All co-authors must read the proofs (Sections V and VI) and the full theory manuscript (`theory/paper/main.pdf`).
