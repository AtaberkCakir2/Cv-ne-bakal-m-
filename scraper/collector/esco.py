"""ESCO eşlemesi: taksonomideki yetkinliklere ESCO kavram URI'si (`esco_uri`) yazar.

Kaynak: ESCO indirme sayfasındaki sınıflandırma CSV'si, İngilizce `skills_en.csv`
(https://esco.ec.europa.eu/en/use-esco/download). Sadece birebir eşleşme kabul edilir: yetkinliğin adı veya bir
eş anlamlısı, ESCO'daki tercih edilen ad, alternatif ad veya "<ad> (computer programming)" biçimiyle aynı olmalı.
Belirsiz (birden fazla ESCO kavramına giden) terimler atlanır; yanlış URI yazmaktansa boş bırakılır.
"""

import csv
import re
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from collector.taxonomy import SKILLS_CSV, SkillRow

_PROGRAMMING_SUFFIX = re.compile(r"\s*\((computer programming|programming language)\)$")


def _norm(term: str) -> str:
    return " ".join(term.lower().split())


def load_esco_index(esco_csv: Path) -> dict[str, set[str]]:
    """terim → o terimi taşıyan ESCO kavram URI'leri."""
    index: dict[str, set[str]] = {}
    with esco_csv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status", "released") != "released":
                continue
            labels = [row.get("preferredLabel", ""), *row.get("altLabels", "").splitlines()]
            for label in labels:
                if not label.strip():
                    continue
                for term in {_norm(label), _norm(_PROGRAMMING_SUFFIX.sub("", label))}:
                    index.setdefault(term, set()).add(row["conceptUri"])
    return index


def map_skills(skills: Iterable[SkillRow], index: dict[str, set[str]]) -> list[SkillRow]:
    mapped: list[SkillRow] = []
    for skill in skills:
        if skill.esco_uri:  # elle girilmiş URI'ye dokunulmaz
            mapped.append(skill)
            continue
        candidates: set[str] = set()
        for term in (skill.canonical_name, *skill.synonyms):
            candidates |= index.get(_norm(term), set())
        mapped.append(replace(skill, esco_uri=candidates.pop()) if len(candidates) == 1 else skill)
    return mapped


def write_skills(skills: list[SkillRow], path: Path = SKILLS_CSV) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["canonical_name", "slug", "category", "synonyms", "esco_uri", "case_sensitive"])
        for s in skills:
            row = [s.canonical_name, s.slug, s.category, "|".join(s.synonyms), s.esco_uri or ""]
            writer.writerow([*row, "1" if s.case_sensitive else ""])
