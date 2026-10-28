"""normalize ve sözleşme çıktısı. Sadece TEST_DATABASE_URL verilince çalışır (test_store.py ile aynı düzen)."""

import argparse
import json
import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.models import JobPosting, JobPostingSkill, Role
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session

from collector.posting import Posting, SourceInfo
from collector.store import run_import
from collector.taxonomy import load_roles, load_skills, seed
from etl.pipeline import iter_contract, normalize

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
REPO = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO / "backend" / "app" / "db" / "alembic.ini"
EXAMPLE = REPO / "contracts" / "examples" / "job_posting.example.json"
SOURCE = SourceInfo(name="test-kaynak", type="api", base_url="https://example.com", rate_limit_sec=1.5)
LONG = " ".join(f"kelime{i}" for i in range(200))

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


def posting(external_id: str, title: str, text: str, day: int = 1) -> Posting:
    return Posting(
        external_id=external_id,
        title_raw=title,
        description_clean=text,
        language="tr",
        company="Örnek Teknoloji A.Ş.",
        posted_at=date(2026, 10, day),
    )


def test_normalize_sets_role_skills_and_deactivates_near_duplicates(session: Session) -> None:
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    run_import(
        session,
        SOURCE,
        [
            posting("1", example["title_raw"], example["description_clean"]),
            posting("2", "Backend Engineer", f"Go ile servis. {LONG}", day=1),
            posting("3", "Backend Engineer", f"Go ile servis. {LONG} yeni", day=20),  # 2'nin güncel hali
            posting("4", "Software Engineer", "Genel ilan, Rust."),
        ],
    )

    result = normalize(session, load_skills(), load_roles())
    assert (result.postings, result.with_role, result.deactivated) == (4, 3, 1)

    roles: dict[str, str] = dict(
        session.execute(select(JobPosting.external_id, Role.slug).join(Role, Role.id == JobPosting.role_id))
        .tuples()
        .all()
    )
    assert roles == {"1": "backend-developer", "2": "backend-developer", "3": "backend-developer"}
    active = set(session.scalars(select(JobPosting.external_id).where(JobPosting.is_active)))
    assert active == {"1", "3", "4"}  # eski kopya pasif, en yenisi kalır

    # Tekrar çalıştırmak bağları çoğaltmaz, pasif ilanı geri açmaz.
    links = session.scalar(select(func.count()).select_from(JobPostingSkill))
    again = normalize(session, load_skills(), load_roles())
    assert session.scalar(select(func.count()).select_from(JobPostingSkill)) == links
    assert again.deactivated == 0
    assert set(session.scalars(select(JobPosting.external_id).where(JobPosting.is_active))) == active


def test_contract_output_matches_example(session: Session) -> None:
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    run_import(session, SOURCE, [posting("1", example["title_raw"], example["description_clean"])])
    normalize(session, load_skills(), load_roles())

    [item] = list(iter_contract(session))
    assert item.keys() == example.keys()
    assert item["role_slug"] == example["role_slug"]
    assert {s["skill"]: s["importance"] for s in example["skills"]}.items() <= {
        s["skill"]: s["importance"] for s in item["skills"]
    }.items()
    # Önce required, sonra preferred.
    importances = [s["importance"] for s in item["skills"]]
    assert importances == sorted(importances, key=lambda i: i != "required")


def test_name_masker_hook_updates_description(session: Session) -> None:
    run_import(session, SOURCE, [posting("1", "Backend Engineer", "İletişim: Ayşe Yılmaz. Python.")])
    result = normalize(
        session, load_skills(), load_roles(), mask_names=lambda text, _lang: text.replace("Ayşe Yılmaz", "[isim]")
    )
    assert result.masked == 1
    assert session.scalar(select(JobPosting.description_clean)) == "İletişim: [isim]. Python."
