"""Bağımlılık kontrolleri: PostgreSQL, Redis, Ollama.

Her kontrol kısa bir zaman aşımıyla paralel çalışır; biri düşse bile diğerlerinin sonucu raporlanır.
Hata mesajları dışarıya sadece hata türü olarak verilir (bağlantı adresi, şifre vb. sızmaz).
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
import psycopg
import redis.asyncio as aioredis

from app.core.config import Settings
from app.schemas.health import DependencyStatus, ReadinessResponse

Check = Callable[[Settings], Awaitable[None]]


def _ping_db(url: str, timeout_s: int) -> None:
    with psycopg.connect(url, connect_timeout=timeout_s) as conn:
        conn.execute("SELECT 1")


async def check_db(settings: Settings) -> None:
    # SQLAlchemy biçimindeki "postgresql+psycopg://" adresini psycopg'nin anlayacağı biçime çevir.
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    # Senkron bağlantı ayrı iş parçacığında: psycopg'nin async modu Windows'un varsayılan
    # ProactorEventLoop'uyla çalışmıyor (ekipte herkes Windows kullanıyor).
    await asyncio.to_thread(_ping_db, url, max(1, int(settings.readiness_timeout_s)))


async def check_redis(settings: Settings) -> None:
    client = aioredis.from_url(settings.redis_url, socket_connect_timeout=settings.readiness_timeout_s)
    try:
        await client.ping()
    finally:
        await client.aclose()


async def check_ollama(settings: Settings) -> None:
    async with httpx.AsyncClient(timeout=settings.readiness_timeout_s) as client:
        response = await client.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
        response.raise_for_status()


CHECKS: dict[str, Check] = {"db": check_db, "redis": check_redis, "ollama": check_ollama}


async def _run(check: Check, settings: Settings) -> DependencyStatus:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(check(settings), timeout=settings.readiness_timeout_s + 0.5)
    except Exception as exc:  # noqa: BLE001 — her hata "hazır değil" demektir
        error = "timeout" if isinstance(exc, TimeoutError) else type(exc).__name__
        return DependencyStatus(ok=False, error=error)
    return DependencyStatus(ok=True, latency_ms=round((time.perf_counter() - start) * 1000, 1))


async def readiness(settings: Settings, checks: dict[str, Check] | None = None) -> ReadinessResponse:
    checks = CHECKS if checks is None else checks
    results = await asyncio.gather(*(_run(fn, settings) for fn in checks.values()))
    statuses = dict(zip(checks, results, strict=True))
    ready = all(s.ok for s in statuses.values())
    return ReadinessResponse(status="ready" if ready else "not_ready", checks=statuses)
