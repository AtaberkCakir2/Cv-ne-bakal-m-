"""Kibar headless tarayıcı (T-016, scraper/kaynak-uygunluk.md kural 2-5).

Her sayfadan önce robots.txt'e bakılır, istekler arası 3-5 sn rastgele beklenir, kendini tanıtan User-Agent kullanılır.
429/5xx ve zaman aşımı tekrar denenir; robots yasağı ve diğer hatalar `BrowserBlockedError` ile çalışmayı durdurur.
Playwright isteğe bağlı bağımlılıktır: pip install -e ".[browser]" && playwright install chromium --only-shell
"""

import random
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from urllib.robotparser import RobotFileParser

import httpx

from collector.http import BACKOFF_BASE_S, RETRY_STATUSES, USER_AGENT

JITTER_S = (3.0, 5.0)
GOTO_TIMEOUT_MS = 30_000

OpenPage = Callable[[str], tuple[int, str]]  # adres -> (HTTP durumu, sayfa HTML'i)


class BrowserBlockedError(RuntimeError):
    """Kaynak bu erişimi istemiyor: atlatılmaz, çalışma `failed` olarak kaydedilir."""


def load_robots(url: str) -> RobotFileParser:
    response = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
    if response.status_code != 200 and response.status_code != 404:
        raise BrowserBlockedError(f"robots.txt okunamadı: HTTP {response.status_code}")
    robots = RobotFileParser()
    robots.parse(response.text.splitlines() if response.status_code == 200 else [])
    return robots


class PageFetcher:
    def __init__(
        self,
        open_page: OpenPage,
        robots: RobotFileParser,
        *,
        jitter: tuple[float, float] = JITTER_S,
        max_retries: int = 3,
    ) -> None:
        self._open_page = open_page
        self._robots = robots
        self._jitter = jitter
        self._max_retries = max_retries
        self._last_request = 0.0
        self.requests = 0

    def get(self, url: str) -> str:
        if not self._robots.can_fetch(USER_AGENT, url):
            raise BrowserBlockedError(f"robots.txt izin vermiyor: {url}")
        for attempt in range(self._max_retries + 1):
            wait = self._last_request + random.uniform(*self._jitter) - time.monotonic()  # noqa: S311 — bekleme süresi
            if wait > 0:
                time.sleep(wait)
            status = None
            try:
                status, body = self._open_page(url)
            except TimeoutError:
                if attempt == self._max_retries:
                    raise
            finally:
                self._last_request = time.monotonic()
                self.requests += 1
            if status == 200:
                return body
            if status is not None and (status not in RETRY_STATUSES or attempt == self._max_retries):
                raise BrowserBlockedError(f"HTTP {status}: {url}")
            time.sleep(BACKOFF_BASE_S * 2.0**attempt)
        raise AssertionError("ulaşılamaz")


@contextmanager
def chromium_fetcher(robots_url: str) -> Iterator[PageFetcher]:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    robots = load_robots(robots_url)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_context(user_agent=USER_AGENT).new_page()
        # Sadece ilan sayfası yüklenir; görsel, CSS ve analitik istekleri kaynağa boşuna yük bindirmesin.
        page.route("**/*", lambda r: r.continue_() if r.request.resource_type == "document" else r.abort())

        def open_page(url: str) -> tuple[int, str]:
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=GOTO_TIMEOUT_MS)
            except PlaywrightError as exc:  # zaman aşımı ve ağ hataları
                raise TimeoutError(str(exc)) from exc
            return (response.status if response else 0), page.content()

        try:
            yield PageFetcher(open_page, robots)
        finally:
            browser.close()
