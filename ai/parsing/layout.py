"""Sayfadaki kelimeleri okuma sırasına dizer; iki sütunlu CV düzenini algılar.

Her iki PDF kütüphanesi de (pdfplumber, PyMuPDF) kelimeleri koordinatlarıyla verir; düzen
mantığı burada tek yerde olduğu için iki yol da aynı sonucu üretir.

Sütun algılama:
1. Sayfanın orta bölgesinde (%25-%75) hiçbir kelimenin (ya da sadece başlık gibi çok az
   kelimenin) kesmediği dikey bir boşluk aranır.
2. Boşluğun iki yanında da kelimelerin en az %20'si olmalı.
3. Sağ ve sol satırların çoğu aynı yükseklikteyse bu sütun değil tablodur ("Python | İleri");
   tablo satır satır okunur, bölünmez.
Sütun varsa önce boşluğu kesen üst başlık (ad, iletişim), sonra sol, sonra sağ sütun okunur.
"""

from __future__ import annotations

import re
import statistics
import unicodedata
from dataclasses import dataclass

GUTTER_SEARCH = (0.25, 0.75)  # sayfa genişliğinin bu aralığında boşluk aranır
MIN_GUTTER_WIDTH = 10.0  # pt
MAX_CROSSING_RATIO = 0.05  # boşluğu kesebilecek kelime oranı (başlık satırları için)
MIN_SIDE_RATIO = 0.20  # her sütunda olması gereken en az kelime oranı
MAX_ALIGNED_RATIO = 0.70  # sağ satırların bu oranından fazlası soldakilerle hizalıysa tablo sayılır
ALIGN_TOLERANCE = 0.15  # hizalı sayılmak için taban çizgisi farkı (kelime yüksekliğinin oranı)
HEADER_ZONE = 0.35  # başlık sadece sayfanın üst kısmında aranır
MIN_WORDS_FOR_COLUMNS = 20


@dataclass(frozen=True)
class Word:
    x0: float
    top: float
    x1: float
    bottom: float
    text: str

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass(frozen=True)
class Page:
    width: float
    height: float
    words: list[Word]


def page_text(page: Page) -> tuple[str, bool]:
    """Sayfa metni ve sayfada sütun algılanıp algılanmadığı."""
    regions = split_columns(page)
    text = "\n\n".join(t for t in (lines_to_text(r) for r in regions) if t)
    return text, len(regions) > 1


def split_columns(page: Page) -> list[list[Word]]:
    words = page.words
    gutter = find_gutter(words, page.width)
    if gutter is None:
        return [words]

    spanning = [w for w in words if w.x0 < gutter < w.x1]
    header_bottom = max((w.bottom for w in spanning if w.bottom <= page.height * HEADER_ZONE), default=0.0)
    header = [w for w in words if w.bottom <= header_bottom]
    body = [w for w in words if w.bottom > header_bottom]
    left = [w for w in body if w.center_x < gutter]
    right = [w for w in body if w.center_x >= gutter]
    return [region for region in (header, left, right) if region]


def find_gutter(words: list[Word], width: float) -> float | None:
    """İki sütun arasındaki boşluğun x koordinatı; sütun yoksa None."""
    if len(words) < MIN_WORDS_FOR_COLUMNS or width <= 0:
        return None
    allowed = max(2, int(len(words) * MAX_CROSSING_RATIO))
    lo, hi = width * GUTTER_SEARCH[0], width * GUTTER_SEARCH[1]

    runs: list[tuple[float, float]] = []
    run_start: float | None = None
    x = lo
    while x <= hi:
        crossing = sum(1 for w in words if w.x0 < x < w.x1)
        if crossing <= allowed:
            run_start = x if run_start is None else run_start
        elif run_start is not None:
            runs.append((run_start, x))
            run_start = None
        x += 1.0
    if run_start is not None:
        runs.append((run_start, hi))

    candidates = [(end - start, (start + end) / 2) for start, end in runs if end - start >= MIN_GUTTER_WIDTH]
    for _, center in sorted(candidates, reverse=True):
        if _is_two_columns(words, center):
            return center
    return None


def _is_two_columns(words: list[Word], gutter: float) -> bool:
    left = [w for w in words if w.x1 <= gutter]
    right = [w for w in words if w.x0 >= gutter]
    if min(len(left), len(right)) < len(words) * MIN_SIDE_RATIO:
        return False
    # Tablo satırları aynı taban çizgisine dizilir; sütunlarda ise satırlar ancak tesadüfen yakın düşer.
    # Bu yüzden tolerans dar tutulur (kütüphaneler kelime kutusu yüksekliğini farklı hesaplar).
    left_lines = _line_bottoms(left)
    right_lines = _line_bottoms(right)
    tol = statistics.median(w.height for w in words) * ALIGN_TOLERANCE
    aligned = sum(1 for y in right_lines if any(abs(y - ly) <= tol for ly in left_lines))
    return aligned / len(right_lines) <= MAX_ALIGNED_RATIO


def _line_bottoms(words: list[Word]) -> list[float]:
    return [statistics.fmean(w.bottom for w in line) for line in group_lines(words)]


def group_lines(words: list[Word]) -> list[list[Word]]:
    """Kelimeleri satırlara ayırır (dikey merkezleri yakın olanlar aynı satır), soldan sağa sıralı."""
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.center_y, w.x0)):
        if lines:
            current = lines[-1]
            ref = statistics.fmean(w.center_y for w in current)
            limit = max(statistics.fmean(w.height for w in current), word.height) * 0.5
            if abs(word.center_y - ref) <= limit:
                current.append(word)
                continue
        lines.append([word])
    return [sorted(line, key=lambda w: w.x0) for line in lines]


def lines_to_text(words: list[Word]) -> str:
    lines = group_lines(words)
    if not lines:
        return ""
    line_height = statistics.median(statistics.fmean(w.height for w in line) for line in lines)
    out: list[str] = []
    prev_bottom: float | None = None
    for line in lines:
        top = min(w.top for w in line)
        if prev_bottom is not None and top - prev_bottom > line_height * 0.8:
            out.append("")  # paragraf/bölüm arası
        out.append(" ".join(w.text for w in line))
        prev_bottom = max(w.bottom for w in line)
    return "\n".join(out)


_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def normalize(text: str) -> str:
    """Bağlı harfleri (ﬁ), birleşik noktalı İ'yi ve gizli tireleri düzeltir; boşlukları sadeleştirir."""
    text = unicodedata.normalize("NFKC", text).replace("­", "")
    text = "\n".join(_SPACES.sub(" ", line).strip() for line in text.splitlines())
    return _BLANK_LINES.sub("\n\n", text).strip()
