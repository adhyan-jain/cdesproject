# One-page contribution summary

**Title.** Bounded Memory and Bounded Work for Scoped Symbol Tables: A Single-Buffer Design
Evaluated on Compiler-Generated Workloads

**Question.** A compiler front end that must run in a fixed memory budget on source text it
cannot trust needs a symbol table that is bounded in advance, fails in a defined way, and
cannot be slowed down by the choice of identifiers. What does that cost?

**What was built.** STRATA, a scoped symbol table in one caller-supplied buffer: a
linear-probing index, one record per visible name holding its innermost declaration, and an
undo stack. The algorithm is the textbook hash-table-plus-undo-stack scheme. An operation that
does not fit is refused and changes nothing. An optional bounded mode fixes the index size,
limits the index probes per call and can use a keyed hash.

**Findings (run `20261013-143828-paper`, 8 projects compiled by an instrumented Tiny C Compiler).**

1. *Memory.* The smallest fixed buffer is 16.4% to 17.9% smaller than that of a conventional
   chained table held to the same single-buffer discipline.
2. *Time.* Not faster than that conventional table: slower on 2 of 8 traces (7% and 11%), no
   established difference on 6. Per-trace verdicts vary between runs; "within about 10%" is
   what holds.
3. *Where the larger gain comes from.* Against the multi-allocation predecessor both
   single-buffer tables are 15% to 37% faster and use far less heap. That gain belongs to the
   storage discipline, not to the compact layout.
4. *A corrected conclusion.* An earlier version looked 11% to 34% slower than the conventional
   table. The cause was rebuild work (index rebuilt on every buffer growth, names hashed
   twice, probe path walked twice), not the design. A strong baseline and per-operation data
   exposed it.
5. *A property and a bound.* Because declarations are removed newest first, the table is
   always bit-for-bit a freshly built table of the live declarations. That makes the
   insertion-only analysis of linear probing applicable and gives a bound on how often a
   probe limit refuses an honest name. The bound and a simulation (240 million samples) show
   that the limit suggested by real traces (64) is too small; 512 is supported.
6. *Hostile identifiers.* Valid C identifiers that collide for every hash seed (a known
   construction, restricted here to identifier characters) slow declarations about 300-fold
   at 32 768 names. A keyed hash removes the effect and costs 20% to 32% of replay time.
7. *In a real compiler.* With chibicc's variable scopes on STRATA the output is identical on
   158 of 158 translation units and compile time changes by -3.7% to +2.2%: no end-to-end
   benefit in a hosted compiler.

**Evidence for the guarantees.** 2.7 million differential checks under sanitizers, every
operation sequence up to length 9 in 8 small configurations (80.6 million), 2.5 million
fuzzing executions of the final code, a mutation check (9 of 9 defects detected), an emulated
Cortex-M3 with 64 KiB. None of this is a proof.

**What is not claimed.** A new algorithm, a faster table, a new attack, hardware results, or
a benefit for compilers that are not memory-constrained.

**Limits.** One laptop; replay rather than a compiler under a budget; emulation; C only;
baselines written by the authors; informal proofs; a limited literature search.

**Artifact.** Code, traces, raw measurements and the scripts that regenerate every number in
the paper: https://github.com/shubhisingh1510/cdesproject
