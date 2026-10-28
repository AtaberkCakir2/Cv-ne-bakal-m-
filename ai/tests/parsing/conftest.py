"""Testler için bellekte PDF üretir. Gerçek CV kullanılmaz; tüm içerik uydurmadır."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import cache

import pymupdf
import pytest

# (x, y, metin, font boyutu)
Item = tuple[float, float, str, float]
MakePdf = Callable[..., bytes]


@cache
def _font_buffer() -> bytes:
    # PyMuPDF'in yerleşik Unicode fontu: Türkçe karakterler (ş, ğ, ı, İ) doğru yazılır.
    return bytes(pymupdf.Font("cjk").buffer)


def make_pdf(pages: Sequence[Sequence[Item]], *, encrypt: bool = False, image_only: bool = False) -> bytes:
    doc = pymupdf.open()
    for items in pages:
        page = doc.new_page(width=595, height=842)  # A4
        if image_only:
            # Taranmış CV benzeri: sadece görüntü, metin katmanı yok.
            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 100), False)
            pix.clear_with(200)
            page.insert_image(pymupdf.Rect(50, 50, 450, 250), pixmap=pix)
            continue
        page.insert_font(fontname="F0", fontbuffer=_font_buffer())
        for x, y, text, size in items:
            page.insert_text((x, y), text, fontname="F0", fontsize=size)
    doc.subset_fonts()
    options: dict[str, object] = {"garbage": 3, "deflate": True}
    if encrypt:
        options.update(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="gizli", owner_pw="sahip")  # type: ignore[attr-defined]
    data = doc.tobytes(**options)
    doc.close()
    return bytes(data)


def single_column_cv() -> list[Item]:
    lines = [
        "[AD SOYAD]",
        "Bilgisayar Mühendisliği öğrencisi · İstanbul",
        "",
        "DENEYİM",
        "Stajyer Yazılım Geliştirici — Haziran 2025 – Eylül 2025",
        "Python ve FastAPI ile REST API uç noktaları geliştirdim.",
        "PostgreSQL sorgularını optimize ettim; servisi Docker ile paketledik.",
        "",
        "YETENEKLER",
        "Python (ileri düzey), Java (orta), SQL, Git, Linux",
        "İngilizce: B2 · Ağ güvenliği, ışık, çiçek, öğrenci, şirket",
    ]
    return [(56, 72 + i * 18, line, 11) for i, line in enumerate(lines) if line]


def two_column_cv() -> list[Item]:
    items: list[Item] = [(56, 60, "[AD SOYAD] — Yazılım Geliştirici · [E-POSTA] · [TELEFON] · [ŞEHİR]", 12)]
    left = ["İLETİŞİM", "[ŞEHİR]", "YETENEKLER", "Python", "Docker", "PostgreSQL", "React", "DİLLER", "İngilizce C1"]
    right = [
        "PROFİL",
        "Üç yıllık deneyime sahip backend geliştiricisiyim.",
        "DENEYİM",
        "Backend Developer — [Şirket] (2023 – halen)",
        "Mikroservis mimarisinde ödeme servisini geliştirdim.",
        "Kubernetes üzerinde dağıtım süreçlerini yönettim.",
        "EĞİTİM",
        "Bilgisayar Mühendisliği — [Üniversite] (2018 – 2022)",
    ]
    # Sol sütun 13 pt, sağ sütun 21 pt aralıkla: satırlar hizalı değil (tablo gibi değil).
    items += [(40, 110 + i * 13, text, 10) for i, text in enumerate(left)]
    items += [(230, 112 + i * 21, text, 10) for i, text in enumerate(right)]
    return items


def table_cv() -> list[Item]:
    rows = [("Yetkinlik", "Seviye"), ("Python", "Orta"), ("SQL", "İleri"), ("R", "Temel"), ("Excel", "İleri")]
    rows += [("Power BI", "Orta"), ("Tableau", "Temel"), ("İletişim", "İleri"), ("Takım çalışması", "İleri")]
    items: list[Item] = []
    for i, (skill, level) in enumerate(rows):
        y = 100 + i * 18
        items += [(56, y, skill, 11), (340, y, level, 11)]
    return items


@pytest.fixture(name="make_pdf")
def make_pdf_fixture() -> MakePdf:
    return make_pdf
