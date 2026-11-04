"""Analiz kuyruğu (T-039). Celery mesajı sadece analiz kimliğini taşır; CV baytları geçici depoda durur (cv_store)."""

import logging
import uuid
from collections.abc import Callable
from typing import Protocol

from redis.exceptions import RedisError

from app.core.config import Settings
from app.services.cv_store import CvStore, RedisCvStore

logger = logging.getLogger(__name__)


class QueueUnavailable(Exception):
    """Analiz kuyruğa alınamadı: Redis yok, CV deposu ayarlanmamış veya kuyruk dolu."""


class AnalysisQueue(Protocol):
    def enqueue(self, analysis_id: uuid.UUID, pdf: bytes) -> None: ...


class CeleryAnalysisQueue:
    def __init__(self, store: CvStore | None, send: Callable[[uuid.UUID], None], limit: int) -> None:
        self._store = store
        self._send = send
        self._limit = limit

    def enqueue(self, analysis_id: uuid.UUID, pdf: bytes) -> None:
        store = self._store
        if store is None:
            # Kalıcı Redis'e düşmektense analiz başlatılmaz (karar #9).
            logger.error("analysis_queue_cv_store_not_configured")
            raise QueueUnavailable
        try:
            # Her CV en fazla 5 MB: bekleyen iş sayısı sınırlanmazsa Redis belleği tükenir.
            if store.count() >= self._limit:
                logger.warning("analysis_queue_full")
                raise QueueUnavailable
            store.put(analysis_id, pdf)
        except (RedisError, OSError) as exc:
            logger.warning("analysis_queue_store_failed: %s", type(exc).__name__)
            raise QueueUnavailable from exc
        try:
            self._send(analysis_id)
        except Exception as exc:  # broker hatası türü ne olursa olsun CV depoda kalmasın
            logger.warning("analysis_queue_publish_failed: %s", type(exc).__name__)
            try:
                store.delete(analysis_id)
            except (RedisError, OSError):
                pass  # anahtar süre aşımıyla silinir
            raise QueueUnavailable from exc


def build_analysis_queue(settings: Settings) -> AnalysisQueue:
    from app.worker.celery_app import publish_analysis

    url = settings.cv_store_url
    store = RedisCvStore(url, settings.analysis_cv_ttl_s) if url else None
    return CeleryAnalysisQueue(store, publish_analysis, settings.analysis_queue_limit)
