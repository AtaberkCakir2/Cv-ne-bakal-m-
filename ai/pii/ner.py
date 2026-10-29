"""Yerel Türkçe NER modeliyle ad tespiti (T-030, karar önerisi: BERTurk NER).

Model: akdeniz27/bert-base-turkish-cased-ner (MIT, ~420 MB, CPU'da CV başına ~170 ms, ~760 MB bellek).
Model bilgisayarda çalışır; metin dışarı gönderilmez (karar #1). Kurallarla (`pii.names`) birlikte kullanılır:

    from pii import mask
    from pii.ner import default_detector

    result = mask(cv_text, "tr", detector=default_detector())  # model kurulu değilse sadece kurallar

İki düzeltme modelin ham çıktısına göre hatayı azaltır (deneyde gerçek yanlış pozitif 13 → 3):
1. Model kelimeleri parçalara böler ("Post" + "##man"); bulunan varlık kapsadığı tam kelimelere genişletilir.
2. Yetkinlik taksonomisindeki kelimeler (Flutter, Kafka, Postman…) ad sayılmaz.

`transformers` ve `torch` isteğe bağlıdır: `pip install -e ".[ner]"`. Yoksa `default_detector()` None döner.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable
from functools import cache
from typing import Any

from pii.names import Lang, NameDetector
from pii.taxonomy import skill_words

log = logging.getLogger(__name__)

MODEL_ID = "akdeniz27/bert-base-turkish-cased-ner"
# Sabit sürüm: model deposu değişse de sonuçlar aynı kalır. Değiştirirken T-030 ölçümünü tekrarla.
MODEL_REVISION = "99995f7d2be4b3a28c74f0d36ee97f8c04ee0571"
MIN_SCORE = 0.5
# BERT en fazla 512 parça görür; metin satır sınırından bu uzunlukta parçalara bölünür.
CHUNK_CHARS = 1000
PERSON_LABELS = frozenset({"PER", "PERSON"})

# transformers pipeline'ının ihtiyacımız olan kısmı: metin → [{"entity_group", "score", "start", "end"}, ...]
Pipeline = Callable[[str], list[dict[str, Any]]]

_WORD = re.compile(r"\w+")


class BertNerDetector:
    """`pii.names.NameDetector` uyumlu ad dedektörü. Model ilk çağrıda yüklenir."""

    def __init__(
        self,
        skip_words: Iterable[str] = (),
        *,
        pipe: Pipeline | None = None,
        model: str = MODEL_ID,
        revision: str = MODEL_REVISION,
        min_score: float = MIN_SCORE,
    ) -> None:
        self._skip = frozenset(w.lower() for w in skip_words)
        self._pipe = pipe
        self._model = model
        self._revision = revision
        self._min_score = min_score

    def __call__(self, text: str, lang: Lang) -> list[tuple[int, int]]:
        spans: list[tuple[int, int]] = []
        for offset, chunk in _chunks(text):
            for ent in self._pipeline()(chunk):
                if ent["entity_group"] not in PERSON_LABELS or float(ent["score"]) < self._min_score:
                    continue
                start, end = offset + int(ent["start"]), offset + int(ent["end"])
                while start > 0 and text[start - 1].isalnum():
                    start -= 1
                while end < len(text) and text[end].isalnum():
                    end += 1
                for m in _WORD.finditer(text, start, end):
                    if m.group().lower() not in self._skip:
                        spans.append((m.start(), m.end()))
        return spans

    def _pipeline(self) -> Pipeline:
        if self._pipe is None:
            from transformers import pipeline

            # aggregation_strategy="first": bir kelimenin parçaları ilk parçanın etiketini alır.
            self._pipe = pipeline(
                "token-classification",
                model=self._model,
                revision=self._revision,
                aggregation_strategy="first",
                device=-1,
            )
        return self._pipe


def _chunks(text: str) -> list[tuple[int, str]]:
    """Metni satır sınırlarından en fazla CHUNK_CHARS uzunluğunda parçalara böler (başlangıç konumuyla)."""
    out: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + CHUNK_CHARS)
        if end < len(text):
            cut = text.rfind("\n", start, end)
            if cut > start:
                end = cut + 1
        out.append((start, text[start:end]))
        start = end
    return out


@cache
def default_detector() -> NameDetector | None:
    """Kurulu ise BERTurk dedektörü (taksonomi filtresiyle), değilse None (sadece kurallar)."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        log.warning("transformers/torch kurulu değil; ad tespiti sadece kurallarla yapılacak")
        return None
    return BertNerDetector(skill_words())
