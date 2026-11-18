"""Remote OK API (https://remoteok.com/api). Şart: Remote OK'nin ilan linkine follow link + kaynak adı."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from collector.clean import clean_description, detect_language
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo
from collector.software import is_software_title

API = "https://remoteok.com/api"
SOURCE = SourceInfo(name="remote-ok", type="api", base_url="https://remoteok.com", rate_limit_sec=1.0)


def parse_job(job: dict[str, Any]) -> Posting | None:
    if "id" not in job or not job.get("position"):
        return None  # ilk eleman yasal uyarı metni
    if not is_software_title(job["position"]):
        return None  # akış tüm kategorileri içerir
    description = clean_description(job.get("description") or "")
    language = detect_language(description)
    if not description or language is None:
        return None
    epoch = job.get("epoch")
    return Posting(
        external_id=str(job["id"]),
        url=job.get("url"),
        title_raw=job["position"],
        company=job.get("company"),
        location=job.get("location") or "Remote",
        description_clean=description,
        language=language,
        posted_at=datetime.fromtimestamp(epoch, tz=UTC).date() if epoch else None,
    )


def fetch(client: PoliteClient) -> Iterator[Posting]:
    for job in client.get_json(API):
        posting = parse_job(job)
        if posting:
            yield posting
