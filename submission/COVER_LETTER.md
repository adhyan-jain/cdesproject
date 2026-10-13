# Submission summary (draft cover letter)

*To be adapted to the venue's form and signed by the authors. Nothing below may be sent until
every item in `SIGNOFF_CHECKLIST.md` is closed.*

Dear Program Committee,

we submit "Bounded Memory and Bounded Work for Scoped Symbol Tables", a work-in-progress
report on scoped symbol tables for compilers that must run inside a fixed memory budget.

The paper does not propose a new algorithm. It reports a measurement: what a compact,
interning, single-buffer table saves and costs against a conventional single-buffer table on
symbol-table events logged by real C compilers, and what it takes to bound the work of each
call on hostile identifiers. The compact table needs a buffer about one sixth smaller and is
not faster; an apparent time penalty of up to a third turned out to be an implementation
artifact, which we diagnose. We also show that last-in-first-out removal keeps a
linear-probing table in the state of a freshly built one, and use this to bound how often a
probe limit refuses an honest name; the bound shows that a limit suggested by real traces
alone would have been too small.

We believe the contribution suits this track because it is an honest incremental result with
negative findings, a strong baseline, and a complete public artifact from which every number
in the paper is regenerated.

Disclosures:

- The measurements come from one laptop; the microcontroller results are from an emulator.
- The implementation, experiments, analysis and text were produced with the assistance of an
  AI coding assistant (Claude, Anthropic) at the direction of the first author. [AUTHORS:
  state here how each author verified the work, in the form the venue requires.]
- The work continues an earlier course project (METIS-X) by two of the authors; it is used as
  a baseline at a pinned commit.
- No part of this work has been published or is under review elsewhere. [AUTHORS: confirm.]
- Conflicts of interest: [AUTHORS: list or state none.]

[AUTHORS: names, affiliations, corresponding author and e-mail.]
