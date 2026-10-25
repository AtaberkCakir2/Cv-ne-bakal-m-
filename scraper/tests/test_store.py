"""Veritabanına yazma. Sadece TEST_DATABASE_URL verilince çalışır (backend/app/db/README.md: ayrı, boş test DB'si).

Şema backend'in Alembic migration'larıyla kurulur; her test kendi işleminde çalışıp geri alınır.
"""

import argparse
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.enums import ScrapeStatus
from app.db.models import JobPosting, ScrapeRun
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session

from collector.posting import Posting, SourceInfo
from collector.store import run_import, source_counts

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "backend" / "app" / "db" / "alembic.ini"
SOURCE = SourceInfo(name="test-kaynak", type="api", base_url="https://example.com", rate_limit_sec=1.5)

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
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as conn:
        trans = conn.begin()
        # store.py commit ettiğinde sadece savepoint kapanır; test sonunda hepsi geri alınır.
        with Session(bind=conn, join_transaction_mode="create_savepoint") as s:
            yield s
        trans.rollback()


def posting(external_id: str, text: str) -> Posting:
    return Posting(external_id=external_id, title_raw="Backend Engineer", description_clean=text, language="en")


def test_import_dedupes_by_external_id_and_content(session: Session) -> None:
    first = run_import(session, SOURCE, [posting("1", "Python and PostgreSQL"), posting("2", "Go and Kubernetes")])
    assert (first.fetched, first.inserted, first.duplicates) == (2, 2, 0)

    # Aynı id tekrar gelir, farklı id'li ama aynı metinli ilan gelir, bir de yeni ilan gelir.
    again = [posting("1", "Python and PostgreSQL"), posting("3", "python  AND postgresql"), posting("4", "Rust")]
    second = run_import(session, SOURCE, again)
    assert (second.fetched, second.inserted, second.duplicates) == (3, 1, 2)

    assert source_counts(session) == [("test-kaynak", 3, 3)]
    runs = session.scalars(select(ScrapeRun).order_by(ScrapeRun.id)).all()
    assert [(r.status, r.inserted, r.duplicates) for r in runs] == [
        (ScrapeStatus.SUCCESS, 2, 0),
        (ScrapeStatus.SUCCESS, 1, 2),
    ]


def test_inactive_import_is_kept_out_of_stats(session: Session) -> None:
    run_import(session, SOURCE, [posting("old", "Legacy PHP")], active=False)
    assert session.scalar(select(JobPosting.is_active).where(JobPosting.external_id == "old")) is False
    assert source_counts(session) == [("test-kaynak", 0, 1)]


def test_failed_source_is_recorded(session: Session) -> None:
    def broken() -> Iterator[Posting]:
        yield posting("1", "ok")
        raise RuntimeError("kaynak 403 döndü")

    with pytest.raises(RuntimeError):
        run_import(session, SOURCE, broken())

    run = session.scalars(select(ScrapeRun)).one()
    assert run.status == ScrapeStatus.FAILED
    assert run.error_log == "RuntimeError: kaynak 403 döndü"
    assert run.finished_at is not None
