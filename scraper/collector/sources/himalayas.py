"""Himalayas açık iş API'si: yazılım aramaları (https://himalayas.app/api).

Şartlar: kaynak linki görünür olur, `applicationLink` değiştirilmez, ilanlar başka iş sitelerine aktarılmaz,
süresi dolan ilan kaldırılır (T-034). Anahtarsız istekler herkesle ortak kotayı kullanır, bu yüzden yavaş ve
sınırlı çekilir.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from collector.clean import clean_description, detect_language
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo

SEARCH_API = "https://himalayas.app/jobs/api/search"
SOURCE = SourceInfo(name="himalayas", type="api", base_url="https://himalayas.app", rate_limit_sec=2.0)

QUERIES = (
    "software engineer",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "mobile developer",
    "devops engineer",
    "data engineer",
    "machine learning engineer",
    "qa engineer",
    "security engineer",
)
SOFTWARE_CATEGORIES = {"Developer", "Data Science"}


def parse_job(job: dict[str, Any]) -> Posting | None:
    if not SOFTWARE_CATEGORIES & set(job.get("parentCategories") or []):
        return None
    description = clean_description(job.get("description") or job.get("excerpt") or "")
    language = detect_language(description)
    if not description or language is None:
        return None
    locations = job.get("locationRestrictions") or []
    pub = job.get("pubDate")
    return Posting(
        external_id=job["guid"],
        url=job["guid"],
        title_raw=job["title"],
        company=job.get("companyName"),
        location=", ".join(locations) if locations else "Remote",
        description_clean=description,
        language=language,
        posted_at=datetime.fromtimestamp(pub, tz=UTC).date() if pub else None,
    )


def fetch(client: PoliteClient, pages_per_query: int = 5) -> Iterator[Posting]:
    seen: set[str] = set()  # sayfalar arasında kayabilir; guid ile tekilleştirilir
    for query in QUERIES:
        for page in range(1, pages_per_query + 1):
            jobs = client.get_json(SEARCH_API, params={"q": query, "sort": "recent", "page": page}).get("jobs") or []
            if not jobs:
                break
            for job in jobs:
                posting = parse_job(job)
                if posting and posting.external_id not in seen:
                    seen.add(posting.external_id)
                    yield posting
