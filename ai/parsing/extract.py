"""CV PDF'inden metin çıkarma (T-020).

Kurallar (karar #9, kabul kriteri):
- Tamamen bellek içi: girdi `bytes`, dosya diske yazılmaz, metin loglanmaz.
- Önce pdfplumber; hata verirse veya çok az metin çıkarsa PyMuPDF yedeği denenir, uzun olan alınır.
- Çok sütunlu CV düzeni `layout` modülünde okuma sırasına dizilir.
- Bozuk / şifreli / büyük PDF için sözleşmedeki hata kodlarıyla `PdfError`.

Metin `MIN_TEXT_CHARS`'tan kısaysa `needs_ocr=True` döner; OCR (T-029) ve gerekirse NO_TEXT_FOUND
hatası bir üst katmanın işidir.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from parsing import backends
from parsing.errors import PdfError, Reason
from parsing.layout import Page, normalize, page_text

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 5
MIN_TEXT_CHARS = 200

Backend = Literal["pdfplumber", "pymupdf"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParseResult:
    text: str
    page_count: int
    backend: Backend
    multi_column_pages: int

    @property
    def needs_ocr(self) -> bool:
        return len(self.text) < MIN_TEXT_CHARS


def extract_text(data: bytes, *, max_bytes: int = MAX_BYTES, max_pages: int = MAX_PAGES) -> ParseResult:
    if len(data) > max_bytes:
        raise PdfError(Reason.TOO_MANY_BYTES)
    if b"%PDF-" not in data[:1024]:
        raise PdfError(Reason.NOT_PDF)

    try:
        page_count, encrypted = backends.inspect(data)
    except Exception as exc:  # noqa: BLE001 — açılamayan her dosya "bozuk" sayılır
        logger.info("PDF açılamadı: %s", type(exc).__name__)
        raise PdfError(Reason.CORRUPT) from exc
    if encrypted:
        raise PdfError(Reason.ENCRYPTED)
    if page_count > max_pages:
        raise PdfError(Reason.TOO_MANY_PAGES)

    readers: list[tuple[Backend, Callable[[bytes], list[Page]]]] = [
        ("pdfplumber", backends.pdfplumber_pages),
        ("pymupdf", backends.pymupdf_pages),
    ]
    best: ParseResult | None = None
    for name, read in readers:
        try:
            result = _build(read(data), name)
        except Exception as exc:  # noqa: BLE001 — bir kütüphane düşerse diğeri denenir
            logger.warning("%s ile okunamadı: %s", name, type(exc).__name__)
            continue
        if best is None or len(result.text) > len(best.text):
            best = result
        if not best.needs_ocr:
            break

    if best is None:
        raise PdfError(Reason.CORRUPT)
    return best


def _build(pages: list[Page], backend: Backend) -> ParseResult:
    texts: list[str] = []
    multi = 0
    for page in pages:
        text, has_columns = page_text(page)
        texts.append(text)
        multi += has_columns
    return ParseResult(
        text=normalize("\n\n".join(texts)),
        page_count=len(pages),
        backend=backend,
        multi_column_pages=multi,
    )
