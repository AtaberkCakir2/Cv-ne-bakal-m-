"""CV metnindeki kişisel verileri LLM'e gitmeden önce maskeler (T-030, karar #9).

Kullanım:
    result = mask(text, "tr")       # MaskResult(text=..., counts={Kind.EMAIL: 1, ...})
    masked = mask_text(text, "tr")  # sadece metin
    posting = mask_posting(text, "tr")  # ilan metni; scraper/etl/pipeline.py NameMasker imzasıyla uyumlu

Maskelenen metin LLM'e, maskelenmemiş metin hiçbir yere gitmez. `counts` loglanabilir (kişisel veri içermez);
metnin kendisi loglanmaz.

Maskeleme idempotenttir: metindeki etiketlere ("[AD SOYAD]" …) dokunulmaz, maskelenmiş metin tekrar maskelenince
değişmez (ilanlar her gece yeniden işlenir).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pii.kinds import PLACEHOLDERS, PRIORITY, Kind
from pii.names import Lang, NameDetector, find_names
from pii.patterns import Span, find_structured


@dataclass(frozen=True)
class MaskResult:
    text: str
    counts: dict[Kind, int] = field(default_factory=dict)


# İlanda kişiye ulaştıran veriler maskelenir; başvuru bağlantısı, şirket adresi ve tarihler iş bilgisidir, kalır.
POSTING_KINDS = frozenset({Kind.NAME, Kind.EMAIL, Kind.PHONE, Kind.TCKN, Kind.IBAN})


_PLACEHOLDER = re.compile("|".join(re.escape(p) for p in PLACEHOLDERS.values()))
# Etiketin yerine aynı uzunlukta, harf/rakam/boşluk olmayan karakter (Unicode özel kullanım alanı): konumlar değişmez,
# hiçbir kural (etiketli alan "name: …", ad yayma, NER) etiketin kelimelerini ad sanmaz.
_NEUTRAL = ""


def mask(text: str, lang: Lang = "tr", *, detector: NameDetector | None = None) -> MaskResult:
    scan, kept = _protect(text)
    return _apply(text, _merge(_outside(text, find_structured(scan) + find_names(scan, lang, detector), kept)))


def mask_text(text: str, lang: Lang = "tr") -> str:
    return mask(text, lang).text


def mask_posting(text: str, lang: Lang = "tr", *, detector: NameDetector | None = None) -> str:
    """İş ilanı metni için: ad, e-posta, telefon, TCKN, IBAN. CV'deki başlık kuralı uygulanmaz (ilk satır ilan
    başlığıdır, ad değil); URL, adres ve tarih maskelenmez."""
    scan, kept = _protect(text)
    structured = [s for s in find_structured(scan) if s.kind in POSTING_KINDS]
    names = find_names(scan, lang, detector, header=False, strict_honorifics=True)
    return _apply(text, _merge(_outside(text, structured + names, kept))).text


def _protect(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Etiketleri nötr karakterlerle örter; örtülen aralıkları döndürür."""
    kept = [(m.start(), m.end()) for m in _PLACEHOLDER.finditer(text)]
    return _PLACEHOLDER.sub(lambda m: _NEUTRAL * len(m.group()), text), kept


def _outside(text: str, spans: list[Span], kept: list[tuple[int, int]]) -> list[Span]:
    """Bulguları etiketlerin dışında kalan parçalarına böler; harf veya rakam içermeyen parça atılır
    ("name: [AD SOYAD]" etiketli alanı yeniden maskelenmez)."""
    if not kept:
        return spans
    out: list[Span] = []
    for span in spans:
        start = span.start
        for k_start, k_end in kept:
            if k_end <= start or k_start >= span.end:
                continue
            out.append(Span(start, k_start, span.kind))
            start = k_end
        out.append(Span(start, span.end, span.kind))
    return [s for s in out if any(c.isalnum() for c in text[s.start : s.end])]


def _apply(text: str, spans: list[Span]) -> MaskResult:
    counts: dict[Kind, int] = {}
    parts: list[str] = []
    last = 0
    for span in spans:
        parts.append(text[last : span.start])
        parts.append(PLACEHOLDERS[span.kind])
        counts[span.kind] = counts.get(span.kind, 0) + 1
        last = span.end
    parts.append(text[last:])
    return MaskResult("".join(parts), counts)


def _merge(spans: list[Span]) -> list[Span]:
    """Çakışan veya iç içe bulguları birleştirir; birleşimin türü önceliği en yüksek olanınkidir."""
    merged: list[Span] = []
    for span in sorted(spans, key=lambda s: (s.start, -s.end)):
        if merged and span.start < merged[-1].end:
            prev = merged[-1]
            kind = max(prev.kind, span.kind, key=lambda k: PRIORITY[k])
            merged[-1] = Span(prev.start, max(prev.end, span.end), kind)
        else:
            merged.append(span)
    return merged
