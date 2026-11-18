"""Panelin Cloudflare Access kilidini uygulamada da doğrular (go-live #14, app/admin/README.md).

Cloudflare Access, `/admin`'e giden ve politikadan geçen her isteğe imzalı bir belge ekler
(`Cf-Access-Jwt-Assertion`, RS256). Bu katman belgenin imzasını, hedef kitlesini (AUD) ve yayıncısını kontrol eder.
Böylece Access ayarı silinse, yanlış yola taşınsa veya bir atlatma yolu bulunsa (ör. `/admin%2Flogin`, README) panel
yine kapalı kalır: tünelden gelen ama Access'ten geçmemiş istek belgesizdir.

Ayar ortam değişkenlerinden okunur (sadece bu paket kullanır, app/core/config'e eklenmedi):
  CF_ACCESS_TEAM_DOMAIN  ör. `old-firefly-f6cd.cloudflareaccess.com`
  CF_ACCESS_AUD          Access uygulamasının "Application Audience (AUD) Tag" değeri
Production'da ikisi de yoksa panel hiç açılmaz (503): eksik ayar sessizce kilidi kaldırmasın. Diğer ortamlarda
(yerel, test, prova) ayar yoksa kontrol yapılmaz.
"""

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import jwt
from starlette.concurrency import run_in_threadpool
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger("careerai.admin.access")

HEADER = b"cf-access-jwt-assertion"
# Cloudflare'in anahtarları döner; PyJWKClient anahtar setini bu süre önbellekte tutar, bilinmeyen `kid` gelirse
# yeniden indirir.
JWKS_CACHE_S = 3600
JWKS_TIMEOUT_S = 5


@dataclass(frozen=True)
class AccessConfig:
    team_domain: str
    audience: str

    @property
    def issuer(self) -> str:
        return f"https://{self.team_domain}"

    @property
    def certs_url(self) -> str:
        return f"{self.issuer}/cdn-cgi/access/certs"


def config_from_env(environ: Mapping[str, str] = os.environ) -> AccessConfig | None:
    team = environ.get("CF_ACCESS_TEAM_DOMAIN", "").strip().removeprefix("https://").rstrip("/")
    audience = environ.get("CF_ACCESS_AUD", "").strip()
    return AccessConfig(team, audience) if team and audience else None


class SigningKeys(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


class AccessGuard:
    """`/admin` alt uygulamasının en dış katmanı (SQLAdmin `middlewares` listesinin ilki)."""

    def __init__(
        self,
        app: ASGIApp,
        config: AccessConfig | None,
        required: bool,
        keys: SigningKeys | None = None,
    ) -> None:
        self.app = app
        self.config = config
        self.required = required
        self.keys: SigningKeys | None = keys
        if keys is None and config is not None:
            self.keys = jwt.PyJWKClient(config.certs_url, lifespan=JWKS_CACHE_S, timeout=JWKS_TIMEOUT_S)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if self.config is None:
            if self.required:
                response = PlainTextResponse(
                    "Yönetim paneli kapalı: Cloudflare Access ayarı eksik (CF_ACCESS_TEAM_DOMAIN, CF_ACCESS_AUD).",
                    status_code=503,
                )
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)
            return

        token = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k == HEADER), "")
        if not token or not await run_in_threadpool(self._valid, token):
            await PlainTextResponse("Erişim yok.", status_code=403)(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _valid(self, token: str) -> bool:
        assert self.config is not None and self.keys is not None
        try:
            key = self.keys.get_signing_key_from_jwt(token).key
            jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={"require": ["exp", "iat", "aud", "iss"]},
            )
        except jwt.PyJWTError as exc:
            # Belgenin kendisi loglanmaz (e-posta içerir); sadece neden.
            log.warning("Cloudflare Access belgesi reddedildi: %s", type(exc).__name__)
            return False
        return True
