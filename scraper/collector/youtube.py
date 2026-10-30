"""YouTube Data API v3: yetkinlik başına eğitim videosu arama ve video bilgisi yenileme (T-046).

Kota (developers.google.com/youtube/v3/determine_quota_cost, 30.10.2026): günde en fazla 100 search.list çağrısı,
videos.list 10.000 birimlik havuzdan çağrı başına 1 birim (50 video). Kota dolunca QuotaExceeded yükselir, çağıran
durur ve ertesi gün kaldığı yerden devam eder; ücret çıkmaz.

Şartlar (developers.google.com/youtube/terms/developer-policies, III.E.4): saklanan API verisi en geç 30 günde bir
yenilenmeli (haftalık `resources.check_links`). İstemciler video linkinin YouTube kaynaklı olduğunu göstermeli ve
YouTube Hizmet Şartları'na link vermeli. İzlenme sayısı sadece filtrede kullanılır, saklanmaz; skor üretilmez.

Anahtar URL'de değil başlıkta gider: httpx hata mesajları ve logları URL'yi içerir.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import batched
from pathlib import Path
from typing import Any

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from collector.clean import Lang
from collector.http import PoliteClient

API = "https://www.googleapis.com/youtube/v3"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
SEARCH_RESULTS = 15
VIDEOS_PER_CALL = 50
MIN_DURATION_MIN = 10
MAX_DURATION_MIN = 12 * 60
MIN_VIEWS: dict[Lang, int] = {"tr": 1_000, "en": 10_000}  # Türkçe içerik az izlenir
QUERY: dict[Lang, str] = {"tr": "{} eğitimi", "en": "{} tutorial"}

_DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
# Harf sınıfı büyük/küçük harf duyarlı: IGNORECASE ile "ı" Latin "i"yi de eşler.
_TURKISH = re.compile(r"[çğıöşüÇĞİÖŞÜ]|(?i:\b(?:eğitim|ders|nedir|kurs|öğren))")
_NON_LATIN = re.compile(r"[^\W\d_a-zA-ZçğıöşüÇĞİÖŞÜâîûáéíóúñäëïü]")
# Başlıkta öğretim ipucu olmalı; tanıtım, kariyer sohbeti ve kurs reklamı elenir.
_LEARNING = re.compile(
    r"(?i:\b(?:eğitim|ders|öğren|kurs|giriş|sıfırdan|başlangıç|temel|uygulamalı|nedir|tutorial|course|learn|beginner"
    r"|crash|guide|introduction|intro|fundamentals|basics|explained|masterclass|bootcamp|training|proje|project))"
)
_PROMO = re.compile(
    r"(?i:garantili|sertifikalar|sertifikanın|gerçek değeri|maaş|kariyer|indirim|kampanya|salary|career|giveaway)"
)
_SHORTS = re.compile(r"#shorts\b", re.IGNORECASE)
_ADVANCED = re.compile(r"\b(ileri seviye|ileri düzey|advanced|expert|masterclass|deep dive)\b", re.IGNORECASE)
_INTERMEDIATE = re.compile(r"\b(orta seviye|orta düzey|intermediate)\b", re.IGNORECASE)


class QuotaExceeded(Exception):
    """Günlük kota doldu."""


class YoutubeError(Exception):
    """API hatası. Mesajda sadece durum kodu var."""


class YoutubeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    youtube_api_key: str = ""


@dataclass(frozen=True)
class Video:
    id: str
    title: str
    duration_min: int
    audio_lang: str | None
    views: int

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"


def duration_minutes(iso: str) -> int:
    """ "PT1H2M30S" → 63 (yukarı yuvarlanır); canlı yayın gibi süresizler 0."""
    m = _DURATION.match(iso)
    if not m:
        return 0
    days, hours, minutes, seconds = (int(g or 0) for g in m.groups())
    return (days * 86400 + hours * 3600 + minutes * 60 + seconds + 59) // 60


def level_of(title: str) -> str:
    """Başlıkta ipucu yoksa `beginner`: eksik yetkinlik önerisinde kullanıcı o konuya yeni başlıyor."""
    if _ADVANCED.search(title):
        return "advanced"
    return "intermediate" if _INTERMEDIATE.search(title) else "beginner"


def _get(client: PoliteClient, key: str, endpoint: str, params: dict[str, str | int]) -> Any:
    try:
        return client.get_json(f"{API}/{endpoint}", params, headers={"X-Goog-Api-Key": key})
    except httpx.HTTPStatusError as e:
        # Günlük arama sınırı 429 rateLimitExceeded, genel kota 403 quotaExceeded döner.
        if e.response.status_code in {403, 429} and "xceeded" in e.response.text:
            raise QuotaExceeded from None
        raise YoutubeError(f"{endpoint}: HTTP {e.response.status_code}") from None


def search_ids(client: PoliteClient, key: str, skill: str, lang: Lang) -> list[str]:
    params: dict[str, str | int] = {
        "part": "id",
        "type": "video",
        "q": QUERY[lang].format(skill),
        "maxResults": SEARCH_RESULTS,
        "relevanceLanguage": lang,
        "safeSearch": "strict",
    }
    return [item["id"]["videoId"] for item in _get(client, key, "search", params).get("items", [])]


def fetch_videos(client: PoliteClient, key: str, ids: Iterable[str]) -> Iterator[Video]:
    """Silinmiş veya özel videolar sonuçta yer almaz. Sıra: istenen sıra."""
    for chunk in batched(ids, VIDEOS_PER_CALL):
        params: dict[str, str | int] = {"part": "snippet,contentDetails,statistics", "id": ",".join(chunk)}
        items = {item["id"]: item for item in _get(client, key, "videos", params).get("items", [])}
        for video_id in chunk:
            if item := items.get(video_id):
                snippet = item["snippet"]
                yield Video(
                    id=video_id,
                    title=snippet["title"],
                    duration_min=duration_minutes(item["contentDetails"]["duration"]),
                    audio_lang=snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage"),
                    views=int(item["statistics"].get("viewCount", 0)),
                )


def is_language(video: Video, lang: Lang) -> bool:
    if video.audio_lang:
        return video.audio_lang.lower().startswith(lang)
    if _NON_LATIN.search(video.title):
        return False
    return bool(_TURKISH.search(video.title)) == (lang == "tr")


def acceptable(video: Video, lang: Lang) -> bool:
    return (
        MIN_DURATION_MIN <= video.duration_min <= MAX_DURATION_MIN
        and video.views >= MIN_VIEWS[lang]
        and not _SHORTS.search(video.title)
        and bool(_LEARNING.search(video.title))
        and not _PROMO.search(video.title)
        and is_language(video, lang)
    )
