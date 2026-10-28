"""Taksonominin kendisi (CSV'ler) ve doğrulama kuralları. T-017 kabul kriterleri burada denetlenir."""

import json
from pathlib import Path

import pytest

from collector.taxonomy import RoleRow, SkillRow, export_json, load_roles, load_skills, validate

REPO = Path(__file__).resolve().parents[2]
PROVISIONAL = REPO / "ai" / "eval" / "dataset" / "skills_provisional.json"
REQUIRED_ROLES = {
    "backend-developer",
    "frontend-developer",
    "full-stack-developer",
    "mobile-developer",
    "data-scientist",
    "devops-engineer",
    "qa-engineer",
    "ml-engineer",
    "security-engineer",
    "game-developer",
}

SKILLS = load_skills()
ROLES = load_roles()


def test_taxonomy_is_consistent() -> None:
    assert validate(SKILLS, ROLES) == []


def test_acceptance_counts() -> None:
    assert len(SKILLS) >= 300
    assert REQUIRED_ROLES <= {r.slug for r in ROLES}


def test_every_category_is_used() -> None:
    assert {s.category for s in SKILLS} == {
        "dil",
        "framework",
        "veritabani",
        "bulut",
        "devops",
        "arac",
        "metodoloji",
        "soft",
    }


def test_synonym_examples_from_acceptance_criteria() -> None:
    js = next(s for s in SKILLS if s.slug == "javascript")
    assert {"js", "ecmascript"} <= set(js.synonyms)


@pytest.mark.skipif(not PROVISIONAL.exists(), reason="ai/eval geçici listesi yok")
def test_burak_provisional_skills_keep_name_slug_and_category() -> None:
    # Burak'ın etiketleri bu adlarla yazıldı; taksonomi onları bozmamalı.
    provisional = json.loads(PROVISIONAL.read_text(encoding="utf-8"))["skills"]
    by_slug = {s.slug: s for s in SKILLS}
    for p in provisional:
        skill = by_slug.get(p["slug"])
        assert skill is not None, p["slug"]
        assert (skill.canonical_name, skill.category) == (p["canonical_name"], p["category"]), p["slug"]


def test_contract_example_skills_exist() -> None:
    example = json.loads((REPO / "contracts" / "examples" / "job_posting.example.json").read_text(encoding="utf-8"))
    names = {s.canonical_name for s in SKILLS}
    assert {s["skill"] for s in example["skills"]} <= names
    assert example["role_slug"] in {r.slug for r in ROLES}


def skill(slug: str, name: str, *synonyms: str, category: str = "dil", case_sensitive: bool = False) -> SkillRow:
    return SkillRow(
        canonical_name=name,
        slug=slug,
        category=category,
        synonyms=synonyms,
        esco_uri=None,
        case_sensitive=case_sensitive,
    )


def test_common_word_names_are_case_sensitive() -> None:
    # Kapsam analizinde "solid understanding" 171 ilanda SOLID sayılıyordu.
    by_slug = {s.slug: s for s in SKILLS}
    assert all(by_slug[slug].case_sensitive for slug in ("solid", "go", "swift", "rust", "express", "spring-boot"))


ROLE = RoleRow(name="Backend Developer", slug="backend-developer", synonyms=("backend engineer",), description="")


@pytest.mark.parametrize(
    ("skills", "expected"),
    [
        ([skill("go", "Go"), skill("go", "Golang")], "skill slug tekrar ediyor: go"),
        ([skill("Go", "Go")], "skill slug biçimi hatalı: 'Go'"),
        ([skill("java", "Java", "js"), skill("javascript", "JavaScript", "js")], "eş anlamlı 'js' iki yetkinlikte"),
        ([skill("java", "Java", "javascript"), skill("javascript", "JavaScript")], "iki yetkinlikte"),
        ([skill("python", "Python", "Py")], "küçük harf olmalı"),
        ([skill("python", "Python", category="programlama")], "bilinmeyen kategori"),
        ([skill("express", "Express", "express", case_sensitive=True)], "harf duyarlı yetkinliğin eş anlamlısı"),
    ],
)
def test_validate_catches_mistakes(skills: list[SkillRow], expected: str) -> None:
    assert any(expected in e for e in validate(skills, [ROLE]))


def test_export_matches_provisional_format(tmp_path: Path) -> None:
    out = tmp_path / "taxonomy.json"
    go = next(s for s in SKILLS if s.slug == "go")
    export_json([*SKILLS[:2], go], out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == {"_aciklama", "version", "categories", "skills"}
    assert data["skills"][2]["case_sensitive"] is True
    assert "case_sensitive" not in data["skills"][0]
    assert data["skills"][0] == {
        "canonical_name": "Python",
        "slug": "python",
        "category": "dil",
        "synonyms": ["python3", "py"],
    }
