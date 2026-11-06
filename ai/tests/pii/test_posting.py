"""İlan metni maskeleme (`mask_posting`): scraper/etl/pipeline.py'deki `mask_names` bağlantı noktası için."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import pytest

from pii import mask_posting, mask_text

POSTING_TR = """Kıdemli Backend Geliştirici
Python Django PostgreSQL
Ekibimize katılacak arkadaş arıyoruz. Başvurular için https://firma.com/kariyer sayfasını ziyaret edin.
Sorularınız için İK uzmanımız Ayşe Yılmaz'a ayse.yilmaz@firma.com veya 0532 000 12 34 üzerinden ulaşabilirsiniz.
Adres: Maslak Mah. Büyükdere Cad. No: 1, Sarıyer/İstanbul · Son başvuru: 15.11.2026"""


def test_title_line_is_kept_but_contact_person_is_masked() -> None:
    out = mask_posting(POSTING_TR, "tr")
    assert out.splitlines()[:2] == ["Kıdemli Backend Geliştirici", "Python Django PostgreSQL"]
    assert "Ayşe" not in out and "Yılmaz" not in out
    assert "[AD SOYAD]'a" in out
    assert "[E-POSTA]" in out and "[TELEFON]" in out


def test_application_link_address_and_dates_are_kept() -> None:
    out = mask_posting(POSTING_TR, "tr")
    assert "https://firma.com/kariyer" in out
    assert "Maslak Mah. Büyükdere Cad." in out
    assert "15.11.2026" in out


def test_cv_masking_still_uses_header_rule() -> None:
    # Fark bilinçli: CV'de ilk satırlardaki ad satırı maskelenir, ilanda başlık kuralı hiç çalışmaz.
    cv = "ZEYNEP KILIÇ\nBackend Geliştirici"  # büyük harfli ad sadece başlık kuralıyla bulunur
    assert mask_text(cv, "tr") == "[AD SOYAD]\nBackend Geliştirici"
    assert mask_posting(cv, "tr") == cv


def test_english_posting_with_labeled_and_honorific_names() -> None:
    text = "Senior Data Engineer\nWe use Spark and Airflow.\nContact: Mr. John Smith (+44 20 7946 0958)."
    out = mask_posting(text, "en")
    assert out.startswith("Senior Data Engineer\n")
    assert "John" not in out and "Smith" not in out
    assert "[TELEFON]" in out


def test_text_without_personal_data_is_unchanged() -> None:
    text = "Frontend Developer\nReact, TypeScript ve Next.js deneyimi; Socket.IO ile gerçek zamanlı uygulamalar."
    assert mask_posting(text, "tr") == text


def test_matches_scraper_name_masker_signature() -> None:
    # scraper/etl/pipeline.py: NameMasker = Callable[[str, Lang], str], Lang = Literal["tr", "en"]
    masker: Callable[[str, Literal["tr", "en"]], str] = mask_posting
    assert isinstance(masker("Kıdemli Geliştirici", "tr"), str)


def test_english_posting_with_turkish_name() -> None:
    assert mask_posting("Contact Ayşe Kaya at hr@acme.example", "en") == "Contact [AD SOYAD] at [E-POSTA]"


def test_company_name_starting_with_first_name_is_masked() -> None:
    # Bilinen sınırlılık: ilk adla başlayan kurum adı ("Deniz Bank") da ad sayılır. İlan için zararsız
    # (yetkinlik kaybı yok); fazla maskelemek kaçırmaktan güvenli.
    assert mask_posting("Deniz Bank projelerinde deneyim", "tr") == "[AD SOYAD] projelerinde deneyim"


# --- #43 incelemesi: tekrar maskeleme ve gerçek ilanlardaki yanlış pozitifler -----------------------------------


def test_masking_is_idempotent() -> None:
    # Etiketli alan ("name:") ve ad yayma etiketin kendisini yeniden maskelemesin ("[AD [AD SOYAD]]").
    text = (
        "About Acme\nContact: Ayşe Kaya\nTool of the same name: VictoriaMetrics\nİletişim: Mert Aydın, 0532 000 12 34"
    )
    once = mask_posting(text, "en")
    assert "[AD [AD SOYAD]]" not in once
    assert mask_posting(once, "en") == once
    assert mask_posting(mask_posting(POSTING_TR, "tr"), "tr") == mask_posting(POSTING_TR, "tr")


def test_cv_masking_is_idempotent() -> None:
    once = mask_text("Ad Soyad: Ayşe Kaya\nE-posta: ayse@example.com · İzmir\nReferans: Dr. Mert Aydın", "tr")
    assert mask_text(once, "tr") == once


def test_english_place_names_and_brands_are_not_names() -> None:
    text = "Offices in the Bay Area, Richards Bay and North Bay. Partner brands: Dr. Squatch, Dr. Martens."
    assert mask_posting(text, "en") == text
    assert mask_posting("Hiring manager: Dr. Sarah Lee", "en") == "Hiring manager: Dr. [AD SOYAD]"
    assert mask_posting("Ekip lideri Dr. Ayşe ile görüşme", "tr") == "Ekip lideri Dr. [AD SOYAD] ile görüşme"


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("Contact Mr. Johnson for details.", "en"),
        ("Ms. Yilmaz will review applications.", "en"),
        ("Mrs. Patel leads the team.", "en"),
        ("Supervisor: Prof. Smith", "en"),
        ("Led by Prof. Dr. Schroiff and Dr. Stafylas.", "en"),
        ("Başvurular Sayın Yılmaz'a iletilir.", "tr"),
    ],
)
def test_single_surname_after_title_is_masked(text: str, lang: Literal["tr", "en"]) -> None:
    # #44 incelemesi: unvandan sonra tek soyadı da gerçek kişidir; istisna sadece marka listesi.
    out = mask_posting(text, lang)
    for name in ("Johnson", "Yilmaz", "Patel", "Smith", "Schroiff", "Stafylas", "Yılmaz"):
        assert name not in out, out
    assert "[AD SOYAD]" in out


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("Contact Ms Nadja Hantschel today.", ["Nadja", "Hantschel"]),
        ("Contact Mr John Doe today.", ["John", "Doe"]),
        ("Mr. J. Smith leads the team.", ["Smith"]),
        ("Supervised by Prof. Dr. H. Meffert.", ["Meffert"]),
        ("Danışman: Dr.Ayhan Yıldırım", ["Ayhan", "Yıldırım"]),
        ("Prof.Dr.H.Meffert ile çalıştım", ["Meffert"]),
    ],
)
def test_undotted_titles_initials_and_missing_spaces_are_masked(text: str, names: list[str]) -> None:
    out = mask_posting(text, "en")
    assert "[AD SOYAD]" in out
    for name in names:
        assert name not in out, out
    # Baş harf de kişiyi tanıtır.
    assert "J." not in out and "H." not in out


@pytest.mark.parametrize(
    "text", ["Ms Excel ve Ms Office biliyorum", "Ms Word, Ms Sql, Ms. PowerPoint", "Mr. Clean", "Mr Clean"]
)
def test_microsoft_products_and_brands_after_title_are_kept(text: str) -> None:
    assert mask_posting(text, "tr") == text


def test_numbers_inside_links_are_not_phone_or_tckn() -> None:
    text = "Apply: https://www.linkedin.com/jobs/view/4438695357"
    assert mask_posting("https://www.linkedin.com/jobs/view/4438695357", "en") == (
        "https://www.linkedin.com/jobs/view/4438695357"
    )
    assert "4438695357" in mask_posting(text, "en")
    # WhatsApp bağlantısındaki numara kişiye ulaştırır: maskelenir.
    assert "905320001234" not in mask_posting("WhatsApp: https://wa.me/905320001234", "tr")


@pytest.mark.parametrize(
    "url",
    [
        "acme.com/contact?phone=05321234567",
        "https://acme.com/call/05321234567",
        "https://acme.com/c?tel=+905321234567",
        "https://acme.com/c?mobile=5321234567&x=1",
        "https://acme.com/form?contact=905321234567",
        "https://acme.com/form?a=1&whatsapp=%2B905321234567",
    ],
)
def test_phone_shaped_numbers_inside_links_are_masked(url: str) -> None:
    # #44 incelemesi: Türkiye ön ekli veya telefon parametresindeki numara bağlantı içinde de telefondur.
    out = mask_posting(f"Bize ulaşın: {url}", "tr")
    assert "1234567" not in out, out
    assert "[TELEFON]" in out


@pytest.mark.parametrize("param", ["tckn", "tc", "TC_No", "kimlik", "national_id"])
def test_tckn_parameter_inside_link_is_masked(param: str) -> None:
    out = mask_posting(f"Form: https://x.com/form?{param}=12345678901&a=1", "tr")
    assert "12345678901" not in out
    assert f"{param}=[TCKN]&a=1" in out


def test_other_numbers_inside_links_are_kept() -> None:
    url = "https://x.com/form?job=12345678901&id=905321234567"
    assert mask_posting(url, "tr") == url


def test_digits_inside_hashes_are_not_tckn() -> None:
    assert mask_posting("build a3f91234567890b2c, id_12345678901", "en") == "build a3f91234567890b2c, id_12345678901"
    assert mask_posting("commit 12345678901abc, abc12345678901", "en") == "commit 12345678901abc, abc12345678901"
    assert mask_posting("TCKN: 12345678901", "tr") == "TCKN: [TCKN]"


@pytest.mark.parametrize(
    "text",
    [
        "TC12345678901",
        "TCKN12345678901",
        "tc12345678901",
        "tckn:12345678901",
        "no12345678901",
        "12345678901TC",
        "T.C.12345678901",
        "T.C. 12345678901",
        "No.12345678901",
        "TCKN,12345678901",
        "kimlikde12345678901",
    ],
)
def test_tckn_attached_to_letters_is_masked(text: str) -> None:
    # #44 incelemesi: sadece hash karakterlerine (küçük harf hex, alt çizgi) bitişik 11 hane atlanır. CV ve ilan.
    assert "12345678901" not in mask_text(text, "tr")
    assert "12345678901" not in mask_posting(text, "tr")


@pytest.mark.parametrize("text", ["oran 3.12345678901", "oran 3,12345678901", "12345678901.5", "12345678901,5"])
def test_decimal_numbers_are_not_tckn(text: str) -> None:
    assert mask_posting(text, "tr") == text
