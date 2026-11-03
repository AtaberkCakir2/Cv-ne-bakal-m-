"""Taksonomi CSV'lerinin okunması; veritabanı ve SQLAlchemy kullanmaz.

Eşleyiciler (etl/skills.py, etl/roles.py) taksonomiyi sadece bu modülden okur; böylece backend paketi kurulmadan da
(ör. sadece ai/'den derlenen worker imajında) çalışır. etl/skills.py eşlemeyi ai/'deki extraction.taxonomy ile
yapar. Doğrulama ve veritabanına yazma `collector.taxonomy`'de.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

TAXONOMY_DIR = Path(__file__).resolve().parents[1] / "taxonomy"
SKILLS_CSV = TAXONOMY_DIR / "skills.csv"
ROLES_CSV = TAXONOMY_DIR / "roles.csv"


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
