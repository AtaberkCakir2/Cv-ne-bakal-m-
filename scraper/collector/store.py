"""İlanları job_postings'e yazar; her çalışma scrape_runs'a kaydedilir.

Tekrar kayıt iki yoldan engellenir: aynı kaynakta aynı external_id ve farklı kaynaklarda aynı metin
(content_hash). İkisi de veritabanındaki unique kısıtlarla; çakışan satır sessizce atlanıp `duplicates` sayılır.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from itertools import islice

from app.db.enums import LangCode, ScrapeStatus, SourceType
from app.db.models import JobPosting, JobSource, ScrapeRun
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from collector.posting import Posting, SourceInfo

BATCH_SIZE = 200
MAX_ERROR_LOG = 2000


@dataclass
class RunResult:
    fetched: int = 0
    inserted: int = 0
    duplicates: int = 0


def ensure_source(session: Session, info: SourceInfo) -> JobSource:
    """Kaynak satırını oluşturur veya günceller. Buraya gelen her kaynak uygunluk tablosunda ✅ (tos_checked)."""
    source = session.scalar(select(JobSource).where(JobSource.name == info.name))
    if source is None:
        source = JobSource(name=info.name)
        session.add(source)
    source.type = SourceType(info.type)
    source.base_url = info.base_url
    source.rate_limit_sec = Decimal(str(info.rate_limit_sec))
    source.tos_checked = True
    source.is_active = True
    session.flush()
    return source


def _batches(postings: Iterable[Posting]) -> Iterator[list[Posting]]:
    it = iter(postings)
    while batch := list(islice(it, BATCH_SIZE)):
        yield batch


def save_postings(session: Session, source_id: int, postings: Iterable[Posting], *, active: bool = True) -> RunResult:
    result = RunResult()
    for batch in _batches(postings):
        rows = [
            {
                "source_id": source_id,
                "external_id": p.external_id,
                "url": p.url,
                "title_raw": p.title_raw,
                "company": p.company,
                "location": p.location,
                "description_clean": p.description_clean,
                "language": LangCode(p.language),
                "posted_at": p.posted_at,
                "content_hash": p.content_hash,
                "is_active": active,
            }
            for p in batch
        ]
        inserted = session.scalars(insert(JobPosting).values(rows).on_conflict_do_nothing().returning(JobPosting.id))
        count = len(inserted.all())
        result.fetched += len(batch)
        result.inserted += count
        result.duplicates += len(batch) - count
        session.commit()  # uzun toplamada yarıda kesilirse eldeki partiler kaybolmasın
    return result


def run_import(session: Session, info: SourceInfo, postings: Iterable[Posting], *, active: bool = True) -> RunResult:
    """Bir kaynağın içe aktarımı; başarısız olsa da scrape_runs'a kaydedilir."""
    source = ensure_source(session, info)
    run = ScrapeRun(source_id=source.id, started_at=datetime.now(UTC), status=ScrapeStatus.RUNNING)
    session.add(run)
    session.commit()
    result = RunResult()
    try:
        result = save_postings(session, source.id, postings, active=active)
        run.status = ScrapeStatus.SUCCESS
    except Exception as exc:
        session.rollback()
        run.status = ScrapeStatus.PARTIAL if result.inserted else ScrapeStatus.FAILED
        run.errors = 1
        # Sadece hata türü ve mesajı; ilan metni (kişisel veri içerebilir) loglanmaz.
        run.error_log = f"{type(exc).__name__}: {exc}"[:MAX_ERROR_LOG]
        raise
    finally:
        run.fetched, run.inserted, run.duplicates = result.fetched, result.inserted, result.duplicates
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
    return result


def source_counts(session: Session) -> list[tuple[str, int, int]]:
    """Kaynak başına (ad, aktif ilan, toplam ilan)."""
    rows = session.execute(
        select(
            JobSource.name,
            func.count(JobPosting.id).filter(JobPosting.is_active),
            func.count(JobPosting.id),
        )
        .join(JobPosting, JobPosting.source_id == JobSource.id, isouter=True)
        .group_by(JobSource.name)
        .order_by(JobSource.name)
    ).all()
    return [(name, active, total) for name, active, total in rows]
