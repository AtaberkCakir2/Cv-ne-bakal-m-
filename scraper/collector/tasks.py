"""Veri işçisinin Celery uygulaması (worker-data, docs/mimari.md): her gece 03:00 (İstanbul) toplama zinciri.

Analiz işçisinden (Burak, ai/) ayrı bir uygulama ve `data` kuyruğu: uzun toplama analiz kuyruğunu bekletmez.
Çalıştırma (beat aynı süreçte, tek eşzamanlılık):

    celery -A collector.tasks worker -B -Q data --concurrency 1 --loglevel INFO
"""

import logging
from typing import Any

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_sessionmaker
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging
from redis import Redis

from collector import resources, taxonomy, youtube
from collector.http import PoliteClient
from collector.nightly import run_nightly

log = logging.getLogger(__name__)
# httpx her isteği INFO'da yazar (gecede yüzlerce satır); hatalar zaten nightly.py'de kaynak adıyla loglanır.
logging.getLogger("httpx").setLevel(logging.WARNING)

QUEUE = "data"
NIGHTLY_TASK = "collector.nightly"
RESOURCES_SEARCH_TASK = "collector.resources_search"
RESOURCES_CHECK_TASK = "collector.resources_check"
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
        },
        # Gece toplamasından sonra. Günlük kota 100 arama; hepsi bitince iş boş döner.
        "kaynak-arama": {
            "task": RESOURCES_SEARCH_TASK,
            "schedule": crontab(hour=6, minute=0),
            "options": {"expires": 6 * 3600},
        },
        "kaynak-kontrol": {
            "task": RESOURCES_CHECK_TASK,
            "schedule": crontab(hour=7, minute=0, day_of_week="sunday"),
            "options": {"expires": 12 * 3600},
        },
    },
)


@setup_logging.connect
def _json_logging(**_: Any) -> None:
    """Celery kendi düz metin logunu kurmasın: API ile aynı JSON + kişisel veri maskeleme (T-067).

    Bu sinyale bağlı bir fonksiyon varsa Celery log ayarına dokunmaz; worker ve beat logları kök logger'dan
    JsonFormatter ile stdout'a çıkar, Alloy oradan Loki'ye taşır.
    """
    configure_logging(get_settings().log_level)
    # configure_logging httpx'i zaten WARNING'e çeker; Celery'nin görev başına iki INFO satırı kalabilir.


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


@app.task(name=RESOURCES_SEARCH_TASK, soft_time_limit=1800, time_limit=2100)
def resources_search() -> dict[str, Any]:
    key = youtube.YoutubeSettings().youtube_api_key
    if not key:
        log.warning("YOUTUBE_API_KEY boş, kaynak araması atlandı")
        return {"skipped": True}
    with get_sessionmaker()() as session:
        r = resources.search_youtube(
            session, PoliteClient(delay_s=resources.YOUTUBE_DELAY_S, max_retries=0), key, taxonomy.load_skills()
        )
    log.info("Kaynak araması: %d arama, %d video, kalan %d", r.searches, r.added, r.remaining)
    return {"searches": r.searches, "added": r.added, "remaining": r.remaining, "quota_hit": r.quota_hit}


@app.task(name=RESOURCES_CHECK_TASK, soft_time_limit=SOFT_LIMIT_S, time_limit=SOFT_LIMIT_S + 600)
def resources_check() -> dict[str, Any]:
    key = youtube.YoutubeSettings().youtube_api_key
    with get_sessionmaker()() as session:
        r = resources.check_links(
            session,
            PoliteClient(delay_s=resources.CHECK_DELAY_S),
            PoliteClient(delay_s=resources.YOUTUBE_DELAY_S, max_retries=0),
            key,
        )
    log.info("Link kontrolü: %d link, %d ölü, %d geri geldi", r.checked, r.dead, r.revived)
    return {"checked": r.checked, "dead": r.dead, "revived": r.revived}
