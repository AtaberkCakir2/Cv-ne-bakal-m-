"""Yetkinlik çıkarımı v1 (T-031). Gerçek taksonomi (scraper/taxonomy/skills.csv) ile; CV'ler sentetik."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from extraction import ExtractedSkill, extract_skills, to_present_skills
from extraction.taxonomy import DEFAULT_TAXONOMY

pytestmark = pytest.mark.skipif(not DEFAULT_TAXONOMY.is_file(), reason="scraper/taxonomy/skills.csv yok")

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "contracts" / "analysis_result.schema.json"
SYN_001 = Path(__file__).resolve().parents[2] / "eval" / "examples" / "synthetic" / "syn-001.md"


def _by_name(text: str, lang: str = "tr") -> dict[str, ExtractedSkill]:
    return {s.skill: s for s in extract_skills(text, lang)}  # type: ignore[arg-type]


# --- Eşleme -------------------------------------------------------------------------------------------------------


def test_word_boundaries_and_punctuated_names() -> None:
    found = _by_name("JavaScript, C++, C#, Node.js ve .NET ile çalıştım. Python.")
    assert {"JavaScript", "C++", "C#", "Node.js", "Python"} <= found.keys()
    assert "Java" not in found


def test_case_sensitive_names_and_synonyms() -> None:
    assert "Go" in _by_name("Backend servislerini Go ile yazdım.")
    assert "Go" not in _by_name("Projeyi canlıya go dedik; ekip go-live için hazırdı.")
    assert "Go" in _by_name("golang ile mikroservis")


def test_synonyms_map_to_canonical_name_and_longest_wins() -> None:
    found = _by_name("k8s, Postgres ve Spring Boot kullandım.")
    assert {"Kubernetes", "PostgreSQL", "Spring Boot"} <= found.keys()


def test_turkish_capitals_are_folded() -> None:
    assert "İngilizce" in _by_name("Yabancı Diller\nİNGİLİZCE (B2)")


# --- CV kuralları (etiketleme kılavuzu) -------------------------------------------------------------------------


def test_goal_sentences_are_skipped() -> None:
    found = _by_name(
        "REST servisleri yazmayı seviyorum; ileride Go ve Kafka öğrenmek istiyorum. Şu an Next.js öğreniyorum.\n"
        "I want to learn Rust. Docker ile servisleri paketledim."
    )
    assert "Docker" in found
    assert not {"Go", "Apache Kafka", "Next.js", "Rust"} & found.keys()


def test_course_lists_are_skipped_but_tools_in_parentheses_count() -> None:
    found = _by_name("Dersler: Kriptografi, İşletim Sistemleri, Web Programlama (PHP)\nProjede Python kullandım.")
    assert "Kriptografi" not in found
    assert {"PHP", "Python"} <= found.keys()


def test_category_heading_is_not_a_skill() -> None:
    found = _by_name("Yetenekler\nDevOps: Docker, Kubernetes, GitHub Actions\nİngilizce: B2")
    assert "DevOps" not in found
    assert {"Docker", "Kubernetes", "GitHub Actions", "İngilizce"} <= found.keys()


def test_spoken_language_needs_language_context() -> None:
    assert "Türkçe" not in _by_name("Türkçe metinlerde sınıflandırma modelleri geliştirdim.")
    assert "Türkçe" in _by_name("Diller\nTürkçe, İngilizce")
    assert _by_name("Türkçe — ana dil")["Türkçe"].level == "advanced"


# --- Seviye ve deneyim yılı -----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "skill", "level"),
    [
        ("Python (ileri düzey), Java (orta), SQL", "Python", "advanced"),
        ("Python (ileri düzey), Java (orta), SQL", "Java", "intermediate"),
        ("Python (ileri düzey), Java (orta), SQL", "SQL", "unknown"),
        ("Jest (temel), Cypress", "Jest", "beginner"),
        ("R — orta", "R", "intermediate"),
        ("İngilizce: B2", "İngilizce", "intermediate"),
        ("English: C1", "İngilizce", "advanced"),
        ("ileri düzey SQL bilgisi", "SQL", "advanced"),
        ("Docker (basic), Kubernetes (advanced)", "Kubernetes", "advanced"),
    ],
)
def test_level_hints(text: str, skill: str, level: str) -> None:
    assert _by_name(text)[skill].level == level


@pytest.mark.parametrize(
    ("text", "skill", "years"),
    [
        ("4 yıl Python deneyimi; Django ile API geliştirdim.", "Python", 4),
        ("4 yıl Python deneyimi; Django ile API geliştirdim.", "Django", None),
        ("TypeScript / JavaScript (4 yıl), Python (temel)", "JavaScript", 4),
        ("5 yıllık sistem yönetimi ve 2 yıllık DevOps deneyimi.", "DevOps", 2),
        ("3+ years of React experience", "React", 3),
        ("2022 – 2026 arasında Java ile çalıştım.", "Java", None),
    ],
)
def test_years_hints(text: str, skill: str, years: int | None) -> None:
    assert _by_name(text)[skill].years == years


def test_skills_section_raises_confidence() -> None:
    found = _by_name("Projelerde Redis kullandım.\nYetenekler\nPython (ileri), Docker\nPython ile otomasyon.")
    assert found["Redis"].confidence == 0.6
    assert found["Docker"].confidence == 0.75
    assert found["Python"].confidence == 0.95  # bölüm + 2 geçiş + seviye
    assert found["Python"].mentions == 2


# --- Uçtan uca ve sözleşme ------------------------------------------------------------------------------------------


def test_synthetic_cv_001() -> None:
    found = _by_name(SYN_001.read_text(encoding="utf-8"))
    assert "Kubernetes" not in found  # "İleride Kubernetes öğrenmeyi hedefliyorum."
    expected = {"Python", "FastAPI", "REST API", "PostgreSQL", "Docker", "GitHub Actions", "Java", "Spring Boot"}
    expected |= {"MySQL", "HTML", "CSS", "JavaScript", "SQL", "Git", "Linux", "Postman", "İngilizce"}
    assert expected <= found.keys()
    assert (found["Python"].level, found["Java"].level, found["İngilizce"].level) == (
        "advanced",
        "intermediate",
        "intermediate",
    )


def test_present_skills_follow_contract() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["present_skills"]["items"]
    items = to_present_skills(extract_skills("Yetenekler\nPython (ileri), Docker", "tr"))
    assert items
    for item in items:
        assert set(schema["required"]) <= item.keys() <= set(schema["properties"])
        assert item["level"] in schema["properties"]["level"]["enum"]
        assert 0 <= item["confidence"] <= 1 and item["verified"] is True


def test_text_without_skills_and_placeholders() -> None:
    assert extract_skills("[AD SOYAD]\n[E-POSTA] · [TELEFON]\nHakkımda\nKitap okumayı severim.", "tr") == []
