// Local JSON API in front of the STRATA engine. Used by the Vite dev server and by serve.mjs.
//
//   GET  /api/health   engine present and answering
//   POST /api/run      { capacity, ops: [{op:"declare",name,type,value} | {op:"declareFrom",name,type,src}
//                                        | {op:"lookup",name} | {op:"enter"} | {op:"exit"}] }
//   POST /api/trace    { trace: "zlib" }  replay a whole stored compiler trace (accuracy + timing)
//
// Every request is validated here and again by the engine. The engine is started with a
// fixed path and no shell; the request only ever becomes its stdin script.
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { enginePath, repoRoot } from "./paths.mjs";

// The eight compiler traces of the paper (TinyCC compiling each project), in workloads/traces/.
export const TRACES = {
  cjson: "cJSON", littlefs: "littlefs", zlib: "zlib", freertos: "FreeRTOS", lua: "Lua",
  tinycc: "TinyCC", sqlite: "SQLite", mbedtls: "Mbed TLS",
};

const NAME = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/;
const MAX_OPS = 400;

export function toScript(body) {
  if (!body || typeof body !== "object") throw new Error("request body must be a JSON object");
  const cap = body.capacity;
  if (!Number.isInteger(cap) || cap < 128 || cap > 65536 || cap % 4) throw new Error("capacity must be 128..65536 bytes, a multiple of 4");
  if (!Array.isArray(body.ops) || body.ops.length > MAX_OPS) throw new Error(`ops must be an array of at most ${MAX_OPS} operations`);
  const lines = [`CAP ${cap}`];
  for (const op of body.ops) {
    switch (op?.op) {
      case "declare":
        if (!NAME.test(op.name ?? "")) throw new Error(`invalid name: ${String(op.name)}`);
        if (!Number.isInteger(op.type) || op.type < 0 || op.type > 255) throw new Error("type must be 0..255");
        if (!Number.isInteger(op.value) || op.value < -2147483648 || op.value > 2147483647) throw new Error("value must be a 32-bit integer");
        lines.push(`D ${op.name} ${op.type} ${op.value}`);
        break;
      case "declareFrom":
        if (!NAME.test(op.name ?? "") || !NAME.test(op.src ?? "")) throw new Error(`invalid name: ${String(op.name)} / ${String(op.src)}`);
        if (!Number.isInteger(op.type) || op.type < 0 || op.type > 255) throw new Error("type must be 0..255");
        lines.push(`V ${op.name} ${op.type} ${op.src}`);
        break;
      case "lookup":
        if (!NAME.test(op.name ?? "")) throw new Error(`invalid name: ${String(op.name)}`);
        lines.push(`L ${op.name}`);
        break;
      case "enter": lines.push("E"); break;
      case "exit": lines.push("X"); break;
      default: throw new Error(`unknown operation: ${String(op?.op)}`);
    }
  }
  return lines.join("\n") + "\n";
}

export function traceScript(name) {
  if (!Object.prototype.hasOwnProperty.call(TRACES, name)) throw new Error(`unknown trace: ${String(name)}`);
  const text = gunzipSync(readFileSync(join(repoRoot, "workloads", "traces", `${name}.trace.gz`))).toString("utf8");
  return "TRACE\n" + text;
}

export function runEngine(script, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    if (!existsSync(enginePath)) return reject(new Error("engine not built: run `npm run engine` in frontend/web"));
    const child = spawn(enginePath, [], { stdio: ["pipe", "pipe", "pipe"], shell: false, windowsHide: true });
    let out = "", err = "";
    const timer = setTimeout(() => { child.kill(); reject(new Error("engine timed out")); }, timeoutMs);
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    child.on("error", (e) => { clearTimeout(timer); reject(e); });
    child.on("close", () => {
      clearTimeout(timer);
      try { resolve(JSON.parse(out)); } catch { reject(new Error(`engine gave no valid answer${err ? ": " + err.trim() : ""}`)); }
    });
    child.stdin.end(script);
  });
}

function send(res, status, obj) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(obj));
}

function readBody(req, limit = 64 * 1024) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => { data += c; if (data.length > limit) { reject(new Error("request too large")); req.destroy(); } });
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });
}

// Connect-style middleware: handles /api/*, passes everything else on.
export async function apiMiddleware(req, res, next) {
  const url = (req.url || "").split("?")[0];
  if (!url.startsWith("/api/")) return next ? next() : undefined;
  try {
    if (url === "/api/health" && req.method === "GET") {
      const r = await runEngine("CAP 256\n");
      return send(res, 200, { ok: r.ok === true, engine: r.engine });
    }
    if (url === "/api/run" && req.method === "POST") {
      let body;
      try { body = JSON.parse(await readBody(req)); } catch { return send(res, 400, { ok: false, error: "body is not valid JSON" }); }
      let script;
      try { script = toScript(body); } catch (e) { return send(res, 400, { ok: false, error: e.message }); }
      const r = await runEngine(script);
      return send(res, r.ok ? 200 : 400, r);
    }
    if (url === "/api/trace" && req.method === "POST") {
      let body;
      try { body = JSON.parse(await readBody(req)); } catch { return send(res, 400, { ok: false, error: "body is not valid JSON" }); }
      let script;
      try { script = traceScript(body?.trace); } catch (e) { return send(res, 400, { ok: false, error: e.message }); }
      const r = await runEngine(script, 120000);
      return send(res, r.ok ? 200 : 400, { ...r, trace: body.trace, label: TRACES[body.trace] });
    }
    return send(res, 404, { ok: false, error: "no such endpoint" });
  } catch (e) {
    return send(res, 503, { ok: false, error: e.message });
  }
}
