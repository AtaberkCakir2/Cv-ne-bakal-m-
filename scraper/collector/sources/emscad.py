"""EMSCAD (Real or Fake Job Postings, CC0): University of the Aegean, Workable ilanları, 2012-2014.

Yedek plan veri seti (T-015): API'ler çalışmasa da sistemin elinde ilan olur. Yerel CSV'den okunur
(`fake_job_postings.csv`, https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction).
Sahte işaretli ilanlar alınmaz. Tarih bilgisi yok ve eski olduğu için içe aktarımda varsayılan olarak pasif yazılır;
yoksa "son 6 ay" talep istatistiğini bozar.
"""

import csv
from collections.abc import Iterator
from pathlib import Path

from collector.clean import clean_description, detect_language
from collector.posting import Posting, SourceInfo
from collector.software import is_software_title

SOURCE = SourceInfo(
    name="kaggle-emscad",
    type="dataset",
    base_url="https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction",
    rate_limit_sec=0,
)

SOFTWARE_FUNCTIONS = {"Information Technology", "Engineering", "Data Analyst"}


def is_software(row: dict[str, str]) -> bool:
    # Sektör tek başına yetmez ("Internet" şirketinde satış ilanı da olur); başlık veya iş fonksiyonu yazılım olmalı.
    return row.get("function") in SOFTWARE_FUNCTIONS or is_software_title(row.get("title", ""))


def parse_row(row: dict[str, str]) -> Posting | None:
    if row.get("fraudulent") != "0" or not is_software(row):
        return None
    # Veri setinde metinler HTML'siz ama satır sonları korunur; açıklama + gereksinimler birlikte.
    body = "\n\n".join(part for part in (row.get("description"), row.get("requirements")) if part)
    description = clean_description(body.replace("\n", "<br>"))
    language = detect_language(description)
    if not description or language is None:
        return None
    return Posting(
        external_id=row["job_id"],
        url=None,
        title_raw=row["title"],
        company=None,  # veri setinde şirket adı yok
        location=row.get("location") or None,
        description_clean=description,
        language=language,
        posted_at=None,
    )


def fetch(csv_path: Path) -> Iterator[Posting]:
    with csv_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            posting = parse_row(row)
            if posting:
                yield posting
