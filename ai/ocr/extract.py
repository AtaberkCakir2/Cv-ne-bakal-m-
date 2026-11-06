"""Taranmış CV'ler için OCR yedeği (T-029).

Kurallar (karar #9, kabul kriteri):
- Tamamen bellek içi. Sayfalar PyMuPDF ile 300 DPI görüntüye çevrilir ve Tesseract'a stdin'den verilir, metin
  stdout'tan okunur. `pdf2image` (PDF'i geçici dosyaya yazar) ve `pytesseract` (görüntüyü geçici dosyaya yazar)
  bu yüzden kullanılmaz.
- OCR metni ve Tesseract'ın stderr'i loglanmaz, hata mesajına girmez.
- Tesseract kurulu değilse veya çalışamazsa `OcrError` (sözleşmede INTERNAL); bu kullanıcının dosyasının suçu değildir.
  OCR çalışıp yine metin çıkmazsa `PdfError(NO_TEXT)` (sözleşmede NO_TEXT_FOUND).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # noqa: S404 — sabit argümanlarla, kabuk olmadan çalışır
from collections.abc import Iterator

import pymupdf

from parsing.errors import PdfError, Reason
from parsing.extract import ParseResult, extract_text
from parsing.layout import normalize

DPI = 300
LANGUAGES = "tur+eng"
PAGE_TIMEOUT_SECONDS = 120
# Bozuk veya kötü niyetli PDF'te dev sayfa belleği doldurmasın: A3'ün 300 DPI hali (4961 px) sığar, üstü küçültülür.
MAX_PAGE_SIDE_PX = 5000
# Boş sayfada Tesseract birkaç gürültü karakteri dönebilir; bu kadar harf yoksa metin çıkmamış sayılır.
MIN_LETTERS = 20

logger = logging.getLogger(__name__)


class OcrError(RuntimeError):
    """Tesseract çalıştırılamadı. Mesajda CV içeriği olmaz."""


def extract_with_ocr(data: bytes) -> ParseResult:
    """PDF'ten metin çıkarır; metin `MIN_TEXT_CHARS`'tan kısaysa OCR'a başvurur. Worker'ın giriş noktası."""
    result = extract_text(data)  # boyut, sayfa sayısı ve şifre denetimleri burada
    if result.needs_ocr:
        text = ocr_pdf(data)
        if len(text) > len(result.text):
            result = ParseResult(text=text, page_count=result.page_count, backend="tesseract", multi_column_pages=0)
    if sum(c.isalpha() for c in result.text) < MIN_LETTERS:
        raise PdfError(Reason.NO_TEXT)
    return result


def ocr_pdf(data: bytes) -> str:
    """Tüm sayfaları sırayla OCR'dan geçirir."""
    command = _command()
    return normalize("\n\n".join(_run(command, page) for page in _render_pages(data)))


def _render_pages(data: bytes) -> Iterator[bytes]:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            for page in doc.pages():
                longest = max(page.rect.width, page.rect.height)
                dpi = min(DPI, int(MAX_PAGE_SIDE_PX * 72 / longest))
                yield page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).tobytes("png")
    except pymupdf.FileDataError as exc:
        raise PdfError(Reason.CORRUPT) from exc


def _command() -> list[str]:
    binary = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not binary:
        raise OcrError("Tesseract bulunamadı (PATH veya TESSERACT_CMD)")
    return [binary, "stdin", "stdout", "-l", LANGUAGES, "--dpi", str(DPI)]


def _run(command: list[str], png: bytes) -> str:
    try:
        done = subprocess.run(  # noqa: S603 — komut sabit, girdi sadece stdin'den
            command, input=png, capture_output=True, timeout=PAGE_TIMEOUT_SECONDS, check=False
        )
    except FileNotFoundError:
        raise OcrError("Tesseract bulunamadı (PATH veya TESSERACT_CMD)") from None
    except subprocess.TimeoutExpired:
        # `from None`: TimeoutExpired yarım OCR çıktısını taşır, hata zincirinde kalmasın.
        raise OcrError(f"Tesseract {PAGE_TIMEOUT_SECONDS} saniyede bitmedi") from None
    if done.returncode != 0:
        logger.warning("Tesseract çıkış kodu: %s", done.returncode)
        raise OcrError(f"Tesseract hata verdi (çıkış kodu {done.returncode})")
    return done.stdout.decode("utf-8", errors="replace")
