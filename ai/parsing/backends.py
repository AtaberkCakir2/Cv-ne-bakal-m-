"""PDF kütüphanelerinden kelime + koordinat okuma. Her şey bellekte; diske hiçbir şey yazılmaz."""

from __future__ import annotations

import io

import pdfplumber
import pymupdf

from parsing.layout import Page, Word


def pdfplumber_pages(data: bytes) -> list[Page]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [
            Page(
                width=float(page.width),
                height=float(page.height),
                words=[
                    Word(float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"]), str(w["text"]))
                    for w in page.extract_words(keep_blank_chars=False, use_text_flow=False)
                ],
            )
            for page in pdf.pages
        ]


def pymupdf_pages(data: bytes) -> list[Page]:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        pages = []
        for page in doc:
            words = [
                Word(float(x0), float(y0), float(x1), float(y1), str(text))
                for x0, y0, x1, y1, text, *_ in page.get_text("words")
            ]
            pages.append(Page(width=float(page.rect.width), height=float(page.rect.height), words=words))
        return pages


def inspect(data: bytes) -> tuple[int, bool]:
    """(sayfa sayısı, şifreli mi). Açılamazsa kütüphanenin hatası yükselir."""
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        encrypted = bool(doc.needs_pass) and not doc.authenticate("")
        return doc.page_count, encrypted
