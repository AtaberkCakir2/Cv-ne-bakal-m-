import asyncio

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services import health as health_service


async def _ok(_: Settings) -> None:
    return None


async def _fail(_: Settings) -> None:
    raise ConnectionRefusedError("postgres://kullanici:sifre@gizli-host")


async def _slow(_: Settings) -> None:
    await asyncio.sleep(5)


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_all_dependencies_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_service, "CHECKS", {"db": _ok, "redis": _ok, "ollama": _ok})
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert set(body["checks"]) == {"db", "redis", "ollama"}
    assert all(c["ok"] for c in body["checks"].values())


def test_not_ready_reports_failing_dependency_without_leaking_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_service, "CHECKS", {"db": _fail, "redis": _ok, "ollama": _slow})
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["db"] == {"ok": False, "latency_ms": None, "error": "ConnectionRefusedError"}
    assert body["checks"]["ollama"]["error"] == "timeout"
    assert body["checks"]["redis"]["ok"] is True
    assert "sifre" not in response.text and "gizli-host" not in response.text


def test_db_check_fails_with_connection_error_not_event_loop_error() -> None:
    # Gerileme testi: Windows'ta async psycopg "ProactorEventLoop" InterfaceError'ı veriyordu;
    # DB açık olsa bile kontrol hep başarısız olurdu. Kapalı portta beklenen hata OperationalError'dır.
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://x:x@127.0.0.1:1/x")
    with pytest.raises(psycopg.OperationalError):
        asyncio.run(health_service.check_db(settings))


def test_ready_with_real_checks_and_no_services_returns_503(client: TestClient) -> None:
    # Gerçek kontrol fonksiyonları; tüm servisler kapalı (conftest'teki adresler).
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert not any(c["ok"] for c in response.json()["checks"].values())
