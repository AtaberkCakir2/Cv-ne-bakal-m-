from datetime import datetime

from pydantic import BaseModel

from app.db.enums import LangCode, ResourceLevel, ResourceProvider, SkillCategory


class RoleOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None


class RoleRefOut(BaseModel):
    slug: str
    name: str


class RoleSkillOut(BaseModel):
    skill: str
    slug: str
    category: SkillCategory
    demand_ratio: float
    posting_count: int


class RoleSkillsOut(BaseModel):
    """Pozisyonun en çok istenen yetkinlikleri (role_skill_stats, son 6 ayın aktif ilanları, gece yenilenir)."""

    role: RoleRefOut
    total_postings: int
    computed_at: datetime | None
    skills: list[RoleSkillOut]


class SkillRefOut(BaseModel):
    slug: str
    name: str


class CatalogResourceOut(BaseModel):
    resource_id: int
    title: str
    url: str
    provider: ResourceProvider
    language: LangCode
    level: ResourceLevel
    duration_min: int | None = None  # analiz sonucundaki gibi: değer yoksa yanıtta yok
    is_free: bool


class SkillResourcesOut(BaseModel):
    skill: SkillRefOut
    resources: list[CatalogResourceOut]
