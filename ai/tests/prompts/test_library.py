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
    assert model_info("llama3.1:8b", get_prompt("skill_extraction")) == example["model"]
