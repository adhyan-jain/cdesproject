// Reads the design tables of the theory manuscript and writes src/data/paper-tables.json for the Theory page,
// and copies the compiled manuscript into public/ so the page can link to it. Nothing is typed by hand.
// Skips quietly when theory/ is not present (the demo itself does not need it).
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const web = join(here, "..");
const paper = join(web, "..", "..", "theory", "paper");

const rows = (file) => readFileSync(join(paper, "tables", file), "utf8")
  .split("\n").filter((l) => l.includes("&") && l.includes("\\\\") && !l.includes("$m$"))
  .map((l) => l.replace("\\\\", "").split("&").map((c) => c.trim()));
const eps = (cell) => {
  const m = cell.match(/10\^\{(-?\d+)\}/);
  return m ? Math.pow(10, Number(m[1])) : Number(cell);
};

if (!existsSync(join(paper, "tables", "tab_band.tex"))) {
  console.log("theory/paper/tables not found: keeping the existing src/data/paper-tables.json");
  process.exit(0);
}

const sustain = rows("tab_sustain.tex").map(([m, e, one, unl, extra]) => ({ m: +m, eps: eps(e), onePush: +one, unlimited: +unl, extra: +extra }));
const header = readFileSync(join(paper, "tables", "tab_band.tex"), "utf8").split("\n").find((l) => l.includes("$s="));
const s = [...header.matchAll(/s=(\d+)/g)].map((x) => +x[1]);
const band = rows("tab_band.tex").map(([m, e, ...L]) => ({ m: +m, eps: eps(e), L: L.map(Number) }));

writeFileSync(join(web, "src", "data", "paper-tables.json"), JSON.stringify({ sustain, band: { s, rows: band } }, null, 1) + "\n");
console.log(`paper-tables.json: ${sustain.length} sustain rows, ${band.length} band rows (s = ${s.join(", ")})`);

const pdf = join(paper, "main.pdf");
if (existsSync(pdf)) {
  mkdirSync(join(web, "public"), { recursive: true });
  copyFileSync(pdf, join(web, "public", "strata-theory-paper.pdf"));
  console.log("copied the manuscript to public/strata-theory-paper.pdf");
}
