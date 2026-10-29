"""İlan metni maskeleme (`mask_posting`): scraper/etl/pipeline.py'deki `mask_names` bağlantı noktası için."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

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
    # Unvandan sonra tam ad veya bilinen ilk ad varsa yine maskelenir.
    assert mask_posting("Hiring manager: Dr. Sarah Lee", "en") == "Hiring manager: Dr. [AD SOYAD]"
    assert mask_posting("Ekip lideri Dr. Ayşe ile görüşme", "tr") == "Ekip lideri Dr. [AD SOYAD] ile görüşme"


def test_numbers_inside_links_are_not_phone_or_tckn() -> None:
    text = "Apply: https://www.linkedin.com/jobs/view/4438695357"
    assert mask_posting("https://www.linkedin.com/jobs/view/4438695357", "en") == (
        "https://www.linkedin.com/jobs/view/4438695357"
    )
    assert "4438695357" in mask_posting(text, "en")
    # WhatsApp bağlantısındaki numara kişiye ulaştırır: maskelenir.
    assert "905320001234" not in mask_posting("WhatsApp: https://wa.me/905320001234", "tr")


def test_digits_inside_hashes_are_not_tckn() -> None:
    assert mask_posting("build a3f91234567890b2c, id_12345678901", "en") == "build a3f91234567890b2c, id_12345678901"
    assert mask_posting("TCKN: 12345678901", "tr") == "TCKN: [TCKN]"
