#!/usr/bin/env python3
"""Instruction-count table of the article (tables/tab_instr.tex) from results/review/instr_counts.csv.

    python3 manuscript/tools/make_instr_table.py

The CSV is written by benchmarks/instr_count.cpp (see docs/REVIEW_MANIFEST.md).
"""
import collections
import csv
import os
import statistics as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NAMES = {"cjson": "cJSON", "freertos": "FreeRTOS", "littlefs": "littlefs", "lua": "Lua",
         "mbedtls": "Mbed TLS", "sqlite": "SQLite", "tinycc": "TinyCC", "zlib": "zlib"}
ORDER = ["zlib", "cjson", "littlefs", "freertos", "lua", "mbedtls", "tinycc", "sqlite"]

d = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(ROOT, "results/review/instr_counts.csv"))):
    d[(r["trace"], r["impl"])].append(int(r["instructions"]))


def med(t, impl):
    return st.median(d[(t, impl)])


rows = ["%s & %.2f & %.2f & %.2f & %.2f & %.2f \\\\" % (
    NAMES[t], med(t, "strata") / 1e6, med(t, "c0_stored_hash") / 1e6, med(t, "c1_no_hash") / 1e6,
    med(t, "strata") / med(t, "c0_stored_hash"), med(t, "strata") / med(t, "c1_no_hash")) for t in ORDER]
tab = r"""\begin{table}[t!]
\strcap{User-Space Instructions for One Replay of Each Trace (Millions, Median of Five Replays; x86-64, \code{g++} \code{-O2}) and the Ratio of \st\ to the Two Conventional Tables. The Count of a Table Varied by at Most 0.03 Percent Between Replays.}
\label{tab:instr}
\centering
\setlength{\tabcolsep}{3pt}
\begin{tabular}{|l|r|r|r|r|r|}
\hline
Project & \st & $C_0$ & $C_1$ & \st/$C_0$ & \st/$C_1$ \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}
\end{table}
"""
open(os.path.join(ROOT, "manuscript/ieee_access/tables/tab_instr.tex"), "w").write(tab)
