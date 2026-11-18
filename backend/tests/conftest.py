import contextlib
import os
from collections.abc import Iterator
from typing import Any

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


# T-069: Veritabanı ve Redis testleri gerçek servis ister. TEST_DATABASE_URL / TEST_REDIS_URL verilmediyse ve Docker
# açıksa testcontainers ile geçici PostgreSQL (pgvector) ve Redis başlatılır; test toplanmadan önce adresleri ortama
# yazılır, oturum bitince kapatılır. Docker yoksa bu testler eskisi gibi atlanır. Kapatmak için:
# CAREERAI_NO_TESTCONTAINERS=1
_containers: list[Any] = []
_started_env: list[str] = []


def _start(env: str, make: Any, url: Any) -> None:
    if os.environ.get(env):
        return
    print(f"testcontainers: {env} için geçici servis başlatılıyor...")
    container = None
    try:
        container = make()
        container.start()
    except Exception as exc:  # Docker kapalı veya kurulu değil: bu servisi isteyen testler atlanır
        if container is not None:
            with contextlib.suppress(Exception):
                container.stop()
        print(f"testcontainers {env} için başlatılamadı ({type(exc).__name__}: {exc}); ilgili testler atlanacak.")
        return
    _containers.append(container)
    _started_env.append(env)
    # Windows'ta localhost önce IPv6'ya gidebilir (backend/README.md): adresler 127.0.0.1 ile verilir.
    os.environ[env] = url(container).replace("@localhost:", "@127.0.0.1:").replace("//localhost:", "//127.0.0.1:")


def pytest_configure(config: pytest.Config) -> None:
    if os.environ.get("CAREERAI_NO_TESTCONTAINERS") or config.option.collectonly or config.option.help:
        return
    try:
        from testcontainers.postgres import PostgresContainer
        from testcontainers.redis import RedisContainer
    except ImportError:
        return
    _start(
        "TEST_DATABASE_URL",
        lambda: PostgresContainer("pgvector/pgvector:pg16", driver="psycopg"),
        lambda c: c.get_connection_url(),
    )
    _start(
        "TEST_REDIS_URL",
        lambda: RedisContainer("redis:7"),
        lambda c: f"redis://{c.get_container_host_ip()}:{c.get_exposed_port(6379)}/0",
    )


def pytest_unconfigure(config: pytest.Config) -> None:
    for env in _started_env:
        os.environ.pop(env, None)
    for container in _containers:
        with contextlib.suppress(Exception):  # biri kapanmazsa diğerleri yine kapatılır (Ryuk da temizler)
            container.stop()
    _containers.clear()
    _started_env.clear()
