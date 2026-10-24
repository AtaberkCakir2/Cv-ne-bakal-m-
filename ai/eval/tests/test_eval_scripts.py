"""ai/eval/scripts testleri. Çalıştırma: pytest ai/eval/tests"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR / "scripts"))

import agreement  # noqa: E402
import check_labels  # noqa: E402
from _common import Report, load_labels, load_skill_names  # noqa: E402

EXAMPLES = EVAL_DIR / "examples"
SKILLS = EVAL_DIR / "dataset" / "skills_provisional.json"


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    target = tmp_path / "dataset"
    shutil.copytree(EXAMPLES, target)
    return target


def test_real_dataset_is_valid() -> None:
    assert check_labels.main([]) == 0


def test_examples_are_valid() -> None:
    assert check_labels.main(["--dataset", str(EXAMPLES), "--skills", str(SKILLS)]) == 0


def test_compare_example_pair() -> None:
    report = Report()
    labels = load_labels(EXAMPLES, load_skill_names(SKILLS), report)
    assert not report.errors
    a, b = agreement.pick_pair(labels["syn-001"], "syn-001")
    result = agreement.compare("syn-001", a, labels["syn-001"][a], b, labels["syn-001"][b])

    assert (a, b) == ("ataberk", "burak")
    assert result.only_a == ["?GitHub Actions", "Kubernetes"]
    assert result.only_b == ["CI/CD"]
    assert result.both == 16
    assert result.f1 == pytest.approx(32 / 35)
    assert [d[0] for d in result.level_diffs] == ["Docker", "FastAPI"]


def test_unknown_skill_without_question_mark_is_error(dataset: Path) -> None:
    path = dataset / "labels" / "syn-001" / "burak.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["skills"].append({"skill": "Apache Kafka", "level": "unknown", "years": None})
    path.write_text(json.dumps(data), encoding="utf-8")
    assert check_labels.main(["--dataset", str(dataset), "--skills", str(SKILLS)]) == 1


def test_real_cv_requires_consent(dataset: Path) -> None:
    with (dataset / "manifest.csv").open("a", encoding="utf-8") as f:
        f.write("cv-002,real,en,multi_column,true,2,backend-developer,\n")
    assert check_labels.main(["--dataset", str(dataset), "--skills", str(SKILLS)]) == 1


def test_write_gold_creates_draft_and_keeps_existing(dataset: Path) -> None:
    assert agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"]) == 0
    gold_path = dataset / "gold" / "syn-001.json"
    draft = json.loads(gold_path.read_text(encoding="utf-8"))

    assert draft["adjudicator"] == "ataberk"  # syn-001: 1 mod 3 → hakem ataberk
    assert len(draft["skills"]) == 14
    assert {p["skill"] for p in draft["_karar_bekleyen"]} == {"Docker", "FastAPI", "Kubernetes", "?GitHub Actions", "CI/CD"}
    # Çözülmemiş taslak doğrulamadan geçmemeli.
    assert check_labels.main(["--dataset", str(dataset), "--skills", str(SKILLS)]) == 1

    gold_path.write_text("{}", encoding="utf-8")
    agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"])
    assert gold_path.read_text(encoding="utf-8") == "{}"


def test_cohen_kappa() -> None:
    assert agreement.cohen_kappa([]) is None
    assert agreement.cohen_kappa([("advanced", "advanced"), ("beginner", "beginner")]) == pytest.approx(1.0)
    assert agreement.cohen_kappa([("advanced", "beginner"), ("beginner", "advanced")]) == pytest.approx(-1.0)
