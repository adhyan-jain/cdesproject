"""Build the manuscript in the institution's Word template and render it to PDF.

Usage:  python3 theory/template/build_docx.py ["/path/to/Paper Template-2.docx"]

The template's package (styles, numbering, footer with page numbers, settings, page size and margins) is kept as is; only
the body of word/document.xml is replaced, and the figures are added as media.  Text comes from content.py, figures from
build/figs (make_figures.py), equations are native Word equations (omml.py).  The PDF is produced with LibreOffice.
"""
import os, re, struct, subprocess, sys, zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from omml import omml

TEMPLATE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/Paper Template-2.docx")
FIGS = os.path.join(HERE, "build", "figs")
OUT = os.path.join(HERE, "build", "STRATA_Theory_Manuscript.docx")

TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'


def find_figure(name):
    for base in (FIGS, os.path.join(HERE, "figures")):
        p = os.path.join(base, name)
        if os.path.exists(p): return p
    raise FileNotFoundError(name)


class Doc:
    def __init__(self):
        self.body, self.media = [], []
        self.fig = self.tab = self.eq = self.alg = 0
        self.cite_order = []                       # keys in order of first citation
        self.cite_numbers = {}

    # ---- inline markup: {b:..} {i:..} {bi:..} {code:..} {sub:..} {sup:..} {cite:k1,k2} ---------------------------------
    def cite(self, keys):
        nums = []
        for k in keys.split(","):
            k = k.strip()
            if k not in self.cite_numbers:
                self.cite_order.append(k); self.cite_numbers[k] = len(self.cite_order)
            nums.append(self.cite_numbers[k])
        nums.sort()
        return "[" + ", ".join(str(n) for n in nums) + "]"

    def r(self, text, b=False, i=False, sz=24, font=TNR, vert=None, color=None, hl=None):
        pr = font + ("<w:b/>" if b else "") + ("<w:i/>" if i else "") + ("<w:color w:val=\"%s\"/>" % color if color else "")
        pr += "<w:sz w:val=\"%d\"/><w:szCs w:val=\"%d\"/>" % (sz, sz) + ("<w:highlight w:val=\"%s\"/>" % hl if hl else "")
        pr += ("<w:vertAlign w:val=\"%s\"/>" % vert if vert else "") + '<w:lang w:val="en-US"/>'
        return '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (pr, escape(text))

    def runs(self, markup, sz=24, b=False, i=False):
        out, pos = [], 0
        for m in re.finditer(r"\{(bi|b|i|code|sub|sup|cite|hl):([^{}]*)\}", markup):
            if m.start() > pos: out.append(self.r(markup[pos:m.start()], b=b, i=i, sz=sz))
            tag, txt = m.groups()
            if tag == "b": out.append(self.r(txt, b=True, i=i, sz=sz))
            elif tag == "i": out.append(self.r(txt, b=b, i=True, sz=sz))
            elif tag == "bi": out.append(self.r(txt, b=True, i=True, sz=sz))
            elif tag == "code": out.append(self.r(txt, b=b, sz=sz - 2, font='<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'))
            elif tag == "sub": out.append(self.r(txt, b=b, i=True, sz=sz, vert="subscript"))
            elif tag == "sup": out.append(self.r(txt, b=b, i=i, sz=sz, vert="superscript"))
            elif tag == "hl": out.append(self.r(txt, b=b, i=i, sz=sz, hl="yellow"))
            elif tag == "cite": out.append(self.r(self.cite(txt), b=b, i=i, sz=sz))
            pos = m.end()
        if pos < len(markup): out.append(self.r(markup[pos:], b=b, i=i, sz=sz))
        return "".join(out)

    # ---- block elements ---------------------------------------------------------------------------------------------
    def ppr(self, jc=None, after=0, before=0, line=360, keep_next=False, left=None, first=None, style=None, num=None, keep_lines=False):
        s = "<w:pPr>" + ('<w:pStyle w:val="%s"/>' % style if style else "") + ("<w:keepNext/>" if keep_next else "") + ("<w:keepLines/>" if keep_lines else "")
        if num is not None: s += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % num
        s += '<w:spacing w:before="%d" w:after="%d" w:line="%d" w:lineRule="auto"/>' % (before, after, line)
        if left is not None or first is not None:
            s += '<w:ind%s%s/>' % (' w:left="%d"' % left if left is not None else "", ' w:firstLine="%d"' % first if first is not None else "")
        if num is not None: s += '<w:contextualSpacing w:val="0"/>'
        if jc: s += '<w:jc w:val="%s"/>' % jc
        return s + "</w:pPr>"

    def para(self, markup, jc="both", sz=24, **kw):
        b = kw.pop("b", False); i = kw.pop("i", False)
        self.body.append("<w:p>%s%s</w:p>" % (self.ppr(jc=jc, **kw), self.runs(markup, sz=sz, b=b, i=i)))

    def heading(self, text, level=1):
        if level == 1:
            self.body.append("<w:p>%s%s</w:p>" % (self.ppr(keep_next=True, before=160, jc="left"), self.r(text, b=True)))
        else:
            self.body.append("<w:p>%s%s</w:p>" % (self.ppr(keep_next=True, before=80, jc="left"), self.runs(text, b=True)))

    def bullets(self, items, num=1, sz=24):
        for it in items:
            self.body.append("<w:p>%s%s</w:p>" % (self.ppr(jc="both", style="ListParagraph", num=num), self.runs(it, sz=sz)))

    def page_break(self):
        self.body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    # ---- figures ----------------------------------------------------------------------------------------------------
    def image(self, path, width_cm):
        with open(path, "rb") as f: head = f.read(32)
        w, h = struct.unpack(">II", head[16:24])
        n = len(self.media) + 1
        name = "image%d.png" % n
        self.media.append((name, path))
        cx = int(width_cm * 360000); cy = int(cx * h / w)
        return ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/><wp:docPr id="%d" name="Picture %d"/>'
                '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
                '<pic:blipFill><a:blip r:embed="rIdImg%d"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
                '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (cx, cy, n, n, n, name, n, cx, cy)

    def figure(self, name, caption, width_cm=15.5):
        self.fig += 1
        self.body.append("<w:p>%s%s</w:p>" % (self.ppr(jc="center", line=240, before=120, keep_next=True), self.image(find_figure(name), width_cm)))
        self.body.append("<w:p>%s%s%s</w:p>" % (self.ppr(jc="both", line=240, after=160, left=0), self.r("Figure %d. " % self.fig, b=True, sz=21), self.runs(caption, sz=21)))
        return self.fig

    # ---- tables -----------------------------------------------------------------------------------------------------
    def table(self, rows, widths_cm, caption, align=None, sz=20, header=True, note=None):
        self.tab += 1
        self.body.append("<w:p>%s%s%s</w:p>" % (self.ppr(jc="both", line=240, before=120, after=60, keep_next=True), self.r("Table %d. " % self.tab, b=True, sz=21), self.runs(caption, sz=21)))
        tw = [int(w * 567) for w in widths_cm]
        x = ['<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>' % sum(tw)]
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            x.append('<w:%s w:val="single" w:sz="4" w:space="0" w:color="808080"/>' % side)
        x.append('</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>')
        x += ['<w:gridCol w:w="%d"/>' % w for w in tw]; x.append("</w:tblGrid>")
        for ri, row in enumerate(rows):
            x.append("<w:tr><w:trPr><w:cantSplit/>%s</w:trPr>" % ("<w:tblHeader/>" if header and ri == 0 else ""))
            for ci, cell in enumerate(row):
                jc = (align[ci] if align else "left")
                shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if header and ri == 0 else ""
                x.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr><w:p>%s%s</w:p></w:tc>' %
                         (tw[ci], shade, self.ppr(jc=jc if not (header and ri == 0) else "center", line=240, after=20, before=20, keep_next=(ri < len(rows) - 1)), self.runs(str(cell), sz=sz, b=(header and ri == 0))))
            x.append("</w:tr>")
        x.append("</w:tbl>")
        self.body.append("".join(x))
        self.body.append("<w:p>%s</w:p>" % self.ppr(line=240, after=120))
        if note: self.para(note, sz=20, line=240, after=120)
        return self.tab

    # ---- equations and algorithms -----------------------------------------------------------------------------------
    def equation(self, latex):
        self.eq += 1
        tw = [int(0.9 * 567), int(15.2 * 567), int(0.9 * 567)]
        cell = lambda w, inner: '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>%s</w:tc>' % (w, inner)
        eqp = '<w:p>%s<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>%s</m:oMathPara></w:p>' % (self.ppr(line=240, jc="center", before=40, after=40), omml(latex))
        num = '<w:p>%s%s</w:p>' % (self.ppr(line=240, jc="right"), self.r("(%d)" % self.eq))
        self.body.append('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>%s</w:tblGrid><w:tr><w:trPr><w:cantSplit/></w:trPr>%s%s%s</w:tr></w:tbl>'
                         % (sum(tw), "".join('<w:gridCol w:w="%d"/>' % w for w in tw), cell(tw[0], "<w:p/>"), cell(tw[1], eqp), cell(tw[2], num)))
        return self.eq

    def algorithm(self, title, lines, caption=None):
        """lines: list of (indent_level, markup). Boxed, numbered lines."""
        self.alg += 1
        tw = int(16.0 * 567)
        rows = ['<w:p>%s%s%s</w:p>' % (self.ppr(line=240, after=40, before=40, left=100, keep_next=True), self.r("Algorithm %d. " % self.alg, b=True, sz=22), self.runs(title, sz=22, b=True))]
        for n, (lvl, txt) in enumerate(lines, 1):
            rows.append('<w:p>%s%s%s</w:p>' % (self.ppr(line=252, after=0, before=0, left=100 + 330 * lvl + 330, first=-330, jc="left", keep_lines=True),
                                                self.r("%d:\t" % n, sz=20), self.runs(txt, sz=21)))
        self.body.append('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>' % tw +
                         "".join('<w:%s w:val="single" w:sz="6" w:space="0" w:color="404040"/>' % s for s in ("top", "left", "bottom", "right")) +
                         '</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="%d"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/></w:tcPr>%s</w:tc></w:tr></w:tbl>' % (tw, tw, "".join(rows)))
        self.body.append("<w:p>%s</w:p>" % self.ppr(line=240, after=100))
        if caption: self.para(caption, sz=21, line=252, after=120)
        return self.alg

    def references(self, entries):
        for i, e in enumerate(entries, 1):
            self.body.append("<w:p>%s%s</w:p>" % (self.ppr(jc="both", style="ColorfulList-Accent11", after=60, line=252, left=567, first=-567), self.runs("[%d] %s" % (i, e), sz=21)))


def package(doc, out=OUT):
    z = zipfile.ZipFile(TEMPLATE)
    names = z.namelist()
    document = z.read("word/document.xml").decode("utf8")
    head = document[: document.index("<w:body>") + len("<w:body>")]
    sect = re.search(r"<w:sectPr.*?</w:sectPr>", document, flags=re.S).group(0)
    new = head + "".join(doc.body) + sect + "</w:body></w:document>"
    rels = z.read("word/_rels/document.xml.rels").decode("utf8")
    add = "".join('<Relationship Id="rIdImg%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/%s"/>' % (i + 1, n) for i, (n, _) in enumerate(doc.media))
    rels = rels.replace("</Relationships>", add + "</Relationships>")
    ctypes = z.read("[Content_Types].xml").decode("utf8")
    if 'Extension="png"' not in ctypes:
        ctypes = ctypes.replace("<Override", '<Default Extension="png" ContentType="image/png"/><Override', 1)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as o:
        for n in names:
            if n == "word/document.xml": o.writestr(n, new)
            elif n == "word/_rels/document.xml.rels": o.writestr(n, rels)
            elif n == "[Content_Types].xml": o.writestr(n, ctypes)
            else: o.writestr(n, z.read(n))
        for n, p in doc.media:
            o.write(p, "word/media/" + n)
    return out


def to_pdf(docx):
    outdir = os.path.dirname(docx)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx], check=True, capture_output=True, timeout=300)
    return docx.replace(".docx", ".pdf")


if __name__ == "__main__":
    import content
    d = Doc()
    content.build(d)
    docx = package(d)
    pdf = to_pdf(docx)
    print("docx:", docx, "\npdf:", pdf, "\nfigures %d, tables %d, equations %d, algorithms %d, references cited %d" % (d.fig, d.tab, d.eq, d.alg, len(d.cite_order)))
