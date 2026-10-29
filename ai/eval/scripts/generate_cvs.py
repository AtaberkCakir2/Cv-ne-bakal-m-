"""Sentetik CV'leri üretir: dataset/cv_specs/<cv_id>.json → dataset/synthetic/<cv_id>.pdf + manifest.csv.

Kullanım:
    python ai/eval/scripts/generate_cvs.py [--dataset DIR] [--only syn-004 syn-005 ...]

Her CV'nin içeriği tek bir JSON dosyasındadır (biçim: ai/eval/README.md → "CV tanım dosyası"). Script:
- tek sütunlu veya kenar çubuklu (çok sütunlu) A4 PDF basar,
- `scanned: true` ise sayfaları görüntüye çevirip yeniden PDF yapar (metin katmanı kalmaz, OCR gerekir),
- manifest.csv'deki satırı JSON'daki alanlardan yazar (manifest elle düzenlenmez).

Şablonun yetkinlik listesi cevap anahtarı değildir; etiketler metinde geçene göre elle verilir.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import sys
from pathlib import Path
from typing import Any

import pymupdf
from _common import DEFAULT_DATASET, EXPERIENCE, LANGUAGES, LAYOUTS, use_utf8_stdout

MANIFEST_FIELDS = [
    "cv_id",
    "source",
    "language",
    "layout",
    "scanned",
    "pages",
    "target_role",
    "experience",
    "double",
    "consent_id",
]
PAGE = pymupdf.paper_rect("a4")
MARGIN = 40
SIDEBAR_WIDTH = 170
HEADER_HEIGHT = 84  # çok sütunlu düzende ad + unvan + iletişim satırı
GUTTER = 22
SCAN_DPI = 150

CSS = """
* { font-family: sans-serif; }
h1 { font-size: 20pt; margin: 0 0 2pt 0; }
.title { font-size: 11pt; margin: 0 0 4pt 0; }
.contact { font-size: 8.5pt; margin: 0 0 10pt 0; }
h2 { font-size: 11pt; margin: 10pt 0 4pt 0; text-transform: uppercase; }
p, li { font-size: 9.5pt; line-height: 1.3; margin: 0 0 3pt 0; }
.item-h { font-size: 10pt; font-weight: bold; margin: 4pt 0 0 0; }
.meta { font-size: 8.5pt; font-style: italic; margin: 0 0 2pt 0; }
ul { margin: 0 0 3pt 0; padding-left: 12pt; }
.sidebar p, .sidebar li { font-size: 9pt; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def section_html(section: dict[str, Any]) -> str:
    parts = [f"<h2>{esc(section['title'])}</h2>"]
    for para in section.get("text", []):
        parts.append(f"<p>{esc(para)}</p>")
    for item in section.get("items", []):
        parts.append(f"<p class='item-h'>{esc(item['heading'])}</p>")
        if item.get("meta"):
            parts.append(f"<p class='meta'>{esc(item['meta'])}</p>")
        for para in item.get("text", []):
            parts.append(f"<p>{esc(para)}</p>")
        if item.get("bullets"):
            parts.append("<ul>" + "".join(f"<li>{esc(b)}</li>" for b in item["bullets"]) + "</ul>")
    if section.get("list"):
        parts.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in section["list"]) + "</ul>")
    return "".join(parts)


def header_html(header: dict[str, Any]) -> str:
    contact = " · ".join(esc(c) for c in header.get("contact", []))
    return (
        f"<h1>{esc(header['name'])}</h1><p class='title'>{esc(header.get('title', ''))}</p>"
        f"<p class='contact'>{contact}</p>"
    )


def render_pdf(spec: dict[str, Any]) -> bytes:
    """CV'yi PDF olarak bellekte üretir."""
    main_html = "".join(section_html(s) for s in spec["main"])
    full = pymupdf.Rect(MARGIN, MARGIN, PAGE.width - MARGIN, PAGE.height - MARGIN)
    buffer = io.BytesIO()
    writer = pymupdf.DocumentWriter(buffer)

    if spec["layout"] == "multi_column":
        sidebar = pymupdf.Story(
            "<div class='sidebar'>" + "".join(section_html(s) for s in spec["sidebar"]) + "</div>", user_css=CSS
        )
        head = pymupdf.Story(header_html(spec["header"]), user_css=CSS)
        main = pymupdf.Story(main_html, user_css=CSS)
        head_rect = pymupdf.Rect(full.x0, full.y0, full.x1, MARGIN + HEADER_HEIGHT)
        top = MARGIN + HEADER_HEIGHT + 6
        side_rect = pymupdf.Rect(MARGIN, top, MARGIN + SIDEBAR_WIDTH, full.y1)
        main_rect = pymupdf.Rect(MARGIN + SIDEBAR_WIDTH + GUTTER, top, full.x1, full.y1)
        device = writer.begin_page(PAGE)
        if _place(device, head, head_rect):
            raise ValueError(f"{spec['cv_id']}: başlık (ad, unvan, iletişim) ayrılan alana sığmıyor; kısaltın")
        if _place(device, sidebar, side_rect):
            raise ValueError(f"{spec['cv_id']}: kenar çubuğu ilk sayfaya sığmıyor; kısaltın")
        more = _place(device, main, main_rect)
        writer.end_page()
        while more:
            device = writer.begin_page(PAGE)
            more = _place(device, main, pymupdf.Rect(main_rect.x0, MARGIN, main_rect.x1, full.y1))
            writer.end_page()
    else:
        story = pymupdf.Story(header_html(spec["header"]) + main_html, user_css=CSS)
        more = True
        while more:
            device = writer.begin_page(PAGE)
            more = _place(device, story, full)
            writer.end_page()
    writer.close()

    doc = pymupdf.open(stream=buffer.getvalue(), filetype="pdf")
    doc.set_metadata({"title": f"Sentetik CV {spec['cv_id']}", "author": "", "producer": "CareerAI ai/eval"})
    data = bytes(doc.tobytes(garbage=3, deflate=True))
    doc.close()
    return _rasterize(data) if spec["scanned"] else data


def _place(device: Any, story: pymupdf.Story, rect: pymupdf.Rect) -> bool:
    """Hikâyenin sığan kısmını sayfaya çizer; devamı varsa True."""
    more, _ = story.place(rect)
    story.draw(device)
    return bool(more)


def _rasterize(data: bytes) -> bytes:
    """Taranmış belge benzetimi: her sayfa gri tonlu JPEG görüntüye çevrilir, metin katmanı kalmaz."""
    src = pymupdf.open(stream=data, filetype="pdf")
    out = pymupdf.open()
    for page in src.pages():
        pix = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
        img = out.new_page(width=page.rect.width, height=page.rect.height)
        img.insert_image(img.rect, stream=pix.tobytes("jpeg", jpg_quality=70))
    out.set_metadata({"title": "", "author": "", "producer": "CareerAI ai/eval"})
    result = out.tobytes(garbage=3, deflate=True)
    out.close()
    src.close()
    return bytes(result)


def validate_spec(spec: dict[str, Any], path: Path) -> list[str]:
    errors = []
    if spec.get("cv_id") != path.stem:
        errors.append(f"{path.name}: cv_id dosya adıyla aynı olmalı")
    for name, allowed in (("language", LANGUAGES), ("layout", LAYOUTS), ("experience", EXPERIENCE)):
        if spec.get(name) not in allowed:
            errors.append(f"{path.name}: {name}='{spec.get(name)}' geçersiz")
    for name in ("scanned", "double"):
        if not isinstance(spec.get(name), bool):
            errors.append(f"{path.name}: {name} true/false olmalı")
    if spec.get("layout") == "multi_column" and not spec.get("sidebar"):
        errors.append(f"{path.name}: çok sütunlu düzende 'sidebar' gerekli")
    if not spec.get("main") or not spec.get("header", {}).get("name"):
        errors.append(f"{path.name}: 'header.name' ve 'main' gerekli")
    return errors


def write_manifest(dataset: Path, updates: dict[str, dict[str, str]]) -> None:
    path = dataset / "manifest.csv"
    rows: dict[str, dict[str, str]] = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            rows = {r["cv_id"]: r for r in csv.DictReader(f)}
    rows.update(updates)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        for cv_id in sorted(rows):
            writer.writerow({k: rows[cv_id].get(k, "") for k in MANIFEST_FIELDS})


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--only", nargs="*", help="Sadece bu cv_id'ler")
    args = parser.parse_args(argv)

    spec_paths = sorted((args.dataset / "cv_specs").glob("syn-*.json"))
    if args.only:
        spec_paths = [p for p in spec_paths if p.stem in set(args.only)]
    errors: list[str] = []
    updates: dict[str, dict[str, str]] = {}
    out_dir = args.dataset / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in spec_paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        if problems := validate_spec(spec, path):
            errors += problems
            continue
        data = render_pdf(spec)
        (out_dir / f"{spec['cv_id']}.pdf").write_bytes(data)
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            pages = doc.page_count
        updates[spec["cv_id"]] = {
            "cv_id": spec["cv_id"],
            "source": "synthetic",
            "language": spec["language"],
            "layout": spec["layout"],
            "scanned": str(spec["scanned"]).lower(),
            "pages": str(pages),
            "target_role": spec["target_role"],
            "experience": spec["experience"],
            "double": str(spec["double"]).lower(),
            "consent_id": "",
        }
        print(f"{spec['cv_id']}: {pages} sayfa, {len(data) // 1024} KB{' (taranmış)' if spec['scanned'] else ''}")

    for e in errors:
        print(f"HATA: {e}")
    if updates:
        write_manifest(args.dataset, updates)
    print(f"\n{len(updates)} CV üretildi, {len(errors)} hata.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
