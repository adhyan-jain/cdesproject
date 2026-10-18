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

The page has three parts:

* **Operations / Write code** (left): click operations one by one, or type a small C program
  (int, float, char, bool, blocks, functions, if/while/for) and Run or Step through it. The code
  is translated into the calls a compiler makes on its symbol table (declare, lookup, enter and
  exit scope); nothing is evaluated. Each event shows the source line it came from.
* **Symbol table and memory buffer** (right): the table's state after the last operation.
* **Accuracy & performance** (below): headline figures and tables read from the recorded paper
  run by `web/scripts/make-results.mjs` (`npm run results` regenerates `src/data/recorded.json`),
  and a live check that replays any of the 8 stored compiler traces through STRATA and the
  conventional single-buffer table (`benchmarks/baselines/arena_chain.hpp`) in the engine,
  checking every answer against the reference model. Live times are from this machine and vary;
  the reported timing is the paper's 31-round run.

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
| `npm test` | 33 checks: the engine against the real table, the code window's C subset, the live trace check, the Theory page's formulas and model |
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
