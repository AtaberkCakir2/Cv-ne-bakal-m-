"""Arbeitnow API (https://www.arbeitnow.com/blog/job-board-api). Şart: uygulamada Arbeitnow.com'a link verilir, izin
geri alınabilir (https://www.arbeitnow.com/terms madde 11). Avrupa ağırlıklı; Almanca ilanlar dil filtresinde elenir."""

import html
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from collector.clean import clean_description, detect_language
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo
from collector.software import is_software_title

API = "https://www.arbeitnow.com/api/job-board-api"
SOURCE = SourceInfo(name="arbeitnow", type="api", base_url="https://www.arbeitnow.com", rate_limit_sec=5.0)
NIGHTLY_PAGES = 2  # sayfa başına 300 ilan, en yeniden eskiye


def parse_job(job: dict[str, Any]) -> Posting | None:
    if not job.get("title") or not is_software_title(job["title"]):
        return None  # akış tüm kategorileri içerir
    # API açıklamayı iki kez kodluyor: "&lt;p&gt;" önce HTML'e döner.
    description = clean_description(html.unescape(job.get("description") or ""))
    language = detect_language(description)
    if not description or language is None:
        return None
    created = job.get("created_at")
    return Posting(
        external_id=job["slug"],
        url=job.get("url"),
        title_raw=job["title"],
        company=job.get("company_name"),
        location="Remote" if job.get("remote") else job.get("location"),
        description_clean=description,
        language=language,
        posted_at=datetime.fromtimestamp(created, UTC).date() if created else None,
    )


def fetch(client: PoliteClient, pages: int = NIGHTLY_PAGES) -> Iterator[Posting]:
    for page in range(1, pages + 1):
        body = client.get_json(API, params={"page": page})
        for job in body.get("data") or []:
            posting = parse_job(job)
            if posting:
                yield posting
        if not (body.get("links") or {}).get("next"):
            return
