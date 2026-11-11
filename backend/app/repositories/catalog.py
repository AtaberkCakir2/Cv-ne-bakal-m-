"""Katalog okuma (T-048): hedef pozisyonlar, pozisyon başına talep istatistikleri, eğitim kaynakları."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, column, select, table
from sqlalchemy.orm import Session

from app.db.enums import LangCode
from app.db.models import Resource, Role, Skill

# Materialized view (0001_ilk_sema.py, docs/veritabani.md); ORM modeli yok, sadece okunur.
ROLE_SKILL_STATS = table(
    "role_skill_stats",
    column("role_id", Integer),
    column("skill_id", Integer),
    column("posting_count", Integer),
    column("total_postings", Integer),
    column("demand_ratio", Numeric(5, 4)),
    column("computed_at", DateTime(timezone=True)),
)


def is_web_url(url: str) -> bool:
    """Kullanıcıya link olarak verilecek adres sadece http(s) olabilir (javascript:, data: vb. asla)."""
    return url.lower().startswith(("https://", "http://"))


@dataclass(frozen=True)
class RoleSkillStat:
    skill: Skill
    posting_count: int
    total_postings: int
    demand_ratio: Decimal
    computed_at: datetime


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_roles(self) -> list[Role]:
        return list(self.session.scalars(select(Role).where(Role.is_active).order_by(Role.name, Role.id)))

    def get_role(self, slug: str) -> Role | None:
        return self.session.scalar(select(Role).where(Role.slug == slug, Role.is_active))

    def role_skills(self, role_id: int, limit: int) -> list[RoleSkillStat]:
        s = ROLE_SKILL_STATS.c
        rows = self.session.execute(
            select(Skill, s.posting_count, s.total_postings, s.demand_ratio, s.computed_at)
            .join(ROLE_SKILL_STATS, s.skill_id == Skill.id)
            .where(s.role_id == role_id, Skill.is_active)
            .order_by(s.demand_ratio.desc(), s.posting_count.desc(), Skill.canonical_name)
            .limit(limit)
        )
        return [RoleSkillStat(*row) for row in rows.tuples()]

    def get_skill(self, slug: str) -> Skill | None:
        return self.session.scalar(select(Skill).where(Skill.slug == slug, Skill.is_active))

    def skill_resources(self, skill_id: int, language: LangCode | None) -> list[Resource]:
        """Erişilebilir kaynaklar: önce ücretsizler, sonra seviyeye göre (başlangıç → ileri)."""
        query = select(Resource).where(Resource.skill_id == skill_id, Resource.is_alive)
        if language is not None:
            query = query.where(Resource.language == language)
        rows = self.session.scalars(
            query.order_by(Resource.is_free.desc(), Resource.level, Resource.title, Resource.id)
        )
        return [r for r in rows if is_web_url(r.url)]
