"""İstek sınırları (T-050). Sayaçlar bellekte (MemoryCounterStore); Redis gerekmez."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.rate_limits import AnalysesRateLimit
from app.api.routers.auth import get_auth_service
from app.core import rate_limit
from app.core.config import get_settings
from app.core.rate_limit import Limit, MemoryCounterStore, RateLimiter
from app.main import create_app
from app.services.auth import AuthError
from tests.conftest import TEST_SETTINGS

API = "/api/v1"
SETTINGS = TEST_SETTINGS.model_copy(
    update={
        "rate_limit_enabled": True,
        "rate_limit_general_per_minute": 5,
        "rate_limit_auth_per_minute": 3,
        "rate_limit_analyses_per_hour": 2,
    }
)


class _NoAuth:
    """Veritabanına gitmeyen sahte servis: izin verilen istekler hemen 401 alır."""

    def __getattr__(self, name: str) -> object:
        def fail(*args: object, **kwargs: object) -> None:
            raise AuthError(401, "test")

        return fail


@pytest.fixture
def limited_app() -> FastAPI:
    app = create_app(SETTINGS)
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    app.dependency_overrides[get_auth_service] = _NoAuth
    return app  # lifespan çalışmadan (TestClient'ı `with` ile açmadan) sayaçlar bellekte kalır


@pytest.fixture
def client(limited_app: FastAPI) -> TestClient:
    # `with` yok: lifespan çalışmasın, Redis istemcisi açılmasın (sayaçlar MemoryCounterStore'da).
    return TestClient(limited_app, raise_server_exceptions=False)


def test_general_limit_returns_problem_with_retry_after_and_cors(client: TestClient) -> None:
    for _ in range(5):
        assert client.get(f"{API}/yok").status_code == 404
    response = client.get(f"{API}/yok", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.status_code == 429
    assert response.headers["content-type"].startswith("application/problem+json")
    assert 1 <= int(response.headers["retry-after"]) <= 60
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"  # tarayıcı 429'u okuyabilsin
    body = response.json()
    assert body["status"] == 429 and body["request_id"] and body["instance"] == f"{API}/yok"


def test_only_liveness_is_exempt(client: TestClient) -> None:
    for _ in range(8):
        assert client.get(f"{API}/health").status_code == 200
    # /health/ready her çağrıda DB/Redis/Ollama'ya gider; dışarıdan sınırsız çağrılmamalı.
    assert 429 in [client.get(f"{API}/health/ready").status_code for _ in range(6)]


def test_auth_endpoints_share_a_stricter_ip_limit(client: TestClient) -> None:
    # Sahte servis: izin verilen istekler 401 alır, önemli olan 429'un ne zaman geldiği.
    statuses = [
        client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "x"}).status_code,
        client.post(f"{API}/auth/forgot-password", json={"email": "a@example.com"}).status_code,
        client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "x"}).status_code,
    ]
    assert 429 not in statuses
    response = client.post(f"{API}/auth/reset-password", json={"token": "t", "new_password": "yeni-parola-123"})
    assert response.status_code == 429
    assert "retry-after" in response.headers
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["request_id"]


def test_disabled_limits_create_no_limiter() -> None:
    app = create_app(TEST_SETTINGS)
    assert getattr(app.state, "rate_limiter", None) is None


def test_refresh_and_logout_are_not_in_the_auth_bucket(client: TestClient) -> None:
    for _ in range(4):
        assert client.post(f"{API}/auth/refresh", json={"refresh_token": "x"}).status_code != 429


def test_analyses_limit_is_per_user(limited_app: FastAPI, client: TestClient) -> None:
    router = APIRouter()

    @router.post("/deneme-analiz", dependencies=[AnalysesRateLimit])
    def create() -> dict[str, bool]:
        return {"ok": True}

    limited_app.include_router(router, prefix=API)
    users = iter([uuid.uuid4()] * 3 + [uuid.uuid4()])
    limited_app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": next(users)})()

    assert [client.post(f"{API}/deneme-analiz").status_code for _ in range(3)] == [200, 200, 429]
    assert client.post(f"{API}/deneme-analiz").status_code == 200  # başka kullanıcı


def test_store_failure_fails_open_and_backs_off() -> None:
    calls = 0

    class Broken:
        async def hit(self, key: str, window_s: int) -> tuple[int, int]:
            nonlocal calls
            calls += 1
            raise OSError("redis yok")

    limiter = RateLimiter(Broken(), SETTINGS)
    limit = Limit("x", 1, 60)
    assert asyncio.run(limiter.retry_after(limit, "s")) is None
    assert asyncio.run(limiter.retry_after(limit, "s")) is None
    assert calls == 1  # bağlantı yoksa bir süre tekrar denenmez


def test_memory_window_resets(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [1000.0]
    # Sadece bu modülün gördüğü saat değişir; asyncio'nun kendi saati etkilenmez.
    monkeypatch.setattr(rate_limit, "time", SimpleNamespace(monotonic=lambda: now[0]))
    limiter = RateLimiter(MemoryCounterStore(), SETTINGS)
    limit = Limit("x", 1, 60)
    assert asyncio.run(limiter.retry_after(limit, "s")) is None
    assert asyncio.run(limiter.retry_after(limit, "s")) == 60
    now[0] += 61
    assert asyncio.run(limiter.retry_after(limit, "s")) is None


def test_ip_is_not_stored_in_clear() -> None:
    limiter = RateLimiter(MemoryCounterStore(), SETTINGS)
    assert "203.0.113.7" not in limiter.ip_subject("203.0.113.7")
