"""Hacker News "Ask HN: Who is hiring?" aylık başlıkları (resmi Firebase API).

Her üst seviye yorum bir ilan. Yorumu yazanın kullanıcı adı (`by`) kişisel veridir, hiç okunmaz/saklanmaz.
Atıf: kaynak "Hacker News" + yorum linki (scraper/kaynak-uygunluk.md).
"""

import re
from collections.abc import Collection, Iterator
from datetime import UTC, datetime
from typing import Any

from collector.clean import clean_description, detect_language, html_to_text
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo

API = "https://hacker-news.firebaseio.com/v0"
SOURCE = SourceInfo(name="hacker-news", type="api", base_url="https://news.ycombinator.com", rate_limit_sec=0.2)

_THREAD_TITLE = re.compile(r"^Ask HN: Who is hiring\? \(\w+ \d{4}\)$")
_LOCATION_HINT = re.compile(r"\b(remote|onsite|on-site|hybrid|in office|worldwide)\b", re.IGNORECASE)
# İlan başlığına yanlışlıkla yazılan "işe alınmak istiyorum" yorumları: bir kişinin kendini tanıtması, ilan değil.
_SEEKER = re.compile(r"\b(willing to relocate|r[ée]sum[ée]/cv|seeking work|looking for work)\s*:", re.IGNORECASE)
_MAX_HEADER = 300


def hiring_threads(client: PoliteClient, months: int) -> list[dict[str, Any]]:
    """En yeni `months` adet aylık başlık. whoishiring hesabı ayrıca "freelancer" ve "wants to be hired" açar."""
    submitted: list[int] = client.get_json(f"{API}/user/whoishiring.json")["submitted"]
    threads: list[dict[str, Any]] = []
    for item_id in submitted:
        item = client.get_json(f"{API}/item/{item_id}.json")
        if item and _THREAD_TITLE.match(item.get("title", "")):
            threads.append(item)
            if len(threads) == months:
                break
    return threads


def parse_comment(item: dict[str, Any]) -> Posting | None:
    if item.get("deleted") or item.get("dead") or not item.get("text"):
        return None
    raw = item["text"]
    if _SEEKER.search(html_to_text(raw)):
        return None  # kişisel veri: iş arayanın profili, saklanmaz
    # İlk paragraf başlık satırı: "Şirket | Pozisyon | Konum | Çalışma şekli".
    header = html_to_text(raw.split("<p>", 1)[0])
    segments = [s.strip() for s in header.split("|") if s.strip()]
    if not segments:
        return None
    location = " | ".join(s for s in segments[1:] if _LOCATION_HINT.search(s)) or None
    description = clean_description(raw)
    language = detect_language(description)
    if language is None:
        return None
    return Posting(
        external_id=str(item["id"]),
        url=f"https://news.ycombinator.com/item?id={item['id']}",
        title_raw=header[:_MAX_HEADER],
        company=segments[0][:200],
        location=location,
        description_clean=description,
        language=language,
        posted_at=datetime.fromtimestamp(item["time"], tz=UTC).date(),
    )


def fetch(client: PoliteClient, months: int = 6, skip_ids: Collection[str] = ()) -> Iterator[Posting]:
    """`skip_ids`: veritabanında zaten olan yorumlar; gece toplamasında sadece yeni yorumlar istenir."""
    for thread in hiring_threads(client, months):
        for comment_id in thread.get("kids", []):
            if str(comment_id) in skip_ids:
                continue
            posting = parse_comment(client.get_json(f"{API}/item/{comment_id}.json") or {})
            if posting:
                yield posting
