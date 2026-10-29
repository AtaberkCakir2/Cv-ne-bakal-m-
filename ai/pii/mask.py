"""CV metnindeki kişisel verileri LLM'e gitmeden önce maskeler (T-030, karar #9).

Kullanım:
    result = mask(text, "tr")       # MaskResult(text=..., counts={Kind.EMAIL: 1, ...})
    masked = mask_text(text, "tr")  # sadece metin; scraper/etl/pipeline.py NameMasker imzasıyla uyumlu

Maskelenen metin LLM'e, maskelenmemiş metin hiçbir yere gitmez. `counts` loglanabilir (kişisel veri içermez);
metnin kendisi loglanmaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pii.kinds import PLACEHOLDERS, PRIORITY, Kind
from pii.names import Lang, NameDetector, find_names
from pii.patterns import Span, find_structured


@dataclass(frozen=True)
class MaskResult:
    text: str
    counts: dict[Kind, int] = field(default_factory=dict)


def mask(text: str, lang: Lang = "tr", *, detector: NameDetector | None = None) -> MaskResult:
    spans = _merge(find_structured(text) + find_names(text, lang, detector))
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


def mask_text(text: str, lang: Lang = "tr") -> str:
    return mask(text, lang).text


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
