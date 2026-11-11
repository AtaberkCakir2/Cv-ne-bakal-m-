"""Yetkinlik çıkarımı v2: yerel LLM (Ollama) + v1 sözlük sonucu (T-032).

    from extraction.llm import extract_skills_v2
    result = extract_skills_v2(masked_text, "tr")
    result.present_skills()   # contracts/analysis_result.schema.json: present_skills
    result.model              # {"name": ..., "prompt_version": ...} (T-044)

Girdi maskelenmiş CV metnidir (pii.mask); LLM'e sadece bu metin gider, istek yerel Ollama'yadır (karar #1).
Birleştirme kuralları:
- v1 (sözlük + kural) temeldir: taksonomideki yetkinlik, istek cümlesi ve ders satırı kuralları v1'den gelir.
- LLM'in taksonomiye eşlenen yetkinliği sadece v1'de de varsa kullanılır; v1'deki bilinmeyen seviye/yılı tamamlar.
  v1'de olmayan taksonomi yetkinliği alınmaz: ya v1 kuralı onu bilerek eledi ("Go öğrenmek istiyorum"), ya metinde yok.
- Taksonomide olmayan yetkinlik `verified=False` (doğrulanmamış) eklenir, ama sadece adı metinde geçiyorsa
  (halüsinasyon filtresi: metinde olmayan ad atılır).
- LLM çalışmazsa (zaman aşımı, bozuk yanıt) v1 sonucu döner; `llm_error` hata kodunu taşır.

Prompt ve modelin metni/çıktısı loglanmaz; sadece sayılar loglanabilir.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from extraction.extract import ExtractedSkill, Level, extract_skills
from extraction.taxonomy import Lang, Matcher, Skill, default_matcher, fold
from prompts import ModelInfo, Prompt, get_prompt, model_info

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.1:8b"  # karar #26
TEMPERATURE = 0.1
# Analiz işçisi kapanırken 200 sn bekliyor (docker-compose worker-analysis); tek çağrı bunun altında kalmalı.
TIMEOUT_SECONDS = 150
NUM_CTX = 8192
LEVELS: tuple[Level, ...] = ("beginner", "intermediate", "advanced", "unknown")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "level": {"type": "string", "enum": list(LEVELS)},
                    "years": {"type": ["integer", "null"]},
                },
                "required": ["skill", "level", "years"],
            },
        }
    },
    "required": ["skills"],
}

# Güven: v1 + LLM aynı yetkinliği bulduysa biraz artar; sadece LLM'in bulduğu doğrulanmamış ad düşüktür.
_BOTH_BONUS = 0.05
_MAX_CONFIDENCE = 0.99
_UNVERIFIED_CONFIDENCE = 0.3
_MAX_NAME_LEN = 60
_MAX_YEARS = 50
_SPLIT = re.compile(r"\s*(?:/|&|,|\+| ve | and )\s*")

LlmErrorCode = Literal["LLM_TIMEOUT", "INTERNAL"]
Transport = Callable[[dict[str, Any]], dict[str, Any]]
"""Ollama /api/chat isteği → yanıt JSON'u. Testlerde sahtesi verilir."""


class LlmError(Exception):
    def __init__(self, code: LlmErrorCode) -> None:
        super().__init__(code)
        self.code: LlmErrorCode = code


@dataclass(frozen=True)
class LlmSkill:
    name: str
    level: Level
    years: int | None


@dataclass
class MergedSkill:
    skill: str  # taksonomideki standart ad; doğrulanmamışsa LLM'in yazdığı ad
    slug: str | None
    level: Level
    years: int | None
    confidence: float
    verified: bool
    source: Literal["v1", "llm", "both"]


@dataclass
class ExtractionResult:
    skills: list[MergedSkill]
    model: ModelInfo
    llm_error: LlmErrorCode | None = None
    rejected: int = field(default=0)  # LLM'in atılan önerileri (metinde yok / v1 kuralı eledi)

    def present_skills(self) -> list[dict[str, Any]]:
        """contracts/analysis_result.schema.json → present_skills."""
        return [
            {"skill": s.skill, "level": s.level, "confidence": round(s.confidence, 2), "verified": s.verified}
            for s in self.skills
        ]


def ollama_transport(url: str | None = None, timeout: float = TIMEOUT_SECONDS) -> Transport:
    base = (url or os.environ.get("OLLAMA_URL") or DEFAULT_URL).rstrip("/")
    if not base.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_URL http(s) olmalı")

    def send(body: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(  # noqa: S310 (şema yukarıda denetlendi; yerel Ollama)
            base + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                data: dict[str, Any] = json.loads(resp.read())
        except TimeoutError:
            raise LlmError("LLM_TIMEOUT") from None
        except urllib.error.URLError as e:
            # Yanıt gövdesi ve hata ayrıntısı loglanmaz: içinde CV parçası olabilir.
            code: LlmErrorCode = "LLM_TIMEOUT" if isinstance(e.reason, TimeoutError) else "INTERNAL"
            raise LlmError(code) from None
        except (OSError, ValueError):
            raise LlmError("INTERNAL") from None
        return data

    return send


def llm_skills(text: str, transport: Transport, *, model: str, prompt: Prompt) -> list[LlmSkill]:
    """Ollama'dan JSON şemasıyla yetkinlik listesi. Şemaya uymayan öğe atılır; yanıt hiç okunamazsa `LlmError`."""
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": prompt.text}, {"role": "user", "content": text}],
        "stream": False,
        "format": SCHEMA,
        "options": {"temperature": TEMPERATURE, "seed": 42, "num_ctx": NUM_CTX},
    }
    response = transport(body)
    try:
        items = json.loads(response["message"]["content"])["skills"]
    except (KeyError, TypeError, ValueError):
        raise LlmError("INTERNAL") from None
    if not isinstance(items, list):
        raise LlmError("INTERNAL")
    out: list[LlmSkill] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("skill"), str):
            continue
        name = " ".join(item["skill"].split())
        if not name or len(name) > _MAX_NAME_LEN:
            continue
        level = item.get("level")
        years = item.get("years")
        out.append(
            LlmSkill(
                name=name,
                level=level if level in LEVELS else "unknown",
                years=years
                if isinstance(years, int) and not isinstance(years, bool) and 0 < years <= _MAX_YEARS
                else None,
            )
        )
    return out


def merge(text: str, v1: list[ExtractedSkill], llm: list[LlmSkill], matcher: Matcher) -> tuple[list[MergedSkill], int]:
    """(birleşik liste, atılan LLM önerisi sayısı). Sıra: önce v1 sırası, sonra doğrulanmamışlar."""
    merged = {
        s.slug: MergedSkill(s.skill, s.slug, s.level, s.years, s.confidence, verified=True, source="v1") for s in v1
    }
    unverified: dict[str, MergedSkill] = {}
    rejected = 0
    folded_text = fold(text, "tr")
    for item in llm:
        skills = _to_taxonomy(item.name, matcher)
        if skills is None:
            key = fold(item.name, "tr")
            if key in unverified or not _appears(key, folded_text) or "[" in item.name:
                rejected += key not in unverified
                continue
            unverified[key] = MergedSkill(
                item.name, None, item.level, item.years, _UNVERIFIED_CONFIDENCE, verified=False, source="llm"
            )
            continue
        for skill in skills:
            current = merged.get(skill.slug)
            if current is None:
                rejected += 1
                continue
            if current.source == "v1":
                current.source = "both"
                current.confidence = min(_MAX_CONFIDENCE, current.confidence + _BOTH_BONUS)
            if current.level == "unknown":
                current.level = item.level
            if current.years is None:
                current.years = item.years
    return list(merged.values()) + list(unverified.values()), rejected


def extract_skills_v2(
    text: str,
    lang: Lang = "tr",
    *,
    transport: Transport | None = None,
    model: str | None = None,
    prompt: Prompt | None = None,
    matcher: Matcher | None = None,
) -> ExtractionResult:
    matcher = matcher or default_matcher()
    model = model or os.environ.get("OLLAMA_MODEL") or DEFAULT_MODEL
    prompt = prompt or get_prompt("skill_extraction")
    v1 = extract_skills(text, lang, matcher=matcher)
    try:
        llm = llm_skills(text, transport or ollama_transport(), model=model, prompt=prompt)
    except LlmError as e:
        fallback = [
            MergedSkill(s.skill, s.slug, s.level, s.years, s.confidence, verified=True, source="v1") for s in v1
        ]
        return ExtractionResult(fallback, model_info(model, prompt), llm_error=e.code)
    skills, rejected = merge(text, v1, llm, matcher)
    return ExtractionResult(skills, model_info(model, prompt), rejected=rejected)


def _to_taxonomy(name: str, matcher: Matcher) -> list[Skill] | None:
    """Adın tamamı bir taksonomi adı/eş anlamlısıysa o yetkinlik; "Git & GitHub" gibi birleşikler parçalanır."""
    whole = _exact(name, matcher)
    if whole is not None:
        return [whole]
    parts = [p for p in _SPLIT.split(name) if p.strip()]
    if len(parts) > 1:
        found = [_exact(p, matcher) for p in parts]
        if all(found):
            return [s for s in found if s is not None]
    return None


def _exact(name: str, matcher: Matcher) -> Skill | None:
    name = name.strip()
    mentions = matcher.mentions(name, "tr")
    if len(mentions) == 1 and mentions[0].start == 0 and mentions[0].end == len(name):
        return mentions[0].skill
    return None


def _appears(folded_name: str, folded_text: str) -> bool:
    return re.search(rf"(?<![\w#+.]){re.escape(folded_name)}(?![\w#+]|\.\w)", folded_text) is not None
