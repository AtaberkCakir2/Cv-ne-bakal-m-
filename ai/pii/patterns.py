"""Yapısı belli kişisel veriler için düzenli ifadeler: e-posta, telefon, TCKN, IBAN, bağlantı, doğum tarihi, adres.

Kural: **kaçırmaktansa fazla maskele.** Bir CV'de 11 haneli her sayı TCKN gibi, her tam tarih (gün.ay.yıl, yıl
1950–2012) doğum tarihi gibi maskelenir; yetkinlik çıkarımı bu bilgilere ihtiyaç duymaz.

Teknoloji adları bağlantı sanılmaz: alan adı uzantıları küçük harfle ve sınırlı bir listeyle aranır, böylece
"Node.js", "ASP.NET", "Vue.js" dokunulmadan kalır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pii.kinds import Kind


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    kind: Kind


EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# Türkiye: +90 / 0090 / 0 ön ekli 10 hane (cep 5xx, sabit 2xx-4xx); parantez, boşluk, nokta, tire serbest.
# Yurt dışı: + ile başlayan, en az 9 haneli numara.
PHONE = re.compile(
    r"(?<![\w+])(?:"
    r"(?:\+90|0090|0)?[\s.-]*\(?[2-5]\d{2}\)?[\s.-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}"
    r"|\+(?!90)\d{1,3}(?:[\s.-]*\(?\d{1,4}\)?){2,5}"
    r")(?![\w])"
)
_PHONE_MIN_DIGITS = 9

# Hash veya kod içindeki 11 hane TCKN değildir ("a3f91234567890b2c", "id_12345678901"): sadece küçük harf hex
# ve alt çizgiye bitişikse atlanır. Diğer harflere bitişik olan maskelenir ("TC12345678901", "no12345678901").
# Önündeki nokta/virgül sadece rakamdan sonra geliyorsa ondalıktır ("3.12345678901"); "T.C.12345678901" maskelenir.
TCKN = re.compile(r"(?<![0-9a-f_])(?<!\d[.,])[1-9]\d{10}(?![.,]\d|[0-9a-f_])")
# "tc"/"tckn" önekiyle bitişik yazılan ("tc12345678901"): "c" hex olduğu için yukarıdaki kural atlar.
TCKN_PREFIXED = re.compile(r"(?<![a-z])tc(?:kn)?[:\s]*([1-9]\d{10})(?![.,]\d|[0-9a-f_])", re.IGNORECASE)

IBAN = re.compile(r"\bTR\s?\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.IGNORECASE)

_TLDS = "com|org|net|io|dev|me|app|co|info|biz|tr|edu|gov|ai|tech|site|xyz|online|page|eu|de|uk|us"
URL = re.compile(
    r"(?:https?://|www\.)\S+"
    rf"|(?<![\w@./-])(?:[a-z0-9-]+\.)+(?:{_TLDS})(?:\.(?:tr|uk))?(?:/[^\s,;)]*)?(?![\w.])"
)

_WHATSAPP = re.compile(r"(?:wa\.me|whatsapp\.com)/(?:send\?phone=)?\+?(\d{9,15})", re.IGNORECASE)
# Bağlantı içinde de telefon sayılan sayılar: Türkiye ön ekiyle yazılmış (05…, +90…, 0090…) veya telefon
# parametresinin değeri ("?phone=…", "&tel=…"). Ön eksiz sayılar (ilan no) bağlantının parçası olarak kalır.
_URL_PHONE_PREFIX = re.compile(r"^(?:\+90|0090|0)")
_URL_PHONE_PARAM = re.compile(r"(?:phone|tel|mobile|gsm|telefon|cep)=$", re.IGNORECASE)

# Alan adı gibi görünen teknoloji adları (küçük harfle yazılınca da bağlantı sayılmasın).
TECH_NAMES = {"socket.io", "asp.net", "ado.net", "vb.net"}

_DATE = r"\d{1,2}[./-]\d{1,2}[./-](?:19[5-9]\d|200\d|201[0-2])"
_DATE_WORDS = (
    r"\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık"
    r"|January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:19[5-9]\d|20[01]\d)"
)
BIRTH_LABELED = re.compile(
    r"\b(?:doğum\s*(?:yeri\s*(?:ve|/)\s*)?tarihi|d\.\s*t\.|date\s+of\s+birth|birth\s*date|d\.o\.b\.?|dob|born(?:\s+on)?)"
    r"(?![\w])\s*[:\-–]?\s*[^\n·|•;]*",
    re.IGNORECASE,
)
FULL_DATE = re.compile(rf"(?<!\d)(?:{_DATE}|{_DATE_WORDS})(?!\d)", re.IGNORECASE)

ADDRESS_LABELED = re.compile(r"(?:^|(?<=\s))(?:adres|ev adresi|address)\s*:\s*[^\n]+", re.IGNORECASE | re.MULTILINE)
# Adres parçası işaretleri: mahalle, sokak, cadde, bulvar, kapı/daire no, apartman, posta kodu + il/ilçe.
ADDRESS_HINT = re.compile(
    r"\b(?:Mah\.|Mh\.|Sok\.|Sk\.|Cad\.|Cd\.|Blv\.|Apt\.|St\.|Ave\.|Rd\.)"
    r"|\b(?:Mahallesi|Sokağı|Sokak|Caddesi|Bulvarı|Apartmanı|Street|Avenue|Road)\b",
    re.IGNORECASE,
)
# "No: 4", "Kat: 2", "D: 5" bilerek ipucu değil: tek başına adres değildir ("No: 1 öncelik"); mahalle/sokak gibi
# güçlü bir ipucuyla aynı alandaysa alan zaten bütünüyle maskelenir.
POSTAL_CODE = re.compile(r"(?<!\d)\d{5}(?!\d)\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+")
# İpucu tek başına yetmez ("Worked at Acme Street Labs"): aynı satırda bir sayı, il adı veya "ilçe/il" de olmalı.
_PROVINCES = (
    "Adana Adıyaman Afyonkarahisar Ağrı Aksaray Amasya Ankara Antalya Ardahan Artvin Aydın Balıkesir Bartın Batman "
    "Bayburt Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli Diyarbakır Düzce Edirne Elazığ "
    "Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane Hakkari Hatay Iğdır Isparta İstanbul İzmir Kahramanmaraş "
    "Karabük Karaman Kars Kastamonu Kayseri Kilis Kırıkkale Kırklareli Kırşehir Kocaeli Konya Kütahya Malatya Manisa "
    "Mardin Mersin Muğla Muş Nevşehir Niğde Ordu Osmaniye Rize Sakarya Samsun Şanlıurfa Siirt Sinop Sivas Şırnak "
    "Tekirdağ Tokat Trabzon Tunceli Uşak Van Yalova Yozgat Zonguldak"
).split()
ADDRESS_ANCHOR = re.compile(r"\d|[A-ZÇĞİÖŞÜa-zçğıöşü]\s*/\s*[A-ZÇĞİÖŞÜ]|\b(?:" + "|".join(_PROVINCES) + r")\b")
# Adres alanı kısadır; ipucu içeren uzun düz yazı satırı adres sayılmaz.
_ADDRESS_MAX_LEN = 80

# Bir satırı alanlara bölen ayraçlar (iletişim satırı: "ad@x.com · 0532 ... · İzmir").
FIELD_SEPARATORS = re.compile(r"\s*(?:·|•|\||;|\t| {3,})\s*")


def find_structured(text: str) -> list[Span]:
    """Yapısı belli verilerin yerleri. Çakışanlar `pii.mask` içinde birleştirilir."""
    spans: list[Span] = []
    spans += [Span(m.start(), m.end(), Kind.EMAIL) for m in EMAIL.finditer(text)]
    spans += [Span(m.start(), m.end(), Kind.IBAN) for m in IBAN.finditer(text)]
    urls = [m for m in URL.finditer(text) if m.group().lower() not in TECH_NAMES]
    spans += [Span(m.start(), m.end(), Kind.URL) for m in urls]
    # Bağlantı içindeki sayı (ilan no: linkedin.com/jobs/view/4438695357) telefon/TCKN değildir; ilan maskelemesi
    # bağlantıyı bıraktığı için bu sayı ayrıca maskelenmesin. Telefon biçimli olanlar (WhatsApp, 05…, ?phone=…)
    # ise telefondur.
    in_url = [(m.start(), m.end()) for m in urls if not _WHATSAPP.search(m.group())]
    for m in urls:
        if w := _WHATSAPP.search(m.group()):
            spans.append(Span(m.start() + w.start(1), m.start() + w.end(1), Kind.PHONE))

    def outside_url(m: re.Match[str]) -> bool:
        return not any(s <= m.start() and m.end() <= e for s, e in in_url)

    def phone_in_url(m: re.Match[str]) -> bool:
        return bool(
            _URL_PHONE_PREFIX.match(m.group()) or _URL_PHONE_PARAM.search(text, max(0, m.start() - 10), m.start())
        )

    for m in PHONE.finditer(text):
        if sum(c.isdigit() for c in m.group()) >= _PHONE_MIN_DIGITS and (outside_url(m) or phone_in_url(m)):
            spans.append(Span(m.start(), m.end(), Kind.PHONE))
    spans += [Span(m.start(), m.end(), Kind.TCKN) for m in TCKN.finditer(text) if outside_url(m)]
    spans += [Span(m.start(1), m.end(1), Kind.TCKN) for m in TCKN_PREFIXED.finditer(text) if outside_url(m)]
    spans += [
        Span(m.start(), m.start() + len(m.group().rstrip()), Kind.BIRTH_DATE) for m in BIRTH_LABELED.finditer(text)
    ]
    spans += [Span(m.start(), m.end(), Kind.BIRTH_DATE) for m in FULL_DATE.finditer(text)]
    spans += [Span(m.start(), m.end(), Kind.ADDRESS) for m in ADDRESS_LABELED.finditer(text)]
    spans += _address_fields(text)
    return spans


def _address_fields(text: str) -> list[Span]:
    """Adres işareti içeren kısa alanlar (satırın ayraçlarla bölünmüş parçası) tümüyle adres sayılır."""
    spans: list[Span] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        anchored = ADDRESS_ANCHOR.search(line) is not None
        pos = 0
        for part in FIELD_SEPARATORS.split(line.rstrip("\n")):
            start = line.find(part, pos)
            if start < 0 or not part.strip():
                continue
            pos = start + len(part)
            hinted = ADDRESS_HINT.search(part) and anchored and len(part.strip()) <= _ADDRESS_MAX_LEN
            if hinted or POSTAL_CODE.search(part):
                spans.append(Span(offset + start, offset + start + len(part), Kind.ADDRESS))
        offset += len(line)
    return spans
