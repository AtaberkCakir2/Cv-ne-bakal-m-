"""PoliteClient: bekleme, geri çekilme ve tekrar deneme (T-034). Ağ yok; bekleme süreleri kaydedilir, uyunmaz."""

from collections.abc import Callable

import httpx
import pytest

from collector import http
from collector.http import USER_AGENT, PoliteClient


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr("collector.http.time.sleep", recorded.append)
    return recorded


def client(responses: list[httpx.Response | Exception], **kwargs: object) -> tuple[PoliteClient, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return PoliteClient(transport=httpx.MockTransport(handler), **kwargs), seen  # type: ignore[arg-type]


def ok() -> httpx.Response:
    return httpx.Response(200, json={"ok": True})


def test_single_identifying_user_agent(sleeps: list[float]) -> None:
    c, seen = client([ok(), ok()], delay_s=0)
    c.get_json("https://example.com/a")
    c.get_json("https://example.com/b")
    # kaynak-uygunluk.md kural 3-4: dönüşümlü/sahte UA yok, her istekte aynı kimlik.
    assert {r.headers["User-Agent"] for r in seen} == {USER_AGENT}


def test_jitter_waits_between_three_and_five_seconds(sleeps: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collector.http.time.monotonic", lambda: 1000.0)  # istekler arası zaman geçmiyor
    c, _ = client([ok(), ok(), ok()], delay_s=1.0, jitter=(3.0, 5.0))
    for _ in range(3):
        c.get_json("https://example.com")
    # İlk istek beklemez; sonraki her istekten önce 3-5 sn.
    assert len(sleeps) == 2 and all(3.0 <= s <= 5.0 for s in sleeps)


def test_source_floor_wins_over_jitter(sleeps: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collector.http.time.monotonic", lambda: 1000.0)
    c, _ = client([ok(), ok()], delay_s=30.0, jitter=(3.0, 5.0))  # Remotive: gecede 1 çağrı, en az 30 sn
    c.get_json("https://example.com")
    c.get_json("https://example.com")
    assert sleeps == [30.0]


@pytest.mark.parametrize(
    "failure",
    [lambda: httpx.Response(503), lambda: httpx.Response(429), lambda: httpx.ConnectTimeout("zaman aşımı")],
)
def test_retries_with_exponential_backoff(sleeps: list[float], failure: Callable[[], object]) -> None:
    c, seen = client([failure(), failure(), ok()], delay_s=0)  # type: ignore[list-item]
    assert c.get_json("https://example.com") == {"ok": True}
    assert len(seen) == 3
    first, second = sleeps
    assert 5.0 <= first <= 7.5 and 10.0 <= second <= 15.0  # 5 sn taban, her denemede iki katı (+ en çok %50)


def test_retry_after_is_honoured_but_capped(sleeps: list[float]) -> None:
    c, _ = client([httpx.Response(429, headers={"Retry-After": "86400"}), ok()], delay_s=0)
    c.get_json("https://example.com")
    assert sleeps == [http.MAX_RETRY_AFTER_S]


def test_forbidden_is_not_retried(sleeps: list[float]) -> None:
    c, seen = client([httpx.Response(403)], delay_s=0)
    with pytest.raises(httpx.HTTPStatusError):
        c.get_json("https://example.com")
    assert len(seen) == 1 and sleeps == []


def test_gives_up_after_max_retries(sleeps: list[float]) -> None:
    c, seen = client([httpx.Response(503)] * 3, delay_s=0, max_retries=2)
    with pytest.raises(httpx.HTTPStatusError):
        c.get_json("https://example.com")
    assert len(seen) == 3
