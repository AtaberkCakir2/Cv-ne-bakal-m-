"""Yetkinlik taksonomisi ve hedef pozisyonlar (T-017).

Tek doğru kaynak `scraper/taxonomy/skills.csv` ve `roles.csv`. Veritabanına `seed` ile yazılır (slug'a göre
ekle/güncelle); CSV'den çıkarılan kayıt silinmez, pasife alınır (ilan ve analizler ona bağlı olabilir).
Eş anlamlılar küçük harf; bir eş anlamlı tek bir yetkinliğe ait olmalı (eşleme belirsiz olmasın).
"""

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.db.enums import SkillCategory
from app.db.models import Role, Skill
from sqlalchemy import select
from sqlalchemy.orm import Session

TAXONOMY_DIR = Path(__file__).resolve().parents[1] / "taxonomy"
SKILLS_CSV = TAXONOMY_DIR / "skills.csv"
ROLES_CSV = TAXONOMY_DIR / "roles.csv"
VERSION = "1"

_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CATEGORIES = {c.value for c in SkillCategory}


@dataclass(frozen=True)
class SkillRow:
    canonical_name: str
    slug: str
    category: str
    synonyms: tuple[str, ...]
    esco_uri: str | None
    # Adı sıradan bir kelimeyle aynı (Go, Swift, SOLID, Spring...): ad sadece bu yazımla eşleşmeli,
    # "solid understanding" SOLID sayılmamalı. Eş anlamlılar (golang, spring boot...) yine harf duyarsız.
    # Veritabanında sütunu yok; eşleyici (T-031) için CSV ve JSON çıktısında taşınır.
    case_sensitive: bool = False


@dataclass(frozen=True)
class RoleRow:
    name: str
    slug: str
    synonyms: tuple[str, ...]
    description: str


def _split(cell: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in cell.split("|") if s.strip())


def load_skills(path: Path = SKILLS_CSV) -> list[SkillRow]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            SkillRow(
                canonical_name=row["canonical_name"].strip(),
                slug=row["slug"].strip(),
                category=row["category"].strip(),
                synonyms=_split(row["synonyms"]),
                esco_uri=row["esco_uri"].strip() or None,
                case_sensitive=row.get("case_sensitive", "").strip() == "1",
            )
            for row in csv.DictReader(f)
        ]


def load_roles(path: Path = ROLES_CSV) -> list[RoleRow]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            RoleRow(
                name=row["name"].strip(),
                slug=row["slug"].strip(),
                synonyms=_split(row["synonyms"]),
                description=row["description"].strip(),
            )
            for row in csv.DictReader(f)
        ]


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
