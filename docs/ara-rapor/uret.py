"""Ara sınav raporunu ara-sinav-raporu.md'den üretir: cikti/ altına baskıya hazır PDF ve düzenlenebilir Word.

Biçim kuralları LEE Tez ve Proje Yazım Kılavuzu'ndan (bkz. README.md).
Kullanım (repo kökünde): python docs/ara-rapor/uret.py
Gerekli: pymupdf, python-docx, Google Chrome, Times New Roman yazı tipi.
"""

import html
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf as fitz
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).parent
OUT = ROOT / "cikti"
IMG = ROOT / "img"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TIMES = r"C:\Windows\Fonts\times.ttf"
FILE_NAME = "CareerAI_Ara_Sinav_Raporu"

# Şekil no -> (görsel, genişlik cm, yatay sayfa mı)
FIGURES = {
    1: ("sekil1.png", 15.0, False),
    2: ("sekil2.png", 23.7, True),
    3: ("sekil3.png", 13.5, False),
    4: ("sekil4.png", 23.7, True),
    5: ("sekil5.png", 8.5, False),
    6: ("sekil6.png", 11.0, False),
}


@dataclass
class Block:
    kind: str  # h0 (numarasız), h1, h2, p, bullet, table, table_cap, fig_cap, figure, sign, ref, abbr, toc, lot, lof, meta
    text: str = ""
    rows: list[list[str]] = field(default_factory=list)
    number: int = 0


def parse(md: str) -> tuple[list[list[str]], list[list[str]], list[Block]]:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S).replace("\r", "")
    outer, inner, body = re.split(r"\n---\n", md, maxsplit=2)
    groups = lambda part: [g.strip().split("\n") for g in part.strip().split("\n\n") if g.strip()]
    blocks: list[Block] = []
    section = ""
    for chunk in re.split(r"\n\s*\n", body):
        chunk = chunk.strip()
        if not chunk or chunk == "---":
            continue
        if chunk.startswith("# "):
            title = chunk[2:].strip()
            section = title
            kind = "h1" if re.match(r"\d+\. ", title) else "h0"
            blocks.append(Block(kind, title))
        elif chunk.startswith("## "):
            blocks.append(Block("h2", chunk[3:].strip()))
        elif chunk.startswith("|"):
            rows = [[c.strip() for c in line.strip("|").split("|")] for line in chunk.split("\n")]
            blocks.append(Block("table", rows=[r for i, r in enumerate(rows) if i != 1]))
        elif chunk.startswith("• "):
            blocks.append(Block("bullet", chunk[2:]))
        elif m := re.fullmatch(r"\*\*Tablo (\d+)\. (.*)\*\*", chunk):
            blocks.append(Block("table_cap", m[2], number=int(m[1])))
        elif m := re.fullmatch(r"\*\*Şekil (\d+)\. (.*)\*\*", chunk):
            blocks.append(Block("figure", number=int(m[1])))
            blocks.append(Block("fig_cap", m[2], number=int(m[1])))
        elif chunk.startswith("[Görsel:"):
            continue
        elif section == "İÇİNDEKİLER":
            blocks.append(Block("toc"))
        elif section == "TABLOLAR DİZİNİ":
            blocks.append(Block("lot"))
        elif section == "ŞEKİLLER DİZİNİ":
            blocks.append(Block("lof"))
        elif section == "KAYNAKLAR":
            blocks.append(Block("ref", chunk))
        elif section == "KISALTMALAR DİZİNİ":
            blocks.append(Block("abbr", chunk))
        elif section in ("ÖZET", "ABSTRACT") and len(chunk.split()) < 25 and not chunk.startswith(("Anahtar", "Keywords")):
            blocks.append(Block("meta", chunk))
        elif re.search(r"\s{5,}", chunk):
            blocks.append(Block("sign", chunk))
        else:
            blocks.append(Block("p", chunk))
    return groups(outer), groups(inner), blocks


def clean(text: str) -> str:
    return re.sub(r"\*([^*]+)\*", r"\1", text).replace("`", "")


# ---------------------------------------------------------------- HTML / PDF
CSS = """
@page { size: A4; margin: 3cm 2cm 3cm 4cm; }
@page cover { margin: 2cm 3cm; }
@page land { size: A4 landscape; margin: 4cm 3cm 2cm 3cm; }
* { box-sizing: border-box; }
body { font-family: 'Times New Roman', serif; font-size: 12pt; color: #000; margin: 0; }
p { margin: 6pt 0; line-height: 1.72; text-align: justify; orphans: 2; widows: 2; }
.single p, p.single { line-height: 1.15; }
h1, h2 { font-size: 12pt; font-weight: bold; line-height: 1.15; margin: 6pt 0; text-align: left; break-after: avoid; }
h1 { break-before: page; }
.h0 { text-align: center; margin: 0 0 24pt 0; }
.cover { page: cover; position: relative; height: 25.6cm; break-after: page; text-align: center; line-height: 1.15; }
.cover div { position: absolute; left: 0; right: 0; }
.bullet { margin: 6pt 0 6pt 1.5cm; text-indent: -0.75cm; }
.bullet span { display: inline-block; width: 0.75cm; text-indent: 0; }
.cap { font-weight: bold; text-align: center; line-height: 1.15; margin: 6pt 0; break-after: avoid; }
.figcap { break-after: auto; break-before: avoid; }
table { border-collapse: collapse; margin: 6pt auto 12pt; width: 100%; max-width: 15cm; font-size: 10.5pt; line-height: 1.15; break-inside: avoid; }
th, td { padding: 0 0.15cm; height: 0.5cm; text-align: center; vertical-align: middle; font-weight: normal; }
th { font-weight: bold; border-top: 0.75pt solid #000; border-bottom: 0.75pt solid #000; }
tr { break-inside: avoid; }
tr:last-child td { border-bottom: 0.75pt solid #000; }
thead { display: table-header-group; }
.fig { text-align: center; margin: 6pt 0; break-after: avoid; }
.landwrap { page: land; break-before: page; break-after: page; }
.ref { line-height: 1.15; margin: 6pt 0 6pt 1cm; text-indent: -1cm; }
.abbr { line-height: 1.15; }
.meta { line-height: 1.72; margin: 0; text-align: left; }
.sign { display: flex; justify-content: space-between; line-height: 1.15; margin-top: 24pt; }
.tocl { display: flex; align-items: baseline; line-height: 1.15; margin: 3pt 0; }
.tocl .t { flex: 0 1 auto; }
.tocl .d { flex: 1 1 auto; border-bottom: 1px dotted #000; margin: 0 4px; transform: translateY(-3px); }
mark { background: #ffe066; }
.mk { position: absolute; font-size: 1px; color: #fff; }
"""

OUTER_TOPS = [4, 12, 18, 22, 26]
INNER_TOPS = [4, 8, 12, 16, 20, 24]


def h(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", t)
    t = t.replace("`", "")
    return re.sub(r"(\[DOLDUR[^\]]*\])", r"<mark>\1</mark>", t)


def cover_html(groups: list[list[str]], tops: list[int], logo: bool) -> str:
    assert len(groups) == len(tops), (len(groups), len(tops))
    parts = []
    for i, (group, top) in enumerate(zip(groups, tops)):
        lines = "<br>".join(h(x) for x in group)
        if logo and i == 0:
            lines = "<mark>[DOLDUR: üniversite logosu, 2 cm]</mark><br>" + lines
        parts.append(f'<div style="top:{top - 2}cm">{lines}</div>')
    return f'<section class="cover">{"".join(parts)}</section>'


def index_entries(blocks: list[Block]) -> tuple[list[Block], list[Block], list[Block]]:
    headings = [b for b in blocks if b.kind in ("h0", "h1", "h2")]
    return headings, [b for b in blocks if b.kind == "table_cap"], [b for b in blocks if b.kind == "fig_cap"]


def toc_line(text: str, page: str, indent: float = 0) -> str:
    return (
        f'<div class="tocl" style="padding-left:{indent}cm"><span class="t">{h(text)}</span>'
        f'<span class="d"></span><span>{page}</span></div>'
    )


def body_html(blocks: list[Block], pages: dict[str, str], marks: bool) -> str:
    headings, tables, figures = index_entries(blocks)
    out: list[str] = []

    def mark(key: str) -> str:
        return f'<span class="mk">§{key}§</span>' if marks else ""

    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b.kind == "h0":
            out.append(f'<h1 class="h0">{mark(f"H{id(b)}")}{h(b.text)}</h1>')
        elif b.kind == "h1":
            out.append(f'<h1>{mark(f"H{id(b)}")}{h(b.text)}</h1>')
        elif b.kind == "h2":
            out.append(f'<h2>{mark(f"H{id(b)}")}{h(b.text)}</h2>')
        elif b.kind == "p":
            out.append(f"<p>{h(b.text)}</p>")
        elif b.kind == "meta":
            out.append(f'<p class="meta">{h(b.text)}</p>')
        elif b.kind == "bullet":
            out.append(f'<p class="bullet"><span>•</span>{h(b.text)}</p>')
        elif b.kind == "sign":
            left, right = re.split(r"\s{5,}", b.text)
            out.append(f'<div class="sign"><span>{h(left)}</span><span>{h(right)}</span></div>')
        elif b.kind == "ref":
            out.append(f'<p class="ref">{h(b.text)}</p>')
        elif b.kind == "abbr":
            out.append(f'<p class="abbr">{h(b.text)}</p>')
        elif b.kind == "table_cap":
            out.append(f'<p class="cap">{mark(f"T{b.number}")}Tablo {b.number}. {h(b.text)}</p>')
        elif b.kind == "table":
            head, *rest = b.rows
            ths = "".join(f"<th>{h(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{h(c)}</td>" for c in r) + "</tr>" for r in rest)
            out.append(f"<table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>")
        elif b.kind == "figure":
            img, width, land = FIGURES[b.number]
            cap = blocks[i + 1]
            uri = (IMG / img).resolve().as_uri()
            fig = (
                f'<div class="fig"><img src="{uri}" style="width:{width}cm;max-height:{13.7 if land else 20.5}cm;'
                f'object-fit:contain"></div><p class="cap figcap">{mark(f"F{b.number}")}Şekil {b.number}. {h(cap.text)}</p>'
            )
            out.append(f'<div class="landwrap">{fig}</div>' if land else fig)
            i += 1
        elif b.kind == "toc":
            for e in headings:
                if e.text == "İÇİNDEKİLER":
                    continue
                out.append(toc_line(e.text, pages.get(f"H{id(e)}", "0"), 0.5 if e.kind == "h2" else 0))
        elif b.kind == "lot":
            out += [toc_line(f"Tablo {e.number}. {e.text}", pages.get(f"T{e.number}", "0")) for e in tables]
        elif b.kind == "lof":
            out += [toc_line(f"Şekil {e.number}. {e.text}", pages.get(f"F{e.number}", "0")) for e in figures]
        i += 1
    return "\n".join(out)


def chrome_pdf(doc_html: str, name: str) -> Path:
    path = OUT / f"_{name}.html"
    path.write_text(doc_html, encoding="utf-8")
    pdf = OUT / f"_{name}.pdf"
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
         f"--print-to-pdf={pdf.resolve()}", path.resolve().as_uri()],
        check=True, capture_output=True, timeout=180,
    )  # fmt: skip
    path.unlink()
    return pdf


def roman(n: int) -> str:
    out = ""
    for v, s in ((10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out += s
            n -= v
    return out


def build_pdf(outer: list[list[str]], inner: list[list[str]], blocks: list[Block]) -> tuple[Path, dict[str, str]]:
    covers = cover_html(outer, OUTER_TOPS, True) + cover_html(inner, INNER_TOPS, False)

    def page_doc(pages: dict[str, str], marks: bool) -> str:
        return (
            f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f"{covers}{body_html(blocks, pages, marks)}</body></html>"
        )

    # 1. geçiş: işaretlerle hangi başlık hangi sayfada, bul.
    first = chrome_pdf(page_doc({}, True), "gecis1")
    doc = fitz.open(first)
    locations: dict[str, int] = {}
    for idx, page in enumerate(doc):
        for key in re.findall(r"§([HTF]\d+)§", page.get_text()):
            locations[key] = idx
    giris_block = next(b for b in blocks if b.kind == "h1")
    giris = locations[f"H{id(giris_block)}"]
    doc.close()
    first.unlink()

    def label(idx: int) -> str:
        return str(idx - giris + 1) if idx >= giris else roman(idx - 1)

    pages = {k: label(v) for k, v in locations.items()}

    # 2. geçiş: gerçek numaralarla, işaretsiz.
    second = chrome_pdf(page_doc(pages, False), "gecis2")
    doc = fitz.open(second)
    for idx, page in enumerate(doc):
        if idx < 2:
            continue
        text = label(idx)
        font = fitz.Font(fontfile=TIMES)
        width = font.text_length(text, 12)
        rect = page.rect
        landscape = rect.width > rect.height
        right = rect.width - (3 if landscape else 2) * 72 / 2.54
        page.insert_text((right - width, rect.height - 1.5 * 72 / 2.54), text, fontsize=12, fontname="tnr", fontfile=TIMES)
    doc.set_metadata({"title": "Yapay Zekâ Destekli Kariyer ve Eğitim Yönlendirme Sistemi", "author": "Ataberk Çakır, Burak Doğan, Anıl Akyıl"})
    final = OUT / f"{FILE_NAME}.pdf"
    doc.save(final, garbage=3, deflate=True)
    count = doc.page_count
    doc.close()
    second.unlink()
    print(f"PDF: {final.name}, {count} sayfa, Giriş sayfası (dosyada): {giris + 1}")
    return final, pages


# ---------------------------------------------------------------- Word
def set_font(run, size: float = 12, bold: bool | None = None, italic: bool | None = None) -> None:
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_text(par, text: str, size: float = 12, bold: bool | None = None) -> None:
    for part in re.split(r"(\*[^*]+\*|\[DOLDUR[^\]]*\])", text.replace("`", "")):
        if not part:
            continue
        if part.startswith("[DOLDUR"):
            run = par.add_run(part)
            set_font(run, size, bold)
            highlight = OxmlElement("w:highlight")
            highlight.set(qn("w:val"), "yellow")
            run._element.get_or_add_rPr().append(highlight)
        elif part.startswith("*"):
            set_font(par.add_run(part[1:-1]), size, bold, True)
        else:
            set_font(par.add_run(part), size, bold)


def fmt(par, *, line: float = 1.5, before: float = 6, after: float = 6, align=WD_ALIGN_PARAGRAPH.JUSTIFY, keep_next=False) -> None:
    pf = par.paragraph_format
    pf.line_spacing = line
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.alignment = align
    pf.keep_with_next = keep_next
    pf.widow_control = True


def margins(section, top: float, bottom: float, left: float, right: float) -> None:
    section.top_margin, section.bottom_margin = Cm(top), Cm(bottom)
    section.left_margin, section.right_margin = Cm(left), Cm(right)
    section.footer_distance = Cm(1.5)


def page_field(section, numfmt: str | None, start: int | None) -> None:
    section.footer.is_linked_to_previous = False
    par = section.footer.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if not par.runs:
        run = par.add_run()
        set_font(run)
        for tag, text in (("begin", None), (None, " PAGE "), ("end", None)):
            if tag:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tag)
            else:
                el = OxmlElement("w:instrText")
                el.text = text
            run._element.append(el)
    # add_section önceki bölümün ayarlarını kopyalar: eski numara ayarı kalırsa numaralama her bölümde başa döner.
    sect = section._sectPr
    for old in sect.findall(qn("w:pgNumType")):
        sect.remove(old)
    if numfmt:
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), numfmt)
        if start is not None:
            pg.set(qn("w:start"), str(start))
        cols = sect.find(qn("w:cols"))
        if cols is not None:
            cols.addprevious(pg)
        else:
            sect.append(pg)


def outline(par, level: int) -> None:
    el = OxmlElement("w:outlineLvl")
    el.set(qn("w:val"), str(level))
    par._p.get_or_add_pPr().append(el)


def table_borders(table) -> None:
    def edge(cell, name: str) -> None:
        tc_pr = cell._tc.get_or_add_tcPr()
        borders = tc_pr.find(qn("w:tcBorders"))
        if borders is None:
            borders = OxmlElement("w:tcBorders")
            tc_pr.append(borders)
        el = OxmlElement(f"w:{name}")
        for k, v in (("val", "single"), ("sz", "6"), ("space", "0"), ("color", "000000")):
            el.set(qn(f"w:{k}"), v)
        borders.append(el)

    for cell in table.rows[0].cells:
        edge(cell, "top")
        edge(cell, "bottom")
    for cell in table.rows[-1].cells:
        edge(cell, "bottom")


def cover_docx(doc, groups: list[list[str]], tops: list[int], logo: bool) -> None:
    previous = 2.0
    for i, (group, top) in enumerate(zip(groups, tops)):
        lines = (["[DOLDUR: üniversite logosu, 2 cm]"] if logo and i == 0 else []) + group
        for j, line in enumerate(lines):
            par = doc.add_paragraph()
            add_text(par, line)
            fmt(par, line=1.0, before=0, after=0, align=WD_ALIGN_PARAGRAPH.CENTER)
            if j == 0:
                # 12 punto tek satır ≈ 0,49 cm; bir sonraki öğe kılavuzdaki konumdan başlasın.
                par.paragraph_format.space_before = Cm(max(top - previous, 0))
        previous = top + len(lines) * 0.49


def build_docx(outer: list[list[str]], inner: list[list[str]], blocks: list[Block], pages: dict[str, str]) -> Path:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for section in doc.sections:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
    first = doc.sections[0]
    margins(first, 2, 2, 3, 3)
    cover_docx(doc, outer, OUTER_TOPS, True)
    doc.add_page_break()
    cover_docx(doc, inner, INNER_TOPS, False)

    roman_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    margins(roman_sec, 3, 3, 4, 2)
    page_field(roman_sec, "lowerRoman", 1)
    headings, tables, figures = index_entries(blocks)
    first_h1 = next(b for b in blocks if b.kind == "h1")

    def toc(text: str, page: str, indent: float = 0) -> None:
        par = doc.add_paragraph()
        add_text(par, f"{clean(text)}\t{page}")
        fmt(par, line=1.0, before=3, after=3, align=WD_ALIGN_PARAGRAPH.LEFT)
        par.paragraph_format.left_indent = Cm(indent)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(15), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

    def portrait_section(numfmt=None) -> None:
        sec = doc.add_section(WD_SECTION.NEW_PAGE)
        sec.orientation = WD_ORIENT.PORTRAIT
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        margins(sec, 3, 3, 4, 2)
        page_field(sec, numfmt, None)

    numfmt_now = "lowerRoman"
    i = 0
    need_break = False
    while i < len(blocks):
        b = blocks[i]
        if b.kind in ("h0", "h1"):
            if b is first_h1:
                sec = doc.add_section(WD_SECTION.NEW_PAGE)
                margins(sec, 3, 3, 4, 2)
                page_field(sec, "decimal", 1)
                numfmt_now = "decimal"
                new_page = False
            else:
                new_page = need_break
            par = doc.add_paragraph()
            par.paragraph_format.page_break_before = new_page
            add_text(par, b.text, bold=True)
            if b.kind == "h0":
                fmt(par, line=1.0, before=0, after=24, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
            else:
                fmt(par, line=1.0, align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
            if b.text != "İÇİNDEKİLER":
                outline(par, 0)
            need_break = True
        elif b.kind == "h2":
            par = doc.add_paragraph()
            add_text(par, b.text, bold=True)
            fmt(par, line=1.0, align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
            outline(par, 1)
        elif b.kind == "p":
            par = doc.add_paragraph()
            add_text(par, b.text)
            fmt(par)
        elif b.kind == "meta":
            par = doc.add_paragraph()
            add_text(par, b.text)
            fmt(par, before=0, after=0, align=WD_ALIGN_PARAGRAPH.LEFT)
        elif b.kind == "bullet":
            par = doc.add_paragraph()
            add_text(par, f"•\t{b.text}")
            fmt(par)
            par.paragraph_format.left_indent = Cm(1.5)
            par.paragraph_format.first_line_indent = Cm(-0.75)
        elif b.kind == "sign":
            left, right = re.split(r"\s{5,}", b.text)
            par = doc.add_paragraph()
            add_text(par, f"{left}\t{right}")
            fmt(par, line=1.0, before=24, after=0, align=WD_ALIGN_PARAGRAPH.LEFT)
            par.paragraph_format.tab_stops.add_tab_stop(Cm(15), WD_TAB_ALIGNMENT.RIGHT)
        elif b.kind == "ref":
            par = doc.add_paragraph()
            add_text(par, b.text)
            fmt(par, line=1.0)
            par.paragraph_format.left_indent = Cm(1)
            par.paragraph_format.first_line_indent = Cm(-1)
        elif b.kind == "abbr":
            par = doc.add_paragraph()
            add_text(par, b.text)
            fmt(par, line=1.0)
        elif b.kind == "table_cap":
            par = doc.add_paragraph()
            add_text(par, f"Tablo {b.number}. {b.text}", bold=True)
            fmt(par, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
        elif b.kind == "table":
            head, *rest = b.rows
            table = doc.add_table(rows=len(b.rows), cols=len(head))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r, row in enumerate(b.rows):
                for c, value in enumerate(row):
                    cell = table.cell(r, c)
                    par = cell.paragraphs[0]
                    add_text(par, value, size=10.5, bold=r == 0)
                    fmt(par, line=1.0, before=0, after=0, align=WD_ALIGN_PARAGRAPH.CENTER)
            table_borders(table)
            tr_pr = table.rows[0]._tr.get_or_add_trPr()
            tr_pr.append(OxmlElement("w:tblHeader"))
            spacer = doc.add_paragraph()
            fmt(spacer, line=1.0, before=0, after=6)
        elif b.kind == "figure":
            img, width, land = FIGURES[b.number]
            cap = blocks[i + 1]
            if land:
                sec = doc.add_section(WD_SECTION.NEW_PAGE)
                sec.orientation = WD_ORIENT.LANDSCAPE
                sec.page_width, sec.page_height = Cm(29.7), Cm(21)
                margins(sec, 4, 2, 3, 3)
                page_field(sec, numfmt_now, None)
            par = doc.add_paragraph()
            fmt(par, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
            pix = fitz.Pixmap(str(IMG / img))
            max_h = 13.7 if land else 20.5
            w = min(width, max_h * pix.width / pix.height)
            par.add_run().add_picture(str(IMG / img), width=Cm(w))
            cap_par = doc.add_paragraph()
            add_text(cap_par, f"Şekil {b.number}. {cap.text}", bold=True)
            fmt(cap_par, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
            if land:
                portrait_section(numfmt_now)
            i += 1
        elif b.kind == "toc":
            for e in headings:
                if e.text != "İÇİNDEKİLER":
                    toc(e.text, pages.get(f"H{id(e)}", ""), 0.5 if e.kind == "h2" else 0)
        elif b.kind == "lot":
            for e in tables:
                toc(f"Tablo {e.number}. {e.text}", pages.get(f"T{e.number}", ""))
        elif b.kind == "lof":
            for e in figures:
                toc(f"Şekil {e.number}. {e.text}", pages.get(f"F{e.number}", ""))
        i += 1
    doc.core_properties.title = "Yapay Zekâ Destekli Kariyer ve Eğitim Yönlendirme Sistemi"
    doc.core_properties.author = "Ataberk Çakır, Burak Doğan, Anıl Akyıl"
    path = OUT / f"{FILE_NAME}.docx"
    doc.save(path)
    print(f"Word: {path.name}")
    return path


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    outer, inner, blocks = parse((ROOT / "ara-sinav-raporu.md").read_text(encoding="utf-8"))
    _, pages = build_pdf(outer, inner, blocks)
    build_docx(outer, inner, blocks, pages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
