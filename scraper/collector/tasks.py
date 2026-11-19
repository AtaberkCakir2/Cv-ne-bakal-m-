"""Veri işçisinin Celery uygulaması (worker-data, docs/mimari.md): her gece 03:00 (İstanbul) toplama zinciri.

Analiz işçisinden (Burak, ai/) ayrı bir uygulama ve `data` kuyruğu: uzun toplama analiz kuyruğunu bekletmez.
Çalıştırma (beat aynı süreçte, tek eşzamanlılık):

    celery -A collector.tasks worker -B -Q data --concurrency 1 --loglevel INFO
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.models import Resource, ScrapeRun
from app.db.session import get_sessionmaker
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging, worker_ready
from redis import Redis
from sqlalchemy import func, select

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
TZ = ZoneInfo("Europe/Istanbul")
NIGHTLY_HOUR = 3
# Saatin hemen ardından açılan işçide beat zaten tetikler; telafi ikinci kez kuyruğa koymasın.
CATCH_UP_GRACE = timedelta(minutes=10)
# Link kontrolü haftalık (pazar 07:00). PC o saatte kapalıysa kaçar; son kontrol bundan eskiyse açılışta yapılır.
CHECK_EVERY = timedelta(days=7)

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
            "schedule": crontab(hour=NIGHTLY_HOUR, minute=0),
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


def missed_nightly(last_started: datetime | None, now: datetime) -> bool:
    """Son planlı gece toplaması (03:00, İstanbul) kaçtı mı (R-18: PC o saatte kapalıydı).

    Son 03:00'ten sonra hiç toplama başlamadıysa kaçmıştır. Hiç toplama yoksa da (yeni kurulum) kaçmış sayılır.
    """
    local = now.astimezone(TZ)
    slot = local.replace(hour=NIGHTLY_HOUR, minute=0, second=0, microsecond=0)
    if local < slot:
        slot -= timedelta(days=1)
    if local - slot < CATCH_UP_GRACE:
        return False
    if last_started is None:
        return True
    if last_started.tzinfo is None:
        last_started = last_started.replace(tzinfo=UTC)
    return last_started < slot


@worker_ready.connect
def _catch_up_missed_nightly(**_: Any) -> None:
    """İşçi açılınca kaçan gece toplamasını hemen kuyruğa koyar (T-075, R-18).

    Celery beat kaçan zamanı telafi etmez: PC 03:00'te kapalıysa o gece toplama hiç olmazdı. Kilit (LOCK_KEY)
    sayesinde beat ile üst üste binmez. Veritabanına ulaşılamazsa işçi yine açılır, sadece uyarı yazılır.
    """
    try:
        with get_sessionmaker()() as session:
            last = session.scalar(select(func.max(ScrapeRun.started_at)))
    except Exception:
        log.exception("Kaçan gece toplaması kontrol edilemedi")
        return
    if missed_nightly(last, datetime.now(UTC)):
        log.warning("Gece toplaması kaçmış (son başlangıç: %s), şimdi başlatılıyor", last)
        nightly.apply_async(expires=6 * 3600)


def missed_link_check(last_checked: datetime | None, now: datetime) -> bool:
    """Haftalık link kontrolü kaçtı mı: son kontrol 7 günden eski veya hiç yapılmamış (go-live #35).

    Pazar 07:00 beat'i PC kapalıyken hiç çalışmaz; production'da kontrol bu yüzden hiç yapılmamıştı.
    """
    if last_checked is None:
        return True
    if last_checked.tzinfo is None:
        last_checked = last_checked.replace(tzinfo=UTC)
    return now - last_checked > CHECK_EVERY + CATCH_UP_GRACE


@worker_ready.connect
def _catch_up_missed_link_check(**_: Any) -> None:
    """İşçi açılınca kaçan haftalık link kontrolünü kuyruğa koyar.

    Kuyruk tek eşzamanlı: aynı açılışta kaçan gece toplaması da varsa ondan sonra çalışır.
    """
    try:
        with get_sessionmaker()() as session:
            last = session.scalar(select(func.max(Resource.last_checked_at)))
    except Exception:
        log.exception("Kaçan link kontrolü kontrol edilemedi")
        return
    if missed_link_check(last, datetime.now(UTC)):
        log.warning("Haftalık link kontrolü kaçmış (son kontrol: %s), kuyruğa kondu", last)
        resources_check.apply_async(expires=12 * 3600)


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
        rep = resources.report(session)
    log.info(
        "Link kontrolü: %d link, %d ölü, %d geri geldi; ölü oranı %%%.1f (hedef < %%%d)",
        r.checked,
        r.dead,
        r.revived,
        rep["dead_ratio"] * 100,
        resources.MAX_DEAD_RATIO_PCT,
    )
    return {"checked": r.checked, "dead": r.dead, "revived": r.revived, "dead_ratio": rep["dead_ratio"]}
