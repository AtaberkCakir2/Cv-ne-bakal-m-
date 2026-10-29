from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app

# Servisler hiçbir testte gerçekten çalışmıyor varsayılır; adresler kapalı portları gösterir.
TEST_SETTINGS = Settings(
    _env_file=None,
    environment="test",
    database_url="postgresql+psycopg://x:x@127.0.0.1:1/x",
    redis_url="redis://127.0.0.1:1/0",
    ollama_url="http://127.0.0.1:1",
    readiness_timeout_s=0.5,
    rate_limit_enabled=False,  # sınır testleri tests/test_rate_limit.py'de
)


@pytest.fixture
def app() -> FastAPI:
    application = create_app(TEST_SETTINGS)
    application.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
