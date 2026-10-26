// Shared number formatting and trace names for the results pages.
export const nf = new Intl.NumberFormat("en-US");
export const compact = (n: number) =>
  n >= 1e6 ? `${trim(n / 1e6)}M` : n >= 1e4 ? `${trim(n / 1e3)}K` : nf.format(n);
const trim = (x: number) => (Math.round(x * 10) / 10).toString();
export const kib = (x: number) => `${x.toFixed(1)} KiB`;
export const pct = (x: number, digits = 1) => `${x.toFixed(digits)}%`;

const TRACE_LABEL: Record<string, string> = {
  cjson: "cJSON", littlefs: "littlefs", zlib: "zlib", freertos: "FreeRTOS",
  lua: "Lua", tinycc: "TinyCC", sqlite: "SQLite", mbedtls: "Mbed TLS",
};
export const TRACE_BLURB: Record<string, string> = {
  cjson: "JSON parser", littlefs: "embedded file system", zlib: "compression library", freertos: "real-time OS kernel",
  lua: "scripting language", tinycc: "C compiler", sqlite: "database engine", mbedtls: "TLS / crypto library",
};
export const traceLabel = (t: string) => TRACE_LABEL[t] ?? t;
