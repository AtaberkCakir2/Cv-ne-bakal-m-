"""Analiz adımının arayüzü. Gerçek akış (PDF, maskeleme, çıkarım, eşleştirme, öneri) T-057'de buraya bağlanır.

AI modülü sonucu sözleşme biçiminde (contracts/analysis_result.schema.json) verir; `output_from_result` bunu
`AnalysisOutput`'a çevirir. Yetkinlik adlarının taksonomiyle eşlenmesi ve kaynakların doğrulanması veritabanına
yazarken yapılır (`analysis_runner`).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings
from app.db.enums import AnalysisErrorCode

# contracts/examples/analysis_result.example.json'ın kopyası; aynılığını tests/test_dev_example.py denetler.
EXAMPLE_RESULT = Path(__file__).resolve().parents[1] / "dev" / "example_result.json"


@dataclass(frozen=True)
class PresentSkill:
    """contracts: present_skills[]. `verified=False`: taksonomide olmayan, LLM tahmini ad."""

    skill: str
    level: str = "unknown"
    confidence: float | None = None
    verified: bool = True


@dataclass(frozen=True)
class SuggestedResource:
    """contracts: missing_skills[].resources[]; sadece kimlik ve gerekçe saklanır, kaynak bilgisi DB'den okunur."""

    resource_id: int
    reason: str | None = None


@dataclass(frozen=True)
class MissingSkill:
    skill: str
    demand_ratio: float
    priority: int | None = None
    resources: tuple[SuggestedResource, ...] = ()


@dataclass(frozen=True)
class AnalysisOutput:
    match_score: Decimal
    postings_analyzed: int
    model_name: str
    prompt_version: str
    present_skills: tuple[PresentSkill, ...] = ()
    missing_skills: tuple[MissingSkill, ...] = ()


def output_from_result(data: Mapping[str, Any]) -> AnalysisOutput:
    """Sözleşme biçimindeki sonuçtan (AI modülü veya örnek) `AnalysisOutput`. Eksik zorunlu alan: KeyError."""
    return AnalysisOutput(
        match_score=Decimal(str(data["match_score"])),
        postings_analyzed=int(data["postings_analyzed"]),
        model_name=str(data["model"]["name"]),
        prompt_version=str(data["model"]["prompt_version"]),
        present_skills=tuple(
            PresentSkill(
                skill=str(p["skill"]),
                level=str(p.get("level") or "unknown"),
                confidence=None if p.get("confidence") is None else float(p["confidence"]),
                verified=bool(p.get("verified", True)),
            )
            for p in data.get("present_skills") or ()
        ),
        missing_skills=tuple(
            MissingSkill(
                skill=str(m["skill"]),
                demand_ratio=float(m["demand_ratio"]),
                priority=None if m.get("priority") is None else int(m["priority"]),
                resources=tuple(
                    SuggestedResource(resource_id=int(r["resource_id"]), reason=r.get("reason"))
                    for r in m.get("resources") or ()
                ),
            )
            for m in data.get("missing_skills") or ()
        ),
    )


class AnalysisFailed(Exception):
    """Tekrar denemenin işe yaramayacağı hata (ör. metin bulunamadı). Mesaj taşımaz: CV parçası sızmasın."""

    def __init__(self, code: AnalysisErrorCode) -> None:
        super().__init__(code.value)
        self.code = code


class Analyzer(Protocol):
    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput: ...


class ExampleAnalyzer:
    """Sadece local/test: AI modülünü beklemeden akışı denemek için sözleşmedeki örneği döner (karar #5).

    Örnekteki yetkinlikler taksonomide varsa sonuca yazılır; örnek kaynak kimlikleri o yetkinliğe ait değilse atılır.
    """

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        del pdf, target_role_id
        return output_from_result(json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8")))


class UnavailableAnalyzer:
    """Gerçek akış bağlanana kadar local/test dışında: kullanıcıya sahte sonuç gösterilmez, analiz başarısız olur."""

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        del pdf, target_role_id
        raise AnalysisFailed(AnalysisErrorCode.INTERNAL)


def build_analyzer(settings: Settings) -> Analyzer:
    return ExampleAnalyzer() if settings.is_explicit_dev else UnavailableAnalyzer()
