// A small C subset, translated into the calls a compiler front end makes on its symbol table:
//
//   int x = 5;   float y = 2.5;   char c = 'a';   bool b = true;   int z;   int a = 1, b = 2;
//   int y = x;                       declare from a variable (x is looked up first)
//   { ... }                          enter_scope / exit_scope
//   int f(int a, int b) { ... }      declare f, then one scope holding the parameters and body
//   if (...) / while (...) / for (int i = 0; ...; ...)   for opens its own scope, as in C99
//   x;  x = y + 1;  return x;  printf("%d", x);           every identifier used is looked up
//
// Nothing is evaluated here: the program only becomes a list of operations, which the C++
// engine runs on strata::Table. Each operation remembers the source line it came from.
import type { Op } from "./engine";
import { C_KEYWORDS, encodeValue, TYPES, type TypeName } from "./values";

export type LineOp = Op & { line: number; ctype?: string; kind?: "var" | "param" | "function" };
// relaxed: accept the wider C that people paste (qualifiers, long/short/unsigned, double, pointers, arrays, do/switch).
// Those types are stored under the nearest of the four tags; ctype keeps the type as written.
export interface CompileOptions { relaxed?: boolean }
export interface Compiled { ops: LineOp[] }
export class CodeError extends Error {
  constructor(message: string, readonly line: number) { super(message); }
}

type Tok = { k: "id" | "num" | "char" | "str" | "p" | "eof"; t: string; line: number };

const LIB = new Set(["printf", "scanf", "puts", "putchar", "getchar", "malloc", "free", "strlen", "strcpy", "memcpy", "memset", "exit", "abs", "sizeof"]);
const UNSUPPORTED_TYPES = new Set(["double", "long", "short", "unsigned", "signed", "struct", "union", "enum", "typedef", "const", "static", "extern", "auto", "register", "volatile"]);
const MAX_OPS = 400;

function lex(src: string): Tok[] {
  const out: Tok[] = [];
  let i = 0, line = 1;
  const at = (k: number) => src[i + k] ?? "";
  while (i < src.length) {
    const c = src[i];
    if (c === "\n") { line++; i++; continue; }
    if (/\s/.test(c)) { i++; continue; }
    if (c === "/" && at(1) === "/") { while (i < src.length && src[i] !== "\n") i++; continue; }
    if (c === "/" && at(1) === "*") {
      const start = line;
      i += 2;
      while (i < src.length && !(src[i] === "*" && at(1) === "/")) { if (src[i] === "\n") line++; i++; }
      if (i >= src.length) throw new CodeError("Comment is never closed with */.", start);
      i += 2;
      continue;
    }
    if (c === "#") { while (i < src.length && src[i] !== "\n") i++; continue; }   // #include etc.
    if (/[A-Za-z_]/.test(c)) {
      let j = i + 1;
      while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j++;
      out.push({ k: "id", t: src.slice(i, j), line });
      i = j;
      continue;
    }
    if (c === "0" && /[xX]/.test(at(1))) {                // hexadecimal
      let j = i + 2;
      while (j < src.length && /[0-9a-fA-FuUlL]/.test(src[j])) j++;
      out.push({ k: "num", t: src.slice(i, j), line });
      i = j;
      continue;
    }
    if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(at(1)))) {
      let j = i;
      while (j < src.length && /[0-9.eE]/.test(src[j])) j++;
      while (j < src.length && /[fFuUlL]/.test(src[j])) j++;
      out.push({ k: "num", t: src.slice(i, j), line });
      i = j;
      continue;
    }
    if (c === "'") {
      let j = i + 1;
      if (src[j] === "\\") j++;
      j++;
      if (src[j] !== "'") throw new CodeError("A char literal holds one character, e.g. 'a'.", line);
      out.push({ k: "char", t: src.slice(i, j + 1), line });
      i = j + 1;
      continue;
    }
    if (c === '"') {
      let j = i + 1;
      while (j < src.length && src[j] !== '"' && src[j] !== "\n") j += src[j] === "\\" ? 2 : 1;
      if (src[j] !== '"') throw new CodeError("String is never closed with \".", line);
      out.push({ k: "str", t: src.slice(i, j + 1), line });
      i = j + 1;
      continue;
    }
    const two = src.slice(i, i + 2);
    if (["==", "!=", "<=", ">=", "&&", "||", "++", "--", "+=", "-=", "*=", "/=", "->", "<<", ">>"].includes(two)) {
      out.push({ k: "p", t: two, line });
      i += 2;
      continue;
    }
    if ("{}()[];,=+-*/%<>!&|^~?:.".includes(c)) { out.push({ k: "p", t: c, line }); i++; continue; }
    throw new CodeError(`Unexpected character '${c}'.`, line);
  }
  out.push({ k: "eof", t: "", line });
  return out;
}

const TYPE_WORDS = new Set<string>([...TYPES, "void"]);

const QUALIFIERS = new Set(["const", "static", "extern", "volatile", "register", "auto", "inline", "restrict"]);
const INT_WORDS = new Set(["long", "short", "unsigned", "signed"]);

export function compile(src: string, opts: CompileOptions = {}): Compiled {
  const relaxed = !!opts.relaxed;
  const toks = lex(src);
  let p = 0;
  const ops: LineOp[] = [];
  let depth = 0;

  const peek = (k = 0) => toks[Math.min(p + k, toks.length - 1)];
  const next = () => toks[p++];
  const is = (t: string, k = 0) => peek(k).k === "p" && peek(k).t === t;
  const expect = (t: string, what?: string) => {
    const tok = next();
    if (tok.k !== "p" || tok.t !== t) throw new CodeError(`Expected '${t}'${what ? " " + what : ""} but found ${tok.k === "eof" ? "the end of the code" : `'${tok.t}'`}.`, tok.line);
    return tok;
  };
  const emit = (op: Op, line: number, extra?: { ctype?: string; kind?: LineOp["kind"] }) => {
    if (ops.length >= MAX_OPS) throw new CodeError(`The program needs more than ${MAX_OPS} table operations; make it shorter.`, line);
    ops.push({ ...op, line, ...(relaxed ? extra : undefined) });
  };
  const identName = (tok: Tok) => {
    if (tok.k !== "id") throw new CodeError(`Expected a variable name but found ${tok.k === "eof" ? "the end of the code" : `'${tok.t}'`}.`, tok.line);
    if (C_KEYWORDS.has(tok.t) || TYPE_WORDS.has(tok.t)) throw new CodeError(`"${tok.t}" is a keyword and cannot be a variable name.`, tok.line);
    if (tok.t.length > 64) throw new CodeError("Names in this demo are limited to 64 characters.", tok.line);
    return tok.t;
  };
  const checkType = (tok: Tok) => {
    if (relaxed && (QUALIFIERS.has(tok.t) || INT_WORDS.has(tok.t) || tok.t === "double")) return;
    if (relaxed && ["struct", "union", "enum", "typedef"].includes(tok.t))
      throw new CodeError(`"${tok.t}" is not analysed yet. The analyser understands variables of the basic C types (int, char, float, double, long, unsigned, ... and pointers or arrays of them).`, tok.line);
    if (UNSUPPORTED_TYPES.has(tok.t)) throw new CodeError(`"${tok.t}" is not supported in this demo; use int, float, char or bool.`, tok.line);
  };
  const isTypeWord = (t: string) => TYPE_WORDS.has(t) || (relaxed && (QUALIFIERS.has(t) || INT_WORDS.has(t) || t === "double"));
  // Is the token the start of a type? Strict: one of the four types or void. Relaxed: also qualifiers, long, double, ...
  const startsType = (tok: Tok) => tok.k === "id" && isTypeWord(tok.t);
  // Consumes a type and returns its tag and the text as written (relaxed: several words).
  const typeSpec = (): { tag: TypeName | "void"; text: string } => {
    const first = next();
    if (!relaxed) return { tag: first.t as TypeName | "void", text: first.t };
    const words = [first.t];
    while (peek().k === "id" && isTypeWord(peek().t)) words.push(next().t);
    const base = words.filter((w) => !QUALIFIERS.has(w));
    if (base.length === 0) throw new CodeError(`"${words.join(" ")}" needs a type after it, e.g. "${words.join(" ")} int".`, first.line);
    const tag: TypeName | "void" =
      base.includes("void") ? "void" : base.includes("float") || base.includes("double") ? "float" :
      base.includes("char") ? "char" : base.includes("bool") ? "bool" : "int";
    return { tag, text: words.join(" ") };
  };
  // Relaxed only: the stars of a pointer declarator.
  const stars = () => { let n = 0; while (relaxed && is("*")) { next(); n++; } return n; };
  const typeText = (base: string, ptr: number, arr: number) => base + (ptr ? " " + "*".repeat(ptr) : "") + "[]".repeat(arr);

  // Tokens of an expression, up to the first of `stops` outside brackets (not consumed).
  const collect = (stops: string[]) => {
    const from = p;
    let nest = 0;
    const operand = (t: Tok) => t.k === "id" || t.k === "num" || t.k === "char" || t.k === "str";
    while (true) {
      const tok = peek();
      if (tok.k === "eof") throw new CodeError("The statement never ends; is a ';' or ')' missing?", tok.line);
      const prev = p > from ? toks[p - 1] : null;
      // Two operands side by side ("1 int", "x y") mean a missing ';' (a cast "(int) x" is fine).
      if (prev && operand(prev) && operand(tok) && prev.t !== "sizeof" && prev.t !== "return" && !(relaxed && isTypeWord(prev.t) && isTypeWord(tok.t)))
        throw new CodeError(`Missing ';' after '${prev.t}'.`, prev.line);
      if (tok.k === "p") {
        if (nest === 0 && stops.includes(tok.t)) return toks.slice(from, p);
        if (tok.t === "(" || tok.t === "[") nest++;
        if (tok.t === ")" || tok.t === "]") { if (nest === 0) throw new CodeError("Unbalanced ')'.", tok.line); nest--; }
        if (tok.t === "{" || tok.t === "}") throw new CodeError(`Unexpected '${tok.t}' inside an expression; is a ';' missing?`, tok.line);
      }
      next();
    }
  };
  // Every identifier in an expression that is not a keyword, a library call or a member name
  // after . or -> is a use of a name, so the compiler looks it up.
  const lookups = (ex: Tok[]) => {
    ex.forEach((tok, i) => {
      if (tok.k !== "id") return;
      const prev = ex[i - 1];
      if (prev && prev.k === "p" && (prev.t === "." || prev.t === "->")) return;
      if (["true", "false", "NULL", "sizeof"].includes(tok.t)) return;
      if (TYPE_WORDS.has(tok.t) || UNSUPPORTED_TYPES.has(tok.t)) return;   // casts
      if (C_KEYWORDS.has(tok.t)) throw new CodeError(`"${tok.t}" cannot be used inside an expression.`, tok.line);
      if (LIB.has(tok.t) && ex[i + 1]?.t === "(") return;
      emit({ op: "lookup", name: tok.t }, tok.line);
    });
  };
  const expr = (stops: string[]) => lookups(collect(stops));
  // Relaxed only: [size] suffixes of an array; names used in a size are looked up.
  const arraySuffix = () => {
    let n = 0;
    while (relaxed && is("[")) { next(); if (!is("]")) expr(["]"]); expect("]"); n++; }
    return n;
  };
  // Relaxed only: a brace initialiser { 1, x, { 2, y } }; every name in it is looked up.
  const braceInit = () => {
    const open = expect("{");
    let nest = 1;
    const inner: Tok[] = [];
    while (nest > 0) {
      const t = next();
      if (t.k === "eof") throw new CodeError("This '{' is never closed with '}'.", open.line);
      if (t.k === "p" && t.t === "{") nest++;
      else if (t.k === "p" && t.t === "}") nest--;
      else inner.push(t);
    }
    lookups(inner);
  };

  // A literal initialiser converted to the declared type, or null when it is not a literal.
  const literal = (type: TypeName, ex: Tok[]): number | null => {
    let n: number;
    if (ex.length === 1 && ex[0].k === "char") {
      const body = ex[0].t.slice(1, -1);
      const ch = body === "\\n" ? "\n" : body === "\\0" ? "\0" : body.replace(/^\\/, "");
      n = ch.charCodeAt(0);
    } else if (ex.length === 1 && (ex[0].t === "true" || ex[0].t === "false")) {
      n = ex[0].t === "true" ? 1 : 0;
    } else if ((ex.length === 1 && ex[0].k === "num") || (ex.length === 2 && ex[0].t === "-" && ex[1].k === "num")) {
      const raw = ex.map((t) => t.t).join("");
      n = Number(/0[xX]/.test(raw) ? raw.replace(/[uUlL]+$/, "") : raw.replace(/[fFuUlL]+$/, ""));
      if (!Number.isFinite(n)) return null;
    } else {
      return null;
    }
    switch (type) {
      case "int": return Math.trunc(n);
      case "float": return (encodeValue("float", String(n)) as { value: number }).value;
      case "char": return Math.max(0, Math.min(127, Math.trunc(n)));
      case "bool": return n !== 0 ? 1 : 0;
    }
  };

  // int a = 1, b = c, d;
  const declarators = (type: TypeName, text: string = type) => {
    while (true) {
      const ptr = stars();
      const nameTok = next();
      const name = identName(nameTok);
      if (is("[") && !relaxed) throw new CodeError("Arrays are not supported in this demo.", nameTok.line);
      const arr = arraySuffix();
      const extra = { ctype: typeText(text, ptr, arr), kind: "var" as const };
      if (relaxed && is("=") && is("{", 1)) {
        next();
        braceInit();
        emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line, extra);
      } else if ((ptr || arr) && is("=")) {
        next();
        lookups(collect([",", ";"]));                      // a pointer is not stored as a literal: only its names are looked up
        emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line, extra);
      } else if (is("=")) {
        next();
        const init = collect([",", ";"]);
        if (init.length === 1 && init[0].k === "id" && !["true", "false"].includes(init[0].t)) {
          const before = ops.length;
          lookups(init);                                   // checks it is a usable name
          ops.length = before;                             // the engine looks it up as part of declareFrom
          emit({ op: "declareFrom", name, type: TYPES.indexOf(type), src: init[0].t }, nameTok.line, extra);
        } else {
          const v = literal(type, init);
          if (v === null) {
            // A general expression is not evaluated: its names are looked up, the value stored is 0.
            lookups(init);
            emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line, extra);
          } else {
            if (type === "int" && (v > 2147483647 || v < -2147483648)) throw new CodeError("An int must fit in 32 bits.", nameTok.line);
            emit({ op: "declare", name, type: TYPES.indexOf(type), value: v }, nameTok.line, extra);
          }
        }
      } else {
        emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line, extra);
      }
      if (is(",")) { next(); continue; }
      expect(";", "after the declaration");
      return;
    }
  };
  const block = (openLine: number, alreadyOpen = false) => {
    if (!alreadyOpen) { emit({ op: "enter" }, openLine); depth++; }
    while (!is("}")) {
      if (peek().k === "eof") throw new CodeError("This '{' is never closed with '}'.", openLine);
      statement();
    }
    const close = next();
    emit({ op: "exit" }, close.line);
    depth--;
  };

  const statement = (): void => {
    const tok = peek();
    if (tok.k === "p" && tok.t === "{") { next(); block(tok.line); return; }
    if (tok.k === "p" && tok.t === "}") throw new CodeError("This '}' has no matching '{'.", tok.line);
    if (tok.k === "p" && tok.t === ";") { next(); return; }
    if (tok.k === "id") checkType(tok);
    if (startsType(tok)) {
      const spec = typeSpec();
      const type = spec.tag;
      // function definition or prototype? (relaxed: it may return a pointer)
      let fptr = 0;
      while (relaxed && is("*", fptr)) fptr++;
      if (peek(fptr).k === "id" && is("(", fptr + 1)) {
        stars();
        const nameTok = next();
        const name = identName(nameTok);
        if (depth > 0) throw new CodeError("Functions can only be defined at the top level.", nameTok.line);
        emit({ op: "declare", name, type: type === "void" ? 0 : TYPES.indexOf(type), value: 0 }, nameTok.line, { ctype: typeText(spec.text, fptr, 0), kind: "function" });
        expect("(");
        const params: { name: string; type: TypeName; line: number; ctype: string }[] = [];
        if (peek().t === "void" && is(")", 1)) next();
        while (!is(")")) {
          const pt = peek();
          checkType(pt);
          if (relaxed ? !startsType(pt) : pt.k !== "id" || !TYPES.includes(pt.t as TypeName))
            throw new CodeError(relaxed ? `Expected a parameter type but found '${pt.t}'.` : "Parameters must be int, float, char or bool.", pt.line);
          const ps = typeSpec();
          const pp = stars();
          if (ps.tag === "void" && !pp) throw new CodeError("A parameter cannot have type void.", pt.line);
          const pname = identName(next());
          const pa = arraySuffix();
          params.push({ type: ps.tag === "void" ? "int" : ps.tag, name: pname, line: pt.line, ctype: typeText(ps.text, pp, pa) });
          if (is(",")) next(); else if (!is(")")) throw new CodeError("Expected ',' or ')' in the parameter list.", peek().line);
        }
        expect(")");
        if (is(";")) { next(); return; }                    // prototype: only the name is declared
        const open = expect("{", "to start the function body");
        emit({ op: "enter" }, open.line);
        depth++;
        for (const prm of params) emit({ op: "declare", name: prm.name, type: TYPES.indexOf(prm.type), value: 0 }, prm.line, { ctype: prm.ctype, kind: "param" });
        block(open.line, true);
        return;
      }
      if (type === "void" && !is("*")) throw new CodeError("A variable cannot have type void.", tok.line);
      declarators(type === "void" ? "int" : type, spec.text);
      return;
    }
    if (relaxed && tok.k === "id" && tok.t === "do") {
      next();
      statement();
      if (peek().t !== "while") throw new CodeError("Expected 'while' after the body of do.", peek().line);
      next(); expect("(", "after while"); expr([")"]); expect(")"); expect(";", "after do ... while (...)");
      return;
    }
    if (relaxed && tok.k === "id" && tok.t === "switch") {
      next(); expect("(", "after switch"); expr([")"]); expect(")"); statement();
      return;
    }
    if (relaxed && tok.k === "id" && (tok.t === "case" || tok.t === "default")) {
      next();
      if (tok.t === "case") expr([":"]);
      expect(":", `after ${tok.t}`);
      return;
    }
    if (relaxed && tok.k === "id" && tok.t === "goto") { next(); identName(next()); expect(";"); return; }
    if (relaxed && tok.k === "id" && is(":", 1) && !C_KEYWORDS.has(tok.t)) { next(); next(); return; }   // a label
    if (tok.k === "id" && (tok.t === "if" || tok.t === "while")) {
      next();
      expect("(", `after ${tok.t}`);
      expr([")"]);
      expect(")");
      statement();
      if (tok.t === "if" && peek().t === "else") { next(); statement(); }
      return;
    }
    if (tok.k === "id" && tok.t === "for") {
      next();
      expect("(", "after for");
      emit({ op: "enter" }, tok.line);                     // the loop variable has its own scope
      depth++;
      if (startsType(peek())) {
        const tt = peek();
        checkType(tt);
        const fs = typeSpec();
        if (fs.tag === "void") throw new CodeError("A variable cannot have type void.", tt.line);
        declarators(fs.tag, fs.text);
      } else { expr([";"]); expect(";"); }
      expr([";"]); expect(";");
      expr([")"]); expect(")");
      statement();
      emit({ op: "exit" }, toks[p - 1].line);
      depth--;
      return;
    }
    if (tok.k === "id" && (tok.t === "return" || tok.t === "break" || tok.t === "continue")) {
      next();
      expr([";"]);
      expect(";");
      return;
    }
    if (tok.k === "id" && C_KEYWORDS.has(tok.t) && !["true", "false"].includes(tok.t))
      throw new CodeError(`"${tok.t}" is not supported in this demo.`, tok.line);
    expr([";"]);
    expect(";", "at the end of the statement");
  };

  while (peek().k !== "eof") statement();
  return { ops };
}

export const EXAMPLES: { title: string; code: string }[] = [
  {
    title: "Shadowing",
    code: `int x = 1;
{
    int x = 2;      // hides the outer x
    printf("%d", x); // uses the inner x
}
x;                  // the outer x is back
`,
  },
  {
    title: "Function with nested scopes",
    code: `int total = 0;

int add(int a, int b) {
    int total = a;  // shadows the global total
    {
        int b = 7;  // shadows the parameter b
        total = total + b;
    }
    return total + b;
}

total;
`,
  },
  {
    title: "Loop variable scope",
    code: `int sum = 0;
for (int i = 0; i < 10; i++) {
    int square = i;
    sum = sum + square;
}
sum;
i;        // not visible here: the loop's scope has ended
`,
  },
  {
    title: "All four types",
    code: `int count = 42;
float rate = 2.5;
char grade = 'A';
bool ready = true;
int copy = rate;    // initialised from a variable: rate is looked up first
`,
  },
  {
    title: "Undeclared name",
    code: `int a = 5;
{
    int b = a;
}
int c = b;          // b's scope has ended: lookup fails
`,
  },
  {
    title: "Fill a 256-byte buffer",
    code: `// Choose a 256 B buffer, then run: the sixth declaration does not fit.
int very_long_variable_name_1 = 1;
int very_long_variable_name_2 = 2;
int very_long_variable_name_3 = 3;
int very_long_variable_name_4 = 4;
int very_long_variable_name_5 = 5;
int very_long_variable_name_6 = 6;
very_long_variable_name_1;
`,
  },
];
