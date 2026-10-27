"""İlan başlığı → hedef pozisyon (roles.csv slug'ı).

Başlık parçalara ayrılır ("Şirket | Pozisyon | Konum" — Hacker News biçimi, "Pozisyon — Remote (US)"), parantez
içleri atılır ve her parçada pozisyon eş anlamlıları aranır. İlk eşleşen parça kazanır; parça içinde en solda başlayan
(eşitse en uzun) eş anlamlı seçilir. "Software Engineer" gibi genel başlıklar hiçbir pozisyona eşlenmez (None):
pozisyonu belirsiz ilan, pozisyon istatistiğini bozmaktansa dışarıda kalır.

İki deneme yapılır: önce başlığın kendisi, olmazsa kıdem ("Senior", "Lead"), "Software" ve teknoloji adları
atılmış hali ("Senior Python Backend Software Engineer" → "backend developer"). Hiçbir parça eşleşmezse pozisyonun
parantez içinde yazıldığı genel başlıklara bakılır: "Founding Engineer (Full-Stack)" → "full stack developer".
"""

import re
from collections.abc import Iterable

from collector.clean import Lang
from collector.taxonomy import RoleRow, SkillRow
from etl.text import fold_phrase

_SEGMENT_SPLIT = re.compile(r"\||\s[—–-]\s|\n")
_BRACKETS = re.compile(r"\([^)]*\)?|\[[^\]]*\]?")
_LIST_SPLIT = re.compile(r"[,/&]|\band\b", re.IGNORECASE)
_PUNCT = re.compile(r"[^\w\s]")

# Meslek adları tek biçime indirilir: "backend engineer", "backend developer", "back-end geliştirici" aynı şey.
_NOUNS = {
    "developer": "developer",
    "developers": "developer",
    "dev": "developer",
    "devs": "developer",
    "engineer": "developer",
    "engineers": "developer",
    "eng": "developer",
    "programmer": "developer",
    "programmers": "developer",
    "geliştirici": "developer",
    "geliştiricisi": "developer",
    "geliştiriciler": "developer",
    "mühendis": "developer",
    "mühendisi": "developer",
    "mühendisleri": "developer",
    "programcı": "developer",
    "programcısı": "developer",
    "scientists": "scientist",
    "analysts": "analyst",
    "testers": "tester",
    "architects": "architect",
    "specialists": "specialist",
}
# İkinci denemede atılan kelimeler. İlk deneme bunlarla yapıldığı için "software tester" yine eşleşir.
_FILLER = {
    "senior",
    "sr",
    "junior",
    "jr",
    "mid",
    "level",
    "lead",
    "staff",
    "principal",
    "founding",
    "head",
    "chief",
    "intern",
    "internship",
    "trainee",
    "ii",
    "iii",
    "iv",
    "software",
    "yazılım",
    "kıdemli",
    "uzman",
    "stajyer",
    "remote",
    "contract",
    "freelance",
}


def _tokens(text: str, lang: Lang) -> list[str]:
    words = _PUNCT.sub(" ", fold_phrase(text, lang)).split()
    return [_NOUNS.get(w, w) for w in words]


class RoleMatcher:
    def __init__(self, roles: Iterable[RoleRow], skills: Iterable[SkillRow] = ()) -> None:
        self._phrases: dict[str, str] = {}
        for role in roles:
            for synonym in (role.name, *role.synonyms):
                phrase = " ".join(_tokens(synonym, "tr"))
                other = self._phrases.setdefault(phrase, role.slug)
                if other != role.slug:
                    raise ValueError(f"pozisyon eş anlamlısı {phrase!r} iki pozisyonda: {other}, {role.slug}")
        role_words = {w for phrase in self._phrases for w in phrase.split()}
        # Tek kelimelik teknoloji adları ("python", "kotlin") ikinci denemede atılır; pozisyon adında geçenler
        # ("android", "flutter", "unity") kalır.
        skill_words = {
            w
            for s in skills
            for term in (s.canonical_name, *s.synonyms)
            if len(words := _tokens(term, "en")) == 1
            for w in words
        }
        self._drop = _FILLER | (skill_words - role_words)
        self._skill_words = skill_words

    def _find(self, tokens: list[str]) -> str | None:
        text = f" {' '.join(tokens)} "
        best: tuple[int, int, str] | None = None
        for phrase, slug in self._phrases.items():
            pos = text.find(f" {phrase} ")
            if pos >= 0 and (best is None or (pos, -len(phrase)) < best[:2]):
                best = (pos, -len(phrase), slug)
        return best[2] if best else None

    def match(self, title: str, lang: Lang = "en") -> str | None:
        # Türkçe başlık iki katlamayla denenir: "OYUN PROGRAMCISI" (I → ı) ve "API Geliştirici" (I → i).
        langs: list[Lang] = ["tr", "en"] if lang == "tr" else [lang]
        segments = _SEGMENT_SPLIT.split(title)
        for segment in segments:
            for variant in langs:
                if slug := self._find_variants(_tokens(_BRACKETS.sub(" ", segment), variant)):
                    return slug
        for segment in segments:
            if "developer" not in _tokens(_BRACKETS.sub(" ", segment), lang):
                continue  # parantez sadece genel meslek adını açıklıyorsa ("Engineer (Backend)") kullanılır
            items = [
                _tokens(item, lang) for b in _BRACKETS.findall(segment) for item in _LIST_SPLIT.split(b.strip("()[]"))
            ]
            # Teknoloji adı olmayan öğe önce: "(Python, Full-Stack)" → full-stack, "Python Developer" (backend) değil.
            # Tek öğe teknoloji adıysa yine kullanılır: "(Android)" → mobil.
            items.sort(key=lambda tokens: all(t in self._skill_words for t in tokens))
            for tokens in items:
                if tokens and (slug := self._find_variants([*tokens, "developer"])):
                    return slug
        return None

    def _find_variants(self, tokens: list[str]) -> str | None:
        return self._find(tokens) or self._find([t for t in tokens if t not in self._drop])
