"""z-test of the exact refusal law against the real strata::Table (see law_vs_table.cpp)."""
import subprocess, sys, os, math
from design_table import refuse
HERE = os.path.dirname(os.path.abspath(__file__))
exe = sys.argv[1]
cases = [(256, 128, 8), (256, 160, 16), (256, 190, 24), (256, 190, 40), (1024, 760, 48), (1024, 760, 96), (1024, 512, 24),
         (4096, 3071, 80), (4096, 3071, 100), (16384, 12287, 80)]   # n one below the 3/4 load limit, so the last name still fits
trials_all = int(sys.argv[2]) if len(sys.argv) > 2 else 400000
tot_mis = 0; worst = 0; tot_coupling = 0
print("   m    n    L    trials   observed   exact-law    z      clean-trials  status/digest mismatches")
rows_tex = []; proc_rows = []
for (m, n, L) in cases:
    trials = trials_all if m < 16384 else trials_all // 4      # a trial at 16 384 slots is 16 times longer
    p = refuse(m, n, [L])[L]
    out = subprocess.check_output([exe, str(m), str(n), str(L), str(trials), str(1000 + m + n + L)]).split()
    (ex, clean, mis, ex_clean, dirty, fill_ref, bfin, bfin_dirty, coup, stored, stored_clean) = [int(v) for v in out]
    z = (ex - trials * p) / math.sqrt(trials * p * (1 - p))
    worst = max(worst, abs(z)); tot_mis += mis; tot_coupling += coup
    print(f"{m:5d} {n:4d} {L:4d} {trials:9d}  {ex/trials:9.5f}  {p:9.5f}  {z:6.2f}  {clean:11d}  {mis}")
    rows_tex.append(f"{m} & {n} & {L} & {trials:,} & {ex/trials:.5f} & {p:.5f} & {z:+.2f} & {clean:,} & {mis} \\\\".replace(",", "\\,"))
    # processes (iii) and (iv): conditional on a refusal-free fill, and continued after refusals
    pc = ex_clean / clean if clean else float("nan")
    proc_rows.append(f"{m} & {n} & {L} & {clean:,} & {dirty:,} & {fill_ref:,} & {pc:.5f} & {bfin/trials:.5f} & {coup} \\\\".replace(",", "\\,"))
    print(f"      (iii) P(refuse | refusal-free fill) = {pc:.5f} over {clean} trials;  (iv) final query refused after continued fill: {bfin/trials:.5f}; "
          f"trials with a refusal in the fill {dirty}, refused fill operations {fill_ref}, coupling violations {coup}")
print(f"max |z| = {worst:.2f}; mismatches = {tot_mis}; coupling violations = {tot_coupling}")
os.makedirs(os.path.join(HERE, "../paper/tables"), exist_ok=True)
with open(os.path.join(HERE, "../paper/tables/tab_lawcheck.rows"), "w") as f:
    f.write("\n".join(rows_tex) + "\n")
with open(os.path.join(HERE, "../paper/tables/tab_lawproc.rows"), "w") as f:
    f.write("\n".join(proc_rows) + "\n")
with open(os.path.join(HERE, "../paper/tables/lawcheck_summary.tex"), "w") as f:
    f.write(f"\\newcommand{{\\LawCheckTrials}}{{{trials_all:,}}}\n".replace(",", "\\,") + f"\\newcommand{{\\LawCheckMaxZ}}{{{worst:.2f}}}\n\\newcommand{{\\LawCheckMismatch}}{{{tot_mis}}}\n\\newcommand{{\\LawCheckCoupling}}{{{tot_coupling}}}\n")
sys.exit(1 if tot_mis or tot_coupling or worst > 4.5 else 0)
