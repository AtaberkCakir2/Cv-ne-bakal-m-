"""Analiz adımının arayüzü. Gerçek akış (PDF, maskeleme, çıkarım, eşleştirme, öneri) T-057'de buraya bağlanır."""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from app.core.config import Settings
from app.db.enums import AnalysisErrorCode

# contracts/examples/analysis_result.example.json'ın kopyası; aynılığını tests/test_dev_example.py denetler.
EXAMPLE_RESULT = Path(__file__).resolve().parents[1] / "dev" / "example_result.json"


@dataclass(frozen=True)
class AnalysisOutput:
    match_score: Decimal
    postings_analyzed: int
    model_name: str
    prompt_version: str


class AnalysisFailed(Exception):
    """Tekrar denemenin işe yaramayacağı hata (ör. metin bulunamadı). Mesaj taşımaz: CV parçası sızmasın."""

    def __init__(self, code: AnalysisErrorCode) -> None:
        super().__init__(code.value)
        self.code = code


class Analyzer(Protocol):
    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput: ...


class ExampleAnalyzer:
    """Sadece local/test: AI modülünü beklemeden akışı denemek için sözleşmedeki örnek değerleri döner (karar #5)."""

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        del pdf, target_role_id
        data = json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8"))
        return AnalysisOutput(
            match_score=Decimal(str(data["match_score"])),
            postings_analyzed=data["postings_analyzed"],
            model_name=data["model"]["name"],
            prompt_version=data["model"]["prompt_version"],
        )


class UnavailableAnalyzer:
    """Gerçek akış bağlanana kadar local/test dışında: kullanıcıya sahte sonuç gösterilmez, analiz başarısız olur."""

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        del pdf, target_role_id
        raise AnalysisFailed(AnalysisErrorCode.INTERNAL)


def build_analyzer(settings: Settings) -> Analyzer:
    return ExampleAnalyzer() if settings.is_explicit_dev else UnavailableAnalyzer()
