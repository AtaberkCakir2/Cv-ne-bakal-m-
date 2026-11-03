"""role_skill_stats yenileme ve okuma (T-045). Sadece TEST_DATABASE_URL ile çalışır (test_store.py ile aynı düzen)."""

import argparse
import os
from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from collector.posting import Posting, SourceInfo
from collector.store import run_import
from collector.taxonomy import load_roles, load_skills, seed
from etl import stats
from etl.pipeline import normalize

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "backend" / "app" / "db" / "alembic.ini"
SOURCE = SourceInfo(name="test-kaynak", type="api", base_url="https://example.com", rate_limit_sec=1.5)
TODAY = date.today()

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
        with Session(bind=conn, join_transaction_mode="create_savepoint") as s:
            seed(s, load_skills(), load_roles())
            yield s
        trans.rollback()


def posting(external_id: str, title: str, text: str, posted_at: date = TODAY) -> Posting:
    return Posting(
        external_id=external_id,
        title_raw=title,
        description_clean=text,
        language="en",
        company=f"Şirket {external_id}",  # benzer ilan temizliği devreye girmesin
        posted_at=posted_at,
    )


def load(session: Session) -> None:
    run_import(
        session,
        SOURCE,
        [
            posting("1", "Backend Engineer", "We use Python and Docker."),
            posting("2", "Backend Developer", "Python services."),
            posting("3", "Backend Engineer", "Python and Kubernetes, old posting.", TODAY - timedelta(days=400)),
            posting("4", "Frontend Engineer", "React and TypeScript."),
            posting("5", "Software Engineer", "Python, but no role."),
        ],
    )
    # Pasif ilan (ör. EMSCAD yedek seti) istatistiğe girmez.
    run_import(session, SOURCE, [posting("6", "Backend Engineer", "Python and Go, inactive.")], active=False)
    normalize(session, load_skills(), load_roles())


def test_refresh_counts_recent_active_postings_with_role(session: Session) -> None:
    load(session)
    assert stats.refresh(session) > 0

    backend = {d.skill: (d.posting_count, d.demand_ratio) for d in stats.top_skills(session, "backend-developer")}
    # 2 ilan: eski (400 gün), pasif ve pozisyonsuz ilanlar sayılmaz.
    assert backend == {"Python": (2, Decimal("1.0000")), "Docker": (1, Decimal("0.5000"))}
    frontend = [d.skill for d in stats.top_skills(session, "frontend-developer")]
    assert set(frontend) == {"React", "TypeScript"}


def test_summaries_flag_low_data_and_include_roles_without_postings(session: Session) -> None:
    load(session)
    stats.refresh(session)
    by_slug = {s.slug: s for s in stats.summaries(session, top=1)}

    assert by_slug["backend-developer"].total_postings == 2
    assert by_slug["backend-developer"].top_skills[0].skill == "Python"
    assert by_slug["backend-developer"].low_data  # 2 < MIN_POSTINGS
    assert by_slug["game-developer"].total_postings == 0
    assert len(by_slug) == len(load_roles())


def test_refresh_is_repeatable(session: Session) -> None:
    load(session)
    first = stats.refresh(session)  # ikinci yenileme CONCURRENTLY yolundan geçer
    assert stats.refresh(session) == first
