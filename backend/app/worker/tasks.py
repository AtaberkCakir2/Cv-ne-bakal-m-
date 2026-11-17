"""Analiz görevi: en fazla 180 sn, geçici hatada bir kez daha denenir (T-039)."""

import uuid
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.services.analysis_runner import AnalysisRunner, RetryLater
from app.services.analyzer import build_analyzer
from app.services.cv_store import RedisCvStore
from app.worker.celery_app import TASK_NAME, celery_app

RETRY_DELAY_S = 5
_settings = get_settings()


@lru_cache
def build_runner() -> AnalysisRunner:
    url = _settings.cv_store_url
    if url is None:
        raise RuntimeError("CV_REDIS_URL ayarlanmamış")
    return AnalysisRunner(get_sessionmaker(), RedisCvStore(url, _settings.analysis_cv_ttl_s), build_analyzer(_settings))


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    name=TASK_NAME,
    max_retries=1,
    soft_time_limit=_settings.analysis_timeout_s,
    time_limit=_settings.analysis_timeout_s + 20,
)
def run_analysis(self: Any, analysis_id: str) -> None:
    try:
        build_runner().run(uuid.UUID(analysis_id), last_attempt=self.request.retries >= self.max_retries)
    except RetryLater as exc:
        raise self.retry(exc=exc, countdown=RETRY_DELAY_S) from exc
