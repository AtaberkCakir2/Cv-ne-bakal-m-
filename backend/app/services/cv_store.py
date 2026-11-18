"""Kuyruktaki CV baytlarının geçici deposu (T-039, karar #9).

Baytlar Celery mesajına konmaz: broker Redis'i kalıcı (AOF/RDB) çalışır ve CV diske yazılırdı. Bu depo kalıcılığı
kapalı, ayrı bir Redis'tir (CV_REDIS_URL). Anahtar süre aşımıyla kendiliğinden silinir, iş bitince hemen silinir.
"""

import uuid
from typing import Protocol, cast

from redis import Redis


def _key(analysis_id: uuid.UUID) -> str:
    return f"cv:{analysis_id}"


class CvStore(Protocol):
    def put(self, analysis_id: uuid.UUID, content: bytes) -> None: ...
    def get(self, analysis_id: uuid.UUID) -> bytes | None: ...
    def delete(self, analysis_id: uuid.UUID) -> None: ...
    def count(self) -> int: ...


class RedisCvStore:
    def __init__(self, url: str, ttl_s: int) -> None:
        self._client = Redis.from_url(url, socket_connect_timeout=2, socket_timeout=5)
        self._ttl_s = ttl_s

    def put(self, analysis_id: uuid.UUID, content: bytes) -> None:
        self._client.set(_key(analysis_id), content, ex=self._ttl_s)

    def get(self, analysis_id: uuid.UUID) -> bytes | None:
        return cast("bytes | None", self._client.get(_key(analysis_id)))

    def delete(self, analysis_id: uuid.UUID) -> None:
        self._client.delete(_key(analysis_id))

    def count(self) -> int:
        return int(self._client.dbsize())  # bu Redis veritabanı sadece CV baytları içindir
