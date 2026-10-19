# Author details the authors must supply or confirm

Nothing below was invented. Where the manuscript needs a value that is not verified, it
contains a visible marker of the form **[AUTHOR: ...]**. A search for `AUTHOR:` in
`overleaf/main.tex` lists every one. The submission is not ready while any marker remains.

## 1. Names and order (as instructed)

| # | Name used in the manuscript | Note |
|---|---|---|
| 1 | Shubhi Singh | |
| 2 | Adhyan Jain | has not reviewed the manuscript, the code changes of 2026-10-13 or the public release |
| 3 | Akshith Venkatataramana | **Confirm spelling.** The instructions say "Venkatataramana"; the repository's earlier draft says "Venkataramana". The instruction's spelling is used. |
| 4 | Arjuman | Confirm whether this is the complete name as it should appear in print. |

Research guide: **Bhuvaneswari M.** (spelled "Bhuvaneshwari M" in the repository; the
instruction's spelling is used). She is thanked in the Acknowledgment and is **not** listed as
an author. Confirm which of the two applies; IEEE requires that every author made a
substantial contribution, drafted or revised the work, approved the final version and agrees
to be accountable for it.

## 2. Needed for the title page

| Item | Status |
|---|---|
| Affiliation of each author | The repository's earlier draft gives "School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India" for all listed authors. This is used in the manuscript and marked for confirmation. Confirm it for **each** of the four authors, with the official form of the institution's name, city, postal code and country. |
| E-mail address of each author | missing |
| Corresponding author | missing (IEEE Access allows one at submission) |
| ORCID of the submitting author | missing; IEEE Access requires a publicly visible, populated ORCID for the submitting author |
| IEEE membership grades | missing; leave out if none |
| Funding or sponsor statement for the first-page footnote | missing; the manuscript says that the authors have to state it |

## 3. Needed for the end matter

| Item | Status |
|---|---|
| Biography of each author (education, positions, research interests) | missing; IEEE Access requires short biographies below the references. The manuscript contains four clearly marked placeholders using `IEEEbiographynophoto`. |
| Author photographs (1 in x 1.25 in) | missing; switch to `IEEEbiography` with a photo file when available |
| Conflict of interest | the manuscript states none **as a placeholder to be confirmed** |
| Author contributions | not written; the repository records commit-level history only for the predecessor project (`docs/CONTRIBUTIONS.md`). The authors must state who did what. |

## 4. Decisions only the authors can take

1. **Disclosure of AI assistance.** IEEE Access requires AI-generated text to be disclosed in the acknowledgments, and each section that uses it to cite the system. The code, experiments, analysis and the text of this manuscript were produced with an AI coding assistant (Claude, Anthropic) at the first author's direction. The Acknowledgment says so in plain words. The authors must check that this matches what they are willing to sign, and that they can explain and defend every part of the paper.
2. **Authorship of the guide** (section 1).
3. **Public release.** The repository was made public on 2026-10-13; confirm with all contributors that this was intended.
4. **Licence of the artifact** (currently MIT, copyright in two authors' names; confirm for four).
5. **Whether the predecessor's authors and guide agree** to the comparison with METIS-X being published.
6. **Article processing charge.** IEEE Access charges USD 2,160 per accepted article (as stated on its submission page on 2026-10-13).

## 5. Technical confirmations

- The authors should re-run `bash scripts/audit/final_verify.sh` and `bash scripts/run_all.sh` themselves before signing the submission.
- A second machine and, ideally, a physical microcontroller would remove the two most visible limitations (see `reports/SUBMISSION_CHECKLIST.md`).
