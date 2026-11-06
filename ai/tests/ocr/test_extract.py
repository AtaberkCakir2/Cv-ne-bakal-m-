"""OCR akışı. Tesseract gerektirmeyen testler sahte süreçle çalışır; gerçek okuma testi kurulu değilse atlanır."""

from __future__ import annotations

import builtins
import io
import os
import shutil
import subprocess
import tempfile
from typing import Any

import pymupdf
import pytest

from ocr import OcrError, extract_with_ocr, ocr_pdf
from parsing import PdfError, Reason
from tests.parsing.conftest import make_pdf, single_column_cv

OCR_TEXT = "Python ve FastAPI ile REST API geliştirdim. Çözüm üretmeyi seven bir öğrenciyim. " * 4


class FakeTesseract:
    """`subprocess.run` yerine geçer; aldığı komutu ve görüntüleri saklar."""

    def __init__(self, stdout: str = OCR_TEXT, returncode: int = 0, stderr: bytes = b"") -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr
        self.commands: list[list[str]] = []
        self.images: list[bytes] = []

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        assert "shell" not in kwargs
        self.commands.append(command)
        self.images.append(kwargs["input"])
        return subprocess.CompletedProcess(command, self.returncode, self.stdout.encode(), self.stderr)


@pytest.fixture
def tesseract(monkeypatch: pytest.MonkeyPatch) -> FakeTesseract:
    fake = FakeTesseract()
    monkeypatch.setenv("TESSERACT_CMD", "tesseract-sahte")
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def scanned(pages: int = 1) -> bytes:
    return make_pdf([[]] * pages, image_only=True)


def test_digital_pdf_does_not_use_ocr(tesseract: FakeTesseract) -> None:
    result = extract_with_ocr(make_pdf([single_column_cv()]))
    assert result.backend != "tesseract"
    assert tesseract.commands == []


def test_scanned_pdf_uses_ocr(tesseract: FakeTesseract) -> None:
    result = extract_with_ocr(scanned())
    assert result.backend == "tesseract"
    assert "FastAPI" in result.text and "öğrenciyim" in result.text
    assert result.page_count == 1


def test_short_text_pdf_uses_ocr(tesseract: FakeTesseract) -> None:
    result = extract_with_ocr(make_pdf([[(56, 72, "Kısa metin", 11)]]))
    assert result.backend == "tesseract"


def test_tesseract_gets_grayscale_300_dpi_png_with_turkish_and_english(tesseract: FakeTesseract) -> None:
    extract_with_ocr(scanned())
    assert tesseract.commands[0] == ["tesseract-sahte", "stdin", "stdout", "-l", "tur+eng", "--dpi", "300"]
    pix = pymupdf.Pixmap(tesseract.images[0])
    assert (pix.width, pix.height) == (2480, 3509)  # A4, 300 DPI
    assert pix.n == 1


def test_every_page_is_read(tesseract: FakeTesseract) -> None:
    assert ocr_pdf(scanned(pages=3)).count("FastAPI") == 12
    assert len(tesseract.images) == 3


def test_huge_page_is_scaled_down(tesseract: FakeTesseract) -> None:
    doc = pymupdf.open()
    doc.new_page(width=14400, height=14400)
    ocr_pdf(doc.tobytes())
    pix = pymupdf.Pixmap(tesseract.images[0])
    assert max(pix.width, pix.height) <= 5000


def test_no_text_after_ocr_is_no_text_error(tesseract: FakeTesseract) -> None:
    tesseract.stdout = " | ~ . "
    with pytest.raises(PdfError) as err:
        extract_with_ocr(scanned())
    assert err.value.reason is Reason.NO_TEXT


def test_digital_text_is_kept_when_ocr_reads_less(tesseract: FakeTesseract) -> None:
    tesseract.stdout = ""
    text = "Python ve Docker biliyorum, SQL yazarım"
    result = extract_with_ocr(make_pdf([[(56, 72, text, 11)]]))
    assert result.backend != "tesseract"
    assert result.text == text


def test_invalid_pdf_does_not_reach_ocr(tesseract: FakeTesseract) -> None:
    with pytest.raises(PdfError):
        extract_with_ocr(b"bu bir pdf degil")
    assert tesseract.commands == []


def test_missing_tesseract_is_ocr_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(OcrError):
        extract_with_ocr(scanned())


def test_wrong_tesseract_path_is_ocr_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*_: Any, **__: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setenv("TESSERACT_CMD", "yok")
    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(OcrError):
        extract_with_ocr(scanned())


def test_failure_does_not_expose_cv_content(tesseract: FakeTesseract, caplog: pytest.LogCaptureFixture) -> None:
    tesseract.returncode = 1
    tesseract.stderr = b"Gizli Aday Bilgisi"
    with pytest.raises(OcrError) as err:
        extract_with_ocr(scanned())
    assert "Gizli" not in str(err.value)
    assert "Gizli" not in caplog.text


def test_timeout_drops_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(command: list[str], **_: Any) -> None:
        raise subprocess.TimeoutExpired(command, 1, output=b"Gizli Aday Bilgisi")

    monkeypatch.setenv("TESSERACT_CMD", "tesseract-sahte")
    monkeypatch.setattr(subprocess, "run", slow)
    with pytest.raises(OcrError) as err:
        extract_with_ocr(scanned())
    assert err.value.__cause__ is None and err.value.__suppress_context__
    assert "Gizli" not in str(err.value)


def test_nothing_is_written_to_disk(tesseract: FakeTesseract, monkeypatch: pytest.MonkeyPatch) -> None:
    data = scanned(pages=2)
    real_open = builtins.open

    def guarded_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        assert not set(mode) & set("wax+"), f"dosya yazılmaya çalışıldı: {file}"
        return real_open(file, mode, *args, **kwargs)

    def no_temp(*_: Any, **__: Any) -> None:
        raise AssertionError("geçici dosya açılmaya çalışıldı")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(io, "open", guarded_open)
    monkeypatch.setattr(os, "open", no_temp)
    for name in ("mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile"):
        monkeypatch.setattr(tempfile, name, no_temp)
    assert extract_with_ocr(data).backend == "tesseract"


@pytest.mark.skipif(not (os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")), reason="Tesseract kurulu değil")
def test_real_tesseract_reads_turkish_scan() -> None:
    doc = pymupdf.open(stream=make_pdf([single_column_cv()]), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=200, colorspace=pymupdf.csGRAY)
    out = pymupdf.open()
    page = out.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=pix.tobytes("png"))

    result = extract_with_ocr(out.tobytes())

    assert result.backend == "tesseract"
    for word in ("FastAPI", "PostgreSQL", "Docker", "Mühendisliği", "öğrenci", "şirket", "çiçek"):
        assert word in result.text, result.text
