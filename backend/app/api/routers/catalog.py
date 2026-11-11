"""Katalog (T-048): hedef pozisyonlar, en çok istenen yetkinlikler, eğitim kaynakları.

Kişisel veri yok; giriş gerekmez (kayıt ve hedef pozisyon seçimi ekranları da kullanır). Veri gece yenilendiği
için kısa süre önbelleğe alınabilir.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.api.deps import DbSession
from app.db.enums import LangCode
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    CatalogResourceOut,
    RoleOut,
    RoleRefOut,
    RoleSkillOut,
    RoleSkillsOut,
    SkillRefOut,
    SkillResourcesOut,
)

roles_router = APIRouter(prefix="/roles", tags=["Katalog"])
skills_router = APIRouter(prefix="/skills", tags=["Katalog"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}
_CACHE = "public, max-age=300"


def get_catalog(db: DbSession) -> CatalogRepository:
    return CatalogRepository(db)


Catalog = Annotated[CatalogRepository, Depends(get_catalog)]


@roles_router.get("", response_model=list[RoleOut], summary="Hedef pozisyonlar")
def list_roles(catalog: Catalog, response: Response) -> list[RoleOut]:
    """Aktif pozisyonlar, ada göre. `id`, `POST /analyses` ve `PATCH /users/me` için `target_role_id`'dir."""
    response.headers["Cache-Control"] = _CACHE
    return [RoleOut(id=r.id, slug=r.slug, name=r.name, description=r.description) for r in catalog.list_roles()]


@roles_router.get(
    "/{slug}/skills",
    response_model=RoleSkillsOut,
    summary="Pozisyonun en çok istenen yetkinlikleri",
    responses={404: {"description": "Pozisyon bulunamadı", **_PROBLEM}},
)
def role_skills(
    slug: str, catalog: Catalog, response: Response, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> RoleSkillsOut:
    """Son 6 ayın aktif ilanlarından, talep oranına göre. İlan yoksa liste boş, `total_postings` 0."""
    role = catalog.get_role(slug)
    if role is None:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı.")
    response.headers["Cache-Control"] = _CACHE
    stats = catalog.role_skills(role.id, limit)
    return RoleSkillsOut(
        role=RoleRefOut(slug=role.slug, name=role.name),
        total_postings=stats[0].total_postings if stats else 0,
        computed_at=stats[0].computed_at if stats else None,
        skills=[
            RoleSkillOut(
                skill=s.skill.canonical_name,
                slug=s.skill.slug,
                category=s.skill.category,
                demand_ratio=float(s.demand_ratio),
                posting_count=s.posting_count,
            )
            for s in stats
        ],
    )


@skills_router.get(
    "/{slug}/resources",
    response_model=SkillResourcesOut,
    response_model_exclude_unset=True,
    summary="Yetkinlik için eğitim kaynakları",
    responses={404: {"description": "Yetkinlik bulunamadı", **_PROBLEM}},
)
def skill_resources(
    slug: str, catalog: Catalog, response: Response, language: LangCode | None = None
) -> SkillResourcesOut:
    """Sadece erişilebilir (haftalık link kontrolünden geçen) kaynaklar; önce ücretsizler."""
    skill = catalog.get_skill(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail="Yetkinlik bulunamadı.")
    response.headers["Cache-Control"] = _CACHE
    return SkillResourcesOut(
        skill=SkillRefOut(slug=skill.slug, name=skill.canonical_name),
        resources=[
            CatalogResourceOut(
                resource_id=r.id,
                title=r.title,
                url=r.url,
                provider=r.provider,
                language=r.language,
                level=r.level,
                is_free=r.is_free,
                **({"duration_min": r.duration_min} if r.duration_min is not None else {}),
            )
            for r in catalog.skill_resources(skill.id, language)
        ],
    )
