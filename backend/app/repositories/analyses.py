"""Analiz kayıtları — GEÇİCİ bellek içi depo.

Ataberk'in `analyses` tablosu ve modelleri (T-012) hazır olunca aynı arayüzle PostgreSQL deposu
yazılacak. Burada sadece veritabanında da tutulacak alanlar var: CV içeriği YOK (karar #9).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass
class AnalysisRecord:
    id: uuid.UUID
    target_role_id: int
    cv_sha256: str
    cv_pages: int
    status: str = "queued"
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AnalysisRepository(Protocol):
    def add(self, record: AnalysisRecord) -> None: ...
    def get(self, analysis_id: uuid.UUID) -> AnalysisRecord | None: ...


class InMemoryAnalysisRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, AnalysisRecord] = {}

    def add(self, record: AnalysisRecord) -> None:
        self._items[record.id] = record

    def get(self, analysis_id: uuid.UUID) -> AnalysisRecord | None:
        return self._items.get(analysis_id)
