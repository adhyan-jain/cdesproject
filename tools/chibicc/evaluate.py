#!/usr/bin/env python3
"""End-to-end evaluation of the three chibicc builds (see build.sh).

    python3 tools/chibicc/evaluate.py [workdir] [rounds]

For every project (sources fetched earlier by tools/tcc-trace/make_traces.sh):
  1. find the translation units that the ORIGINAL chibicc compiles;
  2. compile them with the STRATA and arena builds and compare the assembly byte for byte
     (after normalising the path of the compiler's own header directory in .file lines);
  3. record the original compiler's scope activity (workloads/traces/chibicc_<project>.trace.gz);
  4. time whole-project compilation with each build, interleaved in rotating order;
  5. record the peak resident set size of each build on each unit.
Writes results/chibicc/{units.csv,times.csv,rss.csv,environment.txt}.
"""
import csv
import glob
import gzip
import os
import resource
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/cdes")
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 21
SRC = os.path.join(WORK, "src")
OUT = os.path.join(ROOT, "results", "chibicc")
TMP = os.path.join(WORK, "chibi-tmp")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
VARIANTS = ["orig", "strata", "arena"]
CC = {v: os.path.join(WORK, "cc-" + v, "chibicc") for v in VARIANTS}
FR = os.path.join(SRC, "freertos")
PROJECTS = {
    "cjson": ([], [SRC + "/cjson/cJSON.c", SRC + "/cjson/cJSON_Utils.c"]),
    "littlefs": ([], [SRC + "/littlefs/lfs.c", SRC + "/littlefs/lfs_util.c"]),
    "zlib": (["-I" + SRC + "/zlib"], sorted(glob.glob(SRC + "/zlib/*.c"))),
    "lua": (["-DLUA_USE_POSIX"], sorted(glob.glob(SRC + "/lua/src/*.c"))),
    "freertos": (["-I" + FR + "/include", "-I" + FR + "/portable/ThirdParty/GCC/Posix", "-I" + FR + "/portable/ThirdParty/GCC/Posix/utils",
                  "-I" + ROOT + "/tools/tcc-trace/freertos-config"],
                 [FR + "/" + f for f in ("tasks.c", "queue.c", "list.c", "timers.c", "event_groups.c", "stream_buffer.c", "croutine.c",
                                         "portable/MemMang/heap_4.c")]),
    "mbedtls": (["-I" + SRC + "/mbedtls/include", "-I" + SRC + "/mbedtls/library"], sorted(glob.glob(SRC + "/mbedtls/library/*.c"))),
    "sqlite": ([], sorted(glob.glob(SRC + "/sqlite/*/sqlite3.c"))),
}


def compile_unit(variant, flags, path, out, env=None):
    """Returns (ok, peak RSS in kB of the compiler process tree)."""
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    p = subprocess.run([CC[variant], "-S"] + flags + ["-o", out, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    return p.returncode == 0, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, before


units, good = [], {}
for proj, (flags, files) in PROJECTS.items():
    ok_files = []
    trace = os.path.join(TMP, "chibicc_%s.trace" % proj)
    if os.path.exists(trace):
        os.remove(trace)
    for f in files:
        env = dict(os.environ, CDES_TRACE=trace + ".unit")
        if os.path.exists(trace + ".unit"):
            os.remove(trace + ".unit")
        ok, _, _ = compile_unit("orig", flags, f, os.path.join(TMP, "orig.s"), env)
        same = {}
        if ok:
            with open(trace, "a") as dst, open(trace + ".unit") as src:
                dst.write(src.read())
            for v in ("strata", "arena"):
                ok2, _, _ = compile_unit(v, flags, f, os.path.join(TMP, v + ".s"))
                # the only legitimate difference is the directory of the compiler's own headers in .file lines
                norm = lambda name, var: open(os.path.join(TMP, name), "rb").read().replace(("cc-%s/include" % var).encode(), b"cc-X/include")
                same[v] = ok2 and norm(v + ".s", v) == norm("orig.s", "orig")
            ok_files.append(f)
        units.append({"project": proj, "unit": os.path.basename(f), "original_compiles": int(ok),
                      "strata_identical_asm": int(same.get("strata", False)), "arena_identical_asm": int(same.get("arena", False))})
    good[proj] = ok_files
    if ok_files:
        with open(trace, "rb") as src, gzip.GzipFile(os.path.join(ROOT, "workloads", "traces", "chibicc_%s.trace.gz" % proj), "wb", mtime=0) as dst:
            dst.write(src.read())
    print("%-9s %3d of %3d units compile; identical assembly: strata %d, arena %d" % (
        proj, len(ok_files), len(files), sum(u["strata_identical_asm"] for u in units if u["project"] == proj),
        sum(u["arena_identical_asm"] for u in units if u["project"] == proj)), flush=True)
with open(os.path.join(OUT, "units.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(units[0]))
    w.writeheader()
    w.writerows(units)

# peak RSS per unit: each compile in its own measuring child so ru_maxrss is per unit
rss_rows = []
for proj, files in good.items():
    flags = PROJECTS[proj][0]
    for f in files:
        row = {"project": proj, "unit": os.path.basename(f)}
        for v in VARIANTS:
            out = subprocess.run(["/usr/bin/time", "-f", "%M", CC[v], "-S"] + flags + ["-o", "/dev/null", f],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True).stderr.strip().split("\n")[-1]
            row[v + "_peak_rss_kb"] = int(out)
        rss_rows.append(row)
with open(os.path.join(OUT, "rss.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rss_rows[0]))
    w.writeheader()
    w.writerows(rss_rows)

# whole-project compile time, interleaved rounds
with open(os.path.join(OUT, "times.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["project", "variant", "round", "seconds", "units"])
    for proj, files in good.items():
        if not files:
            continue
        flags = PROJECTS[proj][0]
        for rnd in range(-1, ROUNDS):
            for k in range(3):
                v = VARIANTS[(rnd + 1 + k) % 3]
                t0 = time.perf_counter()
                for src in files:
                    subprocess.run([CC[v], "-S"] + flags + ["-o", "/dev/null", src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                dt = time.perf_counter() - t0
                if rnd >= 0:
                    w.writerow([proj, v, rnd, "%.6f" % dt, len(files)])
        print("timed", proj, flush=True)

with open(os.path.join(OUT, "environment.txt"), "w") as f:
    f.write("chibicc: https://github.com/rui314/chibicc commit 90d1f7f (MIT), patched by tools/chibicc/apply_patch.py\n")
    f.write("builds: cc -std=c11 -O2; back ends g++ -std=c++14 -O2 -fno-exceptions -fno-rtti\n")
    f.write("rounds: %d (+1 warm-up); in each round every build compiles all units of a project, order rotated\n" % ROUNDS)
    f.write("kernel: %s\n" % subprocess.run(["uname", "-sr"], capture_output=True, text=True).stdout.strip())
    f.write("host cc: %s\n" % subprocess.run(["cc", "--version"], capture_output=True, text=True).stdout.split("\n")[0])
print("wrote", OUT)
