"""Python.org iş ilanları (https://www.python.org/jobs/), Playwright PoC'si (T-016). Şart: robots.txt `/jobs/` yolunu
kapatmıyor, https://www.python.org/about/legal/ üçüncü taraf içeriğini tüm kullanıcılara lisanslıyor. Kaynak linki
verilir. Az ilan var (~20) ve Chromium gerektirir: gece akışında değil, elle çalıştırılır."""

import html
import re
from collections.abc import Collection, Iterator
from datetime import date

from collector.browser import PageFetcher, chromium_fetcher
from collector.clean import clean_description, detect_language
from collector.posting import Posting, SourceInfo

BASE = "https://www.python.org"
SOURCE = SourceInfo(name="python-org", type="scrape", base_url=BASE, rate_limit_sec=5.0)

LISTING = re.compile(r'<ol class="list-recent-jobs.*?</ol>', re.S)
ITEM = re.compile(r"<li>(.*?)</li>", re.S)
JOB_LINK = re.compile(r'<a href="(/jobs/(\d+)/)">(.*?)</a>\s*<br\s*/?>(.*?)</span>', re.S)
LOCATION = re.compile(r'class="listing-location">\s*<a [^>]*>(.*?)</a>', re.S)
POSTED = re.compile(r'<time datetime="(\d{4}-\d{2}-\d{2})')
DESCRIPTION = re.compile(r'<div class="job-description">(.*?)</div><!-- end \.job-post-content -->', re.S)
# İletişim bloğu işe alımcının adını ve e-postasını içerir, saklanmaz (kural 6).
CONTACT = re.compile(r"<h2>\s*Contact Info.*", re.S | re.I)


def _text(fragment: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_listing(page: str) -> Iterator[dict[str, str | None]]:
    block = LISTING.search(page)
    for item in ITEM.findall(block.group() if block else ""):
        link = JOB_LINK.search(item)
        if not link:
            continue
        location = LOCATION.search(item)
        posted = POSTED.search(item)
        yield {
            "id": link[2],
            "url": BASE + link[1],
            "title": _text(link[3]),
            "company": _text(link[4]) or None,
            "location": _text(location[1]) if location else None,
            "posted": posted[1] if posted else None,
        }


def parse_detail(job: dict[str, str | None], page: str) -> Posting | None:
    found = DESCRIPTION.search(page)
    description = clean_description(CONTACT.sub("", found[1])) if found else ""
    language = detect_language(description)
    if not description or language is None or not job["id"] or not job["title"]:
        return None
    return Posting(
        external_id=job["id"],
        url=job["url"],
        title_raw=job["title"],
        company=job["company"],
        location=job["location"],
        description_clean=description,
        language=language,
        posted_at=date.fromisoformat(job["posted"]) if job["posted"] else None,
    )


def fetch(pages: PageFetcher, skip_ids: Collection[str] = ()) -> Iterator[Posting]:
    for job in parse_listing(pages.get(f"{BASE}/jobs/")):
        if job["id"] in skip_ids or not job["url"]:
            continue
        posting = parse_detail(job, pages.get(job["url"]))
        if posting:
            yield posting


def scrape() -> Iterator[Posting]:
    with chromium_fetcher(f"{BASE}/robots.txt") as pages:
        yield from fetch(pages)
