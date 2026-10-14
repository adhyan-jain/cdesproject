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

export type LineOp = Op & { line: number };
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

export function compile(src: string): Compiled {
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
  const emit = (op: Op, line: number) => {
    if (ops.length >= MAX_OPS) throw new CodeError(`The program needs more than ${MAX_OPS} table operations; make it shorter.`, line);
    ops.push({ ...op, line });
  };
  const identName = (tok: Tok) => {
    if (tok.k !== "id") throw new CodeError(`Expected a variable name but found ${tok.k === "eof" ? "the end of the code" : `'${tok.t}'`}.`, tok.line);
    if (C_KEYWORDS.has(tok.t) || TYPE_WORDS.has(tok.t)) throw new CodeError(`"${tok.t}" is a keyword and cannot be a variable name.`, tok.line);
    if (tok.t.length > 64) throw new CodeError("Names in this demo are limited to 64 characters.", tok.line);
    return tok.t;
  };
  const checkType = (tok: Tok) => {
    if (UNSUPPORTED_TYPES.has(tok.t)) throw new CodeError(`"${tok.t}" is not supported in this demo; use int, float, char or bool.`, tok.line);
  };

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
      if (prev && operand(prev) && operand(tok) && prev.t !== "sizeof" && prev.t !== "return")
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
      n = Number(ex.map((t) => t.t).join("").replace(/[fFuUlL]+$/, ""));
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
  const declarators = (type: TypeName) => {
    while (true) {
      const nameTok = next();
      const name = identName(nameTok);
      if (is("[")) throw new CodeError("Arrays are not supported in this demo.", nameTok.line);
      if (is("=")) {
        next();
        const init = collect([",", ";"]);
        if (init.length === 1 && init[0].k === "id" && !["true", "false"].includes(init[0].t)) {
          const before = ops.length;
          lookups(init);                                   // checks it is a usable name
          ops.length = before;                             // the engine looks it up as part of declareFrom
          emit({ op: "declareFrom", name, type: TYPES.indexOf(type), src: init[0].t }, nameTok.line);
        } else {
          const v = literal(type, init);
          if (v === null) {
            // A general expression is not evaluated: its names are looked up, the value stored is 0.
            lookups(init);
            emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line);
          } else {
            if (type === "int" && (v > 2147483647 || v < -2147483648)) throw new CodeError("An int must fit in 32 bits.", nameTok.line);
            emit({ op: "declare", name, type: TYPES.indexOf(type), value: v }, nameTok.line);
          }
        }
      } else {
        emit({ op: "declare", name, type: TYPES.indexOf(type), value: 0 }, nameTok.line);
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
    if (tok.k === "id" && TYPE_WORDS.has(tok.t)) {
      next();
      const type = tok.t as TypeName | "void";
      // function definition or prototype?
      if (peek().k === "id" && is("(", 1)) {
        const nameTok = next();
        const name = identName(nameTok);
        if (depth > 0) throw new CodeError("Functions can only be defined at the top level.", nameTok.line);
        emit({ op: "declare", name, type: type === "void" ? 0 : TYPES.indexOf(type), value: 0 }, nameTok.line);
        expect("(");
        const params: { name: string; type: TypeName; line: number }[] = [];
        if (peek().t === "void" && is(")", 1)) next();
        while (!is(")")) {
          const pt = next();
          checkType(pt);
          if (pt.k !== "id" || !TYPES.includes(pt.t as TypeName)) throw new CodeError("Parameters must be int, float, char or bool.", pt.line);
          params.push({ type: pt.t as TypeName, name: identName(next()), line: pt.line });
          if (is(",")) next(); else if (!is(")")) throw new CodeError("Expected ',' or ')' in the parameter list.", peek().line);
        }
        expect(")");
        if (is(";")) { next(); return; }                    // prototype: only the name is declared
        const open = expect("{", "to start the function body");
        emit({ op: "enter" }, open.line);
        depth++;
        for (const prm of params) emit({ op: "declare", name: prm.name, type: TYPES.indexOf(prm.type), value: 0 }, prm.line);
        block(open.line, true);
        return;
      }
      if (type === "void") throw new CodeError("A variable cannot have type void.", tok.line);
      declarators(type);
      return;
    }
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
      if (peek().k === "id" && TYPE_WORDS.has(peek().t)) {
        const tt = next();
        if (tt.t === "void") throw new CodeError("A variable cannot have type void.", tt.line);
        declarators(tt.t as TypeName);
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
