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


def test_db_check_reads_a_table_so_missing_grants_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    # Bağlantı açılıyor ama uygulama rolünün tablo yetkisi yoksa (eksik GRANT) kontrol başarısız olmalı;
    # yalnızca "SELECT 1" bunu yakalamıyordu (#150).
    executed: list[str] = []

    class Conn:
        def __enter__(self) -> "Conn":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, sql: str) -> None:
            executed.append(sql)
            raise psycopg.errors.InsufficientPrivilege("permission denied for table roles")

    monkeypatch.setattr(psycopg, "connect", lambda *_a, **_k: Conn())
    monkeypatch.setattr(health_service, "CHECKS", {"db": health_service.check_db})
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://x:x@127.0.0.1:1/x")
    result = asyncio.run(health_service.readiness(settings))
    assert executed == [health_service.DB_READY_SQL]
    assert result.status == "not_ready"
    assert result.checks["db"].error == "InsufficientPrivilege"
