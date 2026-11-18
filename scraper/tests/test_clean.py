"""Temizleme ve kişisel veri maskeleme. Tüm örnekler uydurmadır."""

import pytest

from collector.clean import (
    EMAIL_MASK,
    PHONE_MASK,
    PROFILE_MASK,
    clean_description,
    content_hash,
    detect_language,
    html_to_text,
    mask_pii,
)


def test_html_to_text_keeps_structure() -> None:
    raw = "Acme | Backend Engineer<p>We use <b>Python</b> &amp; Go.<ul><li>FastAPI</li><li>PostgreSQL</li></ul>"
    assert html_to_text(raw) == "Acme | Backend Engineer\nWe use Python & Go.\n- FastAPI\n- PostgreSQL"


def test_html_entities_in_links_are_decoded() -> None:
    raw = '<a href="https:&#x2F;&#x2F;example.com&#x2F;jobs">https:&#x2F;&#x2F;example.com&#x2F;jobs</a>'
    assert html_to_text(raw) == "https://example.com/jobs"


@pytest.mark.parametrize(
    "text",
    [
        "Apply: jane.doe@example.com",
        "Email jobs [at] example [dot] com",
        "mail me: hr (at) acme (dot) co (dot) uk",
    ],
)
def test_emails_are_masked(text: str) -> None:
    masked = mask_pii(text)
    assert EMAIL_MASK in masked
    assert "@" not in masked and "[at]" not in masked and "(at)" not in masked


@pytest.mark.parametrize("phone", ["+90 532 123 45 67", "+1 (415) 555-0100", "415-555-0100", "(415) 555 0100"])
def test_phones_are_masked(phone: str) -> None:
    assert mask_pii(f"Call {phone} today") == f"Call {PHONE_MASK} today"


@pytest.mark.parametrize(
    "text",
    ["Salary: $150,000 - $200,000", "150000-200000 USD", "Founded in 2026", "Python 3.12, 20+ engineers"],
)
def test_numbers_that_are_not_phones_stay(text: str) -> None:
    assert mask_pii(text) == text


@pytest.mark.parametrize(
    "link", ["https://www.linkedin.com/in/jane-doe", "linkedin.com/in/jane-doe", "tr.linkedin.com/in/jane-doe/"]
)
def test_personal_profile_links_are_masked_company_links_stay(link: str) -> None:
    text = f"Ping {link} or see https://acme.example/careers"
    assert mask_pii(text) == f"Ping {PROFILE_MASK} or see https://acme.example/careers"


def test_clean_description_combines_both() -> None:
    assert clean_description("<p>Reach us: a@b.co</p>") == f"Reach us: {EMAIL_MASK}"


def test_content_hash_ignores_case_and_whitespace() -> None:
    assert content_hash("Python  Developer\n") == content_hash("python developer")
    assert content_hash("Python Developer") != content_hash("Go Developer")


def test_escaped_html_is_unescaped_before_stripping() -> None:
    assert html_to_text("&lt;p&gt;React &amp;amp; Go&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Remote&lt;/li&gt;&lt;/ul&gt;") == (
        "React & Go\n\n- Remote"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("We are hiring a backend engineer with Python experience in the team.", "en"),
        ("Python ve FastAPI bilgisi olan, PostgreSQL deneyimi aranıyor; uzaktan çalışma için bir ekip arkadaşı.", "tr"),
        # İsveççe ve Portekizce: ö/ü/ç var ama Türkçe değil; İngilizce de değil → alınmaz.
        ("Vilka är vi? Vår vision är att vara den absolut bästa arbetsgivaren för en skicklig IT-konsult.", None),
        ("Buscamos uma pessoa Full Stack Developer, responsável por construir, testar e entregar soluções.", None),
        ("Wir suchen einen Entwickler für unser Team in Berlin und bieten flexible Arbeitszeiten.", None),
        # Gerçek HN ilanı biçimi: URL ve teknoloji listesi İngilizce oranını düşürür ama dil İngilizce.
        (
            "Middesk | Full-time | NYC / SF | Hybrid | middesk.com At Middesk, we're building the business identity "
            "infrastructure. Stack: Python, Go, TypeScript, Postgres, Kafka, AWS, Terraform, React, GraphQL.",
            "en",
        ),
        ("https://grnh.se/abc Hiring - Acme", None),
    ],
)
def test_detect_language(text: str, expected: str | None) -> None:
    assert detect_language(text) == expected
