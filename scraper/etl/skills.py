"""İlan metni → taksonomideki yetkinlikler ve önem derecesi (contracts/job_posting.schema.json: skills).

Eşleme CV tarafıyla aynı eşleyiciyle yapılır (Burak'ın `extraction.taxonomy.Matcher`'ı, T-031): CV ve ilan aynı
kuralla etiketlenmezse eşleştirmede yapay eksikler çıkar. Kurallar: kelime sınırı ("Java" "JavaScript" içinde
bulunmaz, "C++" ve ".NET" gibi noktalama içeren adlar çalışır), `case_sensitive` yetkinliğin adı sadece o yazımla
eşleşir ("solid understanding" SOLID değildir) ve çakışan geçişlerde en uzun eşleşme kazanır ("Objective-C" C değil,
"Ruby on Rails" Ruby değil, "Azure DevOps" DevOps değil).

Önem: "Nice to have" / "Tercih sebebi" gibi başlıkların altındaki bölümde veya "... is a plus", "... tercih
sebebidir" diyen cümlede geçen yetkinlik `preferred`, diğerleri `required`. İkisinde birden geçen `required` olur.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal

from extraction.taxonomy import Matcher, Skill

from collector.clean import Lang
from collector.taxonomy_rows import SkillRow

Importance = Literal["required", "preferred"]

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
        rows = list(skills)
        self._rows = {s.slug: s for s in rows}
        self._matcher = Matcher(Skill(s.canonical_name, s.slug, s.category, s.synonyms, s.case_sensitive) for s in rows)

    def find(self, text: str, lang: Lang = "en") -> list[SkillRow]:
        """Metinde geçen yetkinlikler, ilk geçtiği sıraya göre ve tekrarsız."""
        result: dict[str, SkillRow] = {}
        for m in self._matcher.mentions(text, lang):
            result.setdefault(m.skill.slug, self._rows[m.skill.slug])
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
