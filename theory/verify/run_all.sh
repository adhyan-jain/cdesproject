#!/bin/bash
# Regenerates every table, figure data file and numeric macro of the theory paper from the verification
# programs, then builds the PDF.  Needs: g++ (C++14), python3 (standard library only), pdflatex + bibtex.
# Runtime: about 6 minutes (the end-to-end check against the real table dominates).
set -e
cd "$(dirname "$0")"
BUILD=${TMPDIR:-/tmp}/strata_theory_build; mkdir -p "$BUILD"
echo "== exact refusal law vs brute-force enumeration (rational arithmetic)";   python3 exact_law.py
echo "== stack-discipline results (undo, exactness, orphans)";                   python3 lifo_check.py
echo "== safe deletion orders and the orphan law";                               python3 orphan_law.py
echo "== refusal-free fill law (brute force, closed form, design table)";    python3 fill_law.py
echo "== unlimited-run (sustainability) law";                                 python3 sustain_law.py
echo "== re-entrant scope schedules";                                          python3 tree_schedule_check.py
echo "== exact law vs stored 240M-sample simulation";                            python3 design_table.py
echo "== exact law vs the real strata::Table (z-test, bounded/unbounded agree)"
g++ -std=c++14 -O2 -I../../include -o "$BUILD/law_vs_table" law_vs_table.cpp
python3 run_law_check.py "$BUILD/law_vs_table" 400000
echo "== remaining proofs: ledger at every instant, limit/asymptotic corollaries, orphan mean"; python3 proof_checks.py
echo "== design rule table";                                                     python3 design_rule.py > /dev/null
echo "== exact space ledger on the eight traces (reproduces measured minima)";   python3 space_model.py
echo "== persistent versus fresh key (illustration)"
g++ -std=c++14 -O2 -I../../include -o "$BUILD/adaptive_key_demo" adaptive_key_demo.cpp
"$BUILD/adaptive_key_demo" 2048 512 700 5 400 512 600 700 800 | tee adaptive_key_demo.out
python3 adaptive_to_tex.py
echo "== figure data and macros";                                                python3 make_figdata.py
python3 wrap_tables.py
echo "== paper"
cd ../paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > "$BUILD/latexmk.log" 2>&1 && echo "built paper/main.pdf" || { tail -30 "$BUILD/latexmk.log"; exit 1; }
