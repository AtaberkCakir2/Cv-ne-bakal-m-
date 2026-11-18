"""Kibar HTTP istemcisi (scraper/kaynak-uygunluk.md, kural 3-5).

Kendini tanıtan tek User-Agent (dönüşümlü/sahte UA kullanılmaz, kural 3), istekler arası bekleme, 429/5xx ve ağ
hatalarında üstel geri çekilme. 403 ve diğer hatalarda yeniden denenmez: bot koruması aşılmaz, çalışma `failed`
olarak kaydedilir.
"""

import random
import time
from typing import Any

import httpx

USER_AGENT = "CareerAI-Bot/0.1 (bitirme projesi; +https://github.com/AtaberkCakir2/Cv-ne-bakal-m-)"
RETRY_STATUSES = {429, 500, 502, 503, 504}
BACKOFF_BASE_S = 5.0  # ilk tekrar en az bu kadar sonra; her denemede iki katı
MAX_RETRY_AFTER_S = 600.0


class PoliteClient:
    """`delay_s` kaynağın kendi alt sınırı; `jitter` verilirse her istekten önce bu aralıkta rastgele beklenir
    (ikisinden büyüğü). Gece toplaması 3-5 sn kullanır (T-034); elle içe aktarmada jitter yok."""

    def __init__(
        self,
        delay_s: float,
        *,
        jitter: tuple[float, float] | None = None,
        max_retries: int = 4,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True, transport=transport
        )
        self._delay_s = delay_s
        self._jitter = jitter
        self._max_retries = max_retries
        self._last_request = 0.0
        self.requests = 0

    def _gap(self) -> float:
        if self._jitter is None:
            return self._delay_s
        low, high = self._jitter
        return max(self._delay_s, random.uniform(low, high))  # noqa: S311 — güvenlik değil, bekleme süresi

    def _backoff(self, attempt: int, retry_after: str = "") -> float:
        if retry_after.isdigit():
            return min(float(retry_after), MAX_RETRY_AFTER_S)
        base: float = max(self._delay_s, BACKOFF_BASE_S) * 2.0**attempt
        return base + random.uniform(0, base / 2)  # noqa: S311 — aynı anda tekrar denemesinler

    def status(self, url: str) -> int | None:
        """Link kontrolü: son HTTP durum kodu; bağlantı kurulamazsa None. Tekrar denenmez."""
        wait = self._last_request + self._gap() - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            with self._client.stream("GET", url) as response:  # gövde okunmaz
                return response.status_code
        except httpx.TransportError:
            return None
        finally:
            self._last_request = time.monotonic()
            self.requests += 1

    def get_json(
        self, url: str, params: dict[str, str | int] | None = None, *, headers: dict[str, str] | None = None
    ) -> Any:
        for attempt in range(self._max_retries + 1):
            wait = self._last_request + self._gap() - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            try:
                response = self._client.get(url, params=params, headers=headers)
            except httpx.TransportError:
                # Bağlantı/zaman aşımı: geçici olabilir, aynı geri çekilmeyle tekrar denenir.
                if attempt == self._max_retries:
                    raise
                time.sleep(self._backoff(attempt))
                continue
            finally:
                self._last_request = time.monotonic()
                self.requests += 1
            if response.status_code in RETRY_STATUSES and attempt < self._max_retries:
                time.sleep(self._backoff(attempt, response.headers.get("Retry-After", "")))
                continue
            response.raise_for_status()
            return response.json()
        raise AssertionError("ulaşılamaz")

    def close(self) -> None:
        self._client.close()
