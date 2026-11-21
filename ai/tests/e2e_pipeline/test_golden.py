"""Uçtan uca zincir golden testi (T-058): 10 sentetik CV, PDF → sözleşme biçiminde sonuç JSON'u.

- CV'ler `eval/dataset/synthetic/syn-004..013.pdf` (tamamen sentetik, karar #20). Pozisyon talebi ve kaynaklar sabit
  sahte veri (`roles.json`); veritabanı gerekmez.
- **Varsayılan (CI):** LLM yok sayılır (zaman aşımı), zincir v1 sözlük çıkarımı + kurallı öneriyle çalışır: sonuç
  belirleyicidir ve `golden/<cv_id>.json` ile birebir karşılaştırılır. Çıkarım, maskeleme, eşleştirme veya öneri
  kodundaki istenmeyen değişikliği yakalar.
- **Gerçek model (`CAREERAI_OLLAMA_TEST=1`, yerel Ollama):** prompt/model değişikliğinin regresyonunu yakalar: LLM'li
  sonuç da şemaya uymalı, golden'daki (v1) yetkinliklerin hepsini içermeli, LLM hatası olmamalı.
- Her sonuç `contracts/analysis_result.schema.json` ile doğrulanır; CV başlığındaki uydurma ad/e-posta/telefon sonuçta
  geçmemelidir.

Golden dosyalarını bilerek değiştirmek için (fark gözden geçirilip commit'lenir):
    CAREERAI_GOLDEN_UPDATE=1 pytest tests/e2e_pipeline
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from extraction.llm import LlmError
from extraction.taxonomy import DEFAULT_TAXONOMY
from pipeline import AnalysisError, analyze_cv
from pipeline import analyze as analyze_module

HERE = Path(__file__).resolve().parent
AI = HERE.parents[1]
REPO = AI.parent
DATASET = AI / "eval" / "dataset"
GOLDEN = HERE / "golden"
ROLES = json.loads((HERE / "roles.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((REPO / "contracts" / "analysis_result.schema.json").read_text(encoding="utf-8"))
REAL_LLM = os.environ.get("CAREERAI_OLLAMA_TEST") == "1"
UPDATE = os.environ.get("CAREERAI_GOLDEN_UPDATE") == "1"

CVS = [
    row
    for row in csv.DictReader((DATASET / "manifest.csv").open(encoding="utf-8"))
    if (DATASET / "synthetic" / f"{row['cv_id']}.pdf").is_file()
]
SLUGS = sorted(ROLES["roles"])

pytestmark = pytest.mark.skipif(not DEFAULT_TAXONOMY.is_file(), reason="scraper/taxonomy/skills.csv yok")


class Rows:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class FixtureConn:
    """roles.json'dan pozisyon talebi; talep edilen her yetkinliğe iki sabit sahte kaynak."""

    def execute(self, query: str, params: tuple[Any, ...] = (), /) -> Rows:
        q = " ".join(query.split())
        total = ROLES["total_postings"]
        if q.startswith("SELECT slug, name FROM roles WHERE id"):
            idx = params[0] - 1
            return Rows([(SLUGS[idx], ROLES["roles"][SLUGS[idx]][0])] if 0 <= idx < len(SLUGS) else [])
        if q.startswith("SELECT name FROM roles WHERE slug"):
            return Rows([(ROLES["roles"][params[0]][0],)])
        if "sum(total_postings)" in q:
            return Rows([(total * len(SLUGS),)])
        if "FROM role_skill_stats r" in q:
            demand = ROLES["roles"][params[0]][1]
            df = {s: sum(1 for _, d in ROLES["roles"].values() for name, _ in d if name == s) for s, _ in demand}
            return Rows([(s, round(r * total), total, r, df[s] * total // 2, None) for s, r in demand])
        if "FROM resources r" in q:
            rows: list[tuple[Any, ...]] = []
            for skill in params[0]:
                base = 1000 + 10 * sorted({s for _, d in ROLES["roles"].values() for s, _ in d}).index(skill)
                rows.append(
                    (
                        base,
                        skill,
                        f"{skill} temelleri",
                        f"https://example.com/{base}",
                        "docs",
                        "tr",
                        "beginner",
                        60,
                        True,
                    )
                )
                rows.append(
                    (
                        base + 1,
                        skill,
                        f"{skill} ileri",
                        f"https://example.com/{base + 1}",
                        "youtube",
                        "en",
                        "intermediate",
                        120,
                        True,
                    )
                )
            return Rows(rows)
        raise AssertionError(f"beklenmeyen sorgu: {q[:60]}")


def _no_llm(timeout: float) -> Any:
    def send(body: dict[str, Any]) -> dict[str, Any]:
        raise LlmError("LLM_TIMEOUT")

    return send


def run(cv_id: str, slug: str, *, real_llm: bool) -> dict[str, Any]:
    """Sonuç ya da {"error": kod}. Ad tespiti sadece kurallarla (NER kurulu olsun olmasın aynı sonuç)."""
    pdf = (DATASET / "synthetic" / f"{cv_id}.pdf").read_bytes()
    try:
        out = analyze_cv(
            pdf, role_id=SLUGS.index(slug) + 1, conn=FixtureConn(), transport_factory=None if real_llm else _no_llm
        )
    except AnalysisError as e:
        return {"error": e.code}
    return out.result


@pytest.fixture(autouse=True)
def rules_only_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(analyze_module, "_name_detector", lambda: None)


def contract(result: dict[str, Any]) -> dict[str, Any]:
    """İşçinin ekleyeceği alanlarla (kimlik, durum, zaman) sözleşmenin tam nesnesi."""
    return {
        "analysis_id": "00000000-0000-4000-8000-000000000000",
        "status": "done",
        "created_at": "2026-11-21T10:00:00Z",
        "completed_at": "2026-11-21T10:01:00Z",
        **result,
    }


def personal_strings(cv_id: str) -> list[str]:
    spec = json.loads((DATASET / "cv_specs" / f"{cv_id}.json").read_text(encoding="utf-8"))
    header = spec.get("header", {})
    strings = [header.get("name", "")] + [
        c for c in header.get("contact", []) if "@" in c or any(ch.isdigit() for ch in c)
    ]
    return [s for s in strings if s]


def snapshot(result: dict[str, Any]) -> dict[str, Any]:
    """Prompt sürümü karşılaştırmaya girmez (T-074 gibi bilerek yapılan prompt değişikliği golden'ı bozmasın)."""
    return {k: v for k, v in result.items() if k != "model"}


def test_there_are_ten_sample_cvs() -> None:
    assert len(CVS) == 10


@pytest.mark.parametrize("row", CVS, ids=[r["cv_id"] for r in CVS])
def test_pipeline_matches_golden(row: dict[str, str]) -> None:
    cv_id, slug = row["cv_id"], row["target_role"]
    result = run(cv_id, slug, real_llm=False)
    path = GOLDEN / f"{cv_id}.json"
    if UPDATE:
        GOLDEN.mkdir(exist_ok=True)
        path.write_text(
            json.dumps(snapshot(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert snapshot(result) == expected

    if row["scanned"] == "true":
        assert result == {"error": "NO_TEXT_FOUND"}  # OCR yedek akışı (T-029) gelince değişir
        return
    jsonschema.validate(contract(result), SCHEMA)
    assert result["model"]["prompt_version"].startswith("skill_extraction:v")
    text = json.dumps(result, ensure_ascii=False)
    for personal in personal_strings(cv_id):
        assert personal not in text


@pytest.mark.skipif(not REAL_LLM, reason="gerçek Ollama testi kapalı (CAREERAI_OLLAMA_TEST=1)")
@pytest.mark.parametrize("row", [r for r in CVS if r["scanned"] != "true"], ids=lambda r: r["cv_id"])
def test_real_llm_keeps_golden_skills(row: dict[str, str]) -> None:
    """Prompt/model değişikliği regresyonu: LLM, v1'in bulduğu yetkinliği kaybettirmemeli, hata vermemeli."""
    cv_id, slug = row["cv_id"], row["target_role"]
    expected = json.loads((GOLDEN / f"{cv_id}.json").read_text(encoding="utf-8"))
    result = run(cv_id, slug, real_llm=True)
    jsonschema.validate(contract(result), SCHEMA)
    found = {s["skill"] for s in result["present_skills"]}
    assert {s["skill"] for s in expected["present_skills"]} <= found
    text = json.dumps(result, ensure_ascii=False)
    for personal in personal_strings(cv_id):
        assert personal not in text
