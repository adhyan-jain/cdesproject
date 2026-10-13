# Venue candidates and compliance

Researched on 2026-10-13 from the official pages linked below. Dates marked **unverified** are
not on an official page for the 2027 edition and must be checked again before planning.
Nothing here promises acceptance. Costs were not shown on the pages read and are unverified.

## Recommendation

| Rank | Venue | Category | Why |
|---|---|---|---|
| Primary | COMPSAC 2027 Student Research Symposium | student research track | work in progress is explicitly welcome; first author must be a student; 4 pages in IEEE conference format, which `paper/short.tex` already is; published in the COMPSAC proceedings |
| Alternative A | LCTES 2027, work-in-progress / poster paper | short track of a compilers-for-embedded conference | the best topical fit; needs conversion to the ACM template; the 2027 call is not published yet |
| Alternative B | COMPSAC 2027 main symposium | modest general software conference | full-paper deadline verified; `paper/main.tex` would have to be shortened to the (unverified) page limit |

## 1. COMPSAC 2027 Student Research Symposium (primary)

| Item | Finding | Source |
|---|---|---|
| Name, organizer | 51st IEEE International Conference on Computers, Software, and Applications (COMPSAC 2027), IEEE Computer Society | https://ieeecompsac.computer.org/2027/ |
| Dates, place | July 13-16, 2027, Tokyo, Japan | same |
| 2027 deadline for the symposium | **not shown: unverified.** The 2026 edition listed 15 April 2026, extended to 30 April 2026; notification 10 May 2026 | https://ieeecompsac.computer.org/2026/srs-2026/ |
| Scope | students' research in progress, "initial or proof of concept results" | 2026 page |
| Format (2026) | at most 4 pages, 10-point, IEEE conference format, US letter; 150-word abstract; up to 6 keywords | 2026 page |
| Review (2026) | double-blind; names, affiliations and contacts removed | 2026 page |
| Eligibility (2026) | first author must be a student; advisor or collaborators may be co-authors | 2026 page |
| Publication | accepted papers appear in the electronic COMPSAC proceedings after oral or poster presentation | 2027 and 2026 pages |
| Registration | the student author of every accepted paper must register (student fee) and attend | 2026 page |
| AI policy | not on the pages read. **Confirm on the 2027 call** and against IEEE's current author guidelines | unverified for this venue |

Compliance of `paper/short.tex`:

- [x] IEEE conference format, 10 pt, two columns
- [x] 3 pages (limit 4)
- [x] abstract 147 words (limit 150)
- [x] 6 keywords (limit 6)
- [x] anonymous build available: uncomment the line that defines `anonymous` at the top of the file (hides authors, acknowledgment and the artifact citation)
- [ ] self-identifying citation: the METIS repository entry names two of the authors; cite it in the third person or anonymise it as the call requires
- [ ] US letter paper size: IEEEtran defaults to letter; confirm in the PDF properties
- [ ] first author is a student at the time of submission: confirm
- [ ] AI disclosure in the form the 2027 call requires
- [ ] travel to Tokyo and student registration are affordable: decide before submitting

## 2. LCTES 2027 work-in-progress paper (alternative A)

| Item | Finding | Source |
|---|---|---|
| Name, sponsors | ACM SIGPLAN/SIGBED International Conference on Languages, Compilers, and Tools for Embedded Systems; co-located with PLDI | https://www.sigarch.org/call-contributions/lctes-2026/ |
| 2027 edition | **no call published; dates, place and deadline unverified.** The series page lists editions only up to 2026 | https://conf.researchr.org/series/LCTES |
| 2026 dates (for orientation only) | abstracts 6 March 2026, papers 13 March 2026 (AoE); conference 15-16 June 2026 | sigarch page |
| Categories (2026) | full paper: 10 pages plus at most 2 for references and appendix; poster / work-in-progress / invited paper: 4 pages, "original ideas that are likely to trigger interesting discussions" | sigarch page |
| Template, review model, proceedings, artifact evaluation, AI policy | not stated on the pages read: **unverified** | |

Compliance: the content of `paper/short.tex` fits a 4-page work-in-progress paper. It must be
moved to the ACM template that the 2027 call names, and the ACM policy on generative-AI
disclosure must be checked.

## 3. COMPSAC 2027 main symposium (alternative B)

| Item | Finding | Source |
|---|---|---|
| Full papers due | January 31, 2027 | https://ieeecompsac.computer.org/2027/ |
| Notification | April 7, 2027 | same |
| Workshop papers due / notification | April 15, 2027 / May 1, 2027 | same |
| Camera-ready | June 1, 2027 | same |
| Page limit, template, fees, AI policy | not shown: **unverified** | |

Compliance: `paper/main.tex` is 14 pages in IEEE conference format and will exceed a typical
conference limit. The related-work comparison table, the sweep and unit-fit tables and the
synthetic-trace table are the first candidates to move to an appendix or to the artifact.

## Considered and not recommended now

| Venue | Reason |
|---|---|
| ACM SAC 2027 (Gwangju, 5-9 April 2027) | paper and student-research-abstract deadline extended to 16 October 2026 (https://www.sigapp.org/sac/sac2027/): three days after this assessment, with no author sign-off |
| ISEC 2027 (Mumbai, 18-20 February 2027) | research rounds closed in June and September 2026 (https://conf.researchr.org/track/isec-2027/isec-2027-research-papers) |
| POPL 2027 Student Research Competition | deadline 12 October 2026, passed (https://popl27.sigplan.org/track/POPL-2027-student-research-competition) |
| CC 2027 (with CGO, March 2027) | no 2027 call found; a competitive venue for this contribution |
| IEEE Access | a journal-format draft exists (`manuscript/`), but the contribution is modest for a journal article and the article charge is USD 2,160 (https://ieeeaccess.ieee.org/authors/submission-guidelines/) |
