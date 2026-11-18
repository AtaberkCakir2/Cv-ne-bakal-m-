"""Eşleştirme (T-042). Sahte talep ve sahte vektörlerle; veritabanı testi TEST_DATABASE_URL ile."""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest

from matching import MIN_POSTINGS, CvSkill, Demand, idf, load_role_demand, match, parse_vector

REPO = Path(__file__).resolve().parents[3]
N = 1000  # tüm pozisyonlardaki ilan


def vec(*xs: float) -> list[float]:
    norm = math.sqrt(sum(x * x for x in xs))
    return [x / norm for x in xs]


def demand(skill: str, ratio: float, df: int, total: int = 200, vector: list[float] | None = None) -> Demand:
    return Demand(skill, round(ratio * total), total, ratio, df, vector)


BACKEND = [
    demand("Python", 0.80, df=300, vector=vec(1, 0, 0)),
    demand("Docker", 0.60, df=400, vector=vec(0, 1, 0)),
    demand("Git", 0.60, df=900, vector=vec(0, 0, 1)),  # her yerde istenen: düşük IDF
    demand("Express.js", 0.20, df=100, vector=vec(1, 1, 0)),
    demand("COBOL", 0.01, df=5, vector=vec(1, 0, 1)),  # uzun kuyruk: hesaba katılmaz
]


def fake_embed(table: dict[str, list[float]]) -> Any:
    def embed(texts: Sequence[str]) -> list[list[float]]:
        return [table[t] for t in texts]

    return embed


def test_idf_is_smoothed_and_positive() -> None:
    assert idf(N, N) == pytest.approx(1.0)
    assert idf(0, N) > idf(100, N) > idf(900, N) > 0


def test_score_is_weighted_coverage() -> None:
    weights = {d.skill: d.demand_ratio * idf(d.df, N) for d in BACKEND if d.demand_ratio >= 0.05}
    result = match([CvSkill("Python"), CvSkill("Git")], BACKEND, corpus_postings=N)
    expected = 100 * (weights["Python"] + weights["Git"]) / sum(weights.values())
    assert result.match_score == pytest.approx(expected, abs=0.05)
    assert 0 <= result.match_score <= 100
    assert match([CvSkill(d.skill) for d in BACKEND], BACKEND, corpus_postings=N).match_score == 100
    assert match([], BACKEND, corpus_postings=N).match_score == 0


def test_common_skill_counts_less_than_role_specific_one() -> None:
    # Docker ve Git aynı oranda isteniyor; Git her pozisyonda var, Docker daha özgü.
    docker = match([CvSkill("Docker")], BACKEND, corpus_postings=N).match_score
    git = match([CvSkill("Git")], BACKEND, corpus_postings=N).match_score
    assert docker > git


def test_missing_skills_are_sorted_by_demand_ratio() -> None:
    result = match([CvSkill("Python")], BACKEND, corpus_postings=N)
    assert [m.skill for m in result.missing] == ["Docker", "Git", "Express.js"]  # eşit oranda özgü olan önce
    assert [m.priority for m in result.missing] == [1, 2, 3]
    assert "COBOL" not in {m.skill for m in result.missing}


def test_names_match_case_insensitively_but_only_verified() -> None:
    assert match([CvSkill("python")], BACKEND, corpus_postings=N).matched[0].demand == "Python"
    # Doğrulanmamış ad, adı tutsa bile sadece vektörle eşleşebilir; vektör yoksa eşleşmez.
    assert match([CvSkill("Python", verified=False)], BACKEND, corpus_postings=N).matched == []


def test_unverified_name_matches_semantically_above_threshold() -> None:
    near = vec(1, 1, 0.05)  # Express.js'e çok yakın
    far = vec(1, 0.3, 0.9)  # hiçbirine yeterince yakın değil
    embed = fake_embed({"Express": near, "Uzak": far})
    result = match([CvSkill("Express", False), CvSkill("Uzak", False)], BACKEND, corpus_postings=N, embed=embed)
    assert [(m.demand, m.by) for m in result.matched] == [("Express.js", "Express")]
    assert result.matched[0].similarity == pytest.approx(0.9988, abs=1e-3)
    assert "Express.js" not in {m.skill for m in result.missing}


def test_threshold_is_adjustable() -> None:
    embed = fake_embed({"Express": vec(1, 1, 0.5)})  # Express.js ile benzerlik ~0,94
    cv = [CvSkill("Express", False)]
    assert match(cv, BACKEND, corpus_postings=N, embed=embed).matched
    assert not match(cv, BACKEND, corpus_postings=N, embed=embed, threshold=0.97).matched
    with pytest.raises(ValueError):
        match(cv, BACKEND, corpus_postings=N, threshold=0)


def test_semantic_match_gives_partial_credit_and_exact_match_wins() -> None:
    embed = fake_embed({"Py": vec(1, 0, 0.3)})  # Python ile ~0,958
    partial = match([CvSkill("Py", False)], BACKEND, corpus_postings=N, embed=embed)
    exact = match([CvSkill("Python")], BACKEND, corpus_postings=N)
    assert 0 < partial.match_score < exact.match_score
    both = match([CvSkill("Python"), CvSkill("Py", False)], BACKEND, corpus_postings=N, embed=embed)
    assert both.match_score == exact.match_score
    assert [m.by for m in both.matched] == ["Python"]


def test_low_data_flag_follows_decision_23() -> None:
    small = [demand("Python", 0.5, df=10, total=MIN_POSTINGS - 1)]
    assert match([], small, corpus_postings=N).low_data
    assert not match([], BACKEND, corpus_postings=N).low_data
    empty = match([CvSkill("Python")], [], corpus_postings=0)
    assert (empty.match_score, empty.postings_analyzed, empty.low_data, empty.missing) == (0.0, 0, True, [])


def test_min_postings_matches_scraper() -> None:
    stats = (REPO / "scraper" / "etl" / "stats.py").read_text(encoding="utf-8")
    found = re.search(r"^MIN_POSTINGS = (\d+)", stats, re.M)
    assert found and int(found.group(1)) == MIN_POSTINGS


def test_missing_skills_match_contract() -> None:
    schema = json.loads((REPO / "contracts" / "analysis_result.schema.json").read_text(encoding="utf-8"))
    spec = schema["properties"]["missing_skills"]["items"]
    for item in match([CvSkill("Python")], BACKEND, corpus_postings=N).missing_skills():
        assert set(spec["required"]) <= item.keys() <= spec["properties"].keys()
        assert 0 <= item["demand_ratio"] <= 1 and item["priority"] >= 1  # type: ignore[operator]


def test_parse_vector() -> None:
    assert parse_vector("[0.5,-0.25,1e-3]") == [0.5, -0.25, 0.001]


# --- veritabanı ---

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db() -> Iterator[Any]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL verilmedi")
    import psycopg

    with psycopg.connect(TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # Geçici tablolar (pg_temp arama yolunda önce gelir); gerçek tablolara ve view'a dokunulmaz.
        conn.execute("CREATE TEMP TABLE roles (id int PRIMARY KEY, slug text, name text)")
        conn.execute("CREATE TEMP TABLE skills (id int PRIMARY KEY, canonical_name text, embedding vector(3))")
        conn.execute(
            "CREATE TEMP TABLE role_skill_stats (role_id int, skill_id int, posting_count int,"
            " total_postings int, demand_ratio numeric(5,4))"
        )
        conn.execute(
            "INSERT INTO roles VALUES (1, 'backend', 'Backend'), (2, 'frontend', 'Frontend'), (3, 'bos', 'Boş')"
        )
        conn.execute("INSERT INTO skills VALUES (1, 'Python', '[1,0,0]'), (2, 'React', NULL), (3, 'Git', '[0,0,1]')")
        conn.execute(
            "INSERT INTO role_skill_stats VALUES (1, 1, 80, 100, 0.8), (1, 3, 50, 100, 0.5),"
            " (2, 2, 30, 40, 0.75), (2, 3, 20, 40, 0.5)"
        )
        yield conn


def test_role_demand_is_read_from_stats(db: Any) -> None:
    role = load_role_demand(db, "backend")
    assert (role.name, role.corpus_postings) == ("Backend", 140)
    assert [(d.skill, d.demand_ratio, d.df) for d in role.demands] == [("Python", 0.8, 80), ("Git", 0.5, 70)]
    assert role.demands[0].vector == [1.0, 0.0, 0.0]
    assert load_role_demand(db, "frontend").demands[0].vector is None
    assert load_role_demand(db, "bos").demands == []
    with pytest.raises(LookupError):
        load_role_demand(db, "yok")
