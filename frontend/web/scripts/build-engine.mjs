// Compiles frontend/engine/strata_engine.cpp against include/strata/strata.hpp.
// Rebuilds only when the engine source, the STRATA header or the reference model changed.
// Set CXX to choose the compiler (default g++).
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, statSync } from "node:fs";
import { enginePath, repoRoot } from "../server/paths.mjs";
import { join, dirname } from "node:path";

const sources = [
  join(repoRoot, "frontend", "engine", "strata_engine.cpp"),
  join(repoRoot, "include", "strata", "strata.hpp"),
  join(repoRoot, "tests", "reference_model.hpp"),
];
const newest = Math.max(...sources.map((p) => statSync(p).mtimeMs));
if (existsSync(enginePath) && statSync(enginePath).mtimeMs >= newest) {
  console.log(`engine up to date: ${enginePath}`);
  process.exit(0);
}

mkdirSync(dirname(enginePath), { recursive: true });
const cxx = process.env.CXX || "g++";
const args = ["-std=c++14", "-O2", "-Wall", "-Wextra", `-I${join(repoRoot, "include")}`, "-o", enginePath, sources[0]];
if (process.platform === "win32") args.splice(4, 0, "-static");   // no MinGW runtime DLLs needed at run time
try {
  execFileSync(cxx, args, { stdio: "inherit" });
} catch {
  console.error(`\nCould not build the STRATA engine with "${cxx}". Install g++ (C++14) or set CXX.`);
  process.exit(1);
}
console.log(`engine built: ${enginePath}`);
