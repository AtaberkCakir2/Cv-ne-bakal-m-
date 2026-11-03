"""Sentetik CV şablon girdisi (T-019): pozisyon × yetkinlik × eş anlamlı, gerçek ilan talep oranlarıyla.

Burak'ın `ai/eval` şablon betiği bu dosyadan CV iskeleti kurar (hangi pozisyona hangi yetkinlikler, ne sıklıkla).
Talep oranı role_skill_stats'tan (T-045) gelir; eş anlamlılar taksonomiden, CV'de kısaltma ve yazım farkı
üretmek için.

Şablonun yetkinlik listesi **cevap anahtarı değildir**: etiketler CV metninde gerçekten geçene göre elle verilir.

`build()` veritabanı kullanmaz (test edilebilsin); `load_demand()` veritabanından okur.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.models import Role, Skill
from sqlalchemy import select
from sqlalchemy.orm import Session

from collector.taxonomy_rows import RoleRow, SkillRow
from etl.stats import MIN_POSTINGS, role_skill_stats

VERSION = 1
DEFAULT_TOP = 30
# CV'de bu oranın üstündeki yetkinlik "çekirdek" (pozisyonun neredeyse her CV'sinde), altı "yaygın"/"seyrek".
CORE_RATIO = 0.30
COMMON_RATIO = 0.10


@dataclass(frozen=True)
class Demand:
    role_slug: str
    skill_slug: str
    posting_count: int
    total_postings: int
    demand_ratio: Decimal


def tier(ratio: float) -> str:
    if ratio >= CORE_RATIO:
        return "core"
    return "common" if ratio >= COMMON_RATIO else "rare"


def build(
    demand: list[Demand],
    skills: list[SkillRow],
    roles: list[RoleRow],
    *,
    top: int = DEFAULT_TOP,
    computed_at: datetime | None = None,
) -> dict[str, Any]:
    """Her pozisyon için talep oranına göre ilk `top` yetkinlik. İlanı olmayan pozisyon boş listeyle yazılır."""
    skill_by_slug = {s.slug: s for s in skills}
    by_role: dict[str, list[Demand]] = {}
    for d in demand:
        by_role.setdefault(d.role_slug, []).append(d)

    out_roles = []
    for role in roles:
        rows = sorted(
            (d for d in by_role.get(role.slug, []) if d.skill_slug in skill_by_slug),
            key=lambda d: (-d.demand_ratio, skill_by_slug[d.skill_slug].canonical_name),
        )[:top]
        total = max((d.total_postings for d in by_role.get(role.slug, [])), default=0)
        out_roles.append(
            {
                "slug": role.slug,
                "name": role.name,
                "titles": list(role.synonyms),
                "total_postings": total,
                "low_data": total < MIN_POSTINGS,
                "skills": [_skill(skill_by_slug[d.skill_slug], d) for d in rows],
            }
        )

    return {
        "_aciklama": (
            "Sentetik CV şablon girdisi (T-019). scraper'da `python -m collector export-template` ile üretildi; "
            "elle düzenlemeyin. demand_ratio: pozisyonun son 6 aydaki aktif ilanlarının yüzde kaçında isteniyor. "
            f"tier: core ≥ {CORE_RATIO}, common ≥ {COMMON_RATIO}, rare altı. low_data: {MIN_POSTINGS}'den az ilan, "
            "oranlar kaba. titles: CV başlığında kullanılabilecek unvanlar. Yetkinlik listesi cevap anahtarı DEĞİLDİR; "
            "etiketler CV metninde geçene göre elle verilir."
        ),
        "version": VERSION,
        "computed_at": computed_at.isoformat() if computed_at else None,
        "top_per_role": top,
        "roles": out_roles,
    }


def _skill(skill: SkillRow, d: Demand) -> dict[str, Any]:
    ratio = float(d.demand_ratio)
    return {
        "slug": skill.slug,
        "canonical_name": skill.canonical_name,
        "category": skill.category,
        "synonyms": list(skill.synonyms),
        "demand_ratio": round(ratio, 3),
        "posting_count": d.posting_count,
        "tier": tier(ratio),
    }


def load_demand(session: Session) -> tuple[list[Demand], datetime | None]:
    stats = role_skill_stats.c
    rows = session.execute(
        select(Role.slug, Skill.slug, stats.posting_count, stats.total_postings, stats.demand_ratio, stats.computed_at)
        .join(Role, Role.id == stats.role_id)
        .join(Skill, Skill.id == stats.skill_id)
    ).all()
    computed_at = max((r[5] for r in rows if r[5] is not None), default=None)
    return [Demand(r[0], r[1], r[2], r[3], r[4]) for r in rows], computed_at
