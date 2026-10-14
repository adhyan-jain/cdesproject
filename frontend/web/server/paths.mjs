import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
export const webRoot = resolve(here, "..");
export const repoRoot = resolve(here, "..", "..", "..");
export const enginePath = join(repoRoot, "frontend", "engine", "bin", process.platform === "win32" ? "strata_engine.exe" : "strata_engine");
