"""İstek sınırları (T-050): sabit pencereli sayaç, Redis'te.

Sınırlar (docs/gorevler/anil.md, T-050):
- Genel: IP başına dakikada 100 istek (middleware; sadece canlılık ucu /health hariç, /health/ready dahil).
- Kimlik doğrulama: IP başına dakikada 10 istek (giriş, kayıt, doğrulama, şifre sıfırlama uçları birlikte).
- Analiz: kullanıcı başına saatte 5 analiz (`app/api/rate_limits.py`, analiz uçları kimlik doğrulamaya bağlanınca).

Aşılınca 429 + `Retry-After` (saniye) döner, gövde RFC 7807.

Redis'e ulaşılamazsa sınır uygulanmaz ve uyarı loglanır (fail-open): Redis'in çökmesi kimsenin giriş
yapamaması anlamına gelmesin. Bağlantı kurulamayınca 10 sn boyunca Redis denenmez (her istek bağlantı zaman aşımını
beklemesin); tek bir yavaş yanıtta sadece o istek atlanır. IP'ler Redis'e açık yazılmaz, `security.hash_ip` ile
tuzlu özetleri anahtar olur.

Gereksinimler: Redis ≥ 7 (`EXPIRE ... NX`). Vekil (production'da cloudflared, karar #30) arkasında gerçek
istemci IP'si için uvicorn'a `FORWARDED_ALLOW_IPS` (vekilin adresi/alt ağı) verilmeli; verilmezse herkes vekilin
IP'siyle tek sayacı paylaşır. `*` verilmez: uvicorn o zaman `X-Forwarded-For`'daki ilk (istemcinin uydurabileceği)
adresi alır.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol

from fastapi import FastAPI
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core import security
from app.core.config import Settings
from app.core.errors import problem

log = logging.getLogger(__name__)

_RETRY_REDIS_AFTER_S = 10.0
_UNDO_LUA = "if (tonumber(redis.call('GET', KEYS[1]) or '0') > 0) then return redis.call('DECR', KEYS[1]) end return 0"


@dataclass(frozen=True)
class Limit:
    name: str  # anahtar öneki: aynı adı paylaşan uçlar aynı sayacı kullanır
    max_requests: int
    window_s: int


class CounterStore(Protocol):
    async def hit(self, key: str, window_s: int) -> tuple[int, int]:
        """Sayacı bir artırır; (pencerede şimdiye kadarki istek sayısı, pencerenin bitmesine kalan sn) döner."""
        ...

    async def undo(self, key: str) -> None:
        """Son artırmayı geri alır (sayılmaması gereken istek). Pencere bitmişse bir şey yapmaz."""
        ...


class RedisCounterStore:
    def __init__(self, url: str) -> None:
        # Kısa zaman aşımı: Redis yavaşsa istek beklemesin. Bağlantılar event loop'a bağlıdır; bu yüzden istemci
        # uygulama açılırken (lifespan) oluşturulur ve kapanırken kapatılır.
        self._redis = Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)

    async def aclose(self) -> None:
        await self._redis.aclose()

    async def hit(self, key: str, window_s: int) -> tuple[int, int]:
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_s, nx=True)  # süre sadece pencerenin ilk isteğinde konur
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()
        return int(count), int(ttl) if ttl and ttl > 0 else window_s

    async def undo(self, key: str) -> None:
        # Anahtar yoksa (pencere bitti) DECR süresiz bir -1 anahtarı açardı; sadece varsa ve 0'dan büyükse azalt.
        await self._redis.eval(_UNDO_LUA, 1, key)


class MemoryCounterStore:
    """Testler ve Redis'siz tek süreçli geliştirme için. Süresi dolan anahtarları silmez: production'da kullanmayın."""

    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, float]] = {}

    async def hit(self, key: str, window_s: int) -> tuple[int, int]:
        now = time.monotonic()
        count, reset_at = self._counters.get(key, (0, now + window_s))
        if reset_at <= now:
            count, reset_at = 0, now + window_s
        self._counters[key] = (count + 1, reset_at)
        return count + 1, max(1, int(reset_at - now + 0.999))

    async def undo(self, key: str) -> None:
        count, reset_at = self._counters.get(key, (0, 0.0))
        if count > 0 and reset_at > time.monotonic():
            self._counters[key] = (count - 1, reset_at)


class RateLimiter:
    def __init__(self, store: CounterStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings
        self._skip_until = 0.0

    async def retry_after(self, limit: Limit, subject: str) -> int | None:
        """Sınır aşıldıysa kaç saniye sonra tekrar denenebileceğini, aşılmadıysa None döner."""
        return (await self.check(limit, subject))[0]

    async def check(self, limit: Limit, subject: str) -> tuple[int | None, bool]:
        """(retry_after, sayaç bu istekte gerçekten artırıldı mı). İade sadece artırılan isteğe yapılır."""
        if time.monotonic() < self._skip_until:
            return None, False
        try:
            count, ttl = await self.store.hit(f"rl:{limit.name}:{subject}", limit.window_s)
        except (RedisConnectionError, OSError):
            # Bağlantı yok: bir süre deneme. (Zaman aşımı da buraya düşer ama sadece bağlantı kurulamazsa.)
            self._skip_until = time.monotonic() + _RETRY_REDIS_AFTER_S
            log.warning("rate_limit_store_unavailable", exc_info=True)
            return None, False
        except Exception:  # noqa: BLE001 — tek seferlik hata (ör. yavaş yanıt): sadece bu istek sınırsız geçer
            log.warning("rate_limit_check_failed", exc_info=True)
            return None, False
        return (ttl if count > limit.max_requests else None), True

    async def release(self, limit: Limit, subject: str) -> None:
        """Sayılmaması gereken isteği sayaçtan düşer (ör. reddedilen CV yüklemesi). Hata olursa sessizce geçer."""
        if time.monotonic() < self._skip_until:
            return
        try:
            await self.store.undo(f"rl:{limit.name}:{subject}")
        except Exception:  # noqa: BLE001 — iade yapılamazsa en kötü ihtimalle bir hak eksik kalır
            log.warning("rate_limit_release_failed", exc_info=True)

    def ip_subject(self, ip: str | None) -> str:
        return security.hash_ip(ip, self.settings) or "unknown"


def too_many_requests_headers(retry_after: int) -> dict[str, str]:
    return {"Retry-After": str(retry_after)}


TOO_MANY = "Çok fazla istek gönderdiniz. Biraz bekleyip tekrar deneyin."


class GeneralRateLimitMiddleware:
    """IP başına genel sınır. CORS middleware'inin içinde durur ki 429 yanıtı da tarayıcıda okunabilsin."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter, limit: Limit, exempt_paths: frozenset[str]) -> None:
        self.app = app
        self.limiter = limiter
        self.limit = limit
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        retry = await self.limiter.retry_after(self.limit, self.limiter.ip_subject(client[0] if client else None))
        if retry is None:
            await self.app(scope, receive, send)
            return
        response = problem(429, TOO_MANY, instance=scope["path"])
        response.headers.update(too_many_requests_headers(retry))
        await response(scope, receive, send)


def redis_lifespan(limiter: RateLimiter, redis_url: str):  # type: ignore[no-untyped-def]
    """Redis istemcisini uygulamanın event loop'unda açar, kapanışta bağlantı havuzunu kapatır."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        store = RedisCounterStore(redis_url)
        limiter.store = store
        try:
            yield
        finally:
            await store.aclose()

    return lifespan
