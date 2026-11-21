"""T-069: Redis kullanan bileşenler gerçek Redis'e karşı (testcontainers veya TEST_REDIS_URL; yoksa atlanır).

Diğer testler bu bileşenlerin sahtelerini kullanır; burada CV geçici deposunun süre aşımı ve silmesi ile hız
sınırı sayacının pencere davranışı gerçek Redis komutlarıyla doğrulanır.
DİKKAT: TEST_REDIS_URL'deki veritabanı her testten önce ve sonra boşaltılır (FLUSHDB); ayrı bir Redis/DB verin.
"""

import asyncio
import os
import time
import uuid
from collections.abc import Iterator

import pytest
from redis import Redis

from app.core.rate_limit import Limit, RateLimiter, RedisCounterStore
from app.services.cv_store import RedisCvStore
from tests.conftest import TEST_SETTINGS


@pytest.fixture
def redis_client() -> Iterator[Redis]:
    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("TEST_REDIS_URL verilmedi (Docker kapalı)")
    client = Redis.from_url(url)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def redis_url(redis_client: Redis) -> str:
    return str(os.environ["TEST_REDIS_URL"])


def test_cv_store_keeps_bytes_only_until_ttl_and_deletes(redis_client: Redis, redis_url: str) -> None:
    store = RedisCvStore(redis_url, ttl_s=1)
    first, second = uuid.uuid4(), uuid.uuid4()
    store.put(first, b"%PDF-1")
    store.put(second, b"%PDF-2")
    assert store.get(first) == b"%PDF-1" and store.count() == 2
    assert 0 < redis_client.pttl(f"cv:{first}") <= 1000

    store.delete(first)
    assert store.get(first) is None and store.count() == 1

    time.sleep(1.5)  # süre aşımı: unutulan CV kendiliğinden silinir
    assert store.get(second) is None and store.count() == 0


def test_rate_limit_counter_window_and_retry_after(redis_url: str) -> None:
    async def scenario() -> list[int | None]:
        store = RedisCounterStore(redis_url)
        limiter = RateLimiter(store, TEST_SETTINGS)
        limit = Limit(name="t069", max_requests=2, window_s=30)
        try:
            return [await limiter.retry_after(limit, "kisi") for _ in range(3)] + [
                await limiter.retry_after(limit, "baska-kisi")
            ]
        finally:
            await store.aclose()

    first, second, third, other = asyncio.run(scenario())
    assert first is None and second is None  # sınır içinde
    assert third is not None and 0 < third <= 30  # aşıldı: pencerenin kalanı kadar beklenir
    assert other is None  # sayaç kişiye özel


def test_rate_limit_window_is_set_only_once(redis_client: Redis, redis_url: str) -> None:
    key = "rl:t069:pencere"

    async def scenario() -> list[int]:
        store = RedisCounterStore(redis_url)
        try:
            counts = [(await store.hit(key, 5))[0]]
            ttl_first = int(redis_client.pttl(key))
            await asyncio.sleep(1.1)
            counts += [(await store.hit(key, 5))[0] for _ in range(2)]
            ttl_later = int(redis_client.pttl(key))
        finally:
            await store.aclose()
        # EXPIRE ... NX: süre ilk istekte konur, sonraki istekler pencereyi uzatmaz (kalan süre azalmış olmalı).
        assert 0 < ttl_later < ttl_first - 1000
        return counts

    assert asyncio.run(scenario()) == [1, 2, 3]
