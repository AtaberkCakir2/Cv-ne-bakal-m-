"""CV metninden yetkinlik çıkarımı v1: taksonomi sözlüğü + kurallar (T-031). LLM gerektirmez (yedek yol).

    from extraction import extract_skills, to_present_skills
    skills = extract_skills(masked_text, "tr")   # list[ExtractedSkill]
    to_present_skills(skills)                    # contracts/analysis_result.schema.json: present_skills

Girdi maskelenmiş CV metnidir (pii.mask). Kurallar ai/eval/etiketleme-kilavuzu.md ile aynıdır:
- istek/hedef cümlesindeki yetkinlik alınmaz ("ileride Go öğrenmek istiyorum", "Şu an Next.js öğreniyorum");
- ders listesi satırındaki yetkinlik alınmaz ("Dersler: Kriptografi, İşletim Sistemleri");
- kategori başlığı yetkinlik sayılmaz ("DevOps: Docker, Kubernetes" → Docker, Kubernetes);
- konuşulan dil (İngilizce, Türkçe…) sadece Diller bölümünde veya seviyesiyle yazılmışsa alınır
  ("İngilizce: B2" evet, "Türkçe metinlerde sınıflandırma" hayır).
Seviye, adın hemen yanındaki ipucundan okunur ("Python (ileri düzey)", "Java — orta", "ileri düzey SQL", "B2");
deneyim yılı aynı ipucundan veya aynı cümle parçasındaki "N yıl"dan ("4 yıl Python deneyimi").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from extraction.taxonomy import Lang, Matcher, Mention, default_matcher

Level = Literal["beginner", "intermediate", "advanced", "unknown"]
_LEVEL_RANK: dict[Level, int] = {"unknown": 0, "beginner": 1, "intermediate": 2, "advanced": 3}

HUMAN_LANGUAGES = frozenset({"english", "turkish", "german", "french", "spanish", "arabic", "russian", "japanese"})

# Seviye ipuçları (küçük harf). Sıra önemli: "upper intermediate" "intermediate"dan önce denenir.
_LEVEL_WORDS: list[tuple[str, Level]] = [
    (r"ana\s*dil(?:i|im)?|native|mother\s+tongue|anadil", "advanced"),
    (r"c1|c2|fluent|akıcı|proficient|uzman|expert|ileri(?:\s+(?:düzey|seviye))?|advanced|çok\s+iyi", "advanced"),
    (
        r"upper[\s-]intermediate|b1|b2|orta(?:\s+(?:düzey|seviye))?|intermediate|iyi|good|working\s+knowledge",
        "intermediate",
    ),
    (r"a1|a2|temel(?:\s+(?:düzey|seviye))?|başlangıç|beginner|basic|elementary|giriş(?:\s+düzey)?", "beginner"),
]
_LEVEL_RE = [(re.compile(rf"(?<!\w)(?:{p})(?!\w)", re.IGNORECASE), lv) for p, lv in _LEVEL_WORDS]
_LEVEL_BEFORE = re.compile(
    r"(?<!\w)(ileri|orta|temel|başlangıç|advanced|intermediate|basic|beginner)\s+(?:düzey(?:de)?|seviye(?:de)?|level)?\s*$",
    re.IGNORECASE,
)
_YEARS = re.compile(r"(?<!\w)(\d{1,2})\s*\+?\s*(?:yıl(?:lık|dır|dir|ı)?|years?|yrs?)(?!\w)", re.IGNORECASE)
# Adın hemen ardından gelen ipucu: "(ileri düzey)", " — orta", ": B2"
_AFTER_HINT = re.compile(r"^[ \t]*(?:\(([^)\n]{1,40})\)|[:—–-][ \t]*([^,;·|\n(]{1,30}))")

_GOAL = re.compile(
    r"öğren(?:mek|meyi)\s+(?:istiyorum|planlıyorum|hedefliyorum|düşünüyorum)|öğreniyorum|ileride|hedefim"
    r"|want(?:ing)?\s+to\s+learn|plan(?:ning)?\s+to\s+learn|would\s+like\s+to\s+learn|eager\s+to\s+learn"
    r"|currently\s+learning|interested\s+in\s+learning",
    re.IGNORECASE,
)
_COURSES_LINE = re.compile(
    r"^[\s•\-*]*(?:aldığım\s+)?(?:dersler|ders\s+listesi|ilgili\s+dersler|courses|relevant\s+coursework|coursework)\b",
    re.IGNORECASE,
)
_SECTION = re.compile(
    r"^(?:teknik\s+)?(?:yetenekler|yetkinlikler|beceriler|teknik|teknolojiler|araçlar|skills|technical\s+skills"
    r"|tools|technologies|diller|yabancı\s+diller|dil|languages|sertifikalar|certifications|alanlar"
    r"|hakkımda|profil|özet|about|summary|eğitim|education|deneyim|iş\s+deneyimi|experience|staj|internships?"
    r"|projeler|projects|referanslar|references|dersler|courses|relevant\s+coursework)\s*:?$",
    re.IGNORECASE,
)
_SKILL_SECTIONS = re.compile(
    r"^(?:teknik\s+)?(?:yetenekler|yetkinlikler|beceriler|teknik|teknolojiler|araçlar|skills|technical\s+skills"
    r"|tools|technologies)",
    re.IGNORECASE,
)
_LANGUAGE_SECTIONS = re.compile(r"^(?:diller|yabancı\s+diller|dil|languages)", re.IGNORECASE)
_COURSE_SECTIONS = re.compile(r"^(?:dersler|courses|relevant\s+coursework)", re.IGNORECASE)
_LANGUAGE_LABEL = re.compile(r"(?<!\w)(?:dil(?:ler)?|yabancı\s+dil|languages?)\s*:", re.IGNORECASE)
_CLAUSE_END = re.compile(r"[,;.!?\n]|\s·\s")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+|\n")


@dataclass
class ExtractedSkill:
    skill: str  # taksonomideki standart ad
    slug: str
    category: str
    level: Level = "unknown"
    years: int | None = None
    mentions: int = 0
    in_skills_section: bool = False
    confidence: float = field(default=0.0)


@dataclass(frozen=True)
class _Line:
    start: int
    end: int
    section: str  # "skills" | "languages" | "courses" | "other"


def extract_skills(text: str, lang: Lang = "tr", *, matcher: Matcher | None = None) -> list[ExtractedSkill]:
    """Metinde geçen yetkinlikler, ilk geçtiği sıraya göre."""
    matcher = matcher or default_matcher()
    lines = _lines(text)
    goal_spans = [(s, e) for s, e in _sentences(text) if _GOAL.search(text[s:e])]
    result: dict[str, ExtractedSkill] = {}
    for mention in matcher.mentions(text, lang):
        line = next(ln for ln in lines if ln.start <= mention.start < ln.end)
        if not _counts(text, mention, line, goal_spans):
            continue
        s = mention.skill
        item = result.setdefault(s.slug, ExtractedSkill(s.canonical_name, s.slug, s.category))
        item.mentions += 1
        item.in_skills_section |= line.section in ("skills", "languages")
        level, years = _hints(text, mention, line)
        # Yetenekler bölümündeki ipucu öncelikli; yoksa ilk bulunan ipucu.
        if level != "unknown" and (item.level == "unknown" or line.section == "skills"):
            item.level = level
        if years is not None and (item.years is None or years > item.years):
            item.years = years
    for item in result.values():
        item.confidence = _confidence(item)
    return list(result.values())


def to_present_skills(skills: list[ExtractedSkill]) -> list[dict[str, Any]]:
    """contracts/analysis_result.schema.json → present_skills. Sözlükten gelen her yetkinlik taksonomidedir."""
    return [{"skill": s.skill, "level": s.level, "confidence": s.confidence, "verified": True} for s in skills]


# --- Kurallar -----------------------------------------------------------------------------------------------------


def _lines(text: str) -> list[_Line]:
    out: list[_Line] = []
    section = "other"
    pos = 0
    for raw in text.splitlines(keepends=True):
        content = raw.strip().strip("#*_ ")  # Markdown başlığı da olabilir ("## Yetenekler")
        if content and len(content) <= 40 and _SECTION.match(content):
            if _SKILL_SECTIONS.match(content):
                section = "skills"
            elif _LANGUAGE_SECTIONS.match(content):
                section = "languages"
            elif _COURSE_SECTIONS.match(content):
                section = "courses"
            else:
                section = "other"
        line_section = "courses" if _COURSES_LINE.match(raw) else section
        out.append(_Line(pos, pos + len(raw), line_section))
        pos += len(raw)
    if not out or out[-1].end < len(text):
        out.append(_Line(pos, len(text) + 1, section))
    return out


def _sentences(text: str) -> list[tuple[int, int]]:
    spans, last = [], 0
    for m in _SENTENCE_END.finditer(text):
        spans.append((last, m.start()))
        last = m.end()
    spans.append((last, len(text)))
    return spans


def _counts(text: str, mention: Mention, line: _Line, goal_spans: list[tuple[int, int]]) -> bool:
    if line.section == "courses" and not _inside_parens(text, line.start, mention.start):
        return False
    if any(s <= mention.start < e for s, e in goal_spans):
        return False
    before = text[line.start : mention.start]
    after = text[mention.end : line.end]
    # Kategori başlığı: satır başında "DevOps: Docker, …" (ardından seviye gelmiyorsa).
    if not before.strip(" \t•-*") and re.match(r"[ \t]*:[ \t]*\S", after) and _level_in(after[:20]) == "unknown":
        return False
    if mention.skill.slug in HUMAN_LANGUAGES:
        return (
            line.section == "languages"
            or bool(_LANGUAGE_LABEL.search(before))
            or _hints(text, mention, line)[0] != "unknown"
        )
    return True


def _inside_parens(text: str, line_start: int, pos: int) -> bool:
    seg = text[line_start:pos]
    return seg.count("(") > seg.count(")")


def _level_in(s: str) -> Level:
    for rx, lv in _LEVEL_RE:
        if rx.search(s):
            return lv
    return "unknown"


def _hints(text: str, mention: Mention, line: _Line) -> tuple[Level, int | None]:
    after = text[mention.end : line.end]
    level: Level = "unknown"
    years: int | None = None
    m = _AFTER_HINT.match(after)
    if m:
        hint = m.group(1) or m.group(2) or ""
        level = _level_in(hint)
        y = _YEARS.search(hint)
        years = int(y.group(1)) if y else None
    if level == "unknown":
        b = _LEVEL_BEFORE.search(text[line.start : mention.start])
        if b:
            level = _level_in(b.group(1))
    if years is None:
        years = _clause_years(text, mention, line)
    return level, years


def _clause_years(text: str, mention: Mention, line: _Line) -> int | None:
    """Aynı cümle parçasındaki "N yıl": önce addan önceki en yakın, yoksa sonraki."""
    left = line.start
    for m in _CLAUSE_END.finditer(text, line.start, mention.start):
        left = m.end()
    right_m = _CLAUSE_END.search(text, mention.end, line.end)
    right = right_m.start() if right_m else line.end
    before = list(_YEARS.finditer(text, left, mention.start))
    if before:
        return int(before[-1].group(1))
    after = _YEARS.search(text, mention.end, right)
    return int(after.group(1)) if after else None


def _confidence(item: ExtractedSkill) -> float:
    """Sözlük eşleşmesi kesindir; güven yetkinliğin CV'de ne kadar desteklendiğini gösterir (0,6–0,95)."""
    score = 0.6
    if item.in_skills_section:
        score += 0.15
    if item.mentions >= 2:
        score += 0.1
    if item.level != "unknown" or item.years is not None:
        score += 0.1
    return round(min(score, 0.95), 2)
