"""Yetkinlik taksonomisi (scraper/taxonomy/skills.csv) ve metinde geçen yetkinliklerin bulunması.

Eşleme kuralları ilan eşleyicisiyle (scraper/etl/skills.py, Ataberk) aynıdır, CV'de de aynı sonucu versin diye:
- kelime sınırı: "Java" "JavaScript" içinde bulunmaz; "C++", ".NET", "Node.js" gibi noktalama içeren adlar çalışır;
- `case_sensitive` yetkinliğin adı sadece yazıldığı gibi eşleşir ("Go", "SOLID"); eş anlamlıları harf duyarsızdır;
- Türkçe metin iki katlamayla denenir ("İ" → "i"; "I" hem "ı" hem "i"), çünkü teknoloji adları Latin I ile yazılır.
Ortak paket olunca (T-031 sonrası, Ataberk'le) bu modül ve etl/skills.py birleştirilebilir.
"""

from __future__ import annotations

import csv
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

Lang = Literal["tr", "en"]

TAXONOMY_ENV = "CAREERAI_TAXONOMY"
DEFAULT_TAXONOMY = Path(__file__).resolve().parents[2] / "scraper" / "taxonomy" / "skills.csv"

# Önce/sonra gelen karakter adın devamı olmamalı. Sondaki nokta cümle sonu olabilir ("...Python."), ama ardından
# harf geliyorsa ad devam ediyordur ("Node.js").
_BEFORE = r"(?<![\w.#+@])"
_AFTER = r"(?![\w#+]|\.\w)"


@dataclass(frozen=True)
class Skill:
    canonical_name: str  # contracts/analysis_result.schema.json: present_skills[].skill
    slug: str
    category: str
    synonyms: tuple[str, ...]
    case_sensitive: bool = False


@dataclass(frozen=True)
class Mention:
    skill: Skill
    start: int
    end: int


def load_skills(path: Path | None = None) -> list[Skill]:
    path = path or Path(os.environ.get(TAXONOMY_ENV, DEFAULT_TAXONOMY))
    with path.open(encoding="utf-8", newline="") as f:
        return [
            Skill(
                canonical_name=row["canonical_name"].strip(),
                slug=row["slug"].strip(),
                category=row["category"].strip(),
                synonyms=tuple(s.strip() for s in row["synonyms"].split("|") if s.strip()),
                case_sensitive=row.get("case_sensitive", "").strip() == "1",
            )
            for row in csv.DictReader(f)
        ]


def fold(text: str, lang: Lang = "en") -> str:
    """Türkçe kurallı küçük harf; uzunluğu değiştirmez (konumlar metindekiyle aynı kalır)."""
    text = text.replace("İ", "i")
    if lang == "tr":
        text = text.replace("I", "ı")
    return text.lower()


def _alternation(terms: Iterable[str]) -> str:
    # Uzun terim önce: "spring boot" "spring"den, "react native" "react"tan önce denensin.
    return "|".join(re.escape(t) for t in sorted(set(terms), key=lambda t: (-len(t), t)))


class Matcher:
    def __init__(self, skills: Iterable[Skill]) -> None:
        self._by_term: dict[str, Skill] = {}
        self._by_exact: dict[str, Skill] = {}
        for s in skills:
            if s.case_sensitive:
                self._by_exact.setdefault(s.canonical_name, s)
            else:
                self._by_term.setdefault(fold(s.canonical_name), s)
            for syn in s.synonyms:
                self._by_term.setdefault(fold(syn), s)
        self._folded = re.compile(f"{_BEFORE}({_alternation(self._by_term)}){_AFTER}")
        self._exact = re.compile(f"{_BEFORE}({_alternation(self._by_exact)}){_AFTER}") if self._by_exact else None

    def mentions(self, text: str, lang: Lang = "tr") -> list[Mention]:
        """Metindeki tüm geçişler, konum sırasıyla. Çakışan geçişlerde uzun olan kalır ("Spring Boot" > "Spring")."""
        variants = [fold(text, "tr"), fold(text, "en")] if lang == "tr" else [fold(text, lang)]
        found = [
            Mention(self._by_term[m.group(1)], m.start(), m.end()) for v in variants for m in self._folded.finditer(v)
        ]
        if self._exact:
            found += [Mention(self._by_exact[m.group(1)], m.start(), m.end()) for m in self._exact.finditer(text)]
        found.sort(key=lambda m: (m.start, -(m.end - m.start)))
        result: list[Mention] = []
        for m in found:
            if result and m.start < result[-1].end:
                continue
            result.append(m)
        return result


@cache
def default_matcher() -> Matcher:
    return Matcher(load_skills())
