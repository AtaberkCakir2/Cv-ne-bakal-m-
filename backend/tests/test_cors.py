"""CORS: web (Vite) ve masaüstü (Electron, app://careerai) kökenleri izinli, diğerleri değil (T-059)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

API = "/api/v1"


@pytest.fixture
def default_client() -> TestClient:
    # Varsayılan liste: .env'deki CORS_ORIGINS'ten etkilenmesin.
    return TestClient(create_app(Settings(_env_file=None, environment="test")))


def preflight(client: TestClient, origin: str) -> dict[str, str]:
    response = client.options(
        f"{API}/auth/login",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    return dict(response.headers)


@pytest.mark.parametrize("origin", ["app://careerai", "http://127.0.0.1:5173"])
def test_own_origins_are_allowed(default_client: TestClient, origin: str) -> None:
    assert preflight(default_client, origin).get("access-control-allow-origin") == origin


def test_other_origins_are_rejected(default_client: TestClient) -> None:
    assert "access-control-allow-origin" not in preflight(default_client, "https://evil.example.com")
