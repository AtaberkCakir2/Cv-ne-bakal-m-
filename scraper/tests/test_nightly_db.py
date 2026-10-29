"""Gece zinciri (T-034). Sadece TEST_DATABASE_URL ile çalışır (test_store.py düzeni); ağ yok, sahte kaynaklar."""

import argparse
import os
from collections.abc import Callable, Collection, Iterator
from datetime import date
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from app.db.enums import ScrapeStatus
from app.db.models import JobSource, ScrapeRun
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session

from collector.http import PoliteClient
from collector.nightly import NightlySource, known_ids, run_nightly
from collector.posting import Posting, SourceInfo
from collector.store import run_import
from collector.taxonomy import load_roles, load_skills, seed

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "backend" / "app" / "db" / "alembic.ini"

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL verilmedi")


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    assert TEST_DATABASE_URL
    cfg = Config(str(ALEMBIC_INI))
    cfg.cmd_opts = argparse.Namespace(x=[f"url={TEST_DATABASE_URL}"])
    command.upgrade(cfg, "head")
    eng = create_engine(TEST_DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def factory(engine: Engine) -> Iterator[Callable[[], Session]]:
    # run_nightly kendi oturumlarını açıp commit eder; hepsi aynı bağlantıda savepoint olur ve test sonunda geri alınır.
    with engine.connect() as conn:
        trans = conn.begin()

        def make() -> Session:
            return Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)

        with make() as s:
            seed(s, load_skills(), load_roles())
        yield make
        trans.rollback()


def info(name: str) -> SourceInfo:
    return SourceInfo(name=name, type="api", base_url="https://example.com", rate_limit_sec=0)


def posting(external_id: str, text: str) -> Posting:
    return Posting(
        external_id=external_id,
        title_raw="Backend Developer",
        description_clean=text,
        language="en",
        posted_at=date.today(),
    )


def good(name: str, *items: Posting) -> NightlySource:
    return NightlySource(info(name), lambda c, known: [p for p in items if p.external_id not in known])


def failing(name: str, exc: Exception) -> NightlySource:
    def fetch(c: PoliteClient, known: Collection[str]) -> Iterator[Posting]:
        raise exc
        yield  # üreteç

    return NightlySource(info(name), fetch)


def http_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.com")
    return httpx.HTTPStatusError("hata", request=request, response=httpx.Response(status, request=request))


def runs(session: Session) -> dict[str, ScrapeStatus]:
    rows = session.execute(
        select(JobSource.name, ScrapeRun.status).join(ScrapeRun, ScrapeRun.source_id == JobSource.id)
    )
    return dict(rows.tuples().all())


def test_one_source_failing_does_not_stop_the_others(factory: Callable[[], Session]) -> None:
    sources = [
        good("kaynak-a", posting("1", "Python, Django and PostgreSQL for our backend")),
        failing("kaynak-b", RuntimeError("bağlantı koptu")),
        good("kaynak-c", posting("2", "Go and Kubernetes services")),
    ]
    report = run_nightly(factory, sources, jitter=None)

    assert [(s.name, s.status, s.result.inserted) for s in report.sources] == [
        ("kaynak-a", "success", 1),
        ("kaynak-b", "failed", 0),
        ("kaynak-c", "success", 1),
    ]
    assert report.normalized and not report.ok
    # normalize çalıştı: ilanlar "Backend Developer" pozisyonuna ve yetkinliklere bağlandı, istatistik yenilendi.
    assert report.stats_rows
    with factory() as s:
        assert runs(s) == {
            "kaynak-a": ScrapeStatus.SUCCESS,
            "kaynak-b": ScrapeStatus.FAILED,
            "kaynak-c": ScrapeStatus.SUCCESS,
        }
        assert s.scalar(select(func.count()).select_from(JobSource).where(JobSource.is_active)) == 3


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_source_is_deactivated_and_skipped_next_night(factory: Callable[[], Session], status: int) -> None:
    report = run_nightly(factory, [failing("engelli", http_error(status))], jitter=None)
    assert report.sources[0].status == "deactivated"
    with factory() as s:
        assert s.scalar(select(JobSource.is_active).where(JobSource.name == "engelli")) is False

    # Ertesi gece kaynak hiç çağrılmaz ve elle açılana kadar pasif kalır.
    again = run_nightly(factory, [good("engelli", posting("9", "Rust"))], jitter=None)
    assert again.sources[0].status == "skipped"
    with factory() as s:
        assert s.scalar(select(JobSource.is_active).where(JobSource.name == "engelli")) is False


def test_other_http_errors_fail_without_deactivating(factory: Callable[[], Session]) -> None:
    report = run_nightly(factory, [failing("bozuk", http_error(500))], jitter=None)
    assert report.sources[0].status == "failed"
    with factory() as s:
        assert s.scalar(select(JobSource.is_active).where(JobSource.name == "bozuk")) is True


def test_second_night_only_fetches_new_postings(factory: Callable[[], Session]) -> None:
    with factory() as s:
        run_import(s, info("kaynak-a"), [posting("1", "Python and FastAPI")])
        assert known_ids(s, "kaynak-a") == {"1"}

    report = run_nightly(
        factory, [good("kaynak-a", posting("1", "Python and FastAPI"), posting("2", "Java and Spring"))], jitter=None
    )
    assert (report.sources[0].result.fetched, report.inserted) == (1, 1)


def test_quiet_night_still_refreshes_stats(factory: Callable[[], Session]) -> None:
    report = run_nightly(factory, [good("kaynak-a")], jitter=None)
    assert report.ok and not report.normalized and report.stats_rows is not None
