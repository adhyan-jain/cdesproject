// Turns one engine result into the words shown in the status line and the event history.
// Only what the engine reported is described; nothing is assumed to have succeeded.
import type { OpResult } from "./engine";
import { formatValue, scopeName, typeName } from "./values";

export type Tone = "ok" | "info" | "warn" | "error";
export interface Described { title: string; detail: string; tone: Tone; code?: string }

const decl = (name: string, type: number, value: number) => `${typeName(type)} ${name} = ${formatValue(type, value)}`;

export function describe(r: OpResult): Described {
  const where = scopeName(r.depthAfter);
  switch (r.op) {
    case "V":
      if (!r.srcFound)
        return { title: "Undeclared name", detail: `${r.src} is not visible in ${where}, so ${typeName(r.type!)} ${r.name} = ${r.src} cannot be declared.`, tone: "error" };
    // fall through: the source was found and the declaration was made
    case "D": {
      const name = r.name!, d = decl(name, r.type!, r.value!);
      const from = r.op === "V" ? `${r.src} resolved to ${formatValue(r.srcType!, r.srcValue!)}; ` : "";
      if (r.effect === "new") return { title: "Declaration stored", detail: `${from}${d} in ${where}.`, tone: "ok", code: r.status };
      if (r.effect === "shadow") {
        const h = r.hidden!;
        return {
          title: "Declaration stored · shadowing",
          detail: `${d} in ${where} hides ${decl(name, h.type, h.value)} from ${scopeName(h.depth)}. The hidden declaration was saved on the undo stack.`,
          tone: "ok", code: r.status,
        };
      }
      if (r.effect === "redeclared")
        return { title: "Redeclared in the same scope", detail: `${name} already existed in ${where}; its value is now ${formatValue(r.type!, r.value!)}.`, tone: "info", code: r.status };
      if (r.status === "kNoMemory")
        return { title: "Memory limit reached", detail: `${d} was refused: the buffer is full. ${r.changed ? "" : "The table is unchanged (state digest identical before and after)."}`, tone: "error", code: r.status };
      return { title: "Declaration refused", detail: `${d} was refused by the table.`, tone: "error", code: r.status };
    }
    case "L":
      if (r.found) return { title: "Lookup successful", detail: `${r.name} resolves to ${decl(r.name!, r.type!, r.value!)} (declared in ${scopeName(r.depth!)}).`, tone: "ok" };
      return { title: "Name not found", detail: `No visible declaration of ${r.name} in ${where}.`, tone: "warn" };
    case "E":
      if (r.effect === "entered") return { title: "Scope entered", detail: `Now in ${where}. A 2-word scope mark was pushed on the undo stack.`, tone: "ok", code: r.status };
      if (r.status === "kNoMemory") return { title: "Memory limit reached", detail: "No room for a scope mark; the table is unchanged.", tone: "error", code: r.status };
      return { title: "Scope refused", detail: "The table refused to open another scope.", tone: "error", code: r.status };
    case "X": {
      if (r.effect !== "exited") {
        if (r.status === "kNoScope") return { title: "Already at Global scope", detail: "There is no open scope to exit.", tone: "warn", code: r.status };
        return { title: "Exit refused", detail: "The table refused to exit the scope.", tone: "error", code: r.status };
      }
      const parts: string[] = [];
      for (const x of r.restored ?? []) parts.push(`restored ${decl(x.name, x.restored!.type, x.restored!.value)} (${scopeName(x.restored!.depth)})`);
      if (r.removed?.length) parts.push(`removed ${r.removed.map((x) => x.name).join(", ")}`);
      const left = scopeName(r.depthAfter + 1);
      return {
        title: "Scope exited",
        detail: `Left ${left}${parts.length ? ": " + parts.join("; ") : " (it declared nothing)"}. Back in ${where}.`,
        tone: "ok", code: r.status,
      };
    }
  }
}
