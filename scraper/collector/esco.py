"""ESCO eşlemesi: taksonomideki yetkinliklere ESCO kavram URI'si (`esco_uri`) yazar.

Kaynak: ESCO indirme sayfasındaki sınıflandırma CSV'si, İngilizce `skills_en.csv`
(https://esco.ec.europa.eu/en/use-esco/download, ESCO v1.2.1).

Sadece ESCO'nun **tercih edilen adı** ile birebir eşleşme kabul edilir (sondaki parantezli açıklama yok sayılır:
"Jenkins (tools for software configuration management)" → "jenkins"). Alternatif adlar kullanılmaz: ESCO onları
geniş kavramlara toplar ("computer programming" kavramının alternatifleri arasında bash, OCaml, OpenCV; "computer
vision"ınkiler arasında tensorflow, keras var), bunlarla eşlemek yanlış URI yazar. Birden fazla kavrama giden terim
atlanır; yanlış URI yazmaktansa boş bırakılır.
"""

import csv
import re
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from collector.taxonomy_rows import SKILLS_CSV, SkillRow

_TRAILING_NOTE = re.compile(r"\s*\([^)]*\)$")

# Adı aynı ama başka bir şey olan ESCO kavramları (elle incelendi, v1.2.1).
HOMONYMS = {
    "spark": "ESCO'daki SPARK, Java micro framework'ü; Apache Spark değil",
}


def _norm(term: str) -> str:
    return " ".join(term.lower().split())


def load_esco_index(esco_csv: Path) -> dict[str, set[str]]:
    """Tercih edilen ad (parantezli not çıkarılmış) → o adı taşıyan ESCO kavram URI'leri."""
    index: dict[str, set[str]] = {}
    with esco_csv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status", "released") != "released":
                continue
            label = row.get("preferredLabel", "")
            for term in {_norm(label), _norm(_TRAILING_NOTE.sub("", label))}:
                if term:
                    index.setdefault(term, set()).add(row["conceptUri"])
    return index


def map_skills(skills: Iterable[SkillRow], index: dict[str, set[str]]) -> list[SkillRow]:
    mapped: list[SkillRow] = []
    for skill in skills:
        if skill.esco_uri or skill.slug in HOMONYMS:  # elle girilmiş URI'ye dokunulmaz
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
