"""Kuyruktaki bir analizi çalıştırır, durumunu yazar ve CV baytlarını siler (T-039).

Hata mesajları loglanmaz ve saklanmaz, sadece türü ve kodu: mesaj CV parçası içerebilir (karar #9).
"""

import logging
import time
import uuid
from datetime import UTC, datetime

from celery.exceptions import SoftTimeLimitExceeded
from redis.exceptions import RedisError
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import AnalysisErrorCode, AnalysisStatus
from app.db.models import Analysis
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
        try:
            pdf = self.store.get(analysis_id)
            if pdf is None:  # süre aşımıyla silinmiş; tekrar denemek işe yaramaz
                raise AnalysisFailed(AnalysisErrorCode.INTERNAL)
            output = self.analyzer.analyze(pdf, target_role_id)
        except AnalysisFailed as exc:
            self._finish(analysis_id, started, error=exc.code)
        except (TimeoutError, SoftTimeLimitExceeded):
            self._transient(analysis_id, started, AnalysisErrorCode.LLM_TIMEOUT, last_attempt)
        except Exception as exc:  # hangi hata olursa olsun analiz askıda kalmamalı
            logger.warning("analysis_failed: %s", type(exc).__name__)
            self._transient(analysis_id, started, AnalysisErrorCode.INTERNAL, last_attempt)
        else:
            self._finish(analysis_id, started, output=output)

    def _start(self, analysis_id: uuid.UUID) -> int | None:
        """Çalıştırılacak analizin hedef pozisyonunu döner; silinmiş veya bitmişse None."""
        with self.sessions() as session:
            analysis = session.get(Analysis, analysis_id, with_for_update=True)
            if analysis is None or analysis.deleted_at is not None or analysis.status in _FINISHED:
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
            if analysis is not None and analysis.deleted_at is None:
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
        with self.sessions() as session:
            # Analiz sürerken silinmiş olabilir: kilitleyip tekrar oku, silinmişe sonuç yazma.
            analysis = session.get(Analysis, analysis_id, with_for_update=True)
            if analysis is not None and analysis.deleted_at is None:
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
        self._forget(analysis_id)

    def _forget(self, analysis_id: uuid.UUID) -> None:
        try:
            self.store.delete(analysis_id)
        except (RedisError, OSError) as exc:
            logger.warning("analysis_cv_delete_failed: %s", type(exc).__name__)  # süre aşımıyla silinir
