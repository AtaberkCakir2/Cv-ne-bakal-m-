"""En az yetkili uygulama rolü (T-075): infra/pc/app-role.sql production'da API ve veri işçisinin rolünü kurar.

test_migrations.py gibi TEST_DATABASE_URL ister ve o veritabanını sıfırlar (ayrı, boş test veritabanı kullanın).
Rol küme genelidir (careerai_app); betik tekrar çalıştırılabilir olduğu için testler arasında kalması sorun değil.
"""

import argparse
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, make_url, select, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.db.models import AuditLog, User

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "app" / "db" / "alembic.ini"
ROLE_SQL = Path(__file__).resolve().parents[3] / "infra" / "pc" / "app-role.sql"
APP_PASSWORD = "test-uygulama-parolasi"  # noqa: S105 — sadece test veritabanında

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL verilmedi")


def apply_role_sql(engine: Engine) -> None:
    # deploy.sh şifreyi psql değişkeniyle verir; burada aynı yere sabit değer konur.
    sql = ROLE_SQL.read_text(encoding="utf-8").replace(":'app_pw'", f"'{APP_PASSWORD}'")
    # Sürücüye parametresiz verilir: SQL'deki `%I` (format) yer tutucu sanılmasın.
    raw = engine.raw_connection()
    try:
        raw.driver_connection.execute(sql)  # type: ignore[union-attr]
        raw.commit()
    finally:
        raw.close()


@pytest.fixture(scope="module")
def owner_engine() -> Iterator[Engine]:
    assert TEST_DATABASE_URL
    cfg = Config(str(ALEMBIC_INI))
    cfg.cmd_opts = argparse.Namespace(x=[f"url={TEST_DATABASE_URL}"])
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    eng = create_engine(TEST_DATABASE_URL)
    apply_role_sql(eng)
    apply_role_sql(eng)  # her deploy'da tekrar çalışır
    yield eng
    eng.dispose()


@pytest.fixture
def app_session(owner_engine: Engine) -> Iterator[Session]:
    assert TEST_DATABASE_URL
    url = make_url(TEST_DATABASE_URL).set(username="careerai_app", password=APP_PASSWORD)
    eng = create_engine(url)
    with Session(eng) as session:
        yield session
        session.rollback()
    eng.dispose()


def test_role_has_no_admin_attributes(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname = 'careerai_app'"
            )
        ).one()
    assert not any(row)


def test_app_can_read_and_write_data(app_session: Session) -> None:
    user = User(email="uygulama@example.com", password_hash="x")  # noqa: S106 — sahte test verisi
    app_session.add(user)
    app_session.flush()
    app_session.add(AuditLog(user_id=user.id, action="test"))
    app_session.flush()
    assert app_session.scalar(select(User.id).where(User.email == "uygulama@example.com")) == user.id


def test_app_can_delete_user_with_audit_rows(app_session: Session) -> None:
    # audit_logs'ta UPDATE yetkisi yok; user_id'yi NULL yapan FK işlemi yine de çalışmalı.
    user = User(email="silinecek@example.com", password_hash="x")  # noqa: S106
    app_session.add(user)
    app_session.flush()
    app_session.add(AuditLog(user_id=user.id, action="account.delete"))
    app_session.flush()
    app_session.delete(user)
    app_session.flush()
    assert app_session.scalar(select(AuditLog.user_id).where(AuditLog.action == "account.delete")) is None


def test_app_refreshes_stats_only_through_function(app_session: Session) -> None:
    app_session.execute(text("SELECT refresh_role_skill_stats(false)"))
    app_session.execute(text("SELECT refresh_role_skill_stats(true)"))
    with pytest.raises(ProgrammingError, match="must be owner"):
        app_session.execute(text("REFRESH MATERIALIZED VIEW role_skill_stats"))


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TABLE kotu (id int)",
        "DROP TABLE users",
        "ALTER TABLE users ADD COLUMN x int",
        "TRUNCATE users CASCADE",
        "UPDATE audit_logs SET action = 'degisti'",
        "DELETE FROM audit_logs",
        "SELECT * FROM alembic_version",
    ],
)
def test_app_cannot_change_schema_or_history(app_session: Session, statement: str) -> None:
    with pytest.raises(ProgrammingError, match="permission denied|must be owner"):
        app_session.execute(text(statement))


def test_refresh_function_is_not_public(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        public_exec = conn.scalar(
            text("SELECT has_function_privilege('public', 'refresh_role_skill_stats(boolean)', 'EXECUTE')")
        )
    assert public_exec is False
