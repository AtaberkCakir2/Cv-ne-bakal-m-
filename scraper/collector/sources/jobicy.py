"""Jobicy API (https://jobicy.com/jobs-rss-feed). Şart: gösterilen yerde kaynak Jobicy olarak belirtilir; saklama ve
işleme serbest, anahtar gerekmez. Sadece son 7 günün ilanlarını verir, gece çalışması bu pencereyi kapsar."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

from collector.clean import clean_description, detect_language
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo

API = "https://jobicy.com/api/jobs"
SOURCE = SourceInfo(name="jobicy", type="api", base_url="https://jobicy.com", rate_limit_sec=5.0)

# ?get=industries listesinden (01.11.2026). "admin": DevOps & Infrastructure.
INDUSTRIES = ("engineering", "data-science", "admin", "cybersecurity", "qa-testing")


def parse_job(job: dict[str, Any]) -> Posting | None:
    description = clean_description(job.get("jobDescription") or "")
    language = detect_language(description)
    if not description or not job.get("jobTitle") or language is None:
        return None
    published = job.get("pubDate")
    return Posting(
        external_id=str(job["id"]),
        url=job.get("url"),
        title_raw=job["jobTitle"],
        company=job.get("companyName"),
        location=job.get("jobGeo") or "Remote",
        description_clean=description,
        language=language,
        posted_at=datetime.fromisoformat(published).date() if published else None,
    )


def fetch(client: PoliteClient) -> Iterator[Posting]:
    seen: set[str] = set()
    for industry in INDUSTRIES:
        params: dict[str, str | int] = {"industry": industry, "count": 100}
        while True:
            body = client.get_json(API, params=params)
            for job in body.get("jobs") or []:
                posting = parse_job(job) if str(job["id"]) not in seen else None
                seen.add(str(job["id"]))
                if posting:
                    yield posting
            cursor = body.get("nextCursor")
            if not cursor:
                break
            params = {**params, "cursor": cursor}
