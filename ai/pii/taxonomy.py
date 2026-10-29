"""Yetkinlik taksonomisinin kelimeleri: ad tespitinde (kurallar ve NER) bu kelimeler ad sayılmaz.

"Python Django Developer" gibi bir unvan satırı ad sanılıp metnin her yerinde maskelenirse yetkinlik çıkarımı
(T-031, T-032) bozulur. Taksonomi `scraper/taxonomy/skills.csv`'dir; imajda başka yerdeyse `CAREERAI_TAXONOMY`.
"""

from __future__ import annotations

import csv
import logging
import os
import re
from functools import cache
from pathlib import Path

log = logging.getLogger(__name__)

TAXONOMY_ENV = "CAREERAI_TAXONOMY"
DEFAULT_TAXONOMY = Path(__file__).resolve().parents[2] / "scraper" / "taxonomy" / "skills.csv"

_WORD = re.compile(r"\w+")


def load_skill_words(path: Path) -> frozenset[str]:
    """Taksonomideki yetkinlik adı ve eş anlamlılarının kelimeleri (küçük harf)."""
    words: set[str] = set()
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            names = [row["canonical_name"], *row.get("synonyms", "").split("|")]
            for name in names:
                words.update(w.lower() for w in _WORD.findall(name))
    return frozenset(words)


@cache
def skill_words() -> frozenset[str]:
    """Varsayılan taksonominin kelimeleri; dosya yoksa boş küme (uyarıyla)."""
    path = Path(os.environ.get(TAXONOMY_ENV, DEFAULT_TAXONOMY))
    if not path.is_file():
        log.warning("yetkinlik taksonomisi bulunamadı (%s); ad tespiti taksonomi filtresiz çalışacak", path)
        return frozenset()
    return load_skill_words(path)
