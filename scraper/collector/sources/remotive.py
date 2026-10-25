"""Remotive API. Şartlar: günde en fazla birkaç çağrı (gecede 1), ilanlar 24 saat gecikmeli, kaynak adı + link,
başka iş sitelerine aktarım yok (https://github.com/remotive-com/remote-jobs-api)."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

from collector.clean import clean_description, detect_language
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo

API = "https://remotive.com/api/remote-jobs"
SOURCE = SourceInfo(name="remotive", type="api", base_url="https://remotive.com", rate_limit_sec=30.0)


def parse_job(job: dict[str, Any]) -> Posting | None:
    description = clean_description(job.get("description") or "")
    language = detect_language(description)
    if not description or not job.get("title") or language is None:
        return None
    published = job.get("publication_date")
    return Posting(
        external_id=str(job["id"]),
        url=job.get("url"),
        title_raw=job["title"],
        company=job.get("company_name"),
        location=job.get("candidate_required_location") or "Remote",
        description_clean=description,
        language=language,
        posted_at=datetime.fromisoformat(published).date() if published else None,
    )


def fetch(client: PoliteClient) -> Iterator[Posting]:
    for job in client.get_json(API, params={"category": "software-dev"}).get("jobs") or []:
        posting = parse_job(job)
        if posting:
            yield posting
