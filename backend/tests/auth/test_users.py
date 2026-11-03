"""T-049 profil ve KVKK uçları; gerçek PostgreSQL üzerinde (tests/auth/conftest.py)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import AnalysisStatus, SkillCategory, SkillKind
from app.db.models import Analysis, AnalysisSkill, AuditLog, Consent, RefreshToken, Role, Skill, User
from app.services.users import anonymized_email, purge_deleted_users
from tests.auth.test_auth_flow import API, CONSENTS, EMAIL, PASSWORD, bearer, login, register


@pytest.fixture
def client(auth_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(auth_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def role(db_sessionmaker: sessionmaker[Session]) -> Role:
    # roles tablosu testler arasında boşaltılmaz; varsa olanı kullan.
    with db_sessionmaker() as s:
        found = s.scalar(select(Role).where(Role.slug == "test-backend"))
        if found is None:
            found = Role(name="Test Backend", slug="test-backend")
            s.add(found)
            s.commit()
        return found


def signed_in(client: TestClient) -> dict[str, str]:
    register(client)
    return bearer(login(client)["access_token"])


def test_me_includes_target_role(client: TestClient) -> None:
    headers = signed_in(client)
    body = client.get(f"{API}/users/me", headers=headers).json()
    assert body["email"] == EMAIL
    assert body["target_role"] is None


def test_patch_updates_only_sent_fields(client: TestClient, role: Role) -> None:
    headers = signed_in(client)
    response = client.patch(f"{API}/users/me", headers=headers, json={"full_name": "  Deneme Öğrenci  "})
    assert response.status_code == 200
    assert response.json()["full_name"] == "Deneme Öğrenci"

    body = client.patch(f"{API}/users/me", headers=headers, json={"target_role_id": role.id}).json()
    assert body["target_role"] == {"id": role.id, "slug": "test-backend", "name": "Test Backend"}
    assert body["full_name"] == "Deneme Öğrenci"  # gönderilmeyen alan değişmedi

    body = client.patch(f"{API}/users/me", headers=headers, json={"target_role_id": None, "full_name": ""}).json()
    assert body["target_role"] is None and body["full_name"] is None


def test_patch_rejects_unknown_or_inactive_role(
    client: TestClient, role: Role, db_sessionmaker: sessionmaker[Session]
) -> None:
    headers = signed_in(client)
    assert client.patch(f"{API}/users/me", headers=headers, json={"target_role_id": 999_999}).status_code == 422
    with db_sessionmaker() as s:
        s.get_one(Role, role.id).is_active = False
        s.commit()
    try:
        assert client.patch(f"{API}/users/me", headers=headers, json={"target_role_id": role.id}).status_code == 422
    finally:
        with db_sessionmaker() as s:
            s.get_one(Role, role.id).is_active = True
            s.commit()


def test_consents_are_versioned_and_never_overwritten(client: TestClient) -> None:
    headers = signed_in(client)
    assert len(client.get(f"{API}/users/me/consents", headers=headers).json()) == 3

    new = {"consents": [{"consent_type": "kvkk_aydinlatma", "version": "2027-01"}]}
    after = client.post(f"{API}/users/me/consents", headers=headers, json=new).json()
    assert len(after) == 4
    assert {c["version"] for c in after if c["consent_type"] == "kvkk_aydinlatma"} == {"2026-12", "2027-01"}

    # Aynı sürüm tekrar gelirse yeni satır eklenmez (500 de vermez).
    assert len(client.post(f"{API}/users/me/consents", headers=headers, json=new).json()) == 4
    dup = {"consents": [CONSENTS[0], CONSENTS[0]]}
    assert client.post(f"{API}/users/me/consents", headers=headers, json=dup).status_code == 422


def test_export_contains_my_data_but_not_secrets(
    client: TestClient, role: Role, db_sessionmaker: sessionmaker[Session]
) -> None:
    headers = signed_in(client)
    with db_sessionmaker() as s:
        user = s.scalars(select(User)).one()
        skill = s.scalar(select(Skill).where(Skill.slug == "test-python"))
        if skill is None:
            skill = Skill(canonical_name="TestPython", slug="test-python", category=SkillCategory.DIL)
            s.add(skill)
            s.flush()
        analysis = Analysis(
            user_id=user.id, target_role_id=role.id, status=AnalysisStatus.DONE, cv_sha256="a" * 64, cv_pages=2
        )
        s.add(analysis)
        s.flush()
        s.add(AnalysisSkill(analysis_id=analysis.id, skill_id=skill.id, kind=SkillKind.PRESENT))
        s.commit()

    response = client.get(f"{API}/users/me/export", headers=headers)
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["profile"]["email"] == EMAIL
    assert len(data["consents"]) == 3 and len(data["sessions"]) == 1
    assert data["analyses"][0]["cv_sha256"] == "a" * 64
    assert data["analyses"][0]["skills"][0]["skill"] == "TestPython"
    text = response.text
    for secret in ("password_hash", "token_hash", "ip_hash", "argon2"):
        assert secret not in text
    with db_sessionmaker() as s:
        assert s.scalar(select(AuditLog.action).where(AuditLog.action == "data.export")) == "data.export"


def test_delete_requires_password(client: TestClient) -> None:
    headers = signed_in(client)
    response = client.request("DELETE", f"{API}/users/me", headers=headers, json={"password": "yanlis-parola"})
    assert response.status_code == 403  # 401 değil: istemci oturumu yenilemeye çalışmasın
    assert client.get(f"{API}/users/me", headers=headers).status_code == 200


def test_delete_anonymizes_immediately_and_ends_sessions(
    client: TestClient, db_sessionmaker: sessionmaker[Session]
) -> None:
    register(client)
    tokens = login(client)
    headers = bearer(tokens["access_token"])
    assert client.request("DELETE", f"{API}/users/me", headers=headers, json={"password": PASSWORD}).status_code == 204

    assert client.get(f"{API}/users/me", headers=headers).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    with db_sessionmaker() as s:
        user = s.scalars(select(User)).one()
        assert user.deleted_at is not None
        assert user.email == anonymized_email(user.id) and user.full_name is None
        assert all(t.revoked_at is not None for t in s.scalars(select(RefreshToken)))
        assert s.scalar(select(AuditLog.action).where(AuditLog.action == "account.delete")) == "account.delete"
    # E-posta serbest kaldı: aynı adresle yeniden kayıt olunabilir.
    register(client)


def test_purge_removes_only_accounts_deleted_over_30_days_ago(
    client: TestClient, db_sessionmaker: sessionmaker[Session]
) -> None:
    register(client, email="eski@example.com")
    register(client, email="yeni@example.com")
    now = datetime.now(UTC)
    with db_sessionmaker() as s:
        users = {u.email: u for u in s.scalars(select(User))}
        users["eski@example.com"].deleted_at = now - timedelta(days=31)
        users["yeni@example.com"].deleted_at = now - timedelta(days=29)
        old_id = users["eski@example.com"].id
        s.add(AuditLog(user_id=old_id, action="login"))
        s.commit()

    with db_sessionmaker() as s:
        assert purge_deleted_users(s, now) == 1
    with db_sessionmaker() as s:
        assert {u.email for u in s.scalars(select(User))} == {"yeni@example.com"}
        assert s.scalars(select(Consent).where(Consent.user_id == old_id)).all() == []  # CASCADE
        log = s.scalar(select(AuditLog).where(AuditLog.action == "login"))
        assert log is not None and log.user_id is None  # kayıt kalır, kişi bağı kopar


def add_analysis(db_sessionmaker: sessionmaker[Session], email: str, role: Role) -> None:
    with db_sessionmaker() as s:
        user = s.scalars(select(User).where(User.email == email)).one()
        s.add(Analysis(user_id=user.id, target_role_id=role.id, status=AnalysisStatus.QUEUED, cv_sha256="b" * 64))
        s.commit()


def test_patch_rejects_unknown_fields(client: TestClient) -> None:
    headers = signed_in(client)
    assert client.patch(f"{API}/users/me", headers=headers, json={"email": "x@example.com"}).status_code == 422


def test_export_shows_only_my_data(client: TestClient, role: Role, db_sessionmaker: sessionmaker[Session]) -> None:
    register(client, email="baskasi@example.com")
    add_analysis(db_sessionmaker, "baskasi@example.com", role)
    headers = signed_in(client)
    data = client.get(f"{API}/users/me/export", headers=headers).json()
    assert data["analyses"] == [] and len(data["consents"]) == 3 and len(data["sessions"]) == 1
    assert [a["action"] for a in data["activity"]] == []  # dışa aktarma kaydı, bu yanıt üretildikten sonra yazılır
    assert len(client.get(f"{API}/users/me/consents", headers=headers).json()) == 3


def test_after_delete_nothing_identifying_remains_and_old_token_cannot_write(
    client: TestClient, role: Role, db_sessionmaker: sessionmaker[Session]
) -> None:
    headers = signed_in(client)
    add_analysis(db_sessionmaker, EMAIL, role)
    assert client.request("DELETE", f"{API}/users/me", headers=headers, json={"password": PASSWORD}).status_code == 204

    assert client.patch(f"{API}/users/me", headers=headers, json={"full_name": "Geri"}).status_code == 401
    new = {"consents": [{"consent_type": "kvkk_aydinlatma", "version": "2027-01"}]}
    assert client.post(f"{API}/users/me/consents", headers=headers, json=new).status_code == 401
    with db_sessionmaker() as s:
        assert all(t.user_agent is None for t in s.scalars(select(RefreshToken)))
        assert all(a.deleted_at is not None for a in s.scalars(select(Analysis)))
        assert len(s.scalars(select(Consent)).all()) == 3  # yeni rıza eklenmedi


def test_wrong_password_on_delete_is_audited(client: TestClient, db_sessionmaker: sessionmaker[Session]) -> None:
    headers = signed_in(client)
    client.request("DELETE", f"{API}/users/me", headers=headers, json={"password": "x"})
    with db_sessionmaker() as s:
        assert s.scalar(select(AuditLog.action).where(AuditLog.action == "account.delete_failed"))


def test_purge_cascades_to_analyses_and_sessions(
    client: TestClient, role: Role, db_sessionmaker: sessionmaker[Session]
) -> None:
    headers = signed_in(client)
    add_analysis(db_sessionmaker, EMAIL, role)
    client.request("DELETE", f"{API}/users/me", headers=headers, json={"password": PASSWORD})
    with db_sessionmaker() as s:
        assert purge_deleted_users(s, datetime.now(UTC) + timedelta(days=31)) == 1
    with db_sessionmaker() as s:
        assert s.scalars(select(User)).all() == []
        assert s.scalars(select(Analysis)).all() == [] and s.scalars(select(RefreshToken)).all() == []
