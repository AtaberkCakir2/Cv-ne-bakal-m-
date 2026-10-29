from __future__ import annotations

import builtins
import os
import tempfile
from typing import Any

import pytest

from parsing import ErrorCode, PdfError, Reason, extract_text
from parsing import backends as backends_module
from tests.parsing.conftest import make_pdf, single_column_cv, table_cv, two_column_cv


def test_single_column_text_and_turkish_characters() -> None:
    result = extract_text(make_pdf([single_column_cv()]))
    assert result.backend == "pdfplumber"
    assert result.page_count == 1
    assert result.multi_column_pages == 0
    assert not result.needs_ocr
    assert "Python ve FastAPI ile REST API uç noktaları geliştirdim." in result.text
    assert "İngilizce: B2 · Ağ güvenliği, ışık, çiçek, öğrenci, şirket" in result.text
    # Satır sırası korunur
    assert result.text.index("DENEYİM") < result.text.index("YETENEKLER")


def test_two_column_layout_is_read_column_by_column() -> None:
    result = extract_text(make_pdf([two_column_cv()]))
    assert result.multi_column_pages == 1
    text = result.text
    # Başlık önce, sonra sol sütun bütün halinde, sonra sağ sütun.
    assert text.index("[AD SOYAD]") < text.index("İLETİŞİM") < text.index("PROFİL")
    left = text[text.index("İLETİŞİM") : text.index("PROFİL")]
    assert "Python\nDocker\nPostgreSQL\nReact" in left
    assert "Kubernetes" not in left
    # Sağ sütun cümleleri sol sütun kelimeleriyle karışmaz.
    assert "Mikroservis mimarisinde ödeme servisini geliştirdim." in text
    assert "Kubernetes üzerinde dağıtım süreçlerini yönettim." in text


def test_table_rows_are_not_split_into_columns() -> None:
    result = extract_text(make_pdf([table_cv()]))
    assert result.multi_column_pages == 0
    assert "Python Orta" in result.text
    assert "Takım çalışması İleri" in result.text


def test_multiple_pages_are_joined_in_order() -> None:
    page2 = [(56, 72, "REFERANSLAR", 11.0), (56, 90, "İstek üzerine verilir.", 11.0)]
    result = extract_text(make_pdf([single_column_cv(), page2]))
    assert result.page_count == 2
    assert result.text.index("YETENEKLER") < result.text.index("REFERANSLAR")


def test_scanned_pdf_needs_ocr() -> None:
    result = extract_text(make_pdf([[]], image_only=True))
    assert result.text == ""
    assert result.needs_ocr


def test_short_text_needs_ocr() -> None:
    result = extract_text(make_pdf([[(56, 72, "[AD SOYAD]", 11.0)]]))
    assert result.needs_ocr


def _error(data: bytes, **kwargs: Any) -> PdfError:
    with pytest.raises(PdfError) as info:
        extract_text(data, **kwargs)
    return info.value


def test_encrypted_pdf() -> None:
    err = _error(make_pdf([single_column_cv()], encrypt=True))
    assert (err.code, err.reason) == (ErrorCode.PDF_UNREADABLE, Reason.ENCRYPTED)
    assert "şifreli" in err.message


@pytest.mark.parametrize(
    "data",
    [b"%PDF-1.7\n bozuk icerik \x00\x01\x02", b"%PDF-1.4\n" + b"0" * 2000],
    ids=["bozuk", "govdesiz"],
)
def test_corrupt_pdf(data: bytes) -> None:
    err = _error(data)
    assert (err.code, err.reason) == (ErrorCode.PDF_UNREADABLE, Reason.CORRUPT)


def test_truncated_pdf_is_unreadable_or_partially_read() -> None:
    data = make_pdf([single_column_cv()])
    try:
        result = extract_text(data[: len(data) // 3])
    except PdfError as err:
        assert err.code == ErrorCode.PDF_UNREADABLE
    else:
        # PDF kütüphaneleri yarım dosyayı onarabilir; o zaman hata değil, (eksik) sonuç döner.
        assert result.page_count >= 0


@pytest.mark.parametrize("data", [b"", b"PK\x03\x04 zip dosyasi", b"Merhaba"], ids=["bos", "zip", "metin"])
def test_not_a_pdf(data: bytes) -> None:
    err = _error(data)
    assert (err.code, err.reason) == (ErrorCode.PDF_UNREADABLE, Reason.NOT_PDF)


def test_too_large_file() -> None:
    err = _error(b"%PDF-1.7\n" + b"0" * 100, max_bytes=50)
    assert (err.code, err.reason) == (ErrorCode.PDF_TOO_LARGE, Reason.TOO_MANY_BYTES)


def test_too_many_pages() -> None:
    page = [(56, 72, "Sayfa", 11.0)]
    err = _error(make_pdf([page] * 6))
    assert (err.code, err.reason) == (ErrorCode.PDF_TOO_LARGE, Reason.TOO_MANY_PAGES)
    assert extract_text(make_pdf([page] * 5)).page_count == 5


def test_falls_back_to_pymupdf_when_pdfplumber_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(_: bytes) -> None:
        raise RuntimeError("pdfplumber çöktü")

    monkeypatch.setattr(backends_module, "pdfplumber_pages", broken)
    result = extract_text(make_pdf([single_column_cv()]))
    assert result.backend == "pymupdf"
    assert "Python ve FastAPI ile REST API uç noktaları geliştirdim." in result.text


def test_both_backends_give_same_text() -> None:
    data = make_pdf([two_column_cv()])
    from parsing.extract import _build

    plumber = _build(backends_module.pdfplumber_pages(data), "pdfplumber")
    mupdf = _build(backends_module.pymupdf_pages(data), "pymupdf")
    assert plumber.text.split() == mupdf.text.split()
    assert plumber.multi_column_pages == mupdf.multi_column_pages == 1


def test_nothing_is_written_to_disk(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    data = make_pdf([two_column_cv()])
    real_open = builtins.open

    def guarded_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in "wax+"):
            raise AssertionError(f"Diske yazma denemesi: {file!r} ({mode})")
        return real_open(file, mode, *args, **kwargs)

    def no_temp(*_: Any, **__: Any) -> Any:
        raise AssertionError("Geçici dosya oluşturma denemesi")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(os, "open", no_temp)
    for name in ("NamedTemporaryFile", "TemporaryFile", "mkstemp", "SpooledTemporaryFile"):
        monkeypatch.setattr(tempfile, name, no_temp)

    result = extract_text(data)
    assert "Kubernetes" in result.text
