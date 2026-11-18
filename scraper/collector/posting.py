"""Kaynaktan bağımsız ilan kaydı. Alanlar job_postings tablosuyla birebir.

Normalizasyon (pozisyon eşleme, yetkinlik etiketleme) T-033'te yapılır.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from collector.clean import Lang, content_hash


@dataclass(frozen=True)
class SourceInfo:
    name: str  # contracts: source
    type: Literal["api", "scrape", "dataset"]
    base_url: str
    rate_limit_sec: float


@dataclass(frozen=True)
class Posting:
    external_id: str
    title_raw: str
    description_clean: str  # HTML temizlenmiş ve kişisel veri maskelenmiş metin
    language: Lang
    url: str | None = None
    company: str | None = None
    location: str | None = None
    posted_at: date | None = None
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_hash", content_hash(self.description_clean))
