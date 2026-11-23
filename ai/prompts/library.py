"""Prompt kütüphanesi: `prompts/<ad>/<sürüm>.txt`.

Yayımlanmış bir sürüm değiştirilmez; değişiklik yeni dosya (`v2.txt`) ve `CURRENT` güncellemesiyle yapılır. Böylece
analizde kaydedilen `prompt_version`, sonucu üreten metni her zaman gösterir. Dosyaların özeti
`tests/prompts/test_library.py` içinde sabittir.

Prompt örneklerinde gerçek yetkinlik adı kullanılmaz (karar #26): model, örnekteki adı CV'de yokken de yazıyor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

_ROOT = Path(__file__).resolve().parent
_NAME = re.compile(r"[a-z][a-z0-9_]*")
_VERSION = re.compile(r"v[1-9]\d*")

CURRENT = {"skill_extraction": "v2", "recommendation": "v1"}


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    text: str


class ModelInfo(TypedDict):
    """`contracts/analysis_result.schema.json` içindeki `model` nesnesi."""

    name: str
    prompt_version: str


def get_prompt(name: str, version: str | None = None) -> Prompt:
    """`version` verilmezse `CURRENT` içindeki sürüm döner. Bilinmeyen ad veya sürüm `ValueError` verir."""
    resolved = version if version is not None else CURRENT.get(name)
    if resolved is None or not _NAME.fullmatch(name) or not _VERSION.fullmatch(resolved):
        raise ValueError(f"geçersiz prompt: {name} {resolved}")
    path = _ROOT / name / f"{resolved}.txt"
    if not path.is_file():
        raise ValueError(f"prompt bulunamadı: {name} {resolved}")
    # Metin kipi satır sonlarını \n yapar: Windows'ta CRLF ile açılan dosya da aynı metni verir.
    return Prompt(name, resolved, path.read_text(encoding="utf-8"))


def model_info(model_name: str, prompt: Prompt) -> ModelInfo:
    """Analiz sonucuna ve `analyses.model_name` / `analyses.prompt_version` sütunlarına yazılacak değerler."""
    return {"name": model_name, "prompt_version": prompt.version}
