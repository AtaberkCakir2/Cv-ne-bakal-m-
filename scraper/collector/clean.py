"""HTML temizleme, kişisel veri maskeleme ve tekrar kayıt anahtarı.

İlan metnindeki e-posta, telefon ve kişisel profil linkleri veritabanına yazılmadan önce maskelenir
(scraper/kaynak-uygunluk.md, kural 6). Şirket adı ve şirket web sitesi kalır.
"""

import hashlib
import html
import re
from typing import Literal

Lang = Literal["tr", "en"]

EMAIL_MASK = "[e-posta]"
PHONE_MASK = "[telefon]"
PROFILE_MASK = "[profil]"

# </li> yok: her <li> zaten yeni satırla başlar, ikisi birden maddeler arasına boş satır koyar.
_BLOCK_TAGS = re.compile(r"<\s*(br|/p|p|/ul|/ol|/div|/h[1-6]|/tr)\b[^>]*>", re.IGNORECASE)
_LI_TAG = re.compile(r"<\s*li\b[^>]*>", re.IGNORECASE)
_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
# "jobs [at] acme [dot] com" gibi gizlenmiş e-postalar.
_EMAIL_OBFUSCATED = re.compile(
    r"[\w.+-]+\s*[\[(<{]\s*at\s*[\])>}]\s*[\w-]+(\s*[\[(<{]\s*dot\s*[\])>}]\s*[\w-]+)+", re.IGNORECASE
)
# Uluslararası (+90 532 123 45 67) ve ABD (415-555-0100) biçimleri. Maaş aralıkları (150000-200000) eşleşmez.
_PHONE = re.compile(
    r"(?<![\w+])(\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,4}){2,4}|\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b)"
)
# Şemalı veya şemasız ("linkedin.com/in/ad-soyad") yazılan kişisel profil linkleri.
_PROFILE = re.compile(r"(https?://)?([\w-]+\.)?(linkedin\.com/in|t\.me|wa\.me)/[^\s)\]]+", re.IGNORECASE)

# Sadece Türkçede olan harfler: ö/ü/ç İsveççe, Almanca ve Portekizcede de var, onlar sayılmaz.
_TURKISH_CHARS = re.compile(r"[ğışĞİŞ]")
_TURKISH_WORDS = re.compile(r"\b(ve|için|ile|deneyim|aranıyor|tecrübe|bilgisi|olan|bir|çalışma)\b", re.IGNORECASE)
_ENGLISH_WORDS = re.compile(r"\b(the|and|to|of|with|you|we|for|our|in|is|are|will|a)\b", re.IGNORECASE)
# Kaynaklarda görülen diğer diller: Portekizce, İspanyolca, İsveççe, Almanca, Fransızca. İngilizcede geçmeyen kelimeler.
_OTHER_WORDS = re.compile(
    r"\b(uma|para|com|você|não|nossa|nosso|somos|buscamos|och|att|är|för|vår|vi|söker"
    r"|und|wir|die|der|für|mit|sind|nous|vous|pour|avec|nos|est|une|y|con|nuestro|somos)\b",
    re.IGNORECASE,
)


def html_to_text(raw: str) -> str:
    """HTML'i satır yapısını koruyarak düz metne çevirir."""
    if "<" not in raw and "&lt;" in raw:
        raw = html.unescape(raw)  # bazı kaynaklar HTML'i kaçışlı gönderir (&lt;p&gt;)
    text = _LI_TAG.sub("\n- ", raw)
    text = _BLOCK_TAGS.sub("\n", text)
    text = _TAGS.sub("", text)
    text = html.unescape(text)
    lines = [_SPACES.sub(" ", line).strip() for line in text.splitlines()]
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def mask_pii(text: str) -> str:
    text = _PROFILE.sub(PROFILE_MASK, text)
    text = _EMAIL.sub(EMAIL_MASK, text)
    text = _EMAIL_OBFUSCATED.sub(EMAIL_MASK, text)
    return _PHONE.sub(PHONE_MASK, text)


def clean_description(raw_html: str) -> str:
    return mask_pii(html_to_text(raw_html))


def content_hash(text: str) -> str:
    """Aynı ilanın farklı kaynaklardan veya tekrar çekilmesini yakalar (job_postings.content_hash)."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_language(text: str) -> Lang | None:
    """tr, en veya None (başka dil). Yetkinlik çıkarımı sadece TR/EN işlediği için None olan ilan alınmaz."""
    sample = text[:3000]
    if len(_TURKISH_CHARS.findall(sample)) >= 5 and len(_TURKISH_WORDS.findall(sample)) >= 3:
        return "tr"
    # Oran yerine karşılaştırma: URL, teknoloji listesi ve maaş bilgisi İngilizce kelime oranını düşürür ama
    # başka dilin kelimesini artırmaz. Çok kısa, dili belirsiz metin (≤ 1 İngilizce kelime) de alınmaz.
    english = len(_ENGLISH_WORDS.findall(sample))
    if english >= 2 and english > len(_OTHER_WORDS.findall(sample)):
        return "en"
    return None
