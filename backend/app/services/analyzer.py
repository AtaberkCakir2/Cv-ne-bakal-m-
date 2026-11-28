"""Analiz adımının arayüzü. Gerçek akış (PDF, maskeleme, çıkarım, eşleştirme, öneri) `AiAnalyzer` ile ai/pipeline'dan
gelir (T-057); ai paketi sadece analiz işçisi imajında kurulu (ai/Dockerfile, #163).

AI modülü sonucu sözleşme biçiminde (contracts/analysis_result.schema.json) verir; `output_from_result` bunu
`AnalysisOutput`'a çevirir. Yetkinlik adlarının taksonomiyle eşlenmesi ve kaynakların doğrulanması veritabanına
yazarken yapılır (`analysis_runner`).
"""

import json
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from celery.exceptions import SoftTimeLimitExceeded

from app.core.config import Settings
from app.db.enums import AnalysisErrorCode

# contracts/examples/analysis_result.example.json'ın kopyası; aynılığını tests/test_dev_example.py denetler.
EXAMPLE_RESULT = Path(__file__).resolve().parents[1] / "dev" / "example_result.json"

logger = logging.getLogger(__name__)


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


Embed = Callable[[Sequence[str]], list[list[float]]]
_CONNECT_TIMEOUT_S = 10


def _psycopg_url(url: str) -> str:
    """SQLAlchemy adresini (postgresql+psycopg://) psycopg'nin anladığı biçime çevirir."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


class AiAnalyzer:
    """ai/pipeline.analyze_cv'yi çağırır. CV baytları sadece bellekte işlenir; veritabanına salt okunur bağlanılır.

    Ollama adresi ve modeli pipeline tarafından doğrudan süreç ortamından okunur (OLLAMA_URL, OLLAMA_MODEL; Settings
    veya .env dosyası değil): işçi servisinde ortam değişkeni olarak verilmeli. Gömme modeli ilk analizde bir kez
    yüklenir, süresi analizin bütçesinden düşülür; yüklenemezse o süreç boyunca anlamsal eşleşme olmadan devam edilir
    (taksonomideki adlar yine eşleşir).

    `LLM_TIMEOUT` kodu pipeline'ın kendi bütçesi dolduğunda gelir ve kalıcı sayılır (tekrar denemek yine aşar).
    """

    def __init__(self, database_url: str, *, embed: Embed | None = None, load_embed: bool = True) -> None:
        self.database_url = _psycopg_url(database_url)
        self._embed = embed
        self._load_embed = load_embed and embed is None

    def _encoder(self) -> Embed | None:
        if self._load_embed:
            self._load_embed = False
            try:
                from embedding import default_encoder  # type: ignore[import-not-found]  # noqa: PLC0415

                self._embed = default_encoder()
            except SoftTimeLimitExceeded:  # görevin süresi doldu: yutulmamalı, sonraki analiz yeniden dener
                self._load_embed = True
                raise
            except Exception as exc:  # torch/model yoksa analiz yine çalışsın
                logger.warning("embedding_unavailable: %s", type(exc).__name__)
        return self._embed

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        import psycopg  # noqa: PLC0415
        from pipeline import BUDGET_SECONDS, AnalysisError, analyze_cv  # type: ignore[import-not-found]  # noqa: PLC0415

        started = time.monotonic()
        embed = self._encoder()
        try:
            with psycopg.connect(
                self.database_url,
                autocommit=True,
                connect_timeout=_CONNECT_TIMEOUT_S,
                # PgBouncer'a geçilirse bu başlangıç parametresi reddedilebilir; o zaman SET SESSION ... READ ONLY.
                options="-c default_transaction_read_only=on",
            ) as conn:
                budget = BUDGET_SECONDS - (time.monotonic() - started)  # model yükleme süresi düşülür
                out = analyze_cv(pdf, role_id=target_role_id, conn=conn, embed=embed, budget_s=budget)
        except AnalysisError as exc:
            code = exc.code
        else:
            return output_from_result(out.result)
        # except dışında: AnalysisFailed özgün hatayı zincirlemesin (mesajında CV parçası olmasın).
        try:
            mapped = AnalysisErrorCode(code)
        except ValueError:
            mapped = AnalysisErrorCode.INTERNAL
        raise AnalysisFailed(mapped)


def pipeline_available() -> bool:
    """ai/pipeline import edilebiliyor mu (adı aynı başka bir paket veya eksik bağımlılık yanlış seçim yaptırmasın)."""
    try:
        from pipeline import analyze_cv  # type: ignore[import-not-found, unused-ignore]  # noqa: F401, PLC0415
    except ImportError:
        return False
    return True


def build_analyzer(settings: Settings) -> Analyzer:
    """AI paketi kuruluysa (işçi imajı) gerçek akış; değilse local/test'te örnek sonuç, başka ortamda hata."""
    analyzer: Analyzer
    if pipeline_available():
        analyzer = AiAnalyzer(settings.database_url)
    else:
        analyzer = ExampleAnalyzer() if settings.is_explicit_dev else UnavailableAnalyzer()
    logger.info("analyzer=%s", type(analyzer).__name__)
    return analyzer
