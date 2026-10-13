# Independent review of the manuscript

2026-10-13. Written as a skeptical IEEE Access reviewer would read
`overleaf/main.tex` (13 pages). Severity: **Critical** prevents a credible submission,
**Major** substantially weakens scientific validity or the chance of acceptance, **Minor** is
editorial.

**Verdict: not ready to submit.** The text, figures and numbers are complete and consistent
with the evidence, but three critical items are outside what can be fixed from the
repository, and the contribution is modest for a journal article.

## 1. Answers to the fourteen review questions

| # | Question | Assessment |
|---|---|---|
| 1 | Is the problem important? | Moderately. Symbol tables are rarely a bottleneck; the constrained, untrusted-input setting is real but narrow. The manuscript says so. |
| 2 | Is the gap convincingly established? | Partly. No surveyed table has a budget, a refusal guarantee and a probe bound, but the survey is small and the manuscript admits a closer precedent may exist. |
| 3 | Is the contribution technically substantive? | Solid engineering plus two short propositions. No new algorithm. A reviewer looking for algorithmic novelty will be unconvinced. |
| 4 | Is the distinction from existing work clear? | Yes; Table 1 and the related-work section state that the differences are implementation properties. |
| 5 | Is the methodology detailed enough? | Yes: layout, algorithm, rebuild, both propositions with proofs, public artifact. |
| 6 | Are the experiments fair and reproducible? | Fair: the main baseline shares the design's constraints and was written to be strong. Reproducible: every number is generated from stored raw data. Not independent: the baselines are the authors' own. |
| 7 | Are all results supported by evidence? | Yes. Every number comes from `generated_numbers.tex`; claims the data did not support were removed during this review (section 3). |
| 8 | Are the conclusions justified? | Yes, and deliberately modest. |
| 9 | Are limitations disclosed? | Thoroughly, including instability of per-trace verdicts across runs. |
| 10 | Does it follow the IEEE Access format? | Yes: official class of 2026-05-13, abstract 246 words, 8 keywords in alphabetical order, biographies section present (placeholders). |
| 11 | Are citations accurate and relevant? | 25 references, 13 verified by DOI or by running the cited code; books not re-read (`REFERENCE_AUDIT.md`). |
| 12 | Are figures and tables publication quality? | Vector figures, readable at column width, distinguishable without colour. Tables are generated. |
| 13 | Are any claims exaggerated? | None found after the fixes of section 3. The title avoids "novel", "fast" and "secure". |
| 14 | Is the work mature enough? | No: single machine, emulation only, no compiler built on the table, authors have not reviewed it. |

## 2. Open issues

### Critical

| ID | Issue | Why it blocks | Who can fix |
|---|---|---|---|
| C1 | Nine `[AUTHOR: ...]` markers: affiliations to confirm, e-mails, corresponding author, funding statement, four biographies, guide's details, AI statement | IEEE Access requires complete author data, biographies and a submitting author with a public ORCID | authors |
| C2 | **Authorship and responsibility.** The implementation, experiments, analysis and text were produced by an AI assistant at the first author's direction. The co-authors have not reviewed the code, the results or this manuscript. IEEE requires every author to have contributed substantially, to approve the final version and to be accountable for it, and requires AI-generated text to be disclosed. The Acknowledgment discloses it for every section. | A submission whose listed authors cannot explain and defend its content would be a breach of authorship policy regardless of the disclosure. Editors may also decline a manuscript whose text is entirely machine-generated. | authors: read, re-run, rewrite in their own words where they choose to, and decide honestly whether each listed person qualifies as an author |
| C3 | The guide is acknowledged, not listed as an author, per the instructions. The repository's earlier draft lists her as an author. | An authorship dispute after submission is hard to repair | authors and guide |

### Major

| ID | Issue | Effect | Possible remedy |
|---|---|---|---|
| M1 | Limited novelty: textbook algorithm; a known attack; a standard bound. The audit's own assessment is 6.0/10. | The most likely ground for rejection | none within this project; frame honestly as a systems and evaluation article (done) |
| M2 | No compiler runs on the table. The only integration (chibicc) used an earlier version and showed no end-to-end gain. | "Evaluated by replay only" | integrate the final code into TinyCC or chibicc and measure |
| M3 | One machine under a hypervisor; emulated microcontroller with no timing. | External validity | second machine (native Linux); a physical Cortex-M board |
| M4 | Per-trace timing verdicts are not stable across runs of the same code (disclosed in the limitations). | Weakens any fine-grained timing claim | more rounds on a quiet native machine; report the union of runs |
| M5 | Baselines written by the authors; LLVM `ScopedHashTable` and Clang's tables not measured. | Fairness can be questioned | add LLVM ADT as a baseline |
| M6 | Both propositions are argued informally; Proposition 2 assumes an ideal hash and its use against an adversary assumes HalfSipHash-1-3 behaves as one. | A theory-minded reviewer will ask for more | machine-checked proof; cite a formal treatment of the PRF assumption |
| M7 | Literature search of about twenty web queries; several sources at abstract level. | A missed precedent would undermine the gap | systematic review with library access |
| M8 | C only, two small compilers. | Generality | a C++ or scripting-language front end |
| M9 | The sweep and unit-fit results are summarised in one short subsection. | A reviewer may want the memory model validated quantitatively | add the predicted-versus-measured comparison from the artifact |

### Minor

| ID | Issue | Status |
|---|---|---|
| m1 | Footer shows the class's default volume and year; the DOI line is a placeholder | set by IEEE at production |
| m2 | Biographies use the no-photo environment | switch when photographs exist |
| m3 | Per-operation latency (Table 6) is near the timer's resolution and noisy | stated in the text |
| m4 | Several references are web pages (compiler documentation, repositories) | acceptable for software; access dates given |
| m5 | Author name "Venkatataramana" may be a misspelling of "Venkataramana" | flagged in `AUTHOR_DETAILS_REQUIRED.md` |
| m6 | Article length 13 pages | within the recommended 20 |
| m7 | The public repository's `paper/` and `docs/RESULTS.md` still describe an older, slower version | update or remove before reviewers follow the artifact link |

## 3. Issues found during this review and fixed

| Issue | Fix |
|---|---|
| Abstract was 251 words (limit 250) | shortened to 246 |
| Two tables overflowed their column; a stray empty row followed every generated table | headers split, one table made two-column, table bodies read with the expandable input primitive |
| "104 table and trace pairs" was printed as 195 because the run also covered the chibicc traces | text now says 195 pairs over the 15 traces; a separate macro holds the 8-trace count |
| "The two tables are level" in several places, although the full run shows the compact table slower on 2 of 8 traces | replaced by what the data supports: no established difference on most traces, at most about 10 percent |
| "An interning map is faster than both single-buffer designs" | removed: not supported consistently by the data |
| "METIS-X refuses declarations because its probe sequences are capped" | cause removed: observed, not diagnosed |
| A range "11 to 34 percent" typed by hand in the introduction | reworded; the exact range is printed from the data in Section IX-D |
| Small capitals unavailable in the template's Times face | status names set in the monospaced face |
| RADIX-50 mentioned with only a Wikipedia source | mention dropped |
| Quotation from the rustc-hash README unverified | README fetched; quotation confirmed word for word |
| Instability of per-trace verdicts between runs not mentioned | added to the limitations with both runs' figures |

## 4. What would most improve the article

In order: C2 (the authors make the work their own), M2 and M3 (a compiler on a real board),
M7 (literature), M6 (a checked proof). None of these can be produced from the repository
alone.
