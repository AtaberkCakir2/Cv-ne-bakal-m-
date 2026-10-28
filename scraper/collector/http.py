"""Kibar HTTP istemcisi (scraper/kaynak-uygunluk.md, kural 3-5).

Kendini tanıtan User-Agent, istekler arası sabit bekleme, 429/5xx'te geri çekilme. 403 ve diğer hatalarda
yeniden denenmez: bot koruması aşılmaz, çalışma `failed` olarak kaydedilir.
"""

import time
from typing import Any

import httpx

USER_AGENT = "CareerAI-Bot/0.1 (bitirme projesi; +https://github.com/AtaberkCakir2/Cv-ne-bakal-m-)"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class PoliteClient:
    def __init__(self, delay_s: float, *, max_retries: int = 4, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True, transport=transport
        )
        self._delay_s = delay_s
        self._max_retries = max_retries
        self._last_request = 0.0
        self.requests = 0

    def get_json(self, url: str, params: dict[str, str | int] | None = None) -> Any:
        for attempt in range(self._max_retries + 1):
            wait = self._last_request + self._delay_s - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            response = self._client.get(url, params=params)
            self._last_request = time.monotonic()
            self.requests += 1
            if response.status_code in RETRY_STATUSES and attempt < self._max_retries:
                retry_after = response.headers.get("Retry-After", "")
                time.sleep(float(retry_after) if retry_after.isdigit() else self._delay_s * 2**attempt)
                continue
            response.raise_for_status()
            return response.json()
        raise AssertionError("ulaşılamaz")

    def close(self) -> None:
        self._client.close()
