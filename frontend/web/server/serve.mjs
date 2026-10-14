// Serves the built demo (dist/) and the engine API on http://127.0.0.1:5199.
// Works offline. Set PORT to change the port, NO_OPEN=1 to skip opening the browser.
import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { spawn } from "node:child_process";
import { apiMiddleware } from "./api.mjs";
import { webRoot } from "./paths.mjs";

const dist = join(webRoot, "dist");
const port = Number(process.env.PORT) || 5199;
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml",
  ".woff2": "font/woff2", ".woff": "font/woff", ".json": "application/json", ".ico": "image/x-icon" };

if (!existsSync(join(dist, "index.html"))) {
  console.error("dist/ not found: run `npm run build` (or `npm start`) first.");
  process.exit(1);
}

const server = createServer((req, res) => {
  apiMiddleware(req, res, () => {
    const path = normalize(decodeURIComponent((req.url || "/").split("?")[0])).replace(/^([\\/]\.\.)+/, "");
    let file = join(dist, path);
    if (!file.startsWith(dist) || !existsSync(file) || statSync(file).isDirectory()) file = join(dist, "index.html");
    res.setHeader("Content-Type", types[extname(file)] || "application/octet-stream");
    res.end(readFileSync(file));
  });
}).listen(port, "127.0.0.1", () => {
  const url = `http://localhost:${port}`;
  console.log(`STRATA demo running at ${url}  (Ctrl+C to stop)`);
  if (!process.env.NO_OPEN) {
    const cmd = process.platform === "win32" ? ["cmd", ["/c", "start", "", url]] : process.platform === "darwin" ? ["open", [url]] : ["xdg-open", [url]];
    try { spawn(cmd[0], cmd[1], { stdio: "ignore", detached: true }).unref(); } catch { /* open it by hand */ }
  }
});

server.on("error", (e) => {
  if (e.code === "EADDRINUSE") {
    console.error(`Port ${port} is already in use: the demo is probably running already. Open http://localhost:${port}, or close the other window and try again.`);
  } else {
    console.error(e.message);
  }
  process.exit(1);
});
