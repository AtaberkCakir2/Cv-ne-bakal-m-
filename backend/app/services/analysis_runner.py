"""Kuyruktaki bir analizi çalıştırır, durumunu yazar ve CV baytlarını siler (T-039).

Hata mesajları loglanmaz ve saklanmaz, sadece türü ve kodu: mesaj CV parçası içerebilir (karar #9).
"""

import logging
import time
import uuid
from datetime import UTC, datetime

from celery.exceptions import SoftTimeLimitExceeded
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import AnalysisErrorCode, AnalysisStatus, ConsentType
from app.db.models import Analysis, Consent
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
                    session.commit()
        finally:
            self._forget(analysis_id)  # veritabanı hatasında veya süre sınırında da CV kalmasın

    def _forget(self, analysis_id: uuid.UUID) -> None:
        try:
            self.store.delete(analysis_id)
        except (RedisError, OSError) as exc:
            logger.warning("analysis_cv_delete_failed: %s", type(exc).__name__)  # süre aşımıyla silinir


def _has_explicit_consent(session: Session, user_id: uuid.UUID) -> bool:
    stmt = select(Consent.id).where(
        Consent.user_id == user_id, Consent.consent_type == ConsentType.ACIK_RIZA, Consent.withdrawn_at.is_(None)
    )
    return session.scalar(stmt.limit(1)) is not None
