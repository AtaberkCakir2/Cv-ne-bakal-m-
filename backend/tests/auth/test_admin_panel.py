"""Yönetim paneli (T-063, app/admin): sadece admin girer, ilan kaynağı açma kuralı, kaynak doğrulama, denetim kaydı.

Gerçek PostgreSQL ister (tests/auth/conftest.py); fikstürler kullanıcı tablolarını boşaltır, panel tablolarını bu
dosya boşaltır.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.admin import mount_admin, promote
from app.admin.formatting import dt_column, fmt_dt
from app.admin.promote import set_role
from app.core.rate_limit import MemoryCounterStore, RateLimiter
from app.core.security import hash_password
from app.db.enums import ResourceProvider, ScrapeStatus, SkillCategory, SourceType, UserRole
from app.db.models import AuditLog, JobSource, Resource, ScrapeRun, Skill, User
from tests.conftest import TEST_SETTINGS

PASSWORD = "Test-parola-123"  # noqa: S105 — test verisi


@pytest.fixture
def maker(db_sessionmaker: sessionmaker[Session], db_engine: Engine) -> sessionmaker[Session]:
    with db_engine.begin() as conn:
        conn.execute(text("TRUNCATE job_sources, scrape_runs, resources, skills, audit_logs RESTART IDENTITY CASCADE"))
    return db_sessionmaker


@pytest.fixture
def panel(maker: sessionmaker[Session]) -> Iterator[TestClient]:
    app = FastAPI()
    mount_admin(app, TEST_SETTINGS, maker)
    with TestClient(app) as client:
        yield client


def add_user(maker: sessionmaker[Session], email: str, role: UserRole) -> User:
    with maker() as s:
        user = User(email=email, password_hash=hash_password(PASSWORD), role=role, is_verified=True)
        s.add(user)
        s.commit()
        return user


def login(client: TestClient, email: str, password: str = PASSWORD) -> int:
    r = client.post("/admin/login", data={"username": email, "password": password}, follow_redirects=False)
    return int(r.status_code)


def audit_actions(maker: sessionmaker[Session]) -> list[str]:
    with maker() as s:
        return list(s.scalars(select(AuditLog.action).order_by(AuditLog.id)))


def test_anonymous_is_redirected_to_login(panel: TestClient) -> None:
    for path in ("/admin/", "/admin/istatistik", "/admin/resource/list", "/admin/job-source/list"):
        r = panel.get(path, follow_redirects=False)
        assert r.status_code == 302 and r.headers["location"].endswith("/admin/login"), path


def test_normal_user_cannot_log_in(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "ogrenci@ornek.com", UserRole.USER)
    assert login(panel, "ogrenci@ornek.com") == 400
    assert panel.get("/admin/istatistik", follow_redirects=False).status_code == 302
    assert audit_actions(maker) == []


def test_wrong_password_and_unknown_email_fail(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    assert login(panel, "admin@ornek.com", "yanlis-parola") == 400
    assert login(panel, "yok@ornek.com") == 400


def test_admin_sees_pages_and_login_is_audited(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    assert login(panel, "ADMIN@ornek.com") == 302  # e-posta büyük/küçük harf duyarsız (CITEXT)
    page = panel.get("/admin/istatistik")
    assert page.status_code == 200 and "İstatistikler" in page.text
    for path in ("/admin/resource/list", "/admin/job-source/list", "/admin/scrape-run/list"):
        assert panel.get(path).status_code == 200, path
    assert audit_actions(maker) == ["admin.login"]
    # Kişisel veri ekranı yok.
    assert panel.get("/admin/user/list").status_code == 404


def test_demoted_admin_is_logged_out(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    assert login(panel, "admin@ornek.com") == 302
    with maker() as s:
        assert set_role(s, "admin@ornek.com", UserRole.USER)
    assert panel.get("/admin/istatistik", follow_redirects=False).status_code == 302
    assert audit_actions(maker) == ["admin.login", "admin.revoke"]


def test_session_cookie_is_strict_and_scoped(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    r = panel.post("/admin/login", data={"username": "admin@ornek.com", "password": PASSWORD}, follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "careerai_admin=" in cookie and "path=/admin" in cookie and "samesite=strict" in cookie
    assert "httponly" in cookie


def _source(maker: sessionmaker[Session], *, tos_checked: bool) -> int:
    with maker() as s:
        src = JobSource(name="Ornek", type=SourceType.API, tos_checked=tos_checked, is_active=False)
        s.add(src)
        s.flush()
        s.add(ScrapeRun(source_id=src.id, started_at=datetime.now(UTC), status=ScrapeStatus.SUCCESS, fetched=3))
        s.commit()
        return src.id


def _is_active(maker: sessionmaker[Session], source_id: int) -> bool:
    with maker() as s:
        return bool(s.get_one(JobSource, source_id).is_active)


def test_source_without_tos_review_cannot_be_activated(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    login(panel, "admin@ornek.com")
    sid = _source(maker, tos_checked=False)
    r = panel.post(f"/admin/job-source/edit/{sid}", data={"is_active": "y", "rate_limit_sec": "4"})
    assert "incelenmemiş" in r.text
    assert not _is_active(maker, sid)


def test_reviewed_source_can_be_toggled_and_change_is_audited(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    login(panel, "admin@ornek.com")
    sid = _source(maker, tos_checked=True)
    r = panel.post(f"/admin/job-source/edit/{sid}", data={"is_active": "y", "rate_limit_sec": "-1"})
    assert "0 ile 999.9" in r.text and not _is_active(maker, sid)
    # 1 saniyenin altı geçerli (ör. hacker-news 0.2).
    r = panel.post(
        f"/admin/job-source/edit/{sid}", data={"is_active": "y", "rate_limit_sec": "0.2"}, follow_redirects=False
    )
    assert r.status_code == 302
    assert _is_active(maker, sid)
    assert audit_actions(maker) == ["admin.login", "admin.update"]
    # Kaynak silinemez, yeni kaynak panelden eklenemez (ilanlar CASCADE ile silinirdi).
    assert panel.get("/admin/job-source/create").status_code in (403, 404)
    assert panel.get("/admin/istatistik").status_code == 200


def _skill(maker: sessionmaker[Session]) -> int:
    with maker() as s:
        skill = Skill(canonical_name="Python", slug="python", category=SkillCategory.DIL)
        s.add(skill)
        s.commit()
        return skill.id


def _resource_form(skill_id: int, url: str) -> dict[str, str]:
    return {
        "skill": str(skill_id),
        "title": "Python'a giriş",
        "url": url,
        "provider": ResourceProvider.DOCS.value,
        "language": "tr",
        "level": "beginner",
        "is_free": "y",
        "is_alive": "y",
    }


def test_resource_needs_https_url(panel: TestClient, maker: sessionmaker[Session]) -> None:
    add_user(maker, "admin@ornek.com", UserRole.ADMIN)
    login(panel, "admin@ornek.com")
    skill_id = _skill(maker)

    r = panel.post("/admin/resource/create", data=_resource_form(skill_id, "http://ornek.com/python"))
    assert "https://" in r.text
    r = panel.post("/admin/resource/create", data={**_resource_form(skill_id, "https://ornek.com/x"), "skill": ""})
    assert 'class="form-control is-invalid" data-role="select2-ajax"' in r.text  # yetkinlik zorunlu
    r = panel.post(
        "/admin/resource/create", data=_resource_form(skill_id, "  https://ornek.com/python "), follow_redirects=False
    )
    assert r.status_code == 302
    with maker() as s:
        assert s.scalars(select(Resource.url)).all() == ["https://ornek.com/python"]
    assert audit_actions(maker) == ["admin.login", "admin.create"]


def test_promote_unknown_email(maker: sessionmaker[Session]) -> None:
    with maker() as s:
        assert not set_role(s, "yok@ornek.com", UserRole.ADMIN)


def test_login_attempts_are_rate_limited(maker: sessionmaker[Session]) -> None:
    settings = TEST_SETTINGS.model_copy(update={"rate_limit_auth_per_minute": 2})
    app = FastAPI()
    app.state.rate_limiter = RateLimiter(MemoryCounterStore(), settings)
    mount_admin(app, settings, maker)
    with TestClient(app) as client:
        assert [login(client, "yok@ornek.com") for _ in range(3)] == [400, 400, 429]


def test_promote_cli(
    maker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_user(maker, "ogrenci@ornek.com", UserRole.USER)
    monkeypatch.setattr(promote, "get_sessionmaker", lambda: maker)

    assert promote.main(["ogrenci@ornek.com"]) == 0
    assert "admin" in capsys.readouterr().out
    assert promote.main(["ogrenci@ornek.com", "--revoke"]) == 0
    assert promote.main(["yok@ornek.com"]) == 1
    assert audit_actions(maker) == ["admin.grant", "admin.revoke"]


def test_dates_are_shown_in_turkey_time() -> None:
    assert fmt_dt(None) == "—"
    assert fmt_dt(datetime(2026, 11, 15, 21, 30, 59, tzinfo=UTC)) == "16.11.2026 00:30"
    assert fmt_dt(datetime(2026, 11, 15, 21, 30)) == "16.11.2026 00:30"  # saat dilimsiz = UTC
    run = ScrapeRun(started_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert dt_column(run, "started_at") == "01.01.2026 03:00"
