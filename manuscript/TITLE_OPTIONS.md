# Title options

| # | Title | For | Against |
|---|---|---|---|
| A | **Bounded Memory and Bounded Work for Scoped Symbol Tables: A Single-Buffer Design Evaluated on Compiler-Generated Workloads** | Names both guarantees and the evidence; makes no claim of being faster or first | Long |
| B | STRATA: A Single-Buffer Scoped Symbol Table With All-or-Nothing Refusal and a Probe Limit for Memory-Constrained Compilers | Names the artifact and its two properties | Reads as a system announcement; the evaluation, which is the stronger half, is absent |
| C | What Does a Compact Scoped Symbol Table Cost? Memory, Time, and Adversarial Input in One Fixed Buffer | Honest about the trade-off question | Question titles are discouraged in some IEEE style guidance; less searchable |

**Selected: A.** Every phrase is backed by a measured result: bounded memory (fixed buffer,
all-or-nothing refusal, tested), bounded work (static index and probe limit, with a bound and
a measurement), single-buffer design (the artifact), compiler-generated workloads (two
instrumented compilers). It avoids "novel", "efficient", "fast" and "secure", none of which
the evidence would carry: the table is level with, not faster than, the conventional design,
and the security argument rests on an assumed ideal hash.
