"""Analiz işçisinin Celery uygulaması (T-039). Veri işçisinden ayrı uygulama ve kuyruk (scraper/collector/tasks.py).

Çalıştırma (eşzamanlılık 1: dil modeli belleği, docs/mimari.md):

    celery -A app.worker.celery_app worker -Q analysis --concurrency 1 --loglevel INFO
"""

import uuid

from celery import Celery

from app.core.config import get_settings

QUEUE = "analysis"
TASK_NAME = "analysis.run"

celery_app = Celery("careerai-analysis", broker=get_settings().redis_url, include=["app.worker.tasks"])
celery_app.conf.update(
    task_default_queue=QUEUE,
    task_ignore_result=True,  # durum veritabanında (analyses.status)
    task_acks_late=True,  # işçi ölürse iş kaybolmasın
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"socket_connect_timeout": 2, "socket_timeout": 5},
    timezone="Europe/Istanbul",
)


def publish_analysis(analysis_id: uuid.UUID) -> None:
    # retry=False: Redis yoksa istek beklemesin, kullanıcı hemen 503 alsın.
    celery_app.send_task(TASK_NAME, args=[str(analysis_id)], queue=QUEUE, retry=False)
