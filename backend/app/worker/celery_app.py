"""Analiz işçisinin Celery uygulaması (T-039). Veri işçisinden ayrı uygulama ve kuyruk (scraper/collector/tasks.py).

Çalıştırma (eşzamanlılık 1: dil modeli belleği, docs/mimari.md):

    celery -A app.worker.celery_app worker -Q analysis --concurrency 1 --loglevel INFO
"""

import uuid
from typing import Any

from celery import Celery
from celery.signals import setup_logging

from app.core.config import get_settings
from app.core.logging import configure_logging

QUEUE = "analysis"
TASK_NAME = "analysis.run"

celery_app = Celery("careerai-analysis", broker=get_settings().redis_url, include=["app.worker.tasks"])
celery_app.conf.update(
    task_default_queue=QUEUE,
    task_ignore_result=True,  # durum veritabanında (analyses.status)
    task_acks_late=True,  # işçi ana süreci veya bağlantı koparsa iş yeniden teslim edilir
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    # visibility_timeout: görev süresinin (200 sn) ve tekrar gecikmesinin üstünde, yeniden teslim 1 saat beklemesin.
    broker_transport_options={"socket_connect_timeout": 2, "socket_timeout": 5, "visibility_timeout": 600},
    timezone="Europe/Istanbul",
)


@setup_logging.connect  # type: ignore[untyped-decorator]
def _configure_worker_logging(**_: Any) -> None:
    # API ile aynı JSON log ve e-posta/telefon maskeleme; Celery kendi log düzenini kurmaz.
    configure_logging(get_settings().log_level)


def publish_analysis(analysis_id: uuid.UUID) -> None:
    # retry=False: Redis yoksa yeniden deneyerek uzun beklenmesin; kullanıcı birkaç saniyede 503 alır.
    celery_app.send_task(TASK_NAME, args=[str(analysis_id)], queue=QUEUE, retry=False)
