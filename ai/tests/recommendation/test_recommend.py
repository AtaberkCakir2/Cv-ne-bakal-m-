"""Kaynak önerisi (T-043). Sahte kaynak ve sahte Ollama yanıtıyla; veritabanı testi TEST_DATABASE_URL ile."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from extraction.llm import LlmError
from matching import Missing
from recommendation import Resource, load_candidates, percent_suffix, rank_key, recommend, stat_sentence

REPO = Path(__file__).resolve().parents[3]


def res(
    rid: int, skill: str, *, lang: str = "en", level: str = "beginner", free: bool = True, dur: int | None = 60
) -> Resource:
    return Resource(rid, skill, f"Kaynak {rid}", f"https://example.com/{rid}", "youtube", lang, level, dur, free)  # type: ignore[arg-type]


MISSING = [Missing("Docker", 0.75, 1, 1.2), Missing("PostgreSQL", 0.62, 2, 1.0), Missing("Kafka", 0.10, 3, 0.4)]
CANDIDATES = {
    "Docker": [
        res(1, "Docker", level="advanced"),
        res(2, "Docker", lang="tr"),
        res(3, "Docker", free=False),
        res(4, "Docker", dur=30),
        res(5, "Docker", lang="tr", level="intermediate"),
    ],
    "PostgreSQL": [res(10, "PostgreSQL"), res(11, "PostgreSQL", lang="tr", dur=None)],
}


def llm(picks: Any) -> Any:
    calls: list[dict[str, Any]] = []

    def send(body: dict[str, Any]) -> dict[str, Any]:
        calls.append(body)
        return {"message": {"content": json.dumps({"picks": picks})}}

    send.calls = calls  # type: ignore[attr-defined]
    return send


def run(transport: Any = None, **kw: Any) -> Any:
    return recommend(
        MISSING, CANDIDATES, role_name="Backend Developer", postings_analyzed=150, transport=transport, **kw
    )


def test_rule_ranking_prefers_turkish_beginner_free_short() -> None:
    assert [r.resource_id for r in sorted(CANDIDATES["Docker"], key=rank_key)] == [2, 5, 4, 3, 1]


def test_stat_sentence_comes_from_numbers_not_llm() -> None:
    assert (
        stat_sentence(MISSING[0], "Backend Developer", 150)
        == "İncelenen 150 Backend Developer ilanının %75'i Docker istiyor."
    )
    assert stat_sentence(MISSING[0], "Backend Developer", 0) == "Backend Developer ilanlarının %75'i Docker istiyor."


@pytest.mark.parametrize(
    ("n", "suffix"),
    [(75, "i"), (62, "si"), (40, "ı"), (33, "ü"), (100, "ü"), (50, "si"), (10, "u"), (6, "sı"), (9, "u"), (0, "ı")],
)
def test_percent_suffix_follows_turkish_vowel_harmony(n: int, suffix: str) -> None:
    assert percent_suffix(n) == suffix


def test_llm_picks_only_from_candidates_and_writes_reason() -> None:
    t = llm(
        [
            {"skill": "Docker", "resource_id": 4, "reason": "Kısa ve uygulamalı, temelden başlıyorsun"},
            {"skill": "Docker", "resource_id": 999, "reason": "Uydurma kaynak."},  # listede yok
            # Ad uyuşmuyor ama numara Docker'ın adayı: yetkinlik numaradan bulunur.
            {"skill": "PostgreSQL", "resource_id": 2, "reason": "Başka yetkinliğin kaynağı."},
        ]
    )
    rec = run(t)
    docker = rec.picks["Docker"]
    assert [p.resource.resource_id for p in docker] == [4, 2, 5]  # LLM'in seçimleri önce, sonra kurallı sıra
    assert docker[0].by == "llm" and docker[0].reason.endswith("Kısa ve uygulamalı, temelden başlıyorsun.")
    assert docker[0].reason.startswith("İncelenen 150 Backend Developer ilanının %75'i Docker istiyor.")
    # id 2 Docker'a ait: yetkinlik LLM'in yazdığı addan değil numaradan bulunur.
    assert docker[1].by == "llm"
    assert rec.rejected == 1
    ids = {r.resource_id for rs in CANDIDATES.values() for r in rs}
    assert {p.resource.resource_id for ps in rec.picks.values() for p in ps} <= ids


def test_urls_and_fields_come_from_database_never_from_llm() -> None:
    t = llm([{"skill": "Docker", "resource_id": 1, "reason": "Şuradan izle: https://kotu.example/x"}])
    rec = run(t)
    first = rec.picks["Docker"][0]
    assert first.resource.resource_id == 1 and first.by == "rule"  # kaynak geçerli, gerekçe atıldı
    assert "kotu" not in json.dumps(rec.missing_skills(), ensure_ascii=False)
    assert rec.rejected == 1


@pytest.mark.parametrize(
    "reason",
    ["", "   ", "x" * 300, "Bkz. www.site.com", "docker.com'dan oku", "[tıkla](a)", "%90 başarı sağlar", 42, None],
)
def test_bad_reasons_fall_back_to_rule_reason(reason: Any) -> None:
    rec = run(llm([{"skill": "Docker", "resource_id": 2, "reason": reason}]))
    assert rec.picks["Docker"][0].by == "rule"
    assert "Türkçe, başlangıç seviyesinde, ücretsiz" in rec.picks["Docker"][0].reason


def test_duplicates_and_too_many_picks_are_dropped() -> None:
    picks = [{"skill": "Docker", "resource_id": i, "reason": "İyi bir kaynak."} for i in (1, 1, 2, 3, 4)]
    rec = run(llm(picks), per_skill=3)
    assert [p.resource.resource_id for p in rec.picks["Docker"]] == [1, 2, 3]
    assert rec.rejected == 2  # tekrar eden 1, fazla olan 4


@pytest.mark.parametrize("content", ["bozuk", '{"baska": []}', '{"picks": "yok"}'])
def test_broken_llm_response_falls_back_to_rules(content: str) -> None:
    rec = run(lambda body: {"message": {"content": content}})
    assert rec.llm_error == "INTERNAL"
    assert [p.resource.resource_id for p in rec.picks["Docker"]] == [2, 5, 4]
    assert all(p.by == "rule" for ps in rec.picks.values() for p in ps)


def test_llm_timeout_falls_back_to_rules() -> None:
    def timeout(body: dict[str, Any]) -> dict[str, Any]:
        raise LlmError("LLM_TIMEOUT")

    rec = run(timeout)
    assert rec.llm_error == "LLM_TIMEOUT" and len(rec.picks["Docker"]) == 3


def test_llm_sees_only_names_and_resources_and_limited_skills() -> None:
    t = llm([])
    recommend(
        MISSING,
        CANDIDATES,
        role_name="Backend Developer",
        postings_analyzed=150,
        present=["Python", "SQL"],
        transport=t,
        llm_skills=1,
    )
    body = t.calls[0]
    user = body["messages"][1]["content"]
    assert "Python, SQL" in user and "Eksik yetkinlik: Docker" in user
    assert "PostgreSQL" not in user  # llm_skills=1: sadece ilk yetkinlik
    assert "https://" not in user  # LLM'e link gösterilmez
    assert body["format"]["required"] == ["picks"] and body["stream"] is False


def test_no_llm_call_without_candidates_or_when_disabled() -> None:
    def boom(body: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("LLM çağrılmamalı")

    assert recommend(MISSING, {}, role_name="X", postings_analyzed=1, transport=boom).picks["Docker"] == []
    rec = run(boom, use_llm=False)
    assert rec.llm_error is None and len(rec.picks["Docker"]) == 3


def test_output_matches_contract() -> None:
    schema = json.loads((REPO / "contracts" / "analysis_result.schema.json").read_text(encoding="utf-8"))
    item_spec = schema["properties"]["missing_skills"]["items"]
    res_spec = item_spec["properties"]["resources"]["items"]
    out = run(llm([{"skill": "Docker", "resource_id": 2, "reason": "Türkçe ve temelden anlatıyor."}])).missing_skills()
    assert [m["skill"] for m in out] == ["Docker", "PostgreSQL", "Kafka"]
    assert out[2]["resources"] == []  # adayı yok
    for m in out:
        assert set(item_spec["required"]) <= m.keys() <= item_spec["properties"].keys()
        for r in m["resources"]:
            assert set(res_spec["required"]) <= r.keys() <= res_spec["properties"].keys()
            assert r["provider"] in res_spec["properties"]["provider"]["enum"]
            assert r["level"] in res_spec["properties"]["level"]["enum"]
            assert r["url"].startswith("https://example.com/")
    assert out[1]["resources"][0]["resource_id"] == 11 and "duration_min" not in out[1]["resources"][0]  # süre yok


def test_model_info_records_recommendation_prompt() -> None:
    rec = run(llm([]), model="test-model")
    assert rec.model == {"name": "test-model", "prompt_version": "v1"}


# --- veritabanı ---

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db() -> Iterator[Any]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL verilmedi")
    import psycopg

    with psycopg.connect(TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)) as conn:
        # Geçici tablolar (pg_temp arama yolunda önce gelir); gerçek tablolara dokunulmaz.
        conn.execute("CREATE TEMP TABLE skills (id int PRIMARY KEY, canonical_name text)")
        conn.execute(
            "CREATE TEMP TABLE resources (id int PRIMARY KEY, skill_id int, title text, url text, provider text,"
            " language text, level text, duration_min int, is_free bool, is_alive bool)"
        )
        conn.execute("INSERT INTO skills VALUES (1, 'Docker'), (2, 'Git'), (3, 'Kafka')")
        conn.execute(
            "INSERT INTO resources VALUES"
            " (10, 1, 'D1', 'https://e.com/1', 'youtube', 'tr', 'beginner', 45, true, true),"
            " (11, 1, 'D2', 'https://e.com/2', 'docs', 'en', 'advanced', NULL, true, true),"
            " (12, 1, 'Ölü', 'https://e.com/3', 'blog', 'en', 'beginner', 10, true, false),"
            " (20, 2, 'G1', 'https://e.com/4', 'udemy', 'en', 'intermediate', 300, false, true)"
        )
        yield conn


def test_candidates_are_read_from_resources(db: Any) -> None:
    got = load_candidates(db, ["Docker", "Kafka", "Docker"])
    assert list(got) == ["Docker"]  # Kafka'nın kaynağı yok, Git istenmedi
    assert [r.resource_id for r in got["Docker"]] == [10, 11]  # ölü link gelmez
    assert got["Docker"][1].duration_min is None and got["Docker"][0].language == "tr"
    assert load_candidates(db, []) == {}
