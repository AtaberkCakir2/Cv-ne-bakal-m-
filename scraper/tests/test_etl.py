"""T-033 normalizasyonu: pozisyon eşleme, yetkinlik etiketleme ve benzer ilan tespiti (veritabanı gerekmez)."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from collector.taxonomy_rows import load_roles, load_skills
from etl.dedup import DedupItem, near_duplicates
from etl.pipeline import mask_posting_once
from etl.roles import RoleMatcher
from etl.skills import SkillTagger
from etl.text import fold, fold_phrase

EXAMPLE = Path(__file__).resolve().parents[2] / "contracts" / "examples" / "job_posting.example.json"

SKILLS = load_skills()
MATCHER = RoleMatcher(load_roles(), SKILLS)
TAGGER = SkillTagger(SKILLS)


def test_matchers_do_not_import_the_database_layer() -> None:
    # Burak'ın AI worker'ı (T-031) eşleyiciyi backend paketi ve SQLAlchemy olmadan kullanabilmeli (#20 incelemesi).
    code = (
        "import sys\n"
        "import collector.taxonomy_rows, etl.dedup, etl.roles, etl.skills, etl.text\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] in {'app', 'sqlalchemy', 'alembic'}))"
    )
    # cwd: pytest scraper/ dışından çalıştırılsa da collector ve etl bulunsun.
    scraper_dir = Path(__file__).resolve().parents[1]
    out = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=scraper_dir
    )
    assert out.stdout.strip() == "[]"


def test_fold_handles_turkish_dotted_capital() -> None:
    assert fold("İstanbul") == "istanbul"
    assert fold("IŞIK", "tr") == "ışık"
    assert fold("AI Engineer") == "ai engineer"  # İngilizcede I → i
    assert fold_phrase("Back-end_Geliştirici / API") == "back end geliştirici api"


TURKISH_TITLES = {
    "Back-end Geliştirici",
    "Back-end Geliştirici (Python)",
    "BACKEND YAZILIM GELİŞTİRİCİ",
    "Makine Öğrenmesi Mühendisi",
    "OYUN PROGRAMCISI",
    "API Geliştirici",
}


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        # Kabul kriterindeki örnek
        ("Back-end Geliştirici", "backend-developer"),
        ("Back-end Geliştirici (Python)", "backend-developer"),
        ("BACKEND YAZILIM GELİŞTİRİCİ", "backend-developer"),
        ("Senior Python Backend Engineer", "backend-developer"),
        ("Backend Software Engineer", "backend-developer"),
        ("Acme | Full Stack Software Engineer | Remote (US) | $150k", "full-stack-developer"),
        ("Senior Full Stack Engineer (F# / ASP.NET Core / ReactJS) – Remote (Europe)", "full-stack-developer"),
        ("Hevy | Lead React Native Engineer | Barcelona", "mobile-developer"),
        ("Senior Android Kotlin Engineer", "mobile-developer"),
        ("Senior Front-End Engineer (Next.js 16+)", "frontend-developer"),
        ("Aeolus | DevOps Engineer | San Francisco, CA (onsite)", "devops-engineer"),
        ("Senior Data Engineer (AI & LLM Solutions)", "data-engineer"),
        ("Big Data Engineer", "data-engineer"),
        ("Software Test Engineer", "qa-engineer"),
        ("Senior Application Security Engineer", "security-engineer"),
        ("Makine Öğrenmesi Mühendisi", "ml-engineer"),
        ("OYUN PROGRAMCISI", "game-developer"),  # Türkçe büyük I → ı
        ("API Geliştirici", "backend-developer"),  # Türkçe metinde Latin I
        ("Piramidal | Senior Backend Engineers, Frontend Engineers | NYC", "backend-developer"),  # ilk geçen
        ("DrSwarm | Founding Engineer (Full-Stack) | REMOTE", "full-stack-developer"),
        ("Lantern | Software Engineers (Python, Full-Stack) | NYC (Onsite)", "full-stack-developer"),
        ("Acme | Software Engineer (android) | NYC", "mobile-developer"),
        ("Engineer (Backend and Frontend)", "backend-developer"),
        ("Sr Product Engineer (Python & React)", "full-stack-developer"),
        ("Sr QA Automation- Selenium- Remote", "qa-engineer"),
        ("Senior .Net Developer - Remote (McKinney, TX, US)", "backend-developer"),
        ("TrakPro | Senior Rails Engineer | REMOTE", "backend-developer"),
        ("Angular Developer| Offshore", "frontend-developer"),
        # 18.11.2026 production başlıklarından eklenen eş anlamlılar
        ("Mobile Application Developer", "mobile-developer"),
        ("Senior Security Operations Engineer", "security-engineer"),
        ("Detection & Response Engineer", "security-engineer"),
        ("Security Architect", "security-engineer"),
        ("Sr. Staff Machine Learning Systems Engineer", "ml-engineer"),
        ("ML Platform Engineer, Evaluation Systems", "ml-engineer"),
        ("Data Platform Engineer (m/f/d)", "data-engineer"),
        ("Senior Decision Scientist", "data-scientist"),
        ("DevOps - Remote (Only Mexico)", "devops-engineer"),
    ],
)
def test_role_matching(title: str, expected: str) -> None:
    assert MATCHER.match(title, "tr" if title in TURKISH_TITLES else "en") == expected


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer",
        "Senior Software Engineer — Remote (US Only)",
        "Acme | Founding Engineer | NYC",
        "Hi!",
        "",
        "Manager, Site Reliability Engineering",  # yönetici ilanı: "site reliability" tek başına eş anlamlı değil
        "AVP Data Engineering – Business Insurance",
    ],
)
def test_generic_titles_have_no_role(title: str) -> None:
    assert MATCHER.match(title) is None


def tags(text: str, lang: str = "en") -> dict[str, str]:
    return {t.canonical_name: t.importance for t in TAGGER.tag(text, lang)}  # type: ignore[arg-type]


def test_contract_example_is_reproduced() -> None:
    # contracts/examples/job_posting.example.json: ETL bu ilandaki yetkinlikleri aynı önemle bulmalı. Fazlası olabilir
    # (örnekte yazılmamış "REST servisleri" → REST API).
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    expected = {s["skill"]: s["importance"] for s in example["skills"]}
    found = tags(example["description_clean"], example["language"])
    assert {k: found.get(k) for k in expected} == expected
    assert MATCHER.match(example["title_raw"], example["language"]) == example["role_slug"]


def test_word_boundaries_and_punctuated_names() -> None:
    found = tags("We use JavaScript, C++, C# and .NET. Node.js experience; Java is not used.")
    assert {"JavaScript", "C++", "C#", ".NET", "Node.js", "Java"} <= found.keys()
    assert "Java" in tags("Strong Java.")  # cümle sonundaki nokta
    assert "Java" not in tags("JavaScript only")


def test_case_sensitive_names() -> None:
    assert "SOLID" not in tags("You have a solid understanding of APIs.")
    assert "SOLID" in tags("Knowledge of SOLID principles.")
    assert "Go" not in tags("You will go above and beyond.")
    assert "Go" in tags("Services are written in Go and golang tooling.")


@pytest.mark.parametrize(
    ("text", "kept", "dropped"),
    [
        ("Experience with Objective-C and Swift.", "Objective-C", "C"),
        ("We build on Ruby on Rails.", "Ruby on Rails", "Ruby"),
        ("Pipelines run on Azure DevOps.", "Azure DevOps", "DevOps"),
    ],
)
def test_overlapping_names_keep_the_longest(text: str, kept: str, dropped: str) -> None:
    # CV tarafıyla aynı kural (extraction.taxonomy.Matcher): uzun ad içindeki kısa ad ayrı yetkinlik sayılmaz.
    found = tags(text)
    assert kept in found
    assert dropped not in found
    assert "Ruby" in tags("Ruby on Rails and plain Ruby scripts.")  # ayrıca yazılmışsa yine bulunur


def test_synonyms_map_to_canonical() -> None:
    assert "JavaScript" in tags("Modern JS and ECMAScript")
    assert "PostgreSQL" in tags("postgres, psql")


def test_preferred_section_and_inline() -> None:
    text = (
        "Requirements:\n\n- Python\n- PostgreSQL\n\nNice to have:\n\n- Kubernetes\n- Terraform\n\n"
        "Benefits:\n\n- Remote work\n\nExperience with Redis is a plus."
    )
    assert tags(text) == {
        "Python": "required",
        "PostgreSQL": "required",
        "Kubernetes": "preferred",
        "Terraform": "preferred",
        "Redis": "preferred",
    }


def test_required_wins_over_preferred() -> None:
    assert tags("Docker is a plus.\n\nYou must know Docker and Python.")["Docker"] == "required"


def test_turkish_text_with_latin_capital_i() -> None:
    assert "FastAPI" in tags("Python ve FastAPI ile servis geliştireceksin.", "tr")


def test_turkish_preferred_phrase() -> None:
    assert tags("React bilen geliştirici arıyoruz. TypeScript bilgisi tercih sebebidir.", "tr") == {
        "React": "required",
        "TypeScript": "preferred",
    }


BASE = " ".join(f"word{i}" for i in range(200))


def item(
    pid: int, text: str, company: str | None = "Acme", role: str | None = "backend-developer", day: int = 1
) -> DedupItem:
    return DedupItem(pid, company, role, date(2026, 10, day), text)


def test_near_duplicates_keep_newest() -> None:
    edited = BASE.replace("word100", "changed")
    drop = near_duplicates([item(1, BASE, day=1), item(2, edited, day=20), item(3, "tamamen farklı bir ilan")])
    assert drop == {1}


def test_near_duplicates_need_same_company_and_role() -> None:
    assert near_duplicates([item(1, BASE), item(2, BASE, company="Other")]) == set()
    assert near_duplicates([item(1, BASE), item(2, BASE, role="frontend-developer")]) == set()
    assert near_duplicates([item(1, BASE, company=None), item(2, BASE, company=None)]) == set()


def test_different_postings_are_kept() -> None:
    half = " ".join(f"other{i}" for i in range(100)) + " " + " ".join(f"word{i}" for i in range(100))
    assert near_duplicates([item(1, BASE), item(2, half, day=2)]) == set()


def test_masking_twice_does_not_nest_placeholders() -> None:
    # pii.mask_posting kendi etiketini yeniden maskeleyebiliyor ("name: X" → [AD SOYAD], sonra "SOYAD" yayılıyor);
    # normalize her gece çalıştığı için mask_posting_once eski etiketlere dokunmamalı.
    text = "About Acme\n\nWe build the database of the same name: Acme\n\nContact Ayşe Kaya at hr@acme.example"
    once = mask_posting_once(text, "en")
    assert "Ayşe" not in once and "[E-POSTA]" in once
    assert mask_posting_once(once, "en") == once
    assert "[AD [AD SOYAD]]" not in mask_posting_once(mask_posting_once(once, "en"), "en")
