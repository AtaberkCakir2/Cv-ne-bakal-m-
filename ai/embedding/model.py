"""Metin → 384 boyutlu, normalize vektör (T-041).

Model: multilingual-e5-small (docs/mimari.md'deki alternatif; seçim gerekçesi ai/README.md "embedding" ölçümü).
Her metne "query: " öneki eklenir (e5'in benzerlik görevleri için önerdiği biçim). Vektörler birim uzunluktadır;
pgvector'de `<=>` (kosinüs uzaklığı) ile sorgulanır, benzerlik = 1 - uzaklık (docs/veritabani.md).
Model sadece yerelde çalışır; ilk yüklemede Hugging Face'ten indirilir, sonra önbellekten okunur.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
PREFIX = "query: "  # e5 öneki; MiniLM gibi öneksiz model için ""
DIM = 384  # backend/app/db/models/catalog.py EMBEDDING_DIM
BATCH_SIZE = 64

Vector = list[float]


class Encoder(Protocol):
    """Metin listesi → aynı sırada normalize vektörler. Testlerde sahtesi verilir."""

    def __call__(self, texts: Sequence[str]) -> list[Vector]: ...


class SentenceEncoder:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        prefix: str = PREFIX,
        device: str = "cpu",
        batch_size: int = BATCH_SIZE,
    ) -> None:
        from sentence_transformers import SentenceTransformer  # ağır içe aktarma: sadece gerekince

        self.model_name = model_name
        self.prefix = prefix
        self.batch_size = batch_size
        self._model = SentenceTransformer(model_name, device=device)
        dim = self._model.get_embedding_dimension()
        if dim != DIM:
            raise ValueError(f"{model_name} {dim} boyutlu; veritabanı {DIM} bekliyor")

    def __call__(self, texts: Sequence[str]) -> list[Vector]:
        if not texts:
            return []
        out = self._model.encode(
            [self.prefix + t for t in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(x) for x in row] for row in out]


_default: SentenceEncoder | None = None


def default_encoder() -> SentenceEncoder:
    """Süreç başına bir kez yüklenen model (yükleme birkaç saniye sürer)."""
    global _default
    if _default is None:
        _default = SentenceEncoder()
    return _default


def check(vector: Sequence[float]) -> None:
    """Veritabanına yazılacak vektör 384 boyutlu, sonlu ve birim uzunlukta olmalı."""
    if len(vector) != DIM:
        raise ValueError(f"vektör {len(vector)} boyutlu, {DIM} olmalı")
    if not all(math.isfinite(x) for x in vector):
        raise ValueError("vektörde NaN/sonsuz var")
    norm = math.sqrt(sum(x * x for x in vector))
    if abs(norm - 1.0) > 1e-3:
        raise ValueError(f"vektör normalize değil (uzunluk {norm:.4f})")


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """İki normalize vektörün kosinüs benzerliği (pgvector'deki 1 - (a <=> b))."""
    return sum(x * y for x, y in zip(a, b, strict=True))
