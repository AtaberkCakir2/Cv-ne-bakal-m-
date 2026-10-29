"""Pozisyon × yetkinlik talep istatistikleri (T-045): role_skill_stats materialized view'ının yenilenmesi ve okunması.

View'ın tanımı backend/app/db/migrations/versions/0001_ilk_sema.py ve docs/veritabani.md'de: son 6 ayın aktif,
pozisyonu belli ilanları sayılır (pasif ilanlar, ör. EMSCAD ve benzer kopyalar, girmez). Bu modül tanımı değiştirmez;
toplama ve normalize'dan sonra yeniler. Sırası: import → normalize → refresh (`collector normalize` sonunda
kendisi çağırır; gece zamanlaması T-034).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.db.models import Role, Skill
from sqlalchemy import Column, DateTime, Integer, MetaData, Numeric, Table, func, select, text
from sqlalchemy.orm import Session

# Talep oranı bu kadar ilandan azıyla hesaplanan pozisyonlar "az veri" sayılır (docs/kapsam.md, açık soru 2).
MIN_POSTINGS = 50

# Sadece okuma için. Ayrı MetaData: Base.metadata'ya girerse Alembic onu tablo sanıp "alembic check"i bozar.
role_skill_stats = Table(
    "role_skill_stats",
    MetaData(),
    Column("role_id", Integer),
    Column("skill_id", Integer),
    Column("posting_count", Integer),
    Column("total_postings", Integer),
    Column("demand_ratio", Numeric(5, 4)),
    Column("computed_at", DateTime(timezone=True)),
)


def refresh(session: Session) -> int:
    """View'ı yeniler, satır sayısını döner.

    CONCURRENTLY: yenileme sürerken API eski veriyi okumaya devam eder (kilitlenmez). Hiç doldurulmamış view'da
    CONCURRENTLY çalışmaz; o durumda bir kereye mahsus normal yenileme yapılır.
    """
    populated = session.scalar(text("SELECT ispopulated FROM pg_matviews WHERE matviewname = 'role_skill_stats'"))
    concurrently = " CONCURRENTLY" if populated else ""
    session.execute(text(f"REFRESH MATERIALIZED VIEW{concurrently} role_skill_stats"))  # noqa: S608 — sabit metin
    session.commit()
    return session.scalar(select(func.count()).select_from(role_skill_stats)) or 0


@dataclass(frozen=True)
class SkillDemand:
    skill: str  # taksonomideki standart ad (contracts: missing_skills[].skill)
    posting_count: int
    demand_ratio: Decimal  # 0.7500 = ilanların %75'i


@dataclass(frozen=True)
class RoleSummary:
    slug: str
    name: str
    total_postings: int
    top_skills: list[SkillDemand]
    computed_at: datetime | None

    @property
    def low_data(self) -> bool:
        return self.total_postings < MIN_POSTINGS


def top_skills(session: Session, role_slug: str, limit: int = 20) -> list[SkillDemand]:
    """Pozisyonun en çok istenen yetkinlikleri, talep oranına göre (eşitse ada göre)."""
    rows = session.execute(
        select(Skill.canonical_name, role_skill_stats.c.posting_count, role_skill_stats.c.demand_ratio)
        .join(Skill, Skill.id == role_skill_stats.c.skill_id)
        .join(Role, Role.id == role_skill_stats.c.role_id)
        .where(Role.slug == role_slug)
        .order_by(role_skill_stats.c.demand_ratio.desc(), Skill.canonical_name)
        .limit(limit)
    ).all()
    return [SkillDemand(name, count, ratio) for name, count, ratio in rows]


def summaries(session: Session, top: int = 5) -> list[RoleSummary]:
    """Her aktif pozisyon için ilan sayısı ve en çok istenen yetkinlikler; ilanı olmayan pozisyon 0 ile görünür."""
    totals = dict(
        session.execute(
            select(
                role_skill_stats.c.role_id,
                func.max(role_skill_stats.c.total_postings),
            ).group_by(role_skill_stats.c.role_id)
        )
        .tuples()
        .all()
    )
    computed_at = session.scalar(select(func.max(role_skill_stats.c.computed_at)))
    result = [
        RoleSummary(role.slug, role.name, totals.get(role.id, 0), top_skills(session, role.slug, top), computed_at)
        for role in session.scalars(select(Role).where(Role.is_active))
    ]
    return sorted(result, key=lambda r: (-r.total_postings, r.slug))
