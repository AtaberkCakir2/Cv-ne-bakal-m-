"""Yetkinlik taksonomisi ve hedef pozisyonlar (T-017).

Tek doğru kaynak `scraper/taxonomy/skills.csv` ve `roles.csv`. Veritabanına `seed` ile yazılır (slug'a göre
ekle/güncelle); CSV'den çıkarılan kayıt silinmez, pasife alınır (ilan ve analizler ona bağlı olabilir).
Eş anlamlılar küçük harf; bir eş anlamlı tek bir yetkinliğe ait olmalı (eşleme belirsiz olmasın).
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.db.enums import SkillCategory
from app.db.models import Role, Skill
from sqlalchemy import select
from sqlalchemy.orm import Session

# CSV okuma DB'siz modülde; eski importlar (collector.taxonomy.load_skills vb.) çalışmaya devam etsin.
from collector.taxonomy_rows import ROLES_CSV as ROLES_CSV
from collector.taxonomy_rows import SKILLS_CSV as SKILLS_CSV
from collector.taxonomy_rows import TAXONOMY_DIR as TAXONOMY_DIR
from collector.taxonomy_rows import RoleRow as RoleRow
from collector.taxonomy_rows import SkillRow as SkillRow
from collector.taxonomy_rows import load_roles as load_roles
from collector.taxonomy_rows import load_skills as load_skills

VERSION = "1"

_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CATEGORIES = {c.value for c in SkillCategory}


def validate(skills: list[SkillRow], roles: list[RoleRow]) -> list[str]:
    """Sorun listesi; boşsa taksonomi tutarlı."""
    errors: list[str] = []
    for kind, slugs in (("skill", [s.slug for s in skills]), ("role", [r.slug for r in roles])):
        for slug in slugs:
            if not _SLUG.match(slug):
                errors.append(f"{kind} slug biçimi hatalı: {slug!r}")
        for slug in {s for s in slugs if slugs.count(s) > 1}:
            errors.append(f"{kind} slug tekrar ediyor: {slug}")

    names = [s.canonical_name.lower() for s in skills]
    for name in {n for n in names if names.count(n) > 1}:
        errors.append(f"canonical_name tekrar ediyor: {name}")

    # Her terim (ad veya eş anlamlı) tek bir yetkinliğe gitmeli.
    owner: dict[str, str] = {s.canonical_name.lower(): s.slug for s in skills}
    for s in skills:
        if s.category not in CATEGORIES:
            errors.append(f"{s.slug}: bilinmeyen kategori {s.category!r}")
        for syn in s.synonyms:
            if syn != syn.lower():
                errors.append(f"{s.slug}: eş anlamlı küçük harf olmalı: {syn!r}")
            if s.case_sensitive and syn == s.canonical_name.lower():
                # Harf duyarsız eş anlamlı, adın harf duyarlılığını boşa çıkarır ("express" fiili Express.js sayılır).
                errors.append(f"{s.slug}: harf duyarlı yetkinliğin eş anlamlısı adının küçük hali olamaz: {syn!r}")
            other = owner.setdefault(syn.lower(), s.slug)
            if other != s.slug:
                errors.append(f"eş anlamlı {syn!r} iki yetkinlikte: {other}, {s.slug}")

    role_owner: dict[str, str] = {}
    for r in roles:
        for syn in (r.name.lower(), *r.synonyms):
            other = role_owner.setdefault(syn, r.slug)
            if other != r.slug:
                errors.append(f"pozisyon eş anlamlısı {syn!r} iki pozisyonda: {other}, {r.slug}")
    return errors


@dataclass
class SeedResult:
    skills_added: int = 0
    skills_updated: int = 0
    skills_deactivated: int = 0
    roles_added: int = 0
    roles_updated: int = 0
    roles_deactivated: int = 0


def seed(session: Session, skills: list[SkillRow], roles: list[RoleRow]) -> SeedResult:
    """Taksonomiyi veritabanına yazar. Aynı CSV ile tekrar çalıştırmak hiçbir şeyi değiştirmez."""
    if errors := validate(skills, roles):
        raise ValueError("taksonomi tutarsız:\n" + "\n".join(errors))
    result = SeedResult()

    existing_skills = {s.slug: s for s in session.scalars(select(Skill))}
    for row in skills:
        values = {
            "canonical_name": row.canonical_name,
            "category": SkillCategory(row.category),
            "synonyms": list(row.synonyms),
            "esco_uri": row.esco_uri,
            "is_active": True,
        }
        skill = existing_skills.pop(row.slug, None)
        if skill is None:
            session.add(Skill(slug=row.slug, **values))
            result.skills_added += 1
        elif any(getattr(skill, k) != v for k, v in values.items()):
            for k, v in values.items():
                setattr(skill, k, v)
            result.skills_updated += 1
    for skill in existing_skills.values():
        if skill.is_active:
            skill.is_active = False
            result.skills_deactivated += 1

    existing_roles = {r.slug: r for r in session.scalars(select(Role))}
    for rrow in roles:
        rvalues = {
            "name": rrow.name,
            "synonyms": list(rrow.synonyms),
            "description": rrow.description,
            "is_active": True,
        }
        role = existing_roles.pop(rrow.slug, None)
        if role is None:
            session.add(Role(slug=rrow.slug, **rvalues))
            result.roles_added += 1
        elif any(getattr(role, rk) != rv for rk, rv in rvalues.items()):
            for rk, rv in rvalues.items():
                setattr(role, rk, rv)
            result.roles_updated += 1
    for role in existing_roles.values():
        if role.is_active:
            role.is_active = False
            result.roles_deactivated += 1

    session.commit()
    return result


def export_json(skills: list[SkillRow], out: Path) -> None:
    """ai/eval/dataset/skills_provisional.json ile aynı biçim (Burak'ın etiket kontrolü bunu okuyabilir)."""
    data = {
        "_aciklama": (
            "scraper/taxonomy/skills.csv'den üretildi (T-017). Elle düzenlemeyin; CSV'yi değiştirip yeniden üretin."
        ),
        "version": f"taxonomy-{VERSION}",
        "categories": [c.value for c in SkillCategory],
        "skills": [
            {
                "canonical_name": s.canonical_name,
                "slug": s.slug,
                "category": s.category,
                "synonyms": list(s.synonyms),
                **({"case_sensitive": True} if s.case_sensitive else {}),
            }
            for s in skills
        ],
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
