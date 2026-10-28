"""Eşleme için metin katlama (büyük/küçük harf ve ayraç farklarını yok sayma)."""

import re

from collector.clean import Lang

_SEPARATORS = re.compile(r"[-_/]+")
_SPACES = re.compile(r"\s+")


def fold(text: str, lang: Lang = "en") -> str:
    """Türkçe kurallı küçük harf.

    str.lower() "İ"yi "i̇" (i + birleşen nokta) yapar ve "İstanbul" hiçbir eş anlamlıyla eşleşmez. Türkçe metinde
    "I" de "ı" olur; İngilizce metinde "I" yine "i" kalır (aksi halde "AI" → "aı"). Türkçe metinde de teknoloji
    adları Latin I ile yazılır ("FastAPI"), bu yüzden eşleyiciler Türkçe metni iki kuralla da dener (`fold_variants`).
    """
    text = text.replace("İ", "i")
    if lang == "tr":
        text = text.replace("I", "ı")
    return text.lower()


def fold_phrase(text: str, lang: Lang = "en") -> str:
    """Başlık eşlemesi için: küçük harf, tire/alt çizgi/eğik çizgi boşluk olur ("Back-end" = "back end")."""
    return _SPACES.sub(" ", _SEPARATORS.sub(" ", fold(text, lang))).strip()


def fold_variants(text: str, lang: Lang) -> list[str]:
    """Türkçe metin için hem Türkçe ("PROGRAMCISI" → "programcısı") hem İngilizce ("FastAPI" → "fastapi") katlama."""
    return [fold(text, "tr"), fold(text, "en")] if lang == "tr" else [fold(text, lang)]
