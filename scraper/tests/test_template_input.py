"""T-019 şablon girdisi: role_skill_stats satırlarından pozisyon × yetkinlik JSON'u (veritabanı gerekmez)."""

from decimal import Decimal

from collector.taxonomy_rows import RoleRow, SkillRow
from etl.template_input import Demand, build, tier

SKILLS = [
    SkillRow("Python", "python", "dil", ("python3", "py"), None),
    SkillRow("Django", "django", "framework", (), None),
    SkillRow("Docker", "docker", "devops", (), None),
    SkillRow("Go", "go", "dil", ("golang",), None, case_sensitive=True),
]
ROLES = [
    RoleRow("Backend Developer", "backend-developer", ("backend engineer", "backend geliştirici"), ""),
    RoleRow("Game Developer", "game-developer", ("oyun programcısı",), ""),
]


def demand(skill: str, count: int, total: int = 80) -> Demand:
    return Demand("backend-developer", skill, count, total, Decimal(count) / total)


def test_skills_sorted_by_demand_with_synonyms_and_tier() -> None:
    data = build([demand("docker", 20), demand("python", 60), demand("go", 4), demand("django", 20)], SKILLS, ROLES)
    backend = data["roles"][0]
    assert [s["slug"] for s in backend["skills"]] == ["python", "django", "docker", "go"]  # eşitlikte ada göre
    assert backend["skills"][0] == {
        "slug": "python",
        "canonical_name": "Python",
        "category": "dil",
        "synonyms": ["python3", "py"],
        "demand_ratio": 0.75,
        "posting_count": 60,
        "tier": "core",
    }
    assert [s["tier"] for s in backend["skills"]] == ["core", "common", "common", "rare"]
    assert backend["titles"] == ["backend engineer", "backend geliştirici"]
    assert (backend["total_postings"], backend["low_data"]) == (80, False)


def test_top_limit_and_role_without_postings() -> None:
    data = build([demand("python", 60), demand("docker", 20)], SKILLS, ROLES, top=1)
    assert [s["slug"] for s in data["roles"][0]["skills"]] == ["python"]
    game = data["roles"][1]
    assert (game["skills"], game["total_postings"], game["low_data"]) == ([], 0, True)


def test_low_data_and_unknown_skill_is_skipped() -> None:
    # Taksonomiden çıkarılmış ama istatistikte kalmış yetkinlik (view yenilenmeden önce) yazılmaz.
    data = build([demand("python", 10, total=20), demand("kotlin", 5, total=20)], SKILLS, ROLES)
    backend = data["roles"][0]
    assert backend["low_data"] is True
    assert [s["slug"] for s in backend["skills"]] == ["python"]


def test_tier_boundaries() -> None:
    assert (tier(0.30), tier(0.2999), tier(0.10), tier(0.0999)) == ("core", "common", "common", "rare")


def test_explains_it_is_not_an_answer_key() -> None:
    assert "cevap anahtarı DEĞİLDİR" in build([], SKILLS, ROLES)["_aciklama"]
