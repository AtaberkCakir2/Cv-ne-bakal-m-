"""Eğitim kaynağı havuzu (T-046): elle derlenen liste + YouTube araması + haftalık link kontrolü.

Öneri linkleri sadece bu tablodan gelir, LLM link üretmez (karar #10). Elle derlenen liste `taxonomy/resources.csv`.
YouTube aramaları talebi yüksek yetkinlikten başlar; günlük kota dolunca durur, yapılan aramalar `SEARCHED_FILE`'a
yazıldığı için ertesi gün kaldığı yerden devam eder (sonuç vermeyen arama tekrarlanmaz).
"""

import csv
import json
import logging
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.db.enums import LangCode, ResourceLevel, ResourceProvider
from app.db.models import JobPosting, JobPostingSkill, Resource, Skill
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from collector import youtube
from collector.clean import Lang
from collector.http import PoliteClient
from collector.taxonomy_rows import TAXONOMY_DIR, SkillRow
from etl.skills import SkillTagger

log = logging.getLogger(__name__)

RESOURCES_CSV = TAXONOMY_DIR / "resources.csv"
YOUTUBE_CSV = TAXONOMY_DIR / "resources_youtube.csv"
SEARCHED_FILE = TAXONOMY_DIR.parent / "data" / "youtube_searched.json"
WANTED: dict[Lang, int] = {"tr": 3, "en": 2}  # arama başına alınacak video; Türkçe öncelikli
MIN_PER_SKILL = 3
CHECK_DELAY_S = 1.0
YOUTUBE_DELAY_S = 0.2
DEAD_STATUSES = {404, 410}  # 403/429/5xx link ölümü değildir (bot koruması, geçici hata)


def load_csv(path: Path = RESOURCES_CSV) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            {
                "slug": row["skill_slug"].strip(),
                "title": row["title"].strip(),
                "url": row["url"].strip(),
                "provider": ResourceProvider(row["provider"].strip()),
                "language": LangCode(row["language"].strip()),
                "level": ResourceLevel(row["level"].strip()),
                "duration_min": int(row["duration_min"]) if row["duration_min"].strip() else None,
                "is_free": row["is_free"].strip() == "1",
            }
            for row in csv.DictReader(f)
        ]


def _skill_ids(session: Session) -> dict[str, int]:
    return dict(session.execute(select(Skill.slug, Skill.id).where(Skill.is_active)).tuples().all())


def _insert(session: Session, rows: list[dict[str, Any]]) -> int:
    """Aynı URL ikinci kez eklenmez (bir video tek yetkinliğe bağlı). Eklenen satır sayısını döndürür."""
    if not rows:
        return 0
    stmt = insert(Resource).on_conflict_do_nothing(index_elements=["url"]).returning(Resource.id)
    return len(session.execute(stmt, rows).all())


def seed(session: Session, rows: Iterable[dict[str, Any]] | None = None) -> int:
    ids = _skill_ids(session)
    items = list(load_csv() if rows is None else rows)
    if missing := sorted({r["slug"] for r in items} - ids.keys()):
        raise ValueError(f"taksonomide olmayan yetkinlik: {missing[:10]}")
    added = _insert(
        session, [{**{k: v for k, v in r.items() if k != "slug"}, "skill_id": ids[r["slug"]]} for r in items]
    )
    session.commit()
    return added


def skills_by_demand(session: Session, skills: list[SkillRow]) -> list[SkillRow]:
    demand = dict(
        session.execute(
            select(Skill.slug, func.count())
            .join(JobPostingSkill, JobPostingSkill.skill_id == Skill.id)
            .join(JobPosting, JobPosting.id == JobPostingSkill.posting_id)
            .where(JobPosting.is_active)
            .group_by(Skill.slug)
        )
        .tuples()
        .all()
    )
    return sorted(skills, key=lambda s: -demand.get(s.slug, 0))


def _load_searched(path: Path) -> set[str]:
    return set(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else set()


def _save_searched(path: Path, searched: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(searched), ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class SearchResult:
    searches: int = 0
    added: int = 0
    remaining: int = 0
    quota_hit: bool = False


def search_youtube(
    session: Session,
    client: PoliteClient,
    key: str,
    skills: list[SkillRow],
    *,
    limit: int | None = None,
    searched_file: Path = SEARCHED_FILE,
) -> SearchResult:
    """Sıradaki yetkinlikleri arar. `limit`: en fazla bu kadar arama (kotayı denemede harcamamak için)."""
    ids, tagger = _skill_ids(session), SkillTagger(skills)
    searched = _load_searched(searched_file)
    todo = [
        (s, lang) for s in skills_by_demand(session, skills) for lang in WANTED if f"{s.slug}:{lang}" not in searched
    ]
    result = SearchResult()
    for skill, lang in todo[:limit]:
        try:
            found = youtube.search_ids(client, key, skill.canonical_name, lang)
            videos = list(youtube.fetch_videos(client, key, found))
        except youtube.QuotaExceeded:
            result.quota_hit = True
            break
        picked = [
            v
            for v in videos
            if youtube.acceptable(v, lang) and skill.slug in {t.slug for t in tagger.find(v.title, lang)}
        ][: WANTED[lang]]
        result.added += _insert(
            session,
            [
                {
                    "skill_id": ids[skill.slug],
                    "title": v.title,
                    "url": v.url,
                    "provider": ResourceProvider.YOUTUBE,
                    "language": LangCode(lang),
                    "level": ResourceLevel(youtube.level_of(v.title)),
                    "duration_min": v.duration_min,
                    "is_free": True,
                    "last_checked_at": datetime.now(UTC),
                }
                for v in picked
            ],
        )
        session.commit()
        searched.add(f"{skill.slug}:{lang}")
        _save_searched(searched_file, searched)
        result.searches += 1
    result.remaining = len(todo) - result.searches
    return result


def _video_id(url: str) -> str:
    return url.rsplit("=", 1)[-1]


def export_youtube(session: Session, path: Path = YOUTUBE_CSV) -> int:
    """Bulunan videoları yeni ortam için yazar. Başlık ve süre yazılmaz: API verisi repoda 30 günden eski kalır."""
    rows = session.execute(
        select(Skill.slug, Resource.url, Resource.language, Resource.level)
        .join(Skill, Skill.id == Resource.skill_id)
        .where(Resource.provider == ResourceProvider.YOUTUBE, Resource.is_alive)
        .order_by(Skill.slug, Resource.url)
    ).all()
    with path.open("w", encoding="utf-8", newline="") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["skill_slug", "video_id", "language", "level"])
        out.writerows((r.slug, _video_id(r.url), r.language.value, r.level.value) for r in rows)
    return len(rows)


def import_youtube(session: Session, client: PoliteClient, key: str, path: Path = YOUTUBE_CSV) -> int:
    """`export_youtube` dosyasını yükler; başlık ve süre API'den güncel alınır, silinen videolar atlanır."""
    with path.open(encoding="utf-8", newline="") as f:
        items = {row["video_id"]: row for row in csv.DictReader(f)}
    ids = _skill_ids(session)
    now = datetime.now(UTC)
    added = _insert(
        session,
        [
            {
                "skill_id": ids[items[v.id]["skill_slug"]],
                "title": v.title,
                "url": v.url,
                "provider": ResourceProvider.YOUTUBE,
                "language": LangCode(items[v.id]["language"]),
                "level": ResourceLevel(items[v.id]["level"]),
                "duration_min": v.duration_min,
                "is_free": True,
                "last_checked_at": now,
            }
            for v in youtube.fetch_videos(client, key, list(items))
            if items[v.id]["skill_slug"] in ids
        ],
    )
    session.commit()
    return added


@dataclass
class CheckResult:
    checked: int = 0
    dead: int = 0
    revived: int = 0


def check_links(session: Session, client: PoliteClient, yt_client: PoliteClient | None, key: str) -> CheckResult:
    """Haftalık: ölü link pasif, geri gelen tekrar aktif; YouTube başlık ve süreleri yenilenir (30 gün kuralı).

    Anahtar yoksa YouTube satırlarına dokunulmaz. 403/429/5xx ölüm sayılmaz.
    """
    result = CheckResult()
    now = datetime.now(UTC)
    rows = session.execute(select(Resource.id, Resource.url, Resource.provider, Resource.is_alive)).all()

    def mark(resource_id: int, was_alive: bool, alive: bool, **values: Any) -> None:
        result.checked += 1
        result.dead += was_alive and not alive
        result.revived += alive and not was_alive
        session.execute(
            update(Resource).where(Resource.id == resource_id).values(is_alive=alive, last_checked_at=now, **values)
        )

    videos = [r for r in rows if r.provider == ResourceProvider.YOUTUBE]
    if yt_client and key:
        live = {v.id: v for v in youtube.fetch_videos(yt_client, key, [_video_id(r.url) for r in videos])}
        for r in videos:
            video = live.get(_video_id(r.url))
            extra = {"title": video.title, "duration_min": video.duration_min} if video else {}
            mark(r.id, r.is_alive, video is not None, **extra)
        session.commit()

    for r in rows:
        if r.provider == ResourceProvider.YOUTUBE:
            continue
        status = client.status(r.url)
        if status is None or status in DEAD_STATUSES:
            mark(r.id, r.is_alive, False)
        elif status < 400:
            mark(r.id, r.is_alive, True)
        session.commit()
    return result


def report(session: Session) -> dict[str, Any]:
    """Kabul kriteri: toplam ≥ 900, her yetkinlikte ≥ 3 canlı kaynak."""
    counts = Counter(
        dict(
            session.execute(
                select(Skill.slug, func.count())
                .join(Resource, Resource.skill_id == Skill.id)
                .where(Resource.is_alive)
                .group_by(Skill.slug)
            )
            .tuples()
            .all()
        )
    )
    slugs = list(_skill_ids(session))
    return {
        "total": sum(counts.values()),
        "skills": len(slugs),
        "short": sorted(s for s in slugs if counts[s] < MIN_PER_SKILL),
        "languages": dict(
            session.execute(
                select(Resource.language, func.count()).where(Resource.is_alive).group_by(Resource.language)
            )
            .tuples()
            .all()
        ),
    }
