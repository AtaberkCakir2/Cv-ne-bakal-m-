"""Veri işçisinin Celery uygulaması (worker-data, docs/mimari.md): her gece 03:00 (İstanbul) toplama zinciri.

Analiz işçisinden (Burak, ai/) ayrı bir uygulama ve `data` kuyruğu: uzun toplama analiz kuyruğunu bekletmez.
Çalıştırma (beat aynı süreçte, tek eşzamanlılık):

    celery -A collector.tasks worker -B -Q data --concurrency 1 --loglevel INFO
"""

import logging
from typing import Any

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from celery import Celery
from celery.schedules import crontab
from redis import Redis

from collector.nightly import run_nightly

log = logging.getLogger(__name__)
# httpx her isteği INFO'da yazar (gecede yüzlerce satır); hatalar zaten nightly.py'de kaynak adıyla loglanır.
logging.getLogger("httpx").setLevel(logging.WARNING)

QUEUE = "data"
NIGHTLY_TASK = "collector.nightly"
# HN 2 aylık başlıkta yeni yorumlar + 20 Himalayas isteği, 3-5 sn arayla: olağan gece < 1 saat.
SOFT_LIMIT_S = 3 * 3600
LOCK_KEY = "careerai:lock:nightly"

app = Celery("careerai-data", broker=get_settings().redis_url)
app.conf.update(
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_default_queue=QUEUE,
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    task_ignore_result=True,  # sonuç scrape_runs'ta; Redis'te tutulmaz
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "gece-toplama": {
            "task": NIGHTLY_TASK,
            "schedule": crontab(hour=3, minute=0),
            # İşçi kapalıyken kaçan gece ertesi akşama sarkmasın: 6 saat içinde alınmazsa düşer.
            "options": {"expires": 6 * 3600},
        }
    },
)


@app.task(name=NIGHTLY_TASK, soft_time_limit=SOFT_LIMIT_S, time_limit=SOFT_LIMIT_S + 600)
def nightly() -> dict[str, Any]:
    # Elle tetikleme ile beat aynı anda düşerse iki toplama üst üste binmesin.
    lock = Redis.from_url(get_settings().redis_url).lock(LOCK_KEY, timeout=SOFT_LIMIT_S + 600, blocking=False)
    if not lock.acquire():
        log.warning("Gece toplaması zaten çalışıyor, atlandı")
        return {"skipped": True}
    try:
        report = run_nightly(get_sessionmaker())
    finally:
        lock.release()
    log.info("Gece toplaması bitti\n%s", report.summary())
    if not report.ok:
        # İzleme (T-066) Celery'nin hata kaydından uyarı üretecek; kaynak düşmesi sessiz kalmasın.
        log.error("Gece toplamasında başarısız kaynak var")
    return {"inserted": report.inserted, "stats_rows": report.stats_rows, "ok": report.ok}
