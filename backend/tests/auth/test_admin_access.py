"""Panelin Cloudflare Access kontrolü (app/admin/access.py). Veritabanı istemez: belge geçersizse istek panele
ulaşmadan döner, geçerliyse panelin kendi giriş sayfası açılır (o da veritabanına dokunmaz).

Cloudflare yerine testte üretilen bir RSA anahtarı kullanılır; anahtar istemcisi sahtedir (ağ yok).
"""

import time
from collections.abc import Iterator
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.admin import mount_admin
from app.admin.access import AccessConfig, config_from_env
from tests.conftest import TEST_SETTINGS

CONFIG = AccessConfig("ekip-ornek.cloudflareaccess.com", "aud-ornek-123")
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRODUCTION = TEST_SETTINGS.model_copy(update={"environment": "production"})


class FakeKeys:
    """PyJWKClient yerine: her zaman KEY'in açık anahtarını döner."""

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        return jwt.PyJWK.from_dict(
            {**jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True), "alg": "RS256"}
        )


def token(key: Any = KEY, **override: Any) -> str:
    now = int(time.time())
    claims = {
        "aud": [CONFIG.audience],
        "iss": CONFIG.issuer,
        "iat": now,
        "exp": now + 600,
        "email": "ekip@example.com",
    }
    claims.update(override)
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm="RS256")


def client(settings: Any, access: AccessConfig | None, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr("app.admin.access.jwt.PyJWKClient", lambda *a, **k: FakeKeys())
    app = FastAPI()
    mount_admin(app, settings, sessionmaker(), access=access)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def guarded(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    yield from client(PRODUCTION, CONFIG, monkeypatch)


def get_login(c: TestClient, assertion: str | None) -> int:
    headers = {"Cf-Access-Jwt-Assertion": assertion} if assertion is not None else {}
    return int(c.get("/admin/login", headers=headers).status_code)


def test_gecerli_belge_giris_sayfasini_acar(guarded: TestClient) -> None:
    assert get_login(guarded, token()) == 200


@pytest.mark.parametrize(
    "assertion",
    [
        pytest.param(None, id="belge-yok"),
        pytest.param("", id="bos"),
        pytest.param("bozuk.belge.degeri", id="bozuk"),
        pytest.param(token(key=OTHER_KEY), id="baska-anahtar"),
        pytest.param(token(aud=["baska-uygulama"]), id="yanlis-aud"),
        pytest.param(token(iss="https://saldirgan.cloudflareaccess.com"), id="yanlis-yayinci"),
        pytest.param(token(exp=int(time.time()) - 60), id="suresi-dolmus"),
        pytest.param(token(exp=None), id="exp-yok"),
        pytest.param(jwt.encode({"aud": CONFIG.audience, "iss": CONFIG.issuer}, "x" * 32, "HS256"), id="hs256"),
    ],
)
def test_gecersiz_belge_403(guarded: TestClient, assertion: str | None) -> None:
    assert get_login(guarded, assertion) == 403


def test_giris_formu_ve_statikler_de_korunur(guarded: TestClient) -> None:
    form = guarded.post("/admin/login", data={"username": "a@example.com", "password": "x"})
    assert form.status_code == 403
    assert guarded.get("/admin/statics/css/main.css").status_code == 403
    assert guarded.get("/admin/").status_code == 403


def test_productionda_ayar_yoksa_panel_kapali(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CF_ACCESS_TEAM_DOMAIN", raising=False)
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    for c in client(PRODUCTION, None, monkeypatch):
        r = c.get("/admin/login", headers={"Cf-Access-Jwt-Assertion": token()})
        assert r.status_code == 503
        assert "CF_ACCESS_AUD" in r.text


def test_yerelde_ayar_yoksa_kontrol_yok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CF_ACCESS_TEAM_DOMAIN", raising=False)
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    for c in client(TEST_SETTINGS, None, monkeypatch):
        assert get_login(c, None) == 200


def test_ayar_ortam_degiskenlerinden_okunur() -> None:
    env = {"CF_ACCESS_TEAM_DOMAIN": "https://ekip.cloudflareaccess.com/", "CF_ACCESS_AUD": " abc "}
    assert config_from_env(env) == AccessConfig("ekip.cloudflareaccess.com", "abc")
    assert config_from_env({"CF_ACCESS_TEAM_DOMAIN": "ekip.cloudflareaccess.com"}) is None
    assert CONFIG.certs_url == "https://ekip-ornek.cloudflareaccess.com/cdn-cgi/access/certs"
