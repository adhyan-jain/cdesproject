# Presenting the paper: a guide

For presenting *Stack-Disciplined Open Addressing: Exact Undo, Exact Refusal Probabilities, and Key-Lifetime Rules
for Bounded-Memory Scoped Tables* (`theory/paper/main.tex`, 26 pages) to a professor. Plan for **20 minutes plus
questions**; cut lists for 10 and 30 minutes are in section 4.

The guide is built to keep you honest as well as clear. The paper is careful about what is new and what is classical,
and a professor will probe exactly that. Say it before they ask.

---

## 0. The one-page version

**The problem (30 seconds).** A compiler keeps a symbol table. On a small device it must live in one fixed buffer,
refuse cleanly when full, and bound the work of every call. Scopes end in last-in-first-out order.

**The question.** What does that last-in-first-out discipline give an open-addressing hash table?

**The answer in four sentences.**
1. Removing the newest key by clearing its cell is an *exact undo*, for every non-reordering scheme. So every
   insertion-only analysis of the table carries over to push/pop workloads.
2. It is also the *only* safe deletion order for every table; for a given table the safe orders are exactly the linear
   extensions of a "who probed past whom" relation.
3. For a probe-limited table the refusal probabilities are exact: one push, a whole fill, an unlimited run, and (new
   here) any schedule with bounded churn above a persistent set of names. That gives probe limits to choose.
4. Verified by exhaustive enumeration, exact arithmetic, and a real implementation.

**Three things you must say honestly.**
- The undo observation is **elementary**. Its value is what follows from it.
- The refusal law is **classical** (Knuth; Janson–Viola). Our part: a short derivation, exact finite-size use, design tables.
- The proofs are **pen-and-paper, checked by programs**, and the AI-assisted drafting is disclosed (section 5).

**Three numbers to remember** (m = 4096, load 3/4, failure target 10⁻⁶):
- probe limit for one push: **242**; for an unlimited run on a fixed table: **349**;
- guarantee against *any* schedule with 8 names of churn above a persistent set: **410** (+17%);
- at load 1/2, **65%** of keys have no dependents and can be removed out of order; at 3/4 only **37%**.

---

## 1. Before you present

### What to know cold (about 2 hours)
You do not need every proof. You need these five, in your own words:

| Result | Where in the paper | The idea in two sentences |
|---|---|---|
| Theorem 2 (undo) | Section 3 | Inserting a key writes exactly one empty cell, decided only by which cells are occupied. So clearing that cell restores the table that existed before the insertion. Induct along the stack. |
| Theorem 4 (safe orders) | Section 3 | A lookup of *y* walks from its home to its cell and fails if it meets an empty cell on the way. Clearing *x* breaks *y* exactly when *x*'s cell is strictly before *y*'s on *y*'s path; so safe orders are the orders that remove every dependent first. The newest key has no dependents, because a key's path only crosses cells filled before it. |
| Theorem 7 (refusal law) | Section 4 + Appendix A | Cut the ring at its empty cells; each empty cell plus the run after it is a block of random size (Borel, by the cycle lemma), and conditioned on filling the ring the blocks are exchangeable. A new key is refused iff its home starts a window of L occupied cells; a block of g cells has (g−L)⁺ such homes. Sum. |
| Theorem 10 (fill) | Section 4 | A whole monotone fill is refusal-free iff the maximum displacement stays below L. The counts are the ℓ-interval parking functions (Aguilar-Fraga et al.), with a closed-form generating function. |
| Proposition 12 (churn) | Section 4 | Any refusal needs a window of L occupied cells, where the persistent names plus at most s−1 others fill the gaps. So a refusal anywhere implies the persistent part has a window of L cells with at most s−1 empty cells. That probability is the supremum over schedules, and it has a closed-form upper bound. |

Read the proofs of Theorem 2, Theorem 4 and Proposition 12 line by line (they are short). For Theorem 7 read
Appendix A once; it is the longest. This also closes the one gap the disclosure names: *no author has yet recorded a
reading of the proofs.* If you can say "I read and checked these proofs" truthfully, do the reading first.

### Set up the demo (10 minutes, do it the day before)
```bash
cd frontend/web
npm install          # once
npm start            # builds and serves http://localhost:5199
```
Open the **Theory** tab. It runs entirely in the browser, so it works even if the C++ engine is slow to start (the page
header may say "engine offline"; ignore it for the Theory tab). Have the PDF open too (the Theory tab links to it).
Take screenshots of each demo as a backup.

If the professor wants to see the checks run: `bash theory/verify/run_all.sh` takes about 10 minutes. Start it before
you walk in, or show the saved log, or run the 5-second subset `cd frontend/web && npm test`.

---

## 2. Slide plan (14 slides, about 20 minutes)

Each entry: what is on the slide, what to say, how long. Demos are marked **LIVE**.

| # | Slide | Say | Time |
|---|---|---|---|
| 1 | **Title, authors, one-line claim** | "What does last-in-first-out give an open-addressing hash table that has to live in one fixed buffer?" | 0:30 |
| 2 | **The setting**: a symbol table in a compiler; scopes `{ }` push and pop; one fixed buffer; must refuse cleanly | Concrete example: `int x; { int x; ... }`. Why a fixed buffer: microcontrollers, boot loaders. STRATA is the earlier system this builds on. | 2:00 |
| 3 | **The question and the plan**: four things become exact (state after deletions, refusal probability, adversaries, space) | Keep this to one breath. Say what is *not* claimed: no timing, no hardware. | 1:00 |
| 4 | **Open addressing in 60 seconds**: ring of cells, home, probe forward, "non-reordering" | Draw one ring. "Non-reordering: a key never moves after it is placed." | 1:30 |
| 5 | **Theorem 2: stack order is an exact undo** | State it, give the two-sentence proof, then the consequence: "the table always equals the insertion-only table of the live keys". | 2:00 |
| 6 | **LIVE demo 1** (Theory ▸ *Exact undo & deletion order*) | Click *Fill to 70%*. Click *Pop newest* a few times: "Table equals the insertion of the live keys: yes ✓" every time. Then *Clear oldest*: a key can become unreachable. Click a key to show its probe path. "This is Theorem 4." | 2:30 |
| 7 | **Theorem 4 and the orphan law**: safe orders = linear extensions; stack order the only universal one; number of dependents = queue length − 1; mean α/(2(1−α)) | "At load 1/2 about 65% of keys have no dependents; at 3/4 only 37%. Out-of-order deletion is a gamble that gets worse as the table fills." Credit Janson 2005 for the limit law. | 2:00 |
| 8 | **Refusal law (Theorem 7)**: R_m(n,L), the formula | One sentence on the proof (blocks, cycle lemma). Say plainly: "This quantity is classical; we give a short derivation and use it." | 1:30 |
| 9 | **LIVE demo 2** (Theory ▸ *Refusal law & probe limit*) | Leave m=1024, α=0.75, L=130. Read the three cards. "Same table, three questions, three answers." Click *Find L*: 131 for one push, 195 for an unlimited run. | 2:30 |
| 10 | **Fill and unlimited run (Theorem 10, Proposition 11)** | Whole fill: exact limit 306 vs 402 from the union bound, a 24% saving in probes (m=4096, 10⁻⁶). Unlimited run costs about ln m / ln(1/ρ) extra probes (Pittel's scale). | 1:30 |
| 11 | **Proposition 12: persistent names with churn** | "Global names stay, local scopes come and go. A refusal needs a dense window in the persistent part." Statement, one-paragraph proof. | 1:30 |
| 12 | **LIVE demo 3** (Theory ▸ *Persistent names with churn*) | Show the highlighted window; *Run the chain*: the last push is refused. *Estimate over 2000 random tables*: simulation sits below the closed-form bound. Then the paper table: 349 → 359 → 377 → 410 as s goes 1 → 2 → 4 → 8. | 2:00 |
| 13 | **What is new, what is classical, what is not claimed** | The status map (Theory ▸ *What is proved*). Be explicit; this slide is where the professor decides whether to trust you. | 1:30 |
| 14 | **Limits and open problems; thank you** | Open: a limit law for refusals on wide, deep scope trees; an unconditional Theorem 6. Prop 12 is conservative for short runs and uninformative for wide-band schedules. | 1:30 |

The rows add up to about 24 minutes if every one runs long; section 4 shows where to cut.

### Speaking notes for the trickiest slides

**Slide 5 (Theorem 2).** The whole point is that it is simple. Do not apologise for that. Say: "The observation is
elementary. What it buys us is that every known result about insertion-only tables now applies to a table with
deletions, as long as the deletions are in stack order. That is a big transfer for a one-line fact."

**Slide 7 (orphans).** State the direction: *y depends on x* if *x*'s cell lies on *y*'s probe path before *y*'s own cell. Clearing *x* first orphans *y*. The limit law (a discrete M/D/1 queue) is Janson's; what you add is the reading as "orphans after a deletion", the finite-size form, and the converse for orders.

**Slide 10 (fill).** The recurrence is Aguilar-Fraga et al.'s; the large-size behaviour is probably in Petersson's thesis (the paper says it did not extract the statement). What you add: exact finite-size forms and the design table. Say "probably in Petersson", not "equivalent to".

**Slide 12 (Proposition 12).** The supremum is only guaranteed after of the order of m^s chains of pushes. For short runs the plain union bound is smaller (about the first 70 pushes at m=1024, ε=10⁻⁶, s=1). Mention this before you are asked; it shows you know where the result is weak.

---

## 3. The demo, click by click

All three work from the **Theory** tab. None needs the C++ engine.

**Demo 1: Exact undo & deletion order**
1. *Fill to 70%.* (About 17 keys on 24 cells.)
2. *Pop newest* three times. Read the banner each time: "the table is exactly what inserting the remaining keys gives (checked ✓)". The first stat row stays "yes ✓".
3. *Clear oldest.* Likely outcome: a red ring around a key, "Live keys no longer found: 1", first stat flips to "no ✗". Sometimes nothing breaks; say so ("Theorem 4: it is safe only if nothing depended on it") and click *Clear a random key* until one breaks.
4. Click a row in the table to show the dashed probe path, and the orange rings on the keys that depend on it.
5. Last line to say: "Stack order never fails. Anything else is a gamble."

**Demo 2: Refusal law & probe limit**
1. Defaults: m=1024, α=0.75, L=130, s=2. Read the cards: 1.03e-4 for one push, 0.0064 that some name *can* ever be refused, ≤ 0.0107 for any schedule with churn depth 2.
2. Drag L down to 100: all three jump. Drag s to 8: the third card grows fastest. "Churn depth is the price of a guarantee that does not depend on the program."
3. *Find L* (ε=10⁻⁴): 131 / 195 / 204. The first two match the paper's design table; scroll down to point at the two tables.

**Demo 3: Persistent names with churn**
1. Default L=30, s=2: the verdict says whether this random table is vulnerable. *New random table* a few times to see both outcomes.
2. When vulnerable: *Run the chain*. The last push is refused. "This is the constructive half of Proposition 12."
3. *Estimate over 2000 random tables*: the simulated probability sits below the closed-form bound.

**If something breaks:** show the saved screenshots, or the design tables directly in the PDF. The Theory tab is client-side only; a hard reload fixes most problems. `npm test` re-verifies the same formulas against the Python reference in about 5 seconds.

---

## 4. Cutting to size

**10 minutes.** Slides 1, 2, 4, 5, 6 (demo 1, short), 8–9 (demo 2, short), 13, 14. Drop orphans, fill, Proposition 12 (mention in one sentence on slide 13).

**30 minutes.** Add: the proof of Theorem 4(b) on a slide (a key's path only crosses cells filled before it; for any other order there is an assignment that breaks it), the proof of Theorem 7 (blocks and the cycle lemma, one slide), and Section 5 of the paper (keys and adversaries: a fresh key per table keeps the exact law against any adversarial names; a persistent key plus a probe oracle breaks it).

**If the professor interrupts early with questions:** go straight to Demo 1 and the status map. They cover most of what anyone asks.

---

## 5. Questions you will probably get

**"Isn't this just linear probing? What is actually new?"**
The primitives are classical and we say so. New, as far as our search found: (i) the characterisation of safe deletion *orders* and the converse that stack order is the only universal one; (ii) the reading of the Robin Hood displacement law as the number of keys orphaned by a deletion, with the exact finite-size form; (iii) the use of the exact refusal law to pick probe limits, including the whole-fill and unlimited-run versions; (iv) the schedule-free bound for bounded churn (Proposition 12). "None of these is a deep theorem; together they make a framework."

**"What is the hardest result?"**
"Honestly, no single result is deep. The exact refusal law (Theorem 7) has the longest proof and is the one most worth reading line by line; Proposition 12 is the most recent and the one we would most like checked."

**"Why stack discipline? Real compilers do more than that."**
Block scoping is last-in-first-out by construction. Compilers that keep several scopes alive at once (modules, namespaces) are outside this model; say so.

**"Why not a chained hash table or a tree?"**
Those allocate. The target is a single fixed buffer with all-or-nothing refusal and a known memory need. Open addressing is what fits that, which is why the question is about open addressing.

**"Is the refusal law new?"**
No. It is the tail of the classical unsuccessful-search cost (Knuth; Janson and Viola). Our part is a short derivation using only the cycle lemma and the Borel–Tanner identity, the explicit finite-size sum, the proof that the Chernoff-type bound used earlier is loose by a factor growing like L^{3/2}, and the design tables.

**"Your Theorem 6 depends on other people's bounds."**
Yes. It combines exact undo with published insertion bounds (Farach-Colton–Krapivin–Kuszmaul; interlinear probing), and parts (ii) and (iii) of its statement are made under the conditions of those papers. An unconditional version is an open problem.

**"How do you know the proofs are right?"**
Three layers, none a substitute for a human proof reader. (1) Exhaustive enumeration in exact rational arithmetic: 258 triples (m, n, L) for the refusal law, 488 919 state comparisons for exact undo, 397 562 assignment-order pairs for the safe-order theorem, 36 432 occupancy sets for Proposition 12. (2) Comparison with the real implementation: a z-test of the law against the real probe-limited table. (3) An independent re-derivation of Theorem 7 by Knuth's Abel-binomial route (481 cases). Plus a separate cold referee pass on Proposition 12. "Everything reruns with one script."

**"Did an AI write this?"**
Yes, in part, and the repository documents it in full (`docs/AI_USE_DISCLOSURE.md`, and the "Declarations" section of the paper): the AI proposed statements, drafted proofs and wrote the verification programs; the authors direct the work and are responsible for it. Do not play it down, and do not claim to have read anything you have not. The disclosure lists what the AI did *not* do: it did not make timing measurements, did not use a proof assistant, and no author had yet recorded a reading of the proofs. If you have since read them, say that.

**"What about real hardware or timing?"**
Not claimed. The attack results use an idealised oracle; no timing was measured. Embedded runs in the earlier empirical paper were on an emulated Cortex-M3.

**"What can an attacker do?"**
With an independent key per table the exact law holds against arbitrary adversarial names (Proposition 13). With a persistent key and a probe oracle it does not (Propositions 14–15): an adversary can build collisions at a cost we quantify, on the order of m log m queries with a strong oracle. These results are model-based.

**"What is Proposition 12 good for, and where does it fail?"**
It gives a guarantee that does not depend on how long the program runs or in what order it calls things, when there is a persistent set of names and bounded churn above it. It is not sharp for short runs (the plain union bound is smaller for the first tens to hundreds of pushes) and is uninformative when scopes can add many names at once.

**"What would you do next?"**
Two things. A limit law for refusal probabilities on wide, deep scope trees (we tried; simulation shows failures cluster on shared prefixes, a mixture structure we could not turn into a clean statistic). And an unconditional version of Theorem 6, which needs a lower bound for stable schemes under stack discipline.

**"Where would you publish this?"**
Do not speculate. "We have not chosen a venue; the paper is correct and reproducible, and its contribution is a framework plus exact results, not a single hard theorem."

---

## 6. What not to say

- Do not call the refusal law, its Poisson limit, its tail, or the orphan limit law new.
- Do not call Theorem 6 unconditional.
- Do not say the proofs have been formally verified. They are pen-and-paper, checked by programs.
- Do not say the attack was demonstrated on hardware or with timing.
- Do not say the paper settles the scope-tree question. Proposition 12 settles bounded churn above a persistent set.
- Do not describe any result as "deep". If the professor says so first, agree.

## 7. Quick glossary

| Term | Meaning |
|---|---|
| ring, cell, home | the table is a circle of m cells; a key's home is where its hash points; it is placed in the first free cell from its home |
| non-reordering | a key never moves after placement |
| probe limit L | a key is refused if the L cells from its home are all occupied |
| refusal | the all-or-nothing "no": the table is unchanged |
| dependent / orphan | y depends on x if x's cell is on y's probe path before y's cell; clearing x first orphans y |
| block | an empty cell plus the run of occupied cells after it |
| trunk | the persistent names that are never popped |
| churn depth s | the most names live above the trunk at any moment, counting the one being pushed |
| s-vulnerable | some window of L cells holds at most s−1 empty cells |
| load α | n/m, the fraction of cells in use |

## 8. Where everything lives

| What | Where |
|---|---|
| The paper | `theory/paper/main.pdf` (source `main.tex`) |
| The demo | `frontend/web`, tab **Theory** (`npm start`) |
| What is new vs classical | `theory/NOVELTY.md` |
| Proof audit and risk list | `theory/PROOF_AUDIT.md` |
| AI-use account | `docs/AI_USE_DISCLOSURE.md` |
| Reproduce every number | `bash theory/verify/run_all.sh` (about 10 minutes) |
