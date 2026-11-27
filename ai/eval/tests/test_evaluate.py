"""evaluate.py'nin Ollama gerektirmeyen kısımları: puanlama, yüzdelik ve rapor."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR / "scripts"))

import evaluate as e  # noqa: E402


def s(name: str, level: str = "unknown", verified: bool = True) -> dict[str, object]:
    return {"skill": name, "level": level, "years": None, "verified": verified}


def test_key_ignores_case_spaces_and_out_of_taxonomy_mark() -> None:
    assert e.key("?Room") == e.key("room") == e.key(" ROOM ")
    assert e.key("Spring  Boot") == "spring boot"


def test_score_cv_counts_and_levels() -> None:
    pred = [s("Python", "advanced"), s("Docker", "beginner"), s("Room", verified=False), s("Go")]
    gold = [s("Python", "intermediate"), s("Docker", "beginner"), s("?Room"), s("SQL")]
    r = e.score_cv(pred, gold)
    assert (r.counts.tp, r.counts.fp, r.counts.fn) == (3, 1, 1)
    assert r.fp_names == ["Go"] and r.fn_names == ["SQL"]
    assert r.level_pairs == [("beginner", "beginner"), ("intermediate", "advanced"), ("unknown", "unknown")]


def test_score_cv_in_taxonomy_drops_unverified_and_question_marked() -> None:
    pred = [s("Python"), s("Room", verified=False)]
    gold = [s("Python"), s("?Room"), s("SQL")]
    r = e.score_cv(pred, gold, in_taxonomy=True)
    assert (r.counts.tp, r.counts.fp, r.counts.fn) == (1, 0, 1)


def test_counts_metrics_and_empty() -> None:
    c = e.Counts(tp=8, fp=2, fn=2)
    assert c.precision == pytest.approx(0.8) and c.recall == pytest.approx(0.8) and c.f1 == pytest.approx(0.8)
    assert e.Counts().f1 == 0.0


def test_percentile_nearest_rank() -> None:
    xs = list(range(1, 21))  # 1..20
    assert e.percentile(xs, 50) == 10
    assert e.percentile(xs, 95) == 19
    assert e.percentile([7.0], 95) == 7.0
    assert math.isnan(e.percentile([], 50))


def test_level_accuracy_skips_unknown_gold() -> None:
    acc, n = e.level_accuracy([("beginner", "beginner"), ("advanced", "intermediate"), ("unknown", "advanced")])
    assert (acc, n) == (0.5, 2)
    assert math.isnan(e.level_accuracy([("unknown", "unknown")])[0])


def test_report_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = tmp_path / "dataset"
    (dataset / "gold").mkdir(parents=True)
    (dataset / "manifest.csv").write_text(
        "cv_id,source,language,layout,scanned,pages,target_role,experience,double,consent_id\n"
        "syn-004,synthetic,tr,single_column,false,1,x,new_grad,false,\n"
        "syn-005,synthetic,tr,multi_column,true,1,x,intern,false,\n",
        encoding="utf-8",
    )
    for cv, skills in {"syn-004": [s("Python", "advanced"), s("SQL")], "syn-005": [s("Java")]}.items():
        (dataset / "gold" / f"{cv}.json").write_text(
            json.dumps({"cv_id": cv, "adjudicator": "claude", "skills": skills}), encoding="utf-8"
        )
    results = tmp_path / "results"
    results.mkdir()
    monkeypatch.setattr(e, "RESULTS", results)
    records = [
        {
            "cv_id": "syn-004",
            "status": "ok",
            "parse_s": 0.1,
            "mask_s": 0.2,
            "extract_s": 9.0,
            "total_s": 9.3,
            "skills": [s("Python", "advanced"), s("Go")],
        },
        {"cv_id": "syn-005", "status": "needs_ocr", "parse_s": 0.1, "skills": []},
    ]
    (results / "t.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    out = e.report(dataset, "t")
    assert "| Tüm CV'ler (taranmış = boş) | 2 | 0,50 | 0,33 | **0,40** | 1 | 1 | 2 |" in out
    assert "| Metinli PDF'ler | 1 | 0,50 | 0,50 | **0,50** | 1 | 1 | 1 |" in out
    assert "| Toplam (1–3) | 9,3 | 9,3 | 9,3 |" in out
    assert "%100" in out  # Python: advanced = advanced
    assert "SQL (1)" in out and "Go (1)" in out
