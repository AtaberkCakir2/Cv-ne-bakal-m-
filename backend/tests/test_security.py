"""Güvenlik yardımcıları; veritabanı gerekmez (T-037 kod incelemesi bulguları)."""

import uuid

import pytest

from app.core import security
from app.core.config import DEV_JWT_SECRET, Settings

STRONG_SECRET = "x" * 40


def test_dev_secret_is_not_used_when_environment_is_not_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    # ENVIRONMENT unutulursa varsayılan "local" olsa bile geliştirme anahtarıyla token üretilmez / kabul edilmez.
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    settings = Settings(_env_file=None)
    assert settings.jwt_secret == DEV_JWT_SECRET and not settings.auth_ready
    with pytest.raises(security.AuthNotConfiguredError):
        security.create_access_token(uuid.uuid4(), "admin", settings)

    forged = security.create_access_token(uuid.uuid4(), "admin", Settings(_env_file=None, environment="local"))
    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(forged, settings)


def test_explicit_local_or_real_secret_enables_auth() -> None:
    assert Settings(_env_file=None, environment="local").auth_ready
    assert Settings(_env_file=None, environment="test").auth_ready
    assert Settings(_env_file=None, environment="production", jwt_secret=STRONG_SECRET).auth_ready


def test_dev_secret_with_explicit_production_refuses_to_start() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production")


def test_ip_hash_uses_separate_key_when_given() -> None:
    base = Settings(_env_file=None, environment="test")
    separate = Settings(_env_file=None, environment="test", ip_hash_secret="y" * 40)
    assert security.hash_ip("10.0.0.1", base) != security.hash_ip("10.0.0.1", separate)
    assert security.hash_ip(None, base) is None
    assert "10.0.0.1" not in (security.hash_ip("10.0.0.1", base) or "")


def test_auth_errors_are_fresh_objects() -> None:
    from app.services import auth

    assert auth.invalid_credentials() is not auth.invalid_credentials()
