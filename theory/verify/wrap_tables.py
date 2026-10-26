"""Wrap the generated row files (tables/*.rows) into complete tabular environments (tables/*.tex).
\\input of bare rows inside a tabular is fragile with current LaTeX file hooks, so the generators write rows
and this script writes the complete environments that main.tex inputs."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "../paper/tables")
SPECS = {
 "tab_design": ("@{}llrrrrrrr@{}",
   r"load & $\varepsilon$ & $m{=}2^{8}$ & $2^{10}$ & $2^{12}$ & $2^{14}$ & $2^{16}$ & $m\to\infty$ & Chernoff \\"),
 "tab_lawcheck": ("@{}rrrrrrrrr@{}",
   r"$m$ & $n$ & $L$ & trials & observed & exact & $z$ & clean trials & mismatches \\"),
 "tab_lawproc": ("@{}rrrrrrrrr@{}",
   r"$m$ & $n$ & $L$ & clean & with refusal & refused in fill & (iii) $\hat P$ & (iv) $\hat P$ & violations \\"),
 "tab_adaptive": ("@{}rrrrr@{}",
   r"colliders & persistent key (mean) & (max) & fresh key & random names \\"),
 "tab_ladder": ("@{}lrrrrrrrr@{}",
   r"trace & $C_0$ & $C_1$ & $C_2$ & $S_{\mathrm{raw}}$ & $S$ & hash & pack & total \\"),
}
for name, (spec, header) in SPECS.items():
    rows = open(os.path.join(T, name + ".rows")).read().rstrip("\n")
    with open(os.path.join(T, name + ".tex"), "w") as f:
        f.write("\\begin{tabular}{" + spec + "}\n\\toprule\n" + header + "\n\\midrule\n" + rows + "\n\\bottomrule\n\\end{tabular}\n")
print("wrapped", ", ".join(SPECS))
