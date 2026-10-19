"""Reference values for the browser demo's tests (frontend/web/tests/theory.test.mjs).

The demo recomputes the manuscript's formulas in TypeScript.  This script evaluates the same formulas with the
repository's Python implementations (the ones that produce the paper's tables) at a fixed grid of points and writes
them to frontend/web/tests/theory_reference.json; the test compares the two to a relative tolerance.
Run:  python3 theory/verify/make_frontend_reference.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fill_law import R_refusal
from sustain_law import p_bad_float
from band_law import D_float

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend/web/tests/theory_reference.json")

refusal = [(m, int(0.75*m), L) for m, Ls in [(256, (20, 45, 60)), (1024, (60, 100, 150)), (4096, (100, 160, 240))] for L in Ls]
unlimited = [(m, int(0.75*m), L) for m, Ls in [(256, (45, 80, 116)), (1024, (80, 123, 195)), (4096, (130, 162, 256))] for L in Ls]
churn = ([(256, 192, s, L) for s in (1, 2, 4) for L in (60, 90, 120)] +
         [(1024, 768, s, L) for s in (1, 2, 4, 8) for L in (100, 132, 174)] +
         [(4096, 3072, s, L) for s in (2, 8) for L in (171, 219)])

ref = {
    "refusal": [dict(m=m, n=n, L=L, value=R_refusal(m, n, L)) for (m, n, L) in refusal],
    "unlimited": [dict(m=m, n=n, L=L, value=float(p_bad_float(m, n, L))) for (m, n, L) in unlimited],
    "churn": [dict(m=m, n=n, s=s, L=L, value=float(D_float(m, n, s, L))) for (m, n, s, L) in churn],
}
with open(OUT, "w") as f:
    json.dump(ref, f, indent=1)
print("wrote", os.path.normpath(OUT), {k: len(v) for k, v in ref.items()})
