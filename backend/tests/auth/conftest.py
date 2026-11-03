"""Kimlik doğrulama testleri gerçek PostgreSQL ister; TEST_DATABASE_URL yoksa atlanır (CI'da verilir).

Boş bir test veritabanı verin (backend/app/db/README.md, "Testler"). Şema `alembic upgrade head` ile kurulur,
her testten önce kullanıcı tabloları boşaltılır.
"""

import argparse
import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

_DB_PACKAGES = ("sqlalchemy", "alembic", "pgvector")
if not all(importlib.util.find_spec(pkg) for pkg in _DB_PACKAGES):
    collect_ignore_glob = ["test_*.py"]
else:
    from alembic import command
    from alembic.config import Config
    from fastapi import FastAPI
    from sqlalchemy import Engine, create_engine, text
    from sqlalchemy.orm import Session, sessionmaker

    from app.api.deps import get_db
    from app.services.email import OutboxEmailSender

    TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
    ALEMBIC_INI = Path(__file__).resolve().parents[2] / "app" / "db" / "alembic.ini"

    @pytest.fixture(scope="session")
    def db_engine() -> Iterator[Engine]:
        if not TEST_DATABASE_URL:
            pytest.skip("TEST_DATABASE_URL verilmedi")
        cfg = Config(str(ALEMBIC_INI))
        # env.py adresi `-x url=...` argümanından okur (tests/db ile aynı yöntem).
        cfg.cmd_opts = argparse.Namespace(x=[f"url={TEST_DATABASE_URL}"])
        command.upgrade(cfg, "head")
        engine = create_engine(TEST_DATABASE_URL, hide_parameters=True)
        yield engine
        engine.dispose()

    @pytest.fixture
    def db_sessionmaker(db_engine: Engine) -> sessionmaker[Session]:
        with db_engine.begin() as conn:
            conn.execute(text("TRUNCATE users, refresh_tokens, user_tokens, consents RESTART IDENTITY CASCADE"))
        return sessionmaker(bind=db_engine, expire_on_commit=False)

    @pytest.fixture
    def auth_app(app: FastAPI, db_sessionmaker: sessionmaker[Session]) -> FastAPI:
        def _db() -> Iterator[Session]:
            session = db_sessionmaker()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = _db
        app.state.email_sender = OutboxEmailSender()
        return app
