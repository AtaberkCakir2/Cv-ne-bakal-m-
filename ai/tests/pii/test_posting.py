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
    # Fark bilinçli: CV'de ilk satır addır, ilanda başlıktır.
    assert mask_text(POSTING_TR, "tr").startswith("[AD SOYAD]\n")


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
