"""z-test of the exact refusal law against the real strata::Table (see law_vs_table.cpp)."""
import subprocess, sys, os, math
from design_table import refuse
HERE = os.path.dirname(os.path.abspath(__file__))
exe = sys.argv[1]
cases = [(256, 128, 8), (256, 160, 16), (256, 190, 24), (256, 190, 40), (1024, 760, 48), (1024, 760, 96), (1024, 512, 24)]
trials = int(sys.argv[2]) if len(sys.argv) > 2 else 400000
tot_mis = 0; worst = 0
print("   m    n    L    trials   observed   exact-law    z      clean-trials  status/digest mismatches")
rows_tex = []
for (m, n, L) in cases:
    p = refuse(m, n, [L])[L]
    out = subprocess.check_output([exe, str(m), str(n), str(L), str(trials), str(1000 + m + n + L)]).split()
    ex, clean, mis = int(out[0]), int(out[1]), int(out[2])
    z = (ex - trials * p) / math.sqrt(trials * p * (1 - p))
    worst = max(worst, abs(z)); tot_mis += mis
    print(f"{m:5d} {n:4d} {L:4d} {trials:9d}  {ex/trials:9.5f}  {p:9.5f}  {z:6.2f}  {clean:11d}  {mis}")
    rows_tex.append(f"{m} & {n} & {L} & {ex/trials:.5f} & {p:.5f} & {z:+.2f} & {clean:,} & {mis} \\\\".replace(",", "\\,"))
print(f"max |z| = {worst:.2f}; mismatches = {tot_mis}")
os.makedirs(os.path.join(HERE, "../paper/tables"), exist_ok=True)
with open(os.path.join(HERE, "../paper/tables/tab_lawcheck.rows"), "w") as f:
    f.write("\n".join(rows_tex) + "\n")
with open(os.path.join(HERE, "../paper/tables/lawcheck_summary.tex"), "w") as f:
    f.write(f"\\newcommand{{\\LawCheckTrials}}{{{trials:,}}}\n".replace(",", "\\,") + f"\\newcommand{{\\LawCheckMaxZ}}{{{worst:.2f}}}\n\\newcommand{{\\LawCheckMismatch}}{{{tot_mis}}}\n")
sys.exit(1 if tot_mis or worst > 4.5 else 0)
