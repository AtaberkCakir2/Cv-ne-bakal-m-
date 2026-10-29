from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

from parsing import extract_text
from pii import Kind, mask, mask_text

EVAL = Path(__file__).resolve().parents[2] / "eval" / "dataset"


# --- Kabul kriteri: telefon, e-posta, TCKN %100 -------------------------------------------------------------------


def _tckn(rng: random.Random) -> str:
    """Geçerli sağlama haneli rastgele TCKN (gerçek bir kişiye ait olması beklenmez)."""
    d = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    d10 = ((sum(d[0:9:2]) * 7) - sum(d[1:8:2])) % 10
    d11 = (sum(d) + d10) % 10
    return "".join(map(str, [*d, d10, d11]))


PHONE_FORMATS = [
    "0532 000 12 34",
    "05320001234",
    "+90 532 000 12 34",
    "+905320001234",
    "0090 532 000 12 34",
    "(0532) 000 12 34",
    "0 (532) 000-12-34",
    "532.000.12.34",
    "0212 000 45 67",
    "+90 (312) 000 45 67",
    "+44 20 7946 0958",
    "+1 (415) 555-0132",
]
EMAILS = ["ad.soyad@example.com", "a_b-c+cv@sub.example.co.uk", "ADSOYAD@EXAMPLE.ORG", "x1@example.com.tr"]
CONTEXTS = ["Telefon: {}", "{}", "İletişim · {} · İzmir", "Tel ({})", "{}, e-posta için yazın", "Phone: {}."]


@pytest.mark.parametrize("value", PHONE_FORMATS)
@pytest.mark.parametrize("context", CONTEXTS)
def test_every_phone_format_is_masked(value: str, context: str) -> None:
    masked = mask(context.format(value)).text
    assert not re.search(r"\d{3}", masked), masked
    assert "[TELEFON]" in masked or "[TCKN]" in masked


@pytest.mark.parametrize("value", EMAILS)
@pytest.mark.parametrize("context", CONTEXTS)
def test_every_email_is_masked(value: str, context: str) -> None:
    masked = mask(context.format(value)).text
    assert "@" not in masked and "[E-POSTA]" in masked


def test_tckn_is_always_masked() -> None:
    rng = random.Random(30)
    for _ in range(500):
        tckn = _tckn(rng)
        for context in ["T.C. Kimlik No: {}", "TCKN {}", "{}", "Kimlik: {} · Ankara"]:
            masked = mask(context.format(tckn)).text
            assert tckn not in masked and "[TCKN]" in masked, masked


# --- Diğer türler -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Doğum Tarihi: 01.02.2001", Kind.BIRTH_DATE),
        ("Doğum yeri ve tarihi: İzmir, 3 Mart 2000", Kind.BIRTH_DATE),
        ("Date of birth: 12/05/1999", Kind.BIRTH_DATE),
        ("D.T.: 14.07.1998", Kind.BIRTH_DATE),
        ("Lise mezuniyeti 21.06.2010", Kind.BIRTH_DATE),  # tam tarih, yıl ≤ 2012: fazla maskelemek tercih edilir
        ("Atatürk Mah. 123 Sok. No: 4 D: 5 Bornova", Kind.ADDRESS),
        ("Adres: Kızılay, Çankaya / Ankara", Kind.ADDRESS),
        ("35000 İzmir", Kind.ADDRESS),
        ("221B Baker Street, London", Kind.ADDRESS),
        ("IBAN: TR12 0006 1000 0000 1234 5678 90", Kind.IBAN),
        ("github.com/ornek-kullanici", Kind.URL),
        ("https://www.linkedin.com/in/ornek", Kind.URL),
        ("portfolyo.example.com", Kind.URL),
    ],
)
def test_other_kinds(text: str, kind: Kind) -> None:
    result = mask(text)
    assert result.counts.get(kind, 0) >= 1, result.text


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        ("ZEYNEP KILIÇ\nFrontend Geliştirici", ["ZEYNEP", "KILIÇ"]),
        ("Özgeçmiş\nCan Yıldırım\nVeri Bilimci", ["Can Yıldırım"]),
        ("Ad Soyad: Ece Karaca", ["Ece", "Karaca"]),
        ("Name: John Smith", ["John", "Smith"]),
        ("Referans: Prof. Dr. Ahmet Yılmaz — Bilgisayar Müh.", ["Ahmet", "Yılmaz"]),
        ("Projede ekip lideri Ayşe Kaya ile çalıştım.", ["Ayşe", "Kaya"]),
        ("MERT AYDOĞAN\nGeliştirici\nMert'in rolü API yazmaktı; Aydoğan soyadı.", ["Mert", "Aydoğan", "AYDOĞAN"]),
    ],
)
def test_names_are_masked(text: str, hidden: list[str]) -> None:
    masked = mask(text).text
    for word in hidden:
        assert word not in masked, masked
    assert "[AD SOYAD]" in masked


# --- Yetkinlik metni bozulmamalı (yanlış pozitifler) --------------------------------------------------------------

KEEP = [
    "Node.js, Vue.js, Next.js ve ASP.NET Core ile çalıştım; socket.io kullandım.",
    "Python (ileri düzey), Java 17, C# ve C++; .NET 8",
    "Rapor süresini %40 azalttık; 2.048 ilanın %75'i Docker istiyor.",
    "Staj: Temmuz 2025 – Eylül 2025 · 2019-2023 · 2022 – 2026",
    "Takım çalışması, test suite yazımı, roadmap hazırlama, No: 1 öncelik",
    "Lighthouse puanı 71'den 94'e çıktı; 1.200+ aylık kullanıcı; 30+ servis",
    "Spring Boot, Google Cloud, Apache Kafka, Power BI, Visual Studio Code",
]


@pytest.mark.parametrize("text", KEEP)
def test_skill_text_is_not_masked(text: str) -> None:
    result = mask(text)
    assert result.text == text, (result.text, result.counts)


def test_name_does_not_swallow_next_line() -> None:
    # PDF'ten çıkan metinde ad ve unvan ayrı satırlarda; unvan ada katılmamalı.
    masked = mask("Can Yıldırım\nVeri Bilimci · 3 yıl").text
    assert masked == "[AD SOYAD]\nVeri Bilimci · 3 yıl"


def test_mask_text_matches_etl_hook_signature() -> None:
    # scraper/etl/pipeline.py: NameMasker = Callable[[str, Lang], str]
    assert mask_text("ad@example.com", "en") == "[E-POSTA]"


# --- Sentetik CV'ler uçtan uca: PDF → metin → maske --------------------------------------------------------------


def _specs() -> list[dict[str, object]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((EVAL / "cv_specs").glob("syn-*.json"))]


@pytest.mark.parametrize("spec", [s for s in _specs() if not s["scanned"]], ids=lambda s: str(s["cv_id"]))
def test_synthetic_cv_has_no_personal_data_after_masking(spec: dict[str, object]) -> None:
    pdf = EVAL / "synthetic" / f"{spec['cv_id']}.pdf"
    text = extract_text(pdf.read_bytes()).text
    masked = mask(text, str(spec["language"])).text  # type: ignore[arg-type]

    header = spec["header"]
    assert isinstance(header, dict)
    for word in str(header["name"]).split():
        assert word not in masked, f"ad kaldı: {word}"
    for item in header["contact"]:
        if "@" in item or re.search(r"\d{3}", item) or ".example." in item:
            assert item not in masked, f"iletişim kaldı: {item}"
    assert not re.search(r"[\w.+-]+@[\w-]+\.", masked)
    # Yetkinlik bölümü yerinde kalmalı
    assert "Python" in masked or "Java" in masked or "React" in masked or "C#" in masked or "Linux" in masked
