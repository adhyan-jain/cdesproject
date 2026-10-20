# STRATA frontend (interactive demo)

A small web interface for showing what STRATA does: declarations, lookups, nested scopes,
shadowing, scope exit, and a fixed buffer that refuses cleanly when it is full.

**It is connected to the real table.** Every operation is executed by `strata::Table` from
`include/strata/strata.hpp` in fixed mode, inside a C++ engine (`engine/strata_engine.cpp`).
Nothing about the table is re-implemented in JavaScript. The page shows:

* statuses (`kOk`, `kRedeclared`, `kNoMemory`, `kNoScope`, ...) exactly as the table returns them;
* byte counts from `Table::stats()`;
* the buffer layout (index slots, identifier records, undo stack) read back from the buffer the
  table lives in, following the format documented at the top of `strata.hpp`;
* the table's `state_digest()` before and after every call, so a refused call can be seen to
  change nothing;
* three checks after every request: `check_invariants()`, every decoded record equals what
  `resolve()` returns, and every answer equals `tests/reference_model.hpp`.

The top bar has five groups: **Home**, **Try it** (Analyse your code, Live lab), **Results** (Benchmarks, Stress tests),
**Theory** and **About**. Pages use hash routes, so each can be linked directly, e.g. `#/benchmarks`.

* **Analyse your code** (`#/analyse`): paste a C program (int, char, float, double, bool, long, short, unsigned, const,
  static, pointers, arrays, functions, if/while/do/for/switch; not struct/union/enum/typedef). It is translated by
  `src/lib/minic.ts` in relaxed mode into the calls a compiler makes on its symbol table, those run on the real table in the
  engine, and `src/lib/analyse.ts` reports every name (type, kind, scope, line, uses, what it hides), names used but not
  declared, declared twice or never used, and the smallest buffer (256 B, 512 B, … 64 KiB) that refuses nothing.
* **Home** tells the memory story with a scroll-driven diagram (`src/components/MemoryModel.tsx`, a schematic; the Live lab
  shows the real decoded buffer). Motion is skipped when the system asks for reduced motion (`src/lib/motion.ts`).

The other pages:

* **Overview**: what STRATA is, a diagram of the buffer layout, the headline figures, STRATA's
  median memory saving against each conventional design, and a plain verdict on speed.
* **Live lab**: click operations one by one, or type a small C program (int, float, char, bool,
  blocks, functions, if/while/for) and Run or Step through it. The code is translated into the calls
  a compiler makes on its symbol table (declare, lookup, enter and exit scope); nothing is evaluated.
  The right side shows the table and the decoded memory buffer after every operation. The guided
  demo runs here.
* **Benchmarks**: pick one of the 8 compiler traces to see its workload and charts of peak memory,
  allocator calls and replay time for all six tables; then the fair comparison with the conventional
  single-buffer table (smallest fixed buffer, and replay time with 95% intervals); then a live check
  that replays any stored trace through STRATA and the single-buffer table in the engine, checking
  every answer against the reference model. Live times are from this machine and vary; the reported
  timing is the 31-round recorded run.
* **Stress tests**: the bare-metal Cortex-M3 runs under QEMU, hash flooding with and without the keyed
  hash, the shadowing / name-length sweep, chibicc end to end, and the testing totals.
* **Method & limits**: setup, the tables compared, background, limitations, how to reproduce.

Every chart has a Table view with the same numbers. All figures are read from `results/` (and, for
the test totals, from the reports, which the script checks) by `web/scripts/make-results.mjs`;
`npm run results` regenerates `src/data/recorded.json`. Charts are plain SVG in
`web/src/components/charts.tsx`; the series colours were checked for colour-vision deficiency.

### Theory view

The **Theory** tab (next to *Symbol table demo*) accompanies the theory manuscript in `theory/`. It does not use the C++
engine: it recomputes the manuscript's formulas in the browser (`web/src/lib/theory.ts`) and plays a small model of linear
probing. Four pages:

* **Exact undo & deletion order** (Theorems 2 and 4, Proposition 5): push keys on a 24-cell ring, pop the newest and see that the
  table equals the insertion of the live keys; clear any other key and see which keys become unreachable and why.
* **Refusal law & probe limit** (Theorem 7, Propositions 11 and 12): calculators for the refusal probability of one push, the chance
  that a table can ever refuse a fresh name, and the schedule-free bound for bounded churn; a search for the smallest probe limit;
  the paper's two design tables.
* **Persistent names with churn** (Proposition 12): a concrete table, its densest window, the chain of pushes that gets a name
  refused, and simulated probability against the closed-form bound.
* **What is proved**: every result with its status (new, classical with a new finite-size form, conditional, small) and what the
  paper does not claim.

`npm run theory-data` regenerates `src/data/paper-tables.json` from `theory/paper/tables/` and copies the compiled paper to
`public/strata-theory-paper.pdf` (it also runs as part of `npm run build`). `npm test` checks every formula against Python
reference values (`theory/verify/make_frontend_reference.py` regenerates `tests/theory_reference.json`) and checks the model's
claims by brute force: exact undo, that safe deletion orders are exactly the linear extensions of the dependency relation, and
that the constructed chain of pushes is refused.

The demo was added for the project review. It does not change the library, the tests, the
benchmarks or any result.

## Run it

Needs Node.js 18+ and `g++` with C++14 (MinGW on Windows is fine; set `CXX` to use another
compiler). No internet is needed after `npm install`.

```bash
cd frontend/web
npm install        # once
npm start          # builds the engine and the page, serves http://localhost:5199 and opens it
```

On Windows you can also double-click `frontend/start-demo.cmd`.

Other commands, all in `frontend/web`:

| Command | What it does |
|---|---|
| `npm run dev` | development server with hot reload on port 5199 |
| `npm test` | 37 checks: the engine against the real table, the code window's C subset (strict and relaxed), the live trace check, the Theory page's formulas and model |
| `npm run build` | type check and production build into `dist/` |
| `npm run serve` | serve an existing `dist/` without rebuilding |

## How it fits together

```
browser (React, frontend/web/src)
   │  POST /api/run {capacity, ops[]}        the page keeps the list of operations
   ▼
server/api.mjs                               validates names, types, values, limits
   │  stdin: CAP 256 / D count 0 1 / E / X / L count
   ▼
engine/strata_engine.cpp                     replays the list on a fresh strata::Table
   │  stdout: JSON (per-operation results, stats, decoded buffer, checks)
   ▼
browser renders it
```

Each request replays the whole list on a new table, so the C++ table is always the source of
truth, reset is exact, and the guided demo is deterministic. The engine is started with a fixed
path and no shell; requests can only become its input script. Limits: 400 operations, buffers
of 128 B to 64 KiB, names that are C identifiers of up to 64 characters.

The demo stores a C type in STRATA's 8-bit type tag (`int`, `float`, `char`, `bool`) and the
value in its 32-bit value field (a `float` as its IEEE-754 bit pattern).
