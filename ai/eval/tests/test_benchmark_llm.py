"""benchmark_llm.py'nin Ollama gerektirmeyen kısımları."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR / "scripts"))

import benchmark_llm as b  # noqa: E402

ALIASES = {
    "python": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "react": "React",
    "k8s": "Kubernetes",
    "express.js": "Express.js",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
}


def test_normalize_handles_synonyms_and_decorations() -> None:
    assert b.normalize("JS", ALIASES) == ["JavaScript"]
    assert b.normalize("  Python (ileri) ", ALIASES) == ["Python"]
    assert b.normalize("React.js", ALIASES) == ["React"]
    assert b.normalize("Express", ALIASES) == ["Express.js"]
    assert b.normalize("TensorFlow/Keras", ALIASES) == ["TensorFlow", "Keras"]
    assert b.normalize("Python & Uçan halı", ALIASES) is None
    assert b.normalize("Takla atma", ALIASES) is None


def test_parse_output_strict_fenced_and_broken() -> None:
    good = json.dumps({"skills": [{"skill": "Python", "level": "advanced", "years": 3}]})
    assert b.parse_output(good) == (True, True, [{"skill": "Python", "level": "advanced", "years": 3}])
    strict, valid, items = b.parse_output(f"İşte sonuç:\n```json\n{good}\n```")
    assert (strict, valid, len(items)) == (False, True, 1)
    assert b.parse_output('{"skills": [{"skill": "Go", "level": "expert"}]}')[1] is False
    assert b.parse_output("JSON veremiyorum") == (False, False, [])


def test_score_counts_duplicates_once_and_off_taxonomy() -> None:
    s = b.score(["Python", "python", "JS", "Uçan halı"], {"Python", "Kubernetes"}, ALIASES)
    assert (s["tp"], s["fp"], s["fn"], s["off_taxonomy"]) == (1, 1, 1, 1)
    assert s["fn_names"] == ["Kubernetes"]


def test_reference_uses_taxonomy_names() -> None:
    if not b.TAXONOMY.is_file() or not b.REFERENCE.is_file():
        pytest.skip("taksonomi veya referans yok")
    canon = set(b.load_aliases().values())
    ref = json.loads(b.REFERENCE.read_text(encoding="utf-8"))["cvs"]
    unknown = {s for skills in ref.values() for s in skills} - canon
    assert not unknown
