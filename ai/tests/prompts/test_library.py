from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from prompts import CURRENT, get_prompt, model_info

REPO = Path(__file__).resolve().parents[3]

# Yayımlanmış sürümler değişmez. Bu test kırılıyorsa dosyayı geri al, yeni sürüm (v2.txt) aç.
PUBLISHED = {
    ("skill_extraction", "v1"): "7467f9223d34513bf97c3e408a23d1c57b12b2c6d28f0f693ecc99580d59d03b",
    ("skill_extraction", "v2"): "0cd55bfb3708cf3912fd10fc6b326285b84951637347f303796be965cb977a66",
    ("recommendation", "v1"): "1ac6d77b97c8865f6460dd5a09f5ff52303af02a90109143635ad3ac33f9e3e8",
}


@pytest.mark.parametrize(("name", "version"), PUBLISHED)
def test_published_versions_do_not_change(name: str, version: str) -> None:
    digest = hashlib.sha256(get_prompt(name, version).text.encode("utf-8")).hexdigest()
    assert digest == PUBLISHED[(name, version)]


def test_every_prompt_file_is_pinned() -> None:
    root = REPO / "ai" / "prompts"
    assert {(p.parent.name, p.stem) for p in root.glob("*/*.txt")} == set(PUBLISHED)


def test_current_version_is_returned_by_default() -> None:
    for name, version in CURRENT.items():
        prompt = get_prompt(name)
        assert (prompt.name, prompt.version) == (name, version)
        assert prompt.text.strip()


def test_prompt_text_has_unix_line_endings() -> None:
    assert "\r" not in get_prompt("skill_extraction").text


def test_json_example_uses_placeholder_not_a_real_skill() -> None:
    # Karar #26: örnekteki gerçek yetkinlik adını model CV'de yokken de yazıyor.
    text = get_prompt("skill_extraction").text
    example = text[text.index('{"skills"') :]
    assert "<yetkinlik adı>" in example
    assert "Python" not in text and "İngilizce" not in text


def test_recommendation_example_uses_placeholders() -> None:
    text = get_prompt("recommendation").text
    example = text[text.index('{"picks"') :]
    assert "<yetkinlik adı>" in example and "<listedeki numara>" in example
    assert "Python" not in text and "Docker" not in text


@pytest.mark.parametrize(
    ("name", "version"),
    [
        ("yok", None),
        ("skill_extraction", "v99"),
        ("skill_extraction", "1"),
        ("skill_extraction", "../library"),
        ("../prompts", "v1"),
    ],
)
def test_unknown_or_invalid_prompt_is_rejected(name: str, version: str | None) -> None:
    with pytest.raises(ValueError):
        get_prompt(name, version)


def test_model_info_matches_contract_example() -> None:
    example = json.loads((REPO / "contracts/examples/analysis_result.example.json").read_text(encoding="utf-8"))
    # Sözleşme örneği biçimi gösterir (v1); güncel sürüm değişse de biçim aynı kalır.
    assert model_info("llama3.1:8b", get_prompt("skill_extraction", "v1")) == example["model"]


def test_extraction_prompt_marks_cv_as_data() -> None:
    # T-074: CV metni <cv> bloğunda veri; içindeki talimatlar yok sayılır (extraction/llm.py as_data).
    text = get_prompt("skill_extraction").text
    assert "<cv>" in text and "</cv>" in text
