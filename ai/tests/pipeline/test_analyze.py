"""AI zinciri (T-057). Bellekte üretilen sahte CV, sahte Ollama ve sahte veritabanı bağlantısıyla.

CV'deki e-posta, telefon ve ad uydurmadır; testler bunların LLM'e, sonuca ve istatistiklere gitmediğini denetler.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from extraction.llm import LlmError
from pipeline import AnalysisError, analyze_cv, guess_lang, prompt_version
from pipeline.analyze import BUDGET_SECONDS, EXTRACT_MAX_SECONDS, MIN_CALL_SECONDS
from tests.parsing.conftest import make_pdf

REPO = Path(__file__).resolve().parents[3]

EMAIL = "deneme.kisi@example.com"
PHONE = "0532 000 11 22"
NAME = "Zeynep Yılmazoğlu"

CV_LINES = [
    NAME,
    f"{EMAIL} · {PHONE}",
    "Bilgisayar Mühendisliği öğrencisi",
    "",
    "DENEYİM",
    "Stajyer Yazılım Geliştirici — Haziran 2025 – Eylül 2025",
    "Python ve FastAPI ile REST API uç noktaları geliştirdim ve testlerini yazdım.",
    "Veritabanı sorgularını hızlandırdım, ekip ile Git üzerinde çalıştım.",
    "",
    "YETENEKLER",
    "Python (ileri düzey), SQL, Git, Linux",
    "İngilizce: B2",
]


def cv_pdf() -> bytes:
    return make_pdf([[(56, 72 + i * 18, line, 11) for i, line in enumerate(CV_LINES) if line]])


class Rows:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class FakeConn:
    """roles / role_skill_stats / skills / resources sorgularına sahte satır döner."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str, params: tuple[Any, ...] = (), /) -> Rows:
        self.queries.append(query)
        q = " ".join(query.split())
        if q.startswith("SELECT slug, name FROM roles WHERE id"):
            return Rows([("backend-developer", "Backend Developer")] if params == (3,) else [])
        if q.startswith("SELECT name FROM roles WHERE slug"):
            return Rows([("Backend Developer",)])
        if "sum(total_postings)" in q:
            return Rows([(1000,)])
        if "FROM role_skill_stats r" in q:
            return Rows(
                [
                    ("Python", 120, 150, 0.8, 300, None),
                    ("Docker", 112, 150, 0.75, 400, None),
                    ("PostgreSQL", 93, 150, 0.62, 250, None),
                    ("Git", 90, 150, 0.6, 900, None),
                ]
            )
        if "FROM resources r" in q:
            return Rows(
                [
                    (11, "Docker", "Docker'a giriş", "https://example.com/d1", "youtube", "tr", "beginner", 60, True),
                    (
                        12,
                        "Docker",
                        "Docker belgeleri",
                        "https://example.com/d2",
                        "docs",
                        "en",
                        "intermediate",
                        None,
                        True,
                    ),
                    (
                        21,
                        "PostgreSQL",
                        "PostgreSQL temelleri",
                        "https://example.com/p1",
                        "docs",
                        "en",
                        "beginner",
                        90,
                        True,
                    ),
                ]
            )
        raise AssertionError(f"beklenmeyen sorgu: {q[:60]}")


class FakeOllama:
    def __init__(self, *, fail: bool = False) -> None:
        self.bodies: list[dict[str, Any]] = []
        self.timeouts: list[float] = []
        self.fail = fail

    def factory(self, timeout: float) -> Any:
        self.timeouts.append(timeout)

        def send(body: dict[str, Any]) -> dict[str, Any]:
            self.bodies.append(body)
            if self.fail:
                raise LlmError("LLM_TIMEOUT")
            content: dict[str, Any]
            if "skills" in body["format"]["required"]:
                content = {"skills": [{"skill": "FastAPI", "level": "intermediate", "years": None}]}
            else:
                content = {"picks": [{"skill": "Docker", "resource_id": 11, "reason": "Temelden ve Türkçe anlatıyor."}]}
            return {"message": {"content": json.dumps(content)}}

        return send


def run(**kw: Any) -> Any:
    ollama = kw.pop("ollama", None) or FakeOllama()
    conn = kw.pop("conn", None) or FakeConn()
    out = analyze_cv(
        kw.pop("pdf", None) or cv_pdf(), role_id=kw.pop("role_id", 3), conn=conn, transport_factory=ollama.factory, **kw
    )
    return out, ollama, conn


def test_result_follows_contract() -> None:
    out, _, _ = run()
    schema = json.loads((REPO / "contracts" / "analysis_result.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    assert set(out.result) <= set(props)
    assert out.result["target_role"] == {"slug": "backend-developer", "name": "Backend Developer"}
    assert out.result["postings_analyzed"] == 150 and 0 < out.result["match_score"] < 100
    present = {p["skill"] for p in out.result["present_skills"]}
    assert {"Python", "Git"} <= present
    missing = out.result["missing_skills"]
    assert [m["skill"] for m in missing][:2] == ["Docker", "PostgreSQL"]
    item = props["missing_skills"]["items"]
    for m in missing:
        assert set(item["required"]) <= m.keys()
        for r in m["resources"]:
            assert set(item["properties"]["resources"]["items"]["required"]) <= r.keys()
    docker = missing[0]["resources"]
    assert docker[0]["resource_id"] == 11 and docker[0]["reason"].startswith("İncelenen 150 Backend Developer")
    assert out.result["model"]["prompt_version"] == "skill_extraction:v2,recommendation:v1"


def test_personal_data_never_leaves_the_function() -> None:
    out, ollama, _ = run()
    sent = json.dumps(ollama.bodies, ensure_ascii=False)
    kept = json.dumps([out.result, out.stats], ensure_ascii=False, default=str)
    for secret in (EMAIL, PHONE, "Yılmazoğlu"):
        assert secret not in sent and secret not in kept
    assert "[E-POSTA]" in ollama.bodies[0]["messages"][1]["content"]
    # Öneri adımına CV metni gitmez.
    assert "Stajyer" not in ollama.bodies[1]["messages"][1]["content"]


def test_llm_down_still_gives_result_from_v1_and_rules() -> None:
    out, ollama, _ = run(ollama=FakeOllama(fail=True))
    assert out.stats["extraction_llm_error"] == "LLM_TIMEOUT"
    assert out.stats["recommendation_llm_error"] == "LLM_TIMEOUT"
    assert {"Python", "Git"} <= {p["skill"] for p in out.result["present_skills"]}
    assert all(r["reason"] for m in out.result["missing_skills"] for r in m["resources"])


def test_llm_timeouts_follow_the_remaining_budget() -> None:
    _, ollama, _ = run(budget_s=100)
    assert ollama.timeouts[0] <= 80  # 100 - MIN_LLM_SECONDS
    assert ollama.timeouts[1] < 100


def test_extraction_wait_is_capped_so_recommendation_gets_time() -> None:
    # #155 incelemesi: production PC'de çıkarım 145 sn bekleyip bütçeyi bitiriyordu, öneri LLM'i hiç çalışmıyordu.
    _, ollama, _ = run()
    assert ollama.timeouts[0] == pytest.approx(EXTRACT_MAX_SECONDS, abs=1) and EXTRACT_MAX_SECONDS == 90
    # Çıkarım sınırın tamamını kullansa bile öneriye en az 60 sn kalır.
    assert BUDGET_SECONDS - EXTRACT_MAX_SECONDS - 5 >= 60


def _late_factory(now: list[float], timeouts: list[float], answers: list[str], seconds: float) -> Any:
    """Çıkarım çağrısı `seconds` sürer ve sıradaki yanıtı döndürür; öneri çağrısı boş seçim."""

    def factory(timeout: float) -> Any:
        timeouts.append(timeout)

        def send(body: dict[str, Any]) -> dict[str, Any]:
            if "skills" in body["format"]["required"]:
                now[0] += seconds
                return {"message": {"content": answers.pop(0)}}
            return {"message": {"content": json.dumps({"picks": []})}}

        return send

    return factory


def test_retry_after_late_broken_answer_stays_within_extraction_cap() -> None:
    # #158 incelemesi: ilk yanıt 85. saniyede bozuk gelirse ikinci deneme 90 sn daha beklememeli.
    now, answers = [0.0], ["{bozuk", json.dumps({"skills": []})]
    timeouts: list[float] = []
    factory = _late_factory(now, timeouts, answers, 85.0)
    out = analyze_cv(cv_pdf(), role_id=3, conn=FakeConn(), transport_factory=factory, clock=lambda: now[0])
    assert len(answers) == 1  # 90 - 85 = 5 sn < MIN_CALL_SECONDS: ikinci deneme yapılmadı
    assert out.stats["extraction_llm_error"] == "LLM_TIMEOUT"
    assert out.stats["extract_s"] <= EXTRACT_MAX_SECONDS
    assert timeouts[1] >= 60  # öneriye süre kaldı


def test_retry_gets_only_the_time_left_until_extraction_cap() -> None:
    now, answers = [0.0], ["{bozuk", json.dumps({"skills": []})]
    timeouts: list[float] = []
    factory = _late_factory(now, timeouts, answers, 40.0)
    out = analyze_cv(cv_pdf(), role_id=3, conn=FakeConn(), transport_factory=factory, clock=lambda: now[0])
    assert timeouts[:2] == [EXTRACT_MAX_SECONDS, EXTRACT_MAX_SECONDS - 40]
    assert timeouts[1] >= MIN_CALL_SECONDS
    assert out.stats["extraction_llm_error"] is None


def test_no_llm_when_budget_is_spent() -> None:
    ticks = iter([0.0] + [1000.0] * 50)
    out, ollama, _ = run(clock=lambda: next(ticks))
    assert ollama.bodies == []
    assert out.stats["extraction_llm_error"] == "LLM_TIMEOUT"
    assert out.result["missing_skills"][0]["resources"]  # kurallı öneri yine var


@pytest.mark.parametrize(
    ("pdf", "code"),
    [
        (b"PDF degil", "PDF_UNREADABLE"),
        (b"%PDF-1.7\n" + b"0" * (6 * 1024 * 1024), "PDF_TOO_LARGE"),
        (make_pdf([[]], image_only=True), "NO_TEXT_FOUND"),
        (make_pdf([[(56, 72, "Kısa", 11)]]), "NO_TEXT_FOUND"),
    ],
    ids=["pdf-degil", "cok-buyuk", "taranmis", "metin-az"],  # bayt dizisi test adına girmesin
)
def test_pdf_errors_map_to_contract_codes(pdf: bytes, code: str) -> None:
    with pytest.raises(AnalysisError) as exc:
        run(pdf=pdf)
    assert exc.value.code == code and str(exc.value) == code  # mesajda CV parçası yok


def test_unknown_role_is_internal_error() -> None:
    with pytest.raises(AnalysisError) as exc:
        run(role_id=999)
    assert exc.value.code == "INTERNAL"


def test_stats_are_loggable_numbers_and_codes() -> None:
    out, _, _ = run()
    assert out.stats["lang"] == "tr" and out.stats["pages"] == 1
    assert out.stats["masked"].get("email") == 1 and out.stats["masked"].get("phone") == 1
    assert all(isinstance(v, (int, float, str, bool, dict, type(None))) for v in out.stats.values())


def test_guess_lang() -> None:
    assert guess_lang("Deneyim: Python ve SQL ile veri analizi yaptım. Eğitim: üniversitesi") == "tr"
    en = "Experience with Python and SQL for the data team. Education at the university of X, 3 years in industry."
    assert guess_lang(en) == "en"
    assert guess_lang("") == "tr"


def test_prompt_version_fits_column() -> None:
    v = prompt_version({"name": "m", "prompt_version": "v12"}, {"name": "m", "prompt_version": "v12"})
    assert v == "skill_extraction:v12,recommendation:v12" and len(v) <= 60
