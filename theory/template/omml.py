"""A small LaTeX-to-OMML converter: the subset of math the manuscript's equations use.

omml(latex) returns an <m:oMath> element (a string) that Word and LibreOffice render as a native equation.
Supported: letters, digits, Greek, \\frac, ^ and _ (also together), \\sum and \\prod with limits, \\left..\\right
delimiters, \\mathrm, \\mathbb, \\text, relations and operators, [ ] ( ) braces for grouping.
"""
import re
from xml.sax.saxutils import escape

GREEK = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "varepsilon": "ε", "epsilon": "ε", "lambda": "λ", "mu": "μ",
         "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "Phi": "Φ", "Pi": "Π", "Sigma": "Σ", "Delta": "Δ",
         "Lambda": "Λ", "theta": "θ", "omega": "ω", "Omega": "Ω", "kappa": "κ", "eta": "η", "zeta": "ζ"}
SYMBOLS = {"le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "in": "∈", "cdot": "⋅", "times": "×", "ldots": "…",
           "dots": "…", "cdots": "⋯", "to": "→", "infty": "∞", "triangleleft": "◁", "lhd": "◁", "Leftrightarrow": "⇔",
           "Rightarrow": "⇒", "pm": "±", "mid": "∣", "approx": "≈", "sim": "∼", "subseteq": "⊆", "forall": "∀",
           "exists": "∃", "emptyset": "∅", "bmod": "mod", "equiv": "≡", "log": "log", "ln": "ln", "max": "max", "min": "min",
           "exp": "exp", "lim": "lim"}
UPRIGHT_FUNCS = {"log", "ln", "max", "min", "exp", "lim", "bmod"}
BB = {"P": "ℙ", "E": "𝔼", "R": "ℝ", "N": "ℕ", "Z": "ℤ"}
OPS = set("+-=<>,;:!()[]|/")
STOP_BODY = {"=", "≤", "≥", "∈", "⇔", "⇒", ",", ";", "≠", "≈"}


def run(text, upright=False):
    if upright and len(text) > 1 and text.isalpha(): sty = '<m:rPr><m:nor/><m:sty m:val="p"/></m:rPr>'      # a word: normal text
    elif upright: sty = '<m:rPr><m:sty m:val="p"/></m:rPr>'
    else: sty = ""
    return '<m:r>%s<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">%s</m:t></m:r>' % (sty, escape(text))


class P:
    def __init__(self, s):
        self.t = self.tokens(s); self.i = 0

    @staticmethod
    def tokens(s):
        out, i = [], 0
        while i < len(s):
            c = s[i]
            if c == "\\":
                m = re.match(r"\\([A-Za-z]+|.)", s[i:])
                name = m.group(1)
                if name in ("text", "mathrm", "operatorname") and s[i + len(m.group(0)):i + len(m.group(0)) + 1] == "{":
                    j = s.index("}", i + len(m.group(0)))
                    out.append(("RAWTEXT", s[i + len(m.group(0)) + 1:j])); i = j + 1
                    continue
                out.append("\\" + name); i += len(m.group(0))
            elif c.isspace():
                i += 1
            else:
                out.append(c); i += 1
        return out

    def peek(self): return self.t[self.i] if self.i < len(self.t) else None
    def next(self): tok = self.peek(); self.i += 1; return tok

    def group(self):
        """One argument: a {...} group or a single token."""
        if self.peek() == "{":
            self.next(); xml = self.seq(until="}"); self.next(); return xml
        return self.atom_with_scripts()

    def seq(self, until=None, stop_rel=False, depth_ok=True):
        parts = []
        while self.peek() is not None and self.peek() != until:
            if stop_rel and self.peek() in STOP_BODY | {"\\le", "\\ge", "\\in", "\\Leftrightarrow", "\\to", "+", "-", "\\right", "}", ")"}: break
            parts.append(self.atom_with_scripts())
        return "".join(parts)

    def atom_with_scripts(self):
        base, sub, sup = self.atom(), None, None
        while self.peek() in ("^", "_"):
            op = self.next(); arg = self.group()
            if op == "^": sup = arg
            else: sub = arg
        if sub is not None and sup is not None:
            return "<m:sSubSup><m:e>%s</m:e><m:sub>%s</m:sub><m:sup>%s</m:sup></m:sSubSup>" % (base, sub, sup)
        if sup is not None:
            return "<m:sSup><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>" % (base, sup)
        if sub is not None:
            return "<m:sSub><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>" % (base, sub)
        return base

    def atom(self):
        tok = self.next()
        if isinstance(tok, tuple):
            return '<m:r><m:rPr><m:nor/><m:sty m:val="p"/></m:rPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">%s</m:t></m:r>' % escape(tok[1])
        if tok == "{":
            xml = self.seq(until="}"); self.next(); return xml
        if tok.startswith("\\"):
            name = tok[1:]
            if name == "frac":
                a, b = self.group(), self.group()
                return "<m:f><m:num>%s</m:num><m:den>%s</m:den></m:f>" % (a, b)
            if name in ("sum", "prod"):
                sub = sup = ""
                while self.peek() in ("^", "_"):
                    op = self.next(); arg = self.group()
                    if op == "^": sup = arg
                    else: sub = arg
                body = self.seq(stop_rel=True)
                chr_ = "∑" if name == "sum" else "∏"
                return ('<m:nary><m:naryPr><m:chr m:val="%s"/><m:limLoc m:val="undOvr"/>%s%s</m:naryPr><m:sub>%s</m:sub><m:sup>%s</m:sup><m:e>%s</m:e></m:nary>'
                        % (chr_, "" if sub else '<m:subHide m:val="1"/>', "" if sup else '<m:supHide m:val="1"/>', sub, sup, body))
            if name == "left":
                beg = self.next().lstrip("\\"); body = self.seq(until="\\right"); self.next(); end = self.next().lstrip("\\")
                beg = {"{": "{", "lbrace": "{", ".": ""}.get(beg, beg); end = {"}": "}", "rbrace": "}", ".": ""}.get(end, end)
                return '<m:d><m:dPr><m:begChr m:val="%s"/><m:endChr m:val="%s"/></m:dPr><m:e>%s</m:e></m:d>' % (beg, end, body)
            if name == "mathrm" or name == "text" or name == "operatorname":
                self.next() if self.peek() == "{" else None
                txt = []
                while self.peek() not in ("}", None): txt.append(self.next())
                self.next()
                return run("".join(x if not x.startswith("\\") else SYMBOLS.get(x[1:], x[1:]) for x in txt), upright=True)
            if name == "mathbb":
                self.next(); ch = self.next(); self.next(); return run(BB.get(ch, ch), upright=True)
            if name in GREEK: return run(GREEK[name])
            if name in UPRIGHT_FUNCS: return run(SYMBOLS[name], upright=True)
            if name in SYMBOLS: return run(SYMBOLS[name], upright=True)
            if name in (",", ";", ":", " ", "!", "quad", "qquad"): return run(" ", upright=True)
            if name in ("{", "}", "|"): return run(name, upright=True)
            raise ValueError("unsupported LaTeX: " + tok)
        if tok.isdigit() or tok in OPS or tok in ".":
            # collect a number
            if tok.isdigit():
                while self.peek() is not None and self.peek().isdigit(): tok += self.next()
            return run(tok, upright=True)
        if tok == "'": return run("′", upright=True)
        return run(tok)  # a letter: italic


def omml(latex):
    p = P(latex)
    xml = p.seq()
    if p.peek() is not None: raise ValueError("unparsed tail in: " + latex)
    return "<m:oMath>%s</m:oMath>" % xml


if __name__ == "__main__":
    for s in [r"R_m(n,L)=\frac{k}{m}\sum_{g=L+1}^{n+1}(g-L)\,\pi_g",
              r"\mathrm{orph}(x)=Y_c-1,\quad Y_c=(Y_{c-1}-1)^{+}+A_c",
              r"\mathbb{P}(W=0)=\frac{[z^m]\left(\sum_{g\le L}B(g)z^g\right)^{k}}{[z^m]\left(\sum_{g\ge1}B(g)z^g\right)^{k}}"]:
        print(omml(s)[:200], "...")
