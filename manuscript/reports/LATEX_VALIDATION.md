# LaTeX validation

2026-10-13.

## Template

| Item | Value |
|---|---|
| Source | https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip, linked from the IEEE Access submission guidelines page (https://ieeeaccess.ieee.org/authors/submission-guidelines/), downloaded 2026-10-13 |
| SHA-256 of the archive | `60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67` |
| Version | folder `ACCESS_latex_template_20260513`; first line of `access.tex`: "Adjusted 05/13/2026 at the byline author names" |
| Files taken unmodified | `ieeeaccess.cls`, `IEEEtran.cls`, `IEEEtran.bst`, `spotcolor.sty`, 4 `.fd`, 4 `.map`, 16 `.pfb`, 16 `.tfm`, `logo.png`, `notaglinelogo.png`, `bullet.png` |
| Files not taken | the example `access.tex` and its sample images |
| Kept locally at | `manuscript/template_download/` (not part of the Overleaf project) |

The unmodified template was compiled first as a control: 8 pages, no errors.

## Rules read from the template and the guidelines page, and how the manuscript meets them

| Rule | Source | Manuscript |
|---|---|---|
| Class `ieeeaccess`, front matter commands `\history`, `\doi`, `\title`, `\author`, `\address`, `\tfootnote`, `\markboth`, `\corresp`, `abstract`, `keywords`, `\titlepgskip`, `\maketitle`, `\EOD` | template | used as in the example |
| Abstract 150-250 words, one paragraph, no abbreviations, footnotes, references or displayed mathematics | template text | 246 words; none of the excluded elements |
| Keywords: 3 to 10, alphabetical | guidelines page; template | 8, alphabetical |
| Figures placed with the template's `\Figure` command | template | all six |
| Table captions above, figure captions below; no label before a caption | template | followed |
| "Acknowledgment" in the singular; support statements in the first-page footnote | template | followed (footnote is an author placeholder) |
| Bibliography: BibTeX permitted, `.bib` file to be supplied | template text | `references.bib` with `IEEEtran.bst` |
| Biographies for all authors below the references | guidelines page | four entries (placeholders, no photographs) |
| Fewer than 20 pages recommended | guidelines page | 13 |
| AI-generated text disclosed in the acknowledgments | guidelines page | disclosed for every section |
| Abbreviations defined at first use in the body | guidelines page | checked by reading; KiB is used as a unit symbol |

Not stated on the pages that were read, and therefore not claimed: a figure or table count
limit, a reference count limit, a required data-availability or conflict-of-interest section.

## Build

| Item | Value |
|---|---|
| Engine | pdfTeX (MiKTeX 25.12, MiKTeX-pdfTeX 4.23) on Windows 11 |
| Commands | `pdflatex main`, `bibtex main`, `pdflatex main`, `pdflatex main` |
| Result | success, 13 pages, `main.pdf` |
| Clean-directory test | the ZIP was unpacked into an empty directory and built with the same four commands: success, 13 pages |
| Overleaf | **not tested.** No Overleaf account was used. The project uses only pdfLaTeX, BibTeX, the template's files and two standard packages (`algorithm`, `url`), so it is expected to build there, but that is an expectation, not a result. |

## Mechanical checks (`python manuscript/tools/check_manuscript.py`)

All pass: abstract length; no citation or footnote in the abstract; keyword count and order;
0 unresolved references or citations; no LaTeX error; no overfull box beyond those the
unmodified template itself produces; 25 bibliography entries, all cited, no duplicates; 51
labels, no duplicates; every figure, table and algorithm referenced.

## Remaining warnings

| Warning | Count | Cause | Also in the unmodified template? |
|---|---|---|---|
| `Overfull \hbox (505.12177pt too wide) ... while \output is active` | per page | the class's page header | yes |
| `Overfull \hbox (9.2679pt too wide)` at `\maketitle` | 2 | the class's title block | yes |
| `Font shape T1/formata/m/sl undefined` | 12 | the class's heading font has no slanted shape | yes |
| `Font shape T1/pcr/n/n undefined` | 1 | Courier substituted for the monospaced face | no; cosmetic, the substitute is the same family |
| `Underfull \hbox` / `\vbox` | several | justified narrow columns and float placement | yes |

No undefined reference, no undefined citation, no missing figure, no duplicate label.

## PDF inspection

All 13 pages were rendered and read.

| Element | Finding |
|---|---|
| Title block | title, four authors in the instructed order, one affiliation with a bold confirmation marker, corresponding-author and funding placeholders in bold |
| Abstract and index terms | set in the template's style; numbers present (generated) |
| Section hierarchy | I to XII, lettered subsections; unnumbered Data and Code Availability, Acknowledgment, References |
| Figures 1-6 | within the column, legible; legends do not cover data; captions below |
| Tables 1-14 | within their column or the page width; no stray rows; captions above |
| Equations (1), (2), Algorithm 1, Propositions 1-2 with proofs | numbered and referenced correctly |
| References | 25, numbered in order of first citation, IEEE style |
| Biographies | four bold placeholders |
| Footer | "VOLUME 11, 2023" is printed by the class; it is replaced at production |

## Outstanding formatting items

1. Author placeholders (9) and photographs.
2. The DOI line and the publication dates are the template's placeholders.
3. An actual Overleaf build has not been run.
