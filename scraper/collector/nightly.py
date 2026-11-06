"""Gece toplaması (T-034): izinli kaynaklar sırayla → normalize → role_skill_stats.

Her kaynak ayrı çalışır ve `scrape_runs`'a ayrı kaydedilir (store.run_import); biri düşerse diğerleri devam eder.
403 veya tekrar denemelere rağmen 429 alan kaynak pasife alınır (kaynak-uygunluk.md kural 3) ve sonraki gecelerde
atlanır; biri durumu inceleyip `job_sources.is_active`'i elle açana kadar kapalı kalır.

Zamanlama Celery beat'te (collector/tasks.py); elle: `python -m collector nightly`.
"""

import logging
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field

import httpx
from app.db.models import JobPosting, JobSource
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from collector import taxonomy
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo
from collector.sources import arbeitnow, himalayas, hn, jobicy, remoteok, remotive
from collector.store import RunResult, error_summary, run_import
from etl import stats
from etl.pipeline import normalize

log = logging.getLogger(__name__)

JITTER_S = (3.0, 5.0)  # T-034: istekler arası rastgele bekleme (kaynağın kendi alt sınırı daha büyükse o)
BLOCKING_STATUSES = {403, 429}

Fetch = Callable[[PoliteClient, Collection[str]], Iterable[Posting]]


@dataclass(frozen=True)
class NightlySource:
    info: SourceInfo
    fetch: Fetch  # ikinci argüman: bu kaynaktan zaten kayıtlı external_id'ler


# EMSCAD gece çalışmaz: yerel, değişmeyen veri seti.
NIGHTLY_SOURCES: tuple[NightlySource, ...] = (
    # Son 2 aylık başlık: ay başında önceki ayın başlığına hâlâ ilan yazılıyor. Kayıtlı yorumlar istenmez.
    NightlySource(hn.SOURCE, lambda c, known: hn.fetch(c, months=2, skip_ids=known)),
    # Sonuçlar en yeniden eskiye; bir gecede çıkan ilanlar ilk sayfalarda.
    NightlySource(himalayas.SOURCE, lambda c, known: himalayas.fetch(c, pages_per_query=2)),
    NightlySource(remoteok.SOURCE, lambda c, known: remoteok.fetch(c)),
    NightlySource(remotive.SOURCE, lambda c, known: remotive.fetch(c)),  # şart: gecede 1 çağrı
    NightlySource(jobicy.SOURCE, lambda c, known: jobicy.fetch(c)),
    NightlySource(arbeitnow.SOURCE, lambda c, known: arbeitnow.fetch(c)),
)


@dataclass
class SourceOutcome:
    name: str
    status: str  # success | failed | skipped | deactivated
    result: RunResult = field(default_factory=RunResult)
    error: str | None = None


@dataclass
class NightlyReport:
    sources: list[SourceOutcome] = field(default_factory=list)
    normalized: bool = False
    stats_rows: int | None = None

    @property
    def inserted(self) -> int:
        return sum(s.result.inserted for s in self.sources)

    @property
    def ok(self) -> bool:
        return self.stats_rows is not None and all(s.status in {"success", "skipped"} for s in self.sources)

    def summary(self) -> str:
        lines = [
            f"{s.name}: {s.status}, {s.result.fetched} okundu, {s.result.inserted} eklendi"
            + (f" ({s.error})" if s.error else "")
            for s in self.sources
        ]
        lines.append(f"normalize: {'evet' if self.normalized else 'hayır (yeni ilan yok)'}")
        lines.append(f"role_skill_stats: {self.stats_rows if self.stats_rows is not None else 'YENİLENEMEDİ'} satır")
        return "\n".join(lines)


def _source_row(session: Session, name: str) -> JobSource | None:
    return session.scalar(select(JobSource).where(JobSource.name == name))


def known_ids(session: Session, source_name: str) -> set[str]:
    rows = session.scalars(
        select(JobPosting.external_id)
        .join(JobSource, JobPosting.source_id == JobSource.id)
        .where(JobSource.name == source_name)
    )
    return set(rows)


def _collect(
    session_factory: Callable[[], Session], src: NightlySource, jitter: tuple[float, float] | None
) -> SourceOutcome:
    name = src.info.name
    with session_factory() as session:
        row = _source_row(session, name)
        if row is not None and not row.is_active:
            log.warning("%s pasif, atlandı (job_sources.is_active elle açılmalı)", name)
            return SourceOutcome(name, "skipped")
        known = known_ids(session, name)

    client = PoliteClient(delay_s=src.info.rate_limit_sec, jitter=jitter)
    try:
        with session_factory() as session:
            return SourceOutcome(name, "success", run_import(session, src.info, src.fetch(client, known)))
    except httpx.HTTPStatusError as exc:
        outcome = SourceOutcome(name, "failed", error=error_summary(exc))
        if exc.response.status_code in BLOCKING_STATUSES:
            with session_factory() as session:
                session.execute(update(JobSource).where(JobSource.name == name).values(is_active=False))
                session.commit()
            outcome.status = "deactivated"
            log.error("%s %s döndü, kaynak pasife alındı", name, exc.response.status_code)
        else:
            log.error("%s başarısız: %s", name, outcome.error)
        return outcome
    except Exception as exc:
        # run_import çalışmayı scrape_runs'a failed/partial olarak yazdı; diğer kaynaklar devam eder.
        log.exception("%s başarısız", name)
        return SourceOutcome(name, "failed", error=error_summary(exc))
    finally:
        client.close()


def run_nightly(
    session_factory: Callable[[], Session],
    sources: Iterable[NightlySource] = NIGHTLY_SOURCES,
    *,
    jitter: tuple[float, float] | None = JITTER_S,
) -> NightlyReport:
    report = NightlyReport()
    for src in sources:
        outcome = _collect(session_factory, src, jitter)
        log.info("%s: %s, +%d", outcome.name, outcome.status, outcome.result.inserted)
        report.sources.append(outcome)

    # Yeni ilan yoksa normalize gereksiz; ama 6 aylık pencere her gün kaydığı için istatistik yine yenilenir.
    if report.inserted:
        with session_factory() as session:
            normalize(session, taxonomy.load_skills(), taxonomy.load_roles())
        report.normalized = True
    with session_factory() as session:
        report.stats_rows = stats.refresh(session)
    return report
