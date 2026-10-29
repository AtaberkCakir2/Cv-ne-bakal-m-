from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest

from pii import Kind, mask, ner
from pii.ner import DEFAULT_TAXONOMY, BertNerDetector, Pipeline, load_skill_words

# --- Model olmadan: sahte pipeline ile birleştirme, filtre ve parçalama mantığı ------------------------------------


def _fake_pipe(*pieces: tuple[str, str, float]) -> Pipeline:
    """Verilen (alt dizgi, etiket, skor) üçlülerini metinde bulup model çıktısı gibi döndürür."""

    def pipe(text: str) -> list[dict[str, Any]]:
        out = []
        for piece, label, score in pieces:
            for m in re.finditer(re.escape(piece), text):
                out.append({"entity_group": label, "score": score, "start": m.start(), "end": m.end()})
        return out

    return pipe


def _words(text: str, spans: list[tuple[int, int]]) -> list[str]:
    return [text[s:e] for s, e in spans]


def test_subword_entity_expands_to_whole_word() -> None:
    text = "Yöneticim Nehir Tanrıverdi ile çalıştım."
    detector = BertNerDetector(pipe=_fake_pipe(("Nehir Tanrı", "PER", 0.9)))
    assert _words(text, detector(text, "tr")) == ["Nehir", "Tanrıverdi"]


def test_skill_words_are_not_names() -> None:
    text = "Postman ve Flutter ile Ayşe Kaya'nın ekibinde test yazdım."
    pipe = _fake_pipe(("Post", "PER", 0.8), ("Flutt", "PER", 0.7), ("Ayşe Kaya", "PER", 0.99))
    detector = BertNerDetector({"postman", "flutter"}, pipe=pipe)
    assert _words(text, detector(text, "tr")) == ["Ayşe", "Kaya"]


def test_other_labels_and_low_scores_are_ignored() -> None:
    text = "Ankara'da Mert Bilişim'de Deniz ile."
    pipe = _fake_pipe(("Ankara", "LOC", 0.99), ("Mert Bilişim", "ORG", 0.9), ("Deniz", "PER", 0.3))
    assert BertNerDetector(pipe=pipe)(text, "tr") == []


def test_long_text_is_chunked_with_correct_offsets() -> None:
    filler = "Python ve SQL ile veri işleme.\n" * 100
    text = filler + "Referans: Oliver Bennett\n" + filler
    assert len(text) > 3 * ner.CHUNK_CHARS
    calls: list[int] = []
    inner = _fake_pipe(("Oliver Bennett", "PER", 0.95))

    def pipe(chunk: str) -> list[dict[str, Any]]:
        calls.append(len(chunk))
        return inner(chunk)

    spans = BertNerDetector(pipe=pipe)(text, "en")
    assert _words(text, spans) == ["Oliver", "Bennett"]
    assert len(calls) > 1 and max(calls) <= ner.CHUNK_CHARS


def test_detector_plugs_into_mask() -> None:
    text = "Ekip lideri Nehir Tanrıverdi'ye raporladım. Nehir'in desteğiyle Kafka kurduk."
    detector = BertNerDetector(pipe=_fake_pipe(("Nehir Tanrıverdi", "PER", 0.99)))
    result = mask(text, "tr", detector=detector)
    assert "Nehir" not in result.text and "Tanrıverdi" not in result.text
    assert "Kafka" in result.text
    assert result.counts[Kind.NAME] >= 2


def test_taxonomy_words_load() -> None:
    if not DEFAULT_TAXONOMY.is_file():
        pytest.skip("scraper/taxonomy/skills.csv yok")
    words = load_skill_words(DEFAULT_TAXONOMY)
    assert {"python", "flutter", "kafka"} <= words


def test_load_skill_words_reads_synonyms(tmp_path: Path) -> None:
    csv_file = tmp_path / "skills.csv"
    csv_file.write_text("canonical_name,synonyms\nApache Kafka,kafka streams\nPython,py|python3\n", encoding="utf-8")
    assert load_skill_words(csv_file) == {"apache", "kafka", "streams", "python", "py", "python3"}


# --- Gerçek modelle (sadece `pip install -e ".[ner]"` yapılıp model indirilmişse) -------------------------------------

_HAS_NER = all(importlib.util.find_spec(m) is not None for m in ("torch", "transformers"))


@pytest.mark.skipif(not _HAS_NER, reason="transformers/torch kurulu değil (isteğe bağlı [ner] paketi)")
def test_real_model_finds_names_in_running_text() -> None:
    detector = ner.default_detector()
    assert detector is not None
    text = (
        "Stajda yöneticim Nehir Tanrıverdi ile mobil uygulama geliştirdim.\n"
        "Flutter, Postman ve Apache Kafka kullandım. Referans: Oliver Bennett (Lead Engineer)."
    )
    try:
        result = mask(text, "tr", detector=detector)
    except OSError as err:  # model önbellekte yok ve indirilemiyor
        pytest.skip(f"NER modeli yüklenemedi: {err}")
    for name in ("Nehir", "Tanrıverdi", "Oliver", "Bennett"):
        assert name not in result.text
    for skill in ("Flutter", "Postman", "Kafka"):
        assert skill in result.text
