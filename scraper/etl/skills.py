"""İlan metni → taksonomideki yetkinlikler ve önem derecesi (contracts/job_posting.schema.json: skills).

Eşleme taksonomi + eş anlamlılarla, kelime sınırına bakarak yapılır ("Java" "JavaScript" içinde bulunmaz, "C++" ve
".NET" gibi noktalama içeren adlar da çalışır). `case_sensitive` yetkinliklerin adı sadece o yazımla eşleşir
("solid understanding" SOLID değildir); eş anlamlıları her zaman harf duyarsızdır.

Önem: "Nice to have" / "Tercih sebebi" gibi başlıkların altındaki bölümde veya "... is a plus", "... tercih
sebebidir" diyen cümlede geçen yetkinlik `preferred`, diğerleri `required`. İkisinde birden geçen `required` olur.

Not: Bu ilanlar için sözlük eşleyicisidir. Burak'ın CV yetkinlik çıkarımı (T-031) gelince aynı arayüzle
(`tag(text, lang) -> list[TaggedSkill]`) değiştirilebilir veya ortaklaştırılabilir.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal

from collector.clean import Lang
from collector.taxonomy import SkillRow
from etl.text import fold, fold_variants

Importance = Literal["required", "preferred"]

# Önce/sonra gelen karakter yetkinlik adının devamı olmamalı. Sondaki nokta cümle sonu olabilir ("...Python."),
# ama ardından harf geliyorsa ad devam ediyordur ("Node.js").
_BEFORE = r"(?<![\w.#+@])"
_AFTER = r"(?![\w#+]|\.\w)"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+")
_PREFERRED_INLINE = re.compile(
    r"nice[\s-]to[\s-]have|\bpreferred\b|\b(a|big|huge|bonus) plus\b|\bpluses\b|\bbonus\b|\bideally\b|\bdesirable\b"
    r"|would be (great|nice|a plus)|not required|tercih sebeb|tercih edilir|tercihen|\bartı\b|artıdır|avantaj",
    re.IGNORECASE,
)
_PREFERRED_HEADER = re.compile(
    r"nice[\s-]to[\s-]have|bonus points?|preferred (qualifications|skills|experience)|\bpluses\b|\bplus\s*:|bonus\s*:"
    r"|extra credit|tercih sebeb|artılar|avantaj",
    re.IGNORECASE,
)
_ANY_HEADER = re.compile(
    r"requirements|qualifications|responsibilities|what you('ll| will)|about (us|you|the role)|benefits|we offer"
    r"|perks|who you are|must[\s-]have|you have|you bring|aranan|nitelikler|sorumluluklar|iş tanımı|yan haklar",
    re.IGNORECASE,
)
_MAX_HEADER_LEN = 60


@dataclass(frozen=True)
class TaggedSkill:
    slug: str
    canonical_name: str  # contracts: skills[].skill
    importance: Importance


def _alternation(terms: Iterable[str]) -> str:
    # Uzun terim önce: "spring boot" "spring"den, "react native" "react"tan önce denensin.
    return "|".join(re.escape(t) for t in sorted(set(terms), key=lambda t: (-len(t), t)))


def _is_header(line: str) -> bool:
    return (
        len(line) <= _MAX_HEADER_LEN
        and not line.startswith("- ")
        and (line.endswith(":") or bool(_ANY_HEADER.search(line)) or bool(_PREFERRED_HEADER.search(line)))
    )


def sentences(text: str) -> Iterator[tuple[str, bool]]:
    """(cümle, tercih bölümünde/cümlesinde mi) çiftleri."""
    in_preferred = False
    seen_content = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if in_preferred and seen_content:
                in_preferred = False  # bölüm boş satırla biter
            continue
        if _is_header(line):
            in_preferred = bool(_PREFERRED_HEADER.search(line))
            seen_content = False
            # Başlık satırının kendisi de yetkinlik içerebilir ("Nice to have: Kubernetes").
        else:
            seen_content = True
        for sentence in _SENTENCE_SPLIT.split(line):
            yield sentence, in_preferred or bool(_PREFERRED_INLINE.search(sentence))


class SkillTagger:
    def __init__(self, skills: Iterable[SkillRow]) -> None:
        self._by_term: dict[str, SkillRow] = {}
        self._by_exact: dict[str, SkillRow] = {}
        for s in skills:
            # taxonomy.validate: bir terim tek yetkinliğe ait; burada sadece ilk görülen kullanılır.
            if s.case_sensitive:
                self._by_exact.setdefault(s.canonical_name, s)
            else:
                self._by_term.setdefault(fold(s.canonical_name), s)
            for syn in s.synonyms:
                self._by_term.setdefault(fold(syn), s)
        self._folded = re.compile(f"{_BEFORE}({_alternation(self._by_term)}){_AFTER}")
        self._exact = re.compile(f"{_BEFORE}({_alternation(self._by_exact)}){_AFTER}") if self._by_exact else None

    def find(self, text: str, lang: Lang = "en") -> list[SkillRow]:
        """Metinde geçen yetkinlikler, ilk geçtiği sıraya göre ve tekrarsız."""
        found = [
            (m.start(), self._by_term[m.group(1)])
            for variant in fold_variants(text, lang)
            for m in self._folded.finditer(variant)
        ]
        if self._exact:
            found += [(m.start(), self._by_exact[m.group(1)]) for m in self._exact.finditer(text)]
        result: dict[str, SkillRow] = {}
        for _, skill in sorted(found, key=lambda f: f[0]):
            result.setdefault(skill.slug, skill)
        return list(result.values())

    def tag(self, text: str, lang: Lang = "en") -> list[TaggedSkill]:
        importance: dict[str, Importance] = {}
        rows: dict[str, SkillRow] = {}
        for sentence, preferred in sentences(text):
            for skill in self.find(sentence, lang):
                rows.setdefault(skill.slug, skill)
                if not preferred:
                    importance[skill.slug] = "required"
                else:
                    importance.setdefault(skill.slug, "preferred")
        return [TaggedSkill(slug, rows[slug].canonical_name, imp) for slug, imp in importance.items()]
