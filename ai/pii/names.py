"""Kişi adlarının bulunması.

Ad-soyadın yapısı belli olmadığı için kurallar birleştirilir:
1. Etiketli alan: "Ad Soyad: …", "Name: …".
2. Başlık: belgenin ilk satırlarında, 2–4 büyük harfle başlayan kelimeden oluşan ve rakam içermeyen satır
   (CV'lerde ad neredeyse hep en üsttedir).
3. Unvanlı adlar: "Dr. …", "Prof. Dr. …", "Öğr. Gör. …", "Mr. …" (referanslar bölümü).
4. Bilinen bir ilk adla başlayan, büyük harfle devam eden kelime grubu ("… ekip lideri Ayşe Kaya ile …").
5. Bulunan adın kelimeleri metnin geri kalanında büyük harfle geçtiği her yerde de maskelenir ("Mert'in …").

Yetkinlik taksonomisinin kelimeleri ve unvan kelimeleri ("Python Django Developer", "Kıdemli Backend Geliştirici")
başlık satırında ad sayılmaz ve yayılmaz; yoksa unvan satırındaki yetkinlikler bütün CV'de silinir.

Yerel varlık tanıma (NER) modeli `detector` parametresiyle eklenir (`pii.ner.default_detector()`, karar #24);
sonuçları kurallarınkiyle birleştirilir.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Literal

from pii.kinds import Kind
from pii.patterns import Span
from pii.taxonomy import skill_words

Lang = Literal["tr", "en"]
NameDetector = Callable[[str, Lang], list[tuple[int, int]]]

_UPPER = "A-ZÇĞİÖŞÜÂÎÛ"
_LOWER = "a-zçğıöşüâîû"
_WORD = rf"[{_UPPER}][{_LOWER}]+(?:-[{_UPPER}][{_LOWER}]+)?"
_CAPS_WORD = rf"[{_UPPER}]{{2,}}"
_NAME_TOKEN = rf"(?:{_WORD}|{_CAPS_WORD})"
_SP = r"[ \t]+"  # ad kelimeleri arasında boşluk; satır sonu adı bitirir (alt satırdaki unvan ada katılmaz)

LABELED = re.compile(
    r"\b(?:ad[ıi]?\s*(?:ve\s*)?soyad[ıi]?|ad\s*-\s*soyad|isim|full\s+name|name|aday)\s*:\s*([^\n·|•;]+)",
    re.IGNORECASE,
)
HONORIFIC = re.compile(
    r"\b(?:Prof\.\s*Dr\.|Doç\.\s*Dr\.|Dr\.\s*Öğr\.\s*Üyesi|Dr\.|Prof\.|Doç\.|Öğr\.\s*Gör\.|Arş\.\s*Gör\.|Av\.|Müh\."
    # Noktalı unvandan sonra boşluk şart değil ("Dr.Ayhan"); adın önünde baş harfler olabilir ("Prof. Dr. H. Meffert").
    rf"|Mr\.?|Mrs\.?|Ms\.?|Sayın|Bay|Bayan)(?:{_SP}|(?<=\.))"
    rf"((?:[{_UPPER}]\.[ \t]*){{0,3}}{_WORD}(?:{_SP}{_NAME_TOKEN}){{0,2}})"
)
# "Ms" Türkçe CV'lerde Microsoft kısaltmasıdır ("Ms Excel"): bunlar ad değil, yetkinliktir.
_MS_PRODUCTS = frozenset("Excel Office Word Outlook Power Access Project Teams Visio Sql Dos Azure Windows".split())
# Türkçe hitaplar İngilizce metinde ad öneki değildir ("Bay Area", "North Bay").
_TR_ONLY_TITLES = frozenset({"Sayın", "Bay", "Bayan"})
# Unvanla başlayan marka adları. Unvandan sonraki her ad maskelenir ("Mr. Johnson", "Prof. Smith"); fazla maskelemenin
# yetkinlik maliyeti yok, kaçırmanın var. İstisna sadece bu küçük liste.
HONORIFIC_BRANDS = frozenset(
    {
        "Dr. Squatch", "Dr. Martens", "Dr. Dre", "Dr. Oetker", "Dr. Pepper", "Dr. Scholl",
        "Mr. Clean", "Mr. Rooter", "Mr. Electric", "Mr. Bean",
    }
)  # fmt: skip
HEADER_LINE = re.compile(rf"^[ \t]*{_NAME_TOKEN}(?:{_SP}{_NAME_TOKEN}){{1,3}}[ \t]*$")
# İlk satırlarda ad olmayan başlıklar
NOT_A_NAME = re.compile(
    r"^\s*(?:özgeçmiş|ozgecmis|cv|curriculum\s+vitae|resume|résumé|kişisel\s+bilgiler|personal\s+information)\s*$",
    re.IGNORECASE,
)
HEADER_LINES = 3
# Başlıktaki unvan satırının kelimeleri (taksonomide olmayanlar); küçük harf.
TITLE_WORDS = frozenset(
    """
    geliştirici geliştiricisi developer engineer mühendis mühendisi uzman uzmanı specialist kıdemli senior junior
    stajyer intern analist analyst bilimci scientist tasarımcı designer yönetici manager lead lider mimar architect
    danışman consultant öğrenci öğrencisi student backend frontend full stack yazılım software programcı programmer
    """.split()
)

# Sık görülen ilk adlar (Türkçe + birkaç İngilizce). Teknoloji adıyla aynı olanlar bilinçli olarak yok (Ada, Ruby).
FIRST_NAMES = frozenset(
    """
    Ahmet Mehmet Mustafa Ali Hüseyin Hasan İbrahim İsmail Osman Yusuf Murat Ömer Ramazan Halil Süleyman Abdullah
    Mahmut Recep Salih Fatih Kadir Emre Hakan Burak Serkan Onur Mert Can Cem Kaan Emir Eren Efe Arda Baran Berk
    Alp Batuhan Doğan Oğuz Ozan Tolga Uğur Volkan Selim Serdar Sinan Barış Furkan Yiğit Kerem Tuna Tunahan Umut
    Yasin Enes Anıl Ataberk Berkay Çağan Çağrı Deniz Egemen Erdem Gökhan Görkem İlker Kemal Levent Metin Orhan
    Rıza Sarp Taner Tarık Yavuz Yunus Zafer Fatma Ayşe Emine Hatice Zeynep Elif Meryem Şerife Zehra Sultan Hanife
    Merve Özlem Esra Büşra Kübra Seda Sevgi Derya Ebru Ece Ezgi Gizem İrem Melis Selin Sena Simge Tuğba Yasemin
    Aslı Aylin Beril Burcu Ceren Damla Defne Duygu Eda Ela Elçin Gamze Gül Gülşen Hande İpek Nazlı Nur Pınar
    Sibel Şule Tuba Yağmur Zerrin Ayla Berna Cansu Dilara Dilek Ecem Hilal Lale Leyla Nihan Öykü Rabia Sude
    John James Michael David Robert Mary Sarah Emily Anna Laura
    """.split()
)
_FIRST_NAME_PHRASE = re.compile(rf"\b({_WORD})((?:{_SP}{_NAME_TOKEN}){{1,2}})")
_FIRST_NAME_START = re.compile(rf"(?<![\w-]){_WORD}")
_MIN_PROPAGATE_LEN = 3


def find_names(
    text: str,
    lang: Lang = "tr",
    detector: NameDetector | None = None,
    *,
    header: bool = True,
    skip_words: frozenset[str] | None = None,
) -> list[Span]:
    """`header=False`: başlık kuralı (2) uygulanmaz; ilk satırı ad olmayan belgeler için (ilan metni).
    `skip_words`: ad sayılmayacak kelimeler (küçük harf); verilmezse taksonomi + unvan kelimeleri."""
    skip = (skill_words() if skip_words is None else skip_words) | TITLE_WORDS
    spans: list[Span] = []
    for m in LABELED.finditer(text):
        value = m.group(1).rstrip()
        if value:
            spans.append(Span(m.start(1), m.start(1) + len(value), Kind.NAME))
    if header:
        spans += _header_name(text, skip)
    for m in HONORIFIC.finditer(text):
        title, name = text[m.start() : m.start(1)].strip(), m.group(1)
        if lang != "tr" and title in _TR_ONLY_TITLES:
            continue
        last_title = re.split(r"[\s.]+", title.rstrip("."))[-1]
        first_word = name.split()[0]
        if f"{last_title}. {first_word}" in HONORIFIC_BRANDS or (last_title == "Ms" and first_word in _MS_PRODUCTS):
            continue
        spans.append(Span(m.start(1), m.end(1), Kind.NAME))
    # Her ilk ad kendi konumundan denenir: "Contact Ayşe Kaya" grubunda önceki büyük harfli kelime ("Contact")
    # eşleşmeyi yutup ilk adı atlatmasın.
    for w in _FIRST_NAME_START.finditer(text):
        if w.group() in FIRST_NAMES and (phrase := _FIRST_NAME_PHRASE.match(text, w.start())):
            # Addan sonra gelen yetkinlik/unvan kelimesi ada katılmaz ("Mert Python ile …").
            end = w.end()
            for tok in re.finditer(r"\S+", phrase.group(2)):
                if _is_skipped(tok.group(), skip):
                    break
                end = phrase.start(2) + tok.end()
            if end > w.end():
                spans.append(Span(phrase.start(), end, Kind.NAME))
    if detector is not None:
        spans += [Span(start, end, Kind.NAME) for start, end in detector(text, lang)]
    return spans + _propagate(text, spans, skip)


def _is_skipped(word: str, skip: frozenset[str]) -> bool:
    return tr_lower(word) in skip or word.lower() in skip


def _header_name(text: str, skip: frozenset[str]) -> list[Span]:
    offset = 0
    seen = 0
    for line in text.splitlines(keepends=True):
        content = line.strip()
        if content:
            seen += 1
            if seen > HEADER_LINES:
                break
            if (
                not NOT_A_NAME.match(content)
                and HEADER_LINE.match(content)
                and not any(_is_skipped(w, skip) for w in content.split())
            ):
                start = offset + line.index(content)
                return [Span(start, start + len(content), Kind.NAME)]
        offset += len(line)
    return []


def tr_lower(s: str) -> str:
    """Türkçe kurallı küçük harf: I → ı, İ → i (str.lower() İ'yi "i̇" yapar)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_title(s: str) -> str:
    """ "AYDOĞAN" → "Aydoğan", "İSMAİL" → "İsmail"."""
    return tr_upper(s[:1]) + tr_lower(s[1:]) if s else s


def _propagate(text: str, spans: list[Span], skip: frozenset[str]) -> list[Span]:
    """Bulunan adların kelimeleri metnin başka yerlerinde de (büyük harfle, kelime olarak) maskelenir."""
    tokens = {
        token
        for s in spans
        for token in re.findall(rf"[{_UPPER}{_LOWER}]+", text[s.start : s.end])
        if len(token) >= _MIN_PROPAGATE_LEN and token[0].isupper() and not _is_skipped(token, skip)
    }
    if not tokens:
        return []
    variants = tokens | {tr_upper(t) for t in tokens} | {tr_title(t) for t in tokens}
    pattern = re.compile(
        r"(?<![\w])(" + "|".join(re.escape(t) for t in sorted(variants, key=len, reverse=True)) + r")(?![\w])"
    )
    return [Span(m.start(), m.end(), Kind.NAME) for m in pattern.finditer(text)]
