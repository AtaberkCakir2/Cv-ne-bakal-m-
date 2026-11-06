"""T-037 kimlik doğrulama akışları; gerçek PostgreSQL üzerinde (tests/auth/conftest.py)."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import AdminUser
from app.core.security import create_access_token, hash_ip
from app.db.enums import UserRole
from app.db.models import Consent, RefreshToken, User
from app.services.email import EmailMessage, OutboxEmailSender
from tests.conftest import TEST_SETTINGS

API = "/api/v1"
EMAIL = "ogrenci@example.com"
PASSWORD = "dogru-parola-123"
CONSENTS = [
    {"consent_type": "kvkk_aydinlatma", "version": "2026-12"},
    {"consent_type": "acik_riza", "version": "2026-12"},
    {"consent_type": "kullanim_kosullari", "version": "2026-12"},
]


@pytest.fixture
def client(auth_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(auth_app, raise_server_exceptions=False) as c:
        yield c


def outbox(app: FastAPI) -> OutboxEmailSender:
    sender: OutboxEmailSender = app.state.email_sender
    return sender


def token_from_last_mail(app: FastAPI) -> str:
    return parse_qs(urlparse(outbox(app).outbox[-1].link).query)["token"][0]


def register(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> str:
    response = client.post(f"{API}/auth/register", json={"email": email, "password": password, "consents": CONSENTS})
    assert response.status_code == 201, response.text
    return str(response.json()["user_id"])


def login(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> dict[str, str]:
    response = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    data: dict[str, str] = response.json()
    return data


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- kayıt


def test_register_stores_argon2_hash_consents_and_sends_verification(
    client: TestClient, auth_app: FastAPI, db_sessionmaker: sessionmaker[Session]
) -> None:
    user_id = register(client)
    with db_sessionmaker() as s:
        user = s.scalars(select(User)).one()
        assert str(user.id) == user_id
        assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
        assert user.is_verified is False and user.role == UserRole.USER
        consents = s.scalars(select(Consent)).all()
        assert {c.consent_type.value for c in consents} == {c["consent_type"] for c in CONSENTS}
        expected_ip_hash = hash_ip("testclient", TEST_SETTINGS)  # TestClient istemci adresi
        assert expected_ip_hash and all(c.ip_hash == expected_ip_hash for c in consents)  # açık IP saklanmaz
    mail = outbox(auth_app).outbox[-1]
    assert mail.to == EMAIL and "/e-posta-dogrula?token=" in mail.link


def test_register_requires_all_consents(client: TestClient) -> None:
    response = client.post(
        f"{API}/auth/register", json={"email": EMAIL, "password": PASSWORD, "consents": CONSENTS[:2]}
    )
    assert response.status_code == 422
    assert "kullanim_kosullari" in response.json()["detail"]


def test_register_rejects_duplicate_consent(client: TestClient) -> None:
    response = client.post(
        f"{API}/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "consents": [*CONSENTS, CONSENTS[0]]},
    )
    assert response.status_code == 422


def test_register_duplicate_email_is_case_insensitive(client: TestClient) -> None:
    register(client)
    response = client.post(
        f"{API}/auth/register", json={"email": EMAIL.upper(), "password": PASSWORD, "consents": CONSENTS}
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(f"{API}/auth/register", json={"email": EMAIL, "password": "kisa", "consents": CONSENTS})
    assert response.status_code == 422


# --- e-posta doğrulama


def test_verify_email_is_single_use(client: TestClient, auth_app: FastAPI) -> None:
    register(client)
    token = token_from_last_mail(auth_app)
    assert client.post(f"{API}/auth/verify-email", json={"token": token}).status_code == 204
    me = client.get(f"{API}/users/me", headers=bearer(login(client)["access_token"])).json()
    assert me["is_verified"] is True
    assert client.post(f"{API}/auth/verify-email", json={"token": token}).status_code == 400
    assert client.post(f"{API}/auth/verify-email", json={"token": "uydurma"}).status_code == 400


# --- giriş


def test_login_and_me(client: TestClient) -> None:
    register(client)
    tokens = login(client, email="  OGRENCI@example.com ")  # büyük harf ve boşluk normalize edilir
    assert tokens["token_type"] == "bearer" and int(tokens["expires_in"]) == 15 * 60
    me = client.get(f"{API}/users/me", headers=bearer(tokens["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL and me.json()["role"] == "user"


def test_wrong_password_and_unknown_email_look_the_same(client: TestClient) -> None:
    register(client)
    wrong = client.post(f"{API}/auth/login", json={"email": EMAIL, "password": "yanlis-parola"})
    unknown = client.post(f"{API}/auth/login", json={"email": "yok@example.com", "password": "yanlis-parola"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]
    assert wrong.headers["www-authenticate"] == "Bearer"


def test_me_requires_valid_access_token(client: TestClient) -> None:
    user_id = register(client)
    assert client.get(f"{API}/users/me").status_code == 401
    assert client.get(f"{API}/users/me", headers=bearer("bozuk.token.degeri")).status_code == 401

    past = datetime.now(UTC) - timedelta(hours=1)
    expired = create_access_token(uuid.UUID(user_id), "user", TEST_SETTINGS, now=past)
    assert client.get(f"{API}/users/me", headers=bearer(expired)).status_code == 401

    forged = jwt.encode({"sub": user_id, "role": "admin", "type": "access"}, "baska-anahtar-" * 3, algorithm="HS256")
    assert client.get(f"{API}/users/me", headers=bearer(forged)).status_code == 401

    unsigned = jwt.encode({"sub": user_id, "type": "access", "iat": 0, "exp": 9999999999}, "", algorithm="none")
    assert client.get(f"{API}/users/me", headers=bearer(unsigned)).status_code == 401

    refresh_as_access = login(client)["refresh_token"]
    assert client.get(f"{API}/users/me", headers=bearer(refresh_as_access)).status_code == 401


# --- refresh rotasyonu, çalıntı token tespiti, çıkış


def test_refresh_rotates_and_reuse_revokes_all_sessions(
    client: TestClient, db_sessionmaker: sessionmaker[Session]
) -> None:
    register(client)
    first = login(client)
    second = client.post(f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    rotated = second.json()
    assert rotated["refresh_token"] != first["refresh_token"]
    assert client.get(f"{API}/users/me", headers=bearer(rotated["access_token"])).status_code == 200

    # Eski token tekrar gelirse (çalınmış olabilir) yeni token da dahil bütün oturumlar kapanır.
    reused = client.post(f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reused.status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 401
    with db_sessionmaker() as s:
        assert all(t.revoked_at is not None for t in s.scalars(select(RefreshToken)))
        assert all(
            t.token_hash not in (first["refresh_token"], rotated["refresh_token"])
            for t in s.scalars(select(RefreshToken))
        )


def test_expired_refresh_token_is_rejected(client: TestClient, db_sessionmaker: sessionmaker[Session]) -> None:
    register(client)
    tokens = login(client)
    with db_sessionmaker() as s:
        s.execute(update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)))
        s.commit()
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    register(client)
    tokens = login(client)
    assert client.post(f"{API}/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    # Bilinmeyen token ile çıkış da 204 (bilgi sızdırmaz, tekrar denemeye dayanıklı).
    assert client.post(f"{API}/auth/logout", json={"refresh_token": "yok"}).status_code == 204


# --- şifre sıfırlama


def test_forgot_password_does_not_reveal_unknown_email(client: TestClient, auth_app: FastAPI) -> None:
    before = len(outbox(auth_app).outbox)
    assert client.post(f"{API}/auth/forgot-password", json={"email": "yok@example.com"}).status_code == 202
    assert len(outbox(auth_app).outbox) == before


def test_reset_password_changes_password_and_ends_sessions(client: TestClient, auth_app: FastAPI) -> None:
    register(client)
    old = login(client)
    assert client.post(f"{API}/auth/forgot-password", json={"email": EMAIL}).status_code == 202
    token = token_from_last_mail(auth_app)
    new_password = "yeni-parola-456"
    body = {"token": token, "new_password": new_password}
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 204
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 400  # tek kullanımlık

    assert client.post(f"{API}/auth/refresh", json={"refresh_token": old["refresh_token"]}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    assert login(client, password=new_password)["access_token"]


def test_new_reset_link_invalidates_previous_one(client: TestClient, auth_app: FastAPI) -> None:
    register(client)
    client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    first = token_from_last_mail(auth_app)
    client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    body = {"token": first, "new_password": "yeni-parola-456"}
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 400


# --- roller ve silinmiş hesap


def test_admin_role_is_read_from_database(
    client: TestClient, auth_app: FastAPI, db_sessionmaker: sessionmaker[Session]
) -> None:
    router = APIRouter()

    @router.get("/_test/admin")
    def admin_only(user: AdminUser) -> dict[str, str]:
        return {"email": user.email}

    auth_app.include_router(router)
    register(client)
    token = login(client)["access_token"]
    assert client.get("/_test/admin", headers=bearer(token)).status_code == 403
    with db_sessionmaker() as s:
        s.execute(update(User).values(role=UserRole.ADMIN))
        s.commit()
    # Aynı token: rol veritabanından okunduğu için yeni token beklemeden yetki değişir.
    assert client.get("/_test/admin", headers=bearer(token)).status_code == 200


def test_soft_deleted_user_cannot_log_in_or_use_token(
    client: TestClient, db_sessionmaker: sessionmaker[Session]
) -> None:
    register(client)
    tokens = login(client)
    with db_sessionmaker() as s:
        s.execute(update(User).values(deleted_at=datetime.now(UTC)))
        s.commit()
    assert client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    assert client.get(f"{API}/users/me", headers=bearer(tokens["access_token"])).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_email_is_sent_only_after_data_is_committed(
    client: TestClient, auth_app: FastAPI, db_sessionmaker: sessionmaker[Session]
) -> None:
    # Gönderim anında başka bir oturumdan bakınca kayıt görünmeli (commit'ten önce gönderilmiyor).
    seen: list[bool] = []

    class SpySender(OutboxEmailSender):
        def send(self, message: EmailMessage) -> None:
            with db_sessionmaker() as s:
                seen.append(s.scalar(select(User).where(User.email == message.to)) is not None)
            super().send(message)

    auth_app.state.email_sender = SpySender()
    register(client)
    client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    assert seen == [True, True]
