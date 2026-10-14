// STRATA stores a 32-bit value and an 8-bit type tag per declaration. The demo uses the
// tag for a C type and encodes each value into the 32 bits: int as is, float as its
// IEEE-754 bit pattern, char as its code, bool as 0/1.

export const TYPES = ["int", "float", "char", "bool"] as const;
export type TypeName = (typeof TYPES)[number];

const view = new DataView(new ArrayBuffer(4));

export function typeName(tag: number): string {
  return TYPES[tag] ?? `tag ${tag}`;
}

export function encodeValue(type: TypeName, raw: string): { value: number } | { error: string } {
  const s = raw.trim();
  switch (type) {
    case "int": {
      if (!/^-?\d+$/.test(s)) return { error: "An int value must be a whole number, e.g. 42." };
      const n = Number(s);
      if (n < -2147483648 || n > 2147483647) return { error: "An int must fit in 32 bits." };
      return { value: n };
    }
    case "float": {
      const n = Number(s);
      if (s === "" || !Number.isFinite(n)) return { error: "A float value must be a number, e.g. 3.14." };
      view.setFloat32(0, n);
      return { value: view.getInt32(0) };
    }
    case "char": {
      if (s.length !== 1 || s.charCodeAt(0) < 32 || s.charCodeAt(0) > 126) return { error: "A char value must be one printable character, e.g. x." };
      return { value: s.charCodeAt(0) };
    }
    case "bool": {
      if (s !== "true" && s !== "false") return { error: "A bool value must be true or false." };
      return { value: s === "true" ? 1 : 0 };
    }
  }
}

export function formatValue(tag: number, value: number): string {
  switch (tag) {
    case 0: return String(value);
    case 1: {
      view.setInt32(0, value);
      return String(Number(view.getFloat32(0).toPrecision(7)));
    }
    case 2: return `'${String.fromCharCode(value)}'`;
    case 3: return value ? "true" : "false";
    default: return String(value);
  }
}

export const scopeName = (depth: number) => (depth === 0 ? "Global" : `Scope ${depth}`);

export const NAME_RE = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/;
export const C_KEYWORDS = new Set([
  "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for",
  "goto", "if", "inline", "int", "long", "register", "restrict", "return", "short", "signed", "sizeof", "static", "struct",
  "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "bool", "true", "false",
]);

export function nameError(name: string): string | null {
  if (!name) return "Enter a variable name.";
  if (name.length > 64) return "Names in this demo are limited to 64 characters.";
  if (!NAME_RE.test(name)) return "A C identifier starts with a letter or _ and contains only letters, digits and _.";
  if (C_KEYWORDS.has(name)) return `"${name}" is a C keyword, not a variable name.`;
  return null;
}
