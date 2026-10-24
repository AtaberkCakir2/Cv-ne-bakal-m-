"""Analiz kuyruğu arayüzü.

Gerçek kuyruk (Celery + Redis) T-039'da gelecek. O zamana kadar `ExampleResultQueue`, işi hemen
"tamamlanmış" sayar ve sonuç olarak contracts/examples/analysis_result.example.json verisini döner;
böylece web ve mobil ekranlar AI modülünü beklemeden geliştirilebilir (karar #5).

T-039 notu: PDF baytları kuyruğa (Redis) yazılacaksa, Redis'in AOF/RDB kalıcılığı bu veriyi diske
yazar. CV içeriği için ayrı, kalıcılığı kapalı bir Redis veritabanı/örneği kullanılmalı ve iş biter
bitmez silinmeli (karar #9).
"""

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from app.repositories.analyses import AnalysisRecord

# contracts/examples/analysis_result.example.json'ın kopyası: Docker imajı sadece backend/ klasöründen
# derlendiği için contracts/ imajda yok. İki dosyanın aynı kaldığını tests/test_dev_example.py denetler.
EXAMPLE_RESULT = Path(__file__).resolve().parents[1] / "dev" / "example_result.json"


class AnalysisQueue(Protocol):
    def enqueue(self, record: AnalysisRecord, pdf: bytes) -> None: ...


@lru_cache
def _example() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8"))
    return data


class ExampleResultQueue:
    """Geliştirme için sahte kuyruk: PDF'i kullanmaz, saklamaz; örnek sonucu yazar."""

    def enqueue(self, record: AnalysisRecord, pdf: bytes) -> None:
        del pdf  # bilinçli olarak kullanılmıyor ve tutulmuyor
        now = datetime.now(UTC).isoformat()
        result = dict(_example())
        result.update(
            analysis_id=str(record.id),
            status="done",
            created_at=record.created_at.isoformat(),
            completed_at=now,
        )
        record.status = "done"
        record.result = result
