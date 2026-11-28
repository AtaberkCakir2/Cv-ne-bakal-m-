"""Kuyruktaki bir analizi çalıştırır, durumunu yazar ve CV baytlarını siler (T-039).

Hata mesajları loglanmaz ve saklanmaz, sadece türü ve kodu: mesaj CV parçası içerebilir (karar #9).
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from celery.exceptions import SoftTimeLimitExceeded
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import AnalysisErrorCode, AnalysisStatus, ConsentType, SkillKind, SkillLevel
from app.db.models import (
    Analysis,
    AnalysisRecommendation,
    AnalysisSkill,
    AnalysisUnverifiedSkill,
    Consent,
    Resource,
    Skill,
)
from app.services.analyzer import AnalysisFailed, AnalysisOutput, Analyzer
from app.services.cv_store import CvStore

logger = logging.getLogger(__name__)

_FINISHED = (AnalysisStatus.DONE, AnalysisStatus.FAILED)


class RetryLater(Exception):
    """Geçici hata: görev bir kez daha denenmeli. CV baytları silinmedi."""


class AnalysisRunner:
    def __init__(self, sessions: sessionmaker[Session], store: CvStore, analyzer: Analyzer) -> None:
        self.sessions = sessions
        self.store = store
        self.analyzer = analyzer

    def run(self, analysis_id: uuid.UUID, *, last_attempt: bool) -> None:
        target_role_id = self._start(analysis_id)
        if target_role_id is None:
            self._forget(analysis_id)
            return
        started = time.monotonic()
        output: AnalysisOutput | None = None
        permanent: AnalysisErrorCode | None = None
        transient: AnalysisErrorCode | None = None
        try:
            pdf = self.store.get(analysis_id)
            if pdf is None:  # süre aşımıyla silinmiş; tekrar denemek işe yaramaz
                raise AnalysisFailed(AnalysisErrorCode.INTERNAL)
            output = self.analyzer.analyze(pdf, target_role_id)
        except AnalysisFailed as exc:
            permanent = exc.code
        except (TimeoutError, SoftTimeLimitExceeded):
            transient = AnalysisErrorCode.LLM_TIMEOUT
        except Exception as exc:  # hangi hata olursa olsun analiz askıda kalmamalı
            logger.warning("analysis_failed: %s", type(exc).__name__)
            transient = AnalysisErrorCode.INTERNAL
        # except dışında: sonraki bir hata özgün hatayı (mesajında CV parçası olabilir) zincirle loga taşımasın.
        if transient is not None:
            self._transient(analysis_id, started, transient, last_attempt)
        else:
            self._finish(analysis_id, started, output=output, error=permanent)

    def _start(self, analysis_id: uuid.UUID) -> int | None:
        """Çalıştırılacak analizin hedef pozisyonunu döner; silinmiş veya bitmişse None."""
        with self.sessions() as session:
            analysis = session.get(Analysis, analysis_id, with_for_update=True)
            if analysis is None or analysis.deleted_at is not None or analysis.status in _FINISHED:
                return None
            # Yüklemeden sonra açık rıza geri alındıysa CV işlenmez (KVKK md. 11): analiz başarısız sayılır.
            if not _has_explicit_consent(session, analysis.user_id):
                analysis.status = AnalysisStatus.FAILED
                analysis.error_code = AnalysisErrorCode.INTERNAL
                analysis.completed_at = datetime.now(UTC)
                session.commit()
                return None
            analysis.status = AnalysisStatus.PROCESSING
            target_role_id = analysis.target_role_id
            session.commit()
            return target_role_id

    def _transient(self, analysis_id: uuid.UUID, started: float, code: AnalysisErrorCode, last_attempt: bool) -> None:
        if last_attempt:
            self._finish(analysis_id, started, error=code)
            return
        with self.sessions() as session:
            analysis = session.get(Analysis, analysis_id, with_for_update=True)
            if analysis is not None and analysis.deleted_at is None and analysis.status not in _FINISHED:
                analysis.status = AnalysisStatus.QUEUED
                session.commit()
        raise RetryLater

    def _finish(
        self,
        analysis_id: uuid.UUID,
        started: float,
        *,
        output: AnalysisOutput | None = None,
        error: AnalysisErrorCode | None = None,
    ) -> None:
        try:
            with self.sessions() as session:
                # Analiz sürerken silinmiş olabilir: kilitleyip tekrar oku, silinmişe sonuç yazma.
                analysis = session.get(Analysis, analysis_id, with_for_update=True)
                if analysis is not None and analysis.deleted_at is None and analysis.status not in _FINISHED:
                    analysis.status = AnalysisStatus.FAILED if error else AnalysisStatus.DONE
                    analysis.error_code = error
                    analysis.duration_ms = int((time.monotonic() - started) * 1000)
                    analysis.completed_at = datetime.now(UTC)
                    if output is not None:
                        analysis.match_score = output.match_score
                        analysis.postings_analyzed = output.postings_analyzed
                        analysis.model_name = output.model_name
                        analysis.prompt_version = output.prompt_version
                        _write_details(session, analysis_id, output)
                    session.commit()
        finally:
            self._forget(analysis_id)  # veritabanı hatasında veya süre sınırında da CV kalmasın

    def _forget(self, analysis_id: uuid.UUID) -> None:
        try:
            self.store.delete(analysis_id)
        except (RedisError, OSError) as exc:
            logger.warning("analysis_cv_delete_failed: %s", type(exc).__name__)  # süre aşımıyla silinir


# Sütun sınırları (app/db/models/analysis.py).
_NAME_MAX = 100
_REASON_MAX = 1000
_SMALLINT_MAX = 32767


def _write_details(session: Session, analysis_id: uuid.UUID, output: AnalysisOutput) -> None:
    """Yetkinlikleri ve önerileri yazar. AI çıktısı burada doğrulanır, veritabanı kısıtına takılıp sonuç kaybolmasın:

    - Yetkinlik adı taksonomideki standart adla (büyük/küçük harf fark etmez) eşlenir. Taksonomide olmayan
      "doğrulanmış" mevcut yetkinlik doğrulanmamış ad olarak saklanır; taksonomide olmayan eksik yetkinlik atılır.
    - Aynı yetkinlik hem mevcut hem eksikse mevcut sayılır; tekrarlar bir kez yazılır.
    - Kaynak sadece veritabanında varsa ve o eksik yetkinliğe aitse yazılır (karar #10); LLM'in seçtiği numara başka
      bir yetkinliğin kaynağını gösteremez.
    Atılanların sadece sayısı loglanır (adlar CV'den geldiği için loga yazılmaz).
    """
    ids = _skill_ids(
        session, [p.skill for p in output.present_skills if p.verified] + [m.skill for m in output.missing_skills]
    )
    taken: set[int] = set()
    unverified: set[str] = set()
    dropped_skills = dropped_resources = 0

    for p in output.present_skills:
        skill_id = ids.get(_key(p.skill)) if p.verified else None
        level = _level(p.level)
        confidence = _ratio(p.confidence, "0.01")
        if skill_id is not None:
            if skill_id not in taken:
                taken.add(skill_id)
                session.add(
                    AnalysisSkill(
                        analysis_id=analysis_id,
                        skill_id=skill_id,
                        kind=SkillKind.PRESENT,
                        level=level,
                        confidence=confidence,
                    )
                )
            continue
        name = " ".join(p.skill.split())[:_NAME_MAX]
        if not name:
            dropped_skills += 1
            continue
        if name.casefold() in unverified:
            continue
        unverified.add(name.casefold())
        session.add(AnalysisUnverifiedSkill(analysis_id=analysis_id, name=name, level=level, confidence=confidence))

    missing: list[tuple[int, list[tuple[int, str | None]]]] = []
    for m in output.missing_skills:
        skill_id = ids.get(_key(m.skill))
        if skill_id is None:
            dropped_skills += 1
            continue
        if skill_id in taken:
            continue
        taken.add(skill_id)
        priority = m.priority if m.priority is not None and 1 <= m.priority <= _SMALLINT_MAX else None
        session.add(
            AnalysisSkill(
                analysis_id=analysis_id,
                skill_id=skill_id,
                kind=SkillKind.MISSING,
                demand_ratio=_ratio(m.demand_ratio, "0.0001"),
                priority=priority,
            )
        )
        missing.append((skill_id, [(r.resource_id, r.reason) for r in m.resources]))

    owners = _resource_owners(session, [rid for _, resources in missing for rid, _ in resources])
    for skill_id, resources in missing:
        seen: set[int] = set()
        for resource_id, reason in resources:
            if owners.get(resource_id) != skill_id or resource_id in seen:
                dropped_resources += 1
                continue
            seen.add(resource_id)
            text = " ".join((reason or "").split())[:_REASON_MAX] or None
            session.add(
                AnalysisRecommendation(
                    analysis_id=analysis_id,
                    skill_id=skill_id,
                    resource_id=resource_id,
                    rank=len(seen),
                    reason_text=text,
                )
            )
    if dropped_skills or dropped_resources:
        logger.info("analysis_result_dropped: skills=%d resources=%d", dropped_skills, dropped_resources)


def _key(name: str) -> str:
    return " ".join(name.split()).casefold()


def _skill_ids(session: Session, names: list[str]) -> dict[str, int]:
    keys = {_key(n) for n in names if n.strip()}
    if not keys:
        return {}
    # Veritabanında lower() ile daraltılır, eşleme Python'da aynı anahtarla yapılır.
    rows = session.execute(
        select(Skill.id, Skill.canonical_name).where(func.lower(Skill.canonical_name).in_(keys))
    ).all()
    return {_key(name): skill_id for skill_id, name in rows if _key(name) in keys}


def _resource_owners(session: Session, resource_ids: list[int]) -> dict[int, int]:
    if not resource_ids:
        return {}
    rows = session.execute(select(Resource.id, Resource.skill_id).where(Resource.id.in_(set(resource_ids)))).all()
    return {rid: skill_id for rid, skill_id in rows}


def _level(value: str) -> SkillLevel:
    try:
        return SkillLevel(value)
    except ValueError:
        return SkillLevel.UNKNOWN


def _ratio(value: float | None, step: str) -> Decimal | None:
    if value is None or value != value:  # NaN
        return None
    return Decimal(str(min(max(value, 0.0), 1.0))).quantize(Decimal(step))


def _has_explicit_consent(session: Session, user_id: uuid.UUID) -> bool:
    stmt = select(Consent.id).where(
        Consent.user_id == user_id, Consent.consent_type == ConsentType.ACIK_RIZA, Consent.withdrawn_at.is_(None)
    )
    return session.scalar(stmt.limit(1)) is not None
