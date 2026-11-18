"""YouTube filtreleri ve API istemcisi (T-046). Ağ yok, anahtar sahte."""

from typing import Any

import httpx
import pytest

from collector import youtube
from collector.http import PoliteClient
from collector.youtube import Video


def client(handler: Any) -> PoliteClient:
    return PoliteClient(delay_s=0, transport=httpx.MockTransport(handler), max_retries=0)


def video(**kwargs: Any) -> Video:
    defaults: dict[str, Any] = {
        "id": "x",
        "title": "Python Dersleri",
        "duration_min": 60,
        "audio_lang": "tr",
        "views": 5000,
    }
    return Video(**{**defaults, **kwargs})


@pytest.mark.parametrize(
    ("iso", "minutes"), [("PT1H2M30S", 63), ("PT45S", 1), ("P1DT1H", 1500), ("P0D", 0), ("bozuk", 0)]
)
def test_duration(iso: str, minutes: int) -> None:
    assert youtube.duration_minutes(iso) == minutes


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Python Full Course for Beginners", "beginner"),
        ("Docker Eğitimi", "beginner"),
        ("İleri Seviye SQL", "advanced"),
        ("Kubernetes Deep Dive", "advanced"),
        ("Orta Seviye Java", "intermediate"),
    ],
)
def test_level(title: str, level: str) -> None:
    assert youtube.level_of(title) == level


def test_acceptable_filters() -> None:
    assert youtube.acceptable(video(), "tr")
    assert not youtube.acceptable(video(duration_min=5), "tr")
    assert not youtube.acceptable(video(duration_min=800), "tr")
    assert not youtube.acceptable(video(views=500), "tr")
    assert not youtube.acceptable(video(title="Python #shorts"), "tr")
    assert not youtube.acceptable(video(audio_lang="en"), "tr")
    assert not youtube.acceptable(video(title="Python ile neler yapılır"), "tr")  # öğretim ipucu yok
    assert not youtube.acceptable(video(title="İş Garantili Python Eğitimi"), "tr")  # kurs reklamı
    assert not youtube.acceptable(video(title="AWS Sertifikaların Gerçek Değeri Nedir?"), "tr")


@pytest.mark.parametrize(
    ("title", "lang", "ok"),
    [
        ("Python Dersleri", "tr", True),
        ("Python Tutorial", "tr", False),
        ("Python Tutorial", "en", True),
        ("Python Eğitimi", "en", False),
        ("पायथन Python Tutorial", "en", False),
    ],
)
def test_language_from_title_when_metadata_missing(title: str, lang: str, ok: bool) -> None:
    assert youtube.is_language(video(title=title, audio_lang=None), lang) is ok  # type: ignore[arg-type]


def test_key_is_sent_in_header_not_url() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"items": [{"id": {"videoId": "abc"}}]})

    assert youtube.search_ids(client(handler), "gizli", "Docker", "tr") == ["abc"]
    assert seen[0].headers["X-Goog-Api-Key"] == "gizli"
    assert "gizli" not in str(seen[0].url)
    assert seen[0].url.params["q"] == "Docker eğitimi"


def test_quota_and_errors_do_not_leak_details() -> None:
    quota = client(lambda _: httpx.Response(403, json={"error": {"errors": [{"reason": "quotaExceeded"}]}}))
    with pytest.raises(youtube.QuotaExceeded):
        youtube.search_ids(quota, "gizli", "Docker", "tr")
    limit = client(lambda _: httpx.Response(429, json={"error": {"errors": [{"reason": "rateLimitExceeded"}]}}))
    with pytest.raises(youtube.QuotaExceeded):
        youtube.search_ids(limit, "gizli", "Docker", "tr")
    denied = client(lambda _: httpx.Response(403, json={"error": {"errors": [{"reason": "forbidden"}]}}))
    with pytest.raises(youtube.YoutubeError, match="HTTP 403") as e:
        youtube.search_ids(denied, "gizli", "Docker", "tr")
    assert "gizli" not in str(e.value)


def test_fetch_videos_skips_missing_and_keeps_order() -> None:
    item = {
        "id": "b",
        "snippet": {"title": "B", "defaultAudioLanguage": "tr"},
        "contentDetails": {"duration": "PT1H"},
        "statistics": {"viewCount": "12"},
    }
    videos = list(youtube.fetch_videos(client(lambda _: httpx.Response(200, json={"items": [item]})), "k", ["a", "b"]))
    assert [(v.id, v.duration_min, v.views, v.audio_lang) for v in videos] == [("b", 60, 12, "tr")]
    assert videos[0].url == "https://www.youtube.com/watch?v=b"
