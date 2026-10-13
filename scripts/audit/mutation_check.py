#!/usr/bin/env python3
"""Does the fuzzer notice bugs? Inject known defects into a copy of the header and fuzz it.

    python3 scripts/audit/mutation_check.py [seconds per mutant, default 60]

Each mutant is one small edit of include/strata/strata.hpp made in a scratch directory
(the repository is not modified). The fuzzer is built against the mutant and run on the
existing corpus plus new inputs for a limited time. A mutant is "detected" when the fuzzer
stops with a failure. Needs clang++-21; writes reports/artifacts/mutation_check.log.
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK = os.environ.get("FUZZ_DIR", "/opt/strata_fuzz")
SECONDS = sys.argv[1] if len(sys.argv) > 1 else "60"
CXX = os.environ.get("FUZZ_CXX", "clang++-21")

MUTANTS = [
    ("M1", "scope exit does not empty the index slot of a removed name",
     "                w_[e[0]] = 0;                  // first declaration of the name: empty its index slot\n",
     "                                               // (mutant: slot left in place)\n"),
    ("M2", "record pointer not refreshed after the buffer may have moved",
     "            rec = ident(ref);                          // ensure() may have moved the buffer\n",
     "\n"),
    ("M3", "scope exit restores the hidden value but not its type and depth",
     "                rec[1] = (rec[1] & kKeyBits) | e[2];\n",
     "                rec[1] = (rec[1] & kKeyBits);\n"),
    ("M4", "probe limit not enforced when a new name is inserted",
     "        if (opt_.max_probe && stop == kNoSlot) return kProbeLimit;   // no empty slot within the limit\n",
     "\n"),
    ("M5", "length of raw names not kept (names differing in trailing NUL bytes merge)",
     "            tail = static_cast<uint32_t>(len & 3);",
     "            tail = 0;"),
    ("M7", "index rebuild does not restore the value words it borrowed",
     "            rec[0] = e[0];\n            e[0] = slot;\n",
     "            e[0] = slot;\n"),
    ("M8", "undo entries not updated when the index is rebuilt",
     "            rec[0] = e[0];\n            e[0] = slot;\n",
     "            rec[0] = e[0];\n"),
    ("M9", "new name placed at the remembered slot although the index was rebuilt",
     "        if (stop != kNoSlot && idx_ == idx_before) {",
     "        if (stop != kNoSlot) {"),
    ("M6", "a refused shadowing declaration still overwrites the visible value",
     "            if (!ensure(3, 0)) return kNoMemory;\n",
     "            if (!ensure(3, 0)) { rec[0] = static_cast<uint32_t>(value); return kNoMemory; }\n"),
]


def main():
    with open(os.path.join(ROOT, "include/strata/strata.hpp"), encoding="utf-8") as fh:
        original = fh.read()
    lines = [f"seconds per mutant: {SECONDS}; compiler: {CXX}", ""]
    detected = 0
    for mid, what, old, new in MUTANTS:
        if original.count(old) != 1:
            lines.append(f"{mid} | NOT APPLIED | {what} | pattern found {original.count(old)} times")
            continue
        d = os.path.join(WORK, "mutants", mid)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(os.path.join(d, "include/strata"))
        os.makedirs(os.path.join(d, "tests"))
        os.makedirs(os.path.join(d, "corpus"))
        with open(os.path.join(d, "include/strata/strata.hpp"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original.replace(old, new))
        for f in ("fuzz_strata.cpp", "reference_model.hpp"):
            shutil.copy(os.path.join(ROOT, "tests", f), os.path.join(d, "tests", f))
        build = subprocess.run([CXX, "-std=c++14", "-g", "-O1", "-fsanitize=fuzzer,address,undefined",
                                "-fno-sanitize-recover=all", "-o", "fuzz", "tests/fuzz_strata.cpp"],
                               cwd=d, capture_output=True, text=True)
        if build.returncode != 0:
            lines.append(f"{mid} | BUILD FAILED | {what} | {build.stderr[:200]}")
            continue
        t0 = time.time()
        run = subprocess.run(["./fuzz", "-max_len=4096", f"-max_total_time={SECONDS}", "corpus",
                              os.path.join(WORK, "corpus")], cwd=d, capture_output=True, text=True)
        took = time.time() - t0
        reason = ""
        for line in run.stderr.splitlines():
            if "FUZZ FAILURE" in line or "ERROR: AddressSanitizer" in line or "runtime error" in line:
                reason = line.strip()[:140]
                break
        if run.returncode != 0:
            detected += 1
            lines.append(f"{mid} | DETECTED after {took:.1f} s | {what} | {reason}")
        else:
            lines.append(f"{mid} | NOT DETECTED in {SECONDS} s | {what} |")
    lines += ["", f"detected {detected} of {len(MUTANTS)} mutants"]
    out = "\n".join(lines) + "\n"
    os.makedirs(os.path.join(ROOT, "reports/artifacts"), exist_ok=True)
    with open(os.path.join(ROOT, "reports/artifacts/mutation_check.log"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
