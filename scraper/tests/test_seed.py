"""Taksonominin veritabanına yazılması. Sadece TEST_DATABASE_URL verilince çalışır (test_store.py ile aynı düzen)."""

import argparse
import os
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.models import Role, Skill
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session

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
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as conn:
        trans = conn.begin()
        with Session(bind=conn, join_transaction_mode="create_savepoint") as s:
            yield s
        trans.rollback()


def test_seed_is_idempotent(session: Session) -> None:
    skills, roles = load_skills(), load_roles()
    first = seed(session, skills, roles)
    assert (first.skills_added, first.roles_added) == (len(skills), len(roles))

    second = seed(session, skills, roles)
    assert (second.skills_added, second.skills_updated, second.roles_added, second.roles_updated) == (0, 0, 0, 0)

    js = session.scalars(select(Skill).where(Skill.slug == "javascript")).one()
    assert js.canonical_name == "JavaScript" and "js" in js.synonyms
    assert (session.scalar(select(func.count(Role.id)).where(Role.is_active)) or 0) >= 10


def test_removed_skill_is_deactivated_and_changes_are_applied(session: Session) -> None:
    skills, roles = load_skills(), load_roles()
    seed(session, skills, roles)

    without_cobol = [s for s in skills if s.slug != "cobol"]
    renamed = [replace(s, synonyms=(*s.synonyms, "py3")) if s.slug == "python" else s for s in without_cobol]
    result = seed(session, renamed, roles)

    assert (result.skills_deactivated, result.skills_updated) == (1, 1)
    cobol = session.scalars(select(Skill).where(Skill.slug == "cobol")).one()
    assert cobol.is_active is False  # silinmez: ilan ve analizler ona bağlı olabilir
    python = session.scalars(select(Skill).where(Skill.slug == "python")).one()
    assert "py3" in python.synonyms

    seed(session, skills, roles)  # geri eklenince tekrar aktif
    session.refresh(cobol)
    assert cobol.is_active is True
