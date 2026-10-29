"""ai/eval/scripts testleri. Çalıştırma: pytest ai/eval/tests"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR / "scripts"))

import _common  # noqa: E402
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
    assert result.only_a == ["?Swagger", "Kubernetes"]
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


@pytest.mark.parametrize(
    ("skill", "message"),
    [
        (" Docker", "boşluk"),
        ("Postgres", "→ 'PostgreSQL' yazın"),
        ("?k8s", "→ 'Kubernetes' yazın"),
    ],
)
def test_bad_skill_names_are_reported(skill: str, message: str) -> None:
    report = Report()
    _common.validate_skills(
        Path("x.json"), [{"skill": skill, "level": "unknown", "years": None}], load_skill_names(SKILLS), report
    )
    assert len(report.errors) == 1
    assert message in report.errors[0]


@pytest.mark.parametrize(
    "row",
    [
        "cv-002,real,en,multi_column,true,2,backend-developer,experienced,false,IZN-1",  # karar #20: gerçek CV yok
        "syn-002,synthetic,en,multi_column,true,2,backend-developer,senior,false,",  # bilinmeyen deneyim
        "syn-002,synthetic,en,multi_column,true,2,backend-developer,intern,evet,",  # double true/false olmalı
    ],
    ids=["gercek", "deneyim", "double"],
)
def test_invalid_manifest_rows_are_errors(dataset: Path, row: str) -> None:
    with (dataset / "manifest.csv").open("a", encoding="utf-8") as f:
        f.write(row + "\n")
    assert check_labels.main(["--dataset", str(dataset), "--skills", str(SKILLS)]) == 1


def test_single_labeled_cv_is_copied_to_gold(dataset: Path) -> None:
    with (dataset / "manifest.csv").open("a", encoding="utf-8") as f:
        f.write("syn-002,synthetic,en,multi_column,false,1,frontend-developer,experienced,false,\n")
    label_dir = dataset / "labels" / "syn-002"
    label_dir.mkdir()
    skills = [{"skill": "React", "level": "advanced", "years": 3}]
    (label_dir / "ataberk.json").write_text(
        json.dumps({"cv_id": "syn-002", "annotator": "ataberk", "skills": skills, "notes": ""}), encoding="utf-8"
    )
    assert agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"]) == 0
    gold = json.loads((dataset / "gold" / "syn-002.json").read_text(encoding="utf-8"))
    assert (gold["adjudicator"], gold["skills"]) == ("ataberk", skills)
    assert "_karar_bekleyen" not in gold


def test_double_cv_with_one_label_waits_for_second(dataset: Path) -> None:
    """syn-001 double=true: ilk etiket tek başına gold'a girmez; ikinci etiket gelince taslak yazılır (#34)."""
    burak = dataset / "labels" / "syn-001" / "burak.json"
    burak_text = burak.read_text(encoding="utf-8")
    burak.unlink()
    assert agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"]) == 0
    gold_path = dataset / "gold" / "syn-001.json"
    assert not gold_path.exists()

    burak.write_text(burak_text, encoding="utf-8")
    assert agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"]) == 0
    draft = json.loads(gold_path.read_text(encoding="utf-8"))
    assert draft["_karar_bekleyen"]


def test_single_label_not_in_manifest_is_not_copied(dataset: Path) -> None:
    label_dir = dataset / "labels" / "syn-002"
    label_dir.mkdir()
    (label_dir / "ataberk.json").write_text(
        json.dumps({"cv_id": "syn-002", "annotator": "ataberk", "skills": [], "notes": ""}), encoding="utf-8"
    )
    agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"])
    assert not (dataset / "gold" / "syn-002.json").exists()


def test_write_gold_creates_draft_and_keeps_existing(dataset: Path) -> None:
    assert agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"]) == 0
    gold_path = dataset / "gold" / "syn-001.json"
    draft = json.loads(gold_path.read_text(encoding="utf-8"))

    assert draft["adjudicator"] == "ataberk"  # syn-001: 1 mod 3 → hakem ataberk
    assert len(draft["skills"]) == 14
    assert {p["skill"] for p in draft["_karar_bekleyen"]} == {"Docker", "FastAPI", "Kubernetes", "?Swagger", "CI/CD"}
    # Çözülmemiş taslak doğrulamadan geçmemeli.
    assert check_labels.main(["--dataset", str(dataset), "--skills", str(SKILLS)]) == 1

    gold_path.write_text("{}", encoding="utf-8")
    agreement.main(["--dataset", str(dataset), "--skills", str(SKILLS), "--write-gold"])
    assert gold_path.read_text(encoding="utf-8") == "{}"


def test_cohen_kappa() -> None:
    assert agreement.cohen_kappa([]) is None
    assert agreement.cohen_kappa([("advanced", "advanced"), ("beginner", "beginner")]) == pytest.approx(1.0)
    assert agreement.cohen_kappa([("advanced", "beginner"), ("beginner", "advanced")]) == pytest.approx(-1.0)
