"""Eksik yetkinlikler için eğitim kaynağı önerisi (T-043, RAG).

    from recommendation import load_candidates, recommend
    candidates = load_candidates(conn, [m.skill for m in result.missing])
    rec = recommend(result.missing, candidates, role_name="Backend Developer", postings_analyzed=150,
                    present=["Python", "SQL"])
    rec.missing_skills()   # contracts/analysis_result.schema.json: missing_skills (resources dolu)

Akış: eksik yetkinliğin aday kaynakları veritabanından çekilir (`resources`, sadece canlı link). LLM bu listeden seçer
ve gerekçe yazar; sonuç doğrulanır:
- Seçilen `resource_id` o yetkinliğin aday listesinde değilse atılır. Link, başlık ve diğer alanlar her zaman
  veritabanındaki kayıttan gelir; LLM'in yazdığı hiçbir şey link olamaz (karar #10).
- Gerekçede link/adres varsa, boşsa veya çok uzunsa atılır; yerine kurallı gerekçe yazılır.
- İlan istatistiği ("İncelenen 150 ... ilanının %75'i Docker istiyor.") koddan üretilir, LLM sayı yazmaz.
- LLM çalışmazsa veya az seçerse eksik kalan yerler kurallı sırayla doldurulur (Türkçe, başlangıç, ücretsiz önce).

LLM'e CV metni gitmez: sadece pozisyon adı, eksik ve mevcut yetkinlik adları ve kaynak bilgileri.
LLM'e giden kaynak başlıkları üçüncü taraf metnidir (YouTube); bu yüzden çıktı sadece numara + doğrulanan gerekçedir.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from extraction.llm import DEFAULT_MODEL, LlmError, LlmErrorCode, Transport, ollama_transport
from matching.score import Missing
from prompts import ModelInfo, Prompt, get_prompt, model_info

Provider = Literal["youtube", "udemy", "coursera", "btk_akademi", "docs", "blog", "other"]
Level = Literal["beginner", "intermediate", "advanced"]

PER_SKILL = 3  # yetkinlik başına önerilen kaynak
CANDIDATES_PER_SKILL = 8  # LLM'e gösterilen aday (prompt kısa kalsın)
# CPU'da üretim yavaş (~8 token/sn); LLM sadece öncelikli yetkinliklerin gerekçesini yazar, kalanlar kurallı.
LLM_SKILLS = 5
TEMPERATURE = 0.2
NUM_CTX = 8192
MAX_REASON_CHARS = 240
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "resource_id": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["skill", "resource_id", "reason"],
            },
        }
    },
    "required": ["picks"],
}

_LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
_LEVEL_TR = {"beginner": "başlangıç", "intermediate": "orta", "advanced": "ileri"}
_LEVEL_PHRASE = {"beginner": "başlangıç seviyesinde", "intermediate": "orta seviyede", "advanced": "ileri seviyede"}
# Sayının okunuşundaki son kelimeye göre iyelik eki: %75'i (beş-i), %62'si (iki-si), %40'ı (kırk-ı), %100'ü (yüz-ü).
_UNIT_SUFFIX = ("", "i", "si", "ü", "ü", "i", "sı", "si", "i", "u")
_TENS_SUFFIX = ("ı", "u", "si", "u", "ı", "si", "ı", "i", "i", "ı")  # sıfır, on, yirmi, otuz, kırk, elli, ...
_LINK = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|org|net|io|dev|tr|be)\b|\]\(", re.IGNORECASE)


@dataclass(frozen=True)
class Resource:
    resource_id: int
    skill: str
    title: str
    url: str
    provider: Provider
    language: Literal["tr", "en"]
    level: Level
    duration_min: int | None
    is_free: bool


@dataclass(frozen=True)
class Pick:
    resource: Resource
    reason: str
    by: Literal["llm", "rule"]  # gerekçeyi kim yazdı


@dataclass
class Recommendation:
    missing: list[Missing]
    picks: dict[str, list[Pick]]
    model: ModelInfo
    llm_error: LlmErrorCode | None = None
    rejected: int = field(default=0)  # LLM'in atılan seçimleri (listede yok, tekrar, bozuk gerekçe)

    def missing_skills(self) -> list[dict[str, Any]]:
        """contracts/analysis_result.schema.json → missing_skills (`resources` dolu)."""
        out: list[dict[str, Any]] = []
        for m in self.missing:
            resources = []
            for p in self.picks.get(m.skill, []):
                r = p.resource
                item: dict[str, Any] = {
                    "resource_id": r.resource_id,
                    "title": r.title,
                    "url": r.url,
                    "provider": r.provider,
                    "language": r.language,
                    "level": r.level,
                    "is_free": r.is_free,
                    "reason": p.reason,
                }
                if r.duration_min is not None:
                    item["duration_min"] = r.duration_min
                resources.append(item)
            out.append(
                {
                    "skill": m.skill,
                    "demand_ratio": round(m.demand_ratio, 4),
                    "priority": m.priority,
                    "resources": resources,
                }
            )
        return out


def rank_key(r: Resource) -> tuple[int, int, int, int, int]:
    """Kurallı sıra: Türkçe, başlangıç seviyesi, ücretsiz, kısa süre önce; eşitlikte küçük id (kararlı sonuç)."""
    return (
        r.language != "tr",
        _LEVEL_ORDER[r.level],
        not r.is_free,
        r.duration_min if r.duration_min is not None else 10**6,
        r.resource_id,
    )


def stat_sentence(m: Missing, role_name: str, postings_analyzed: int) -> str:
    """İlan istatistiği cümlesi; sayılar sadece buradan gelir."""
    percent = round(m.demand_ratio * 100)
    share = f"%{percent}'{percent_suffix(percent)}"
    if postings_analyzed > 0:
        return f"İncelenen {postings_analyzed} {role_name} ilanının {share} {m.skill} istiyor."
    return f"{role_name} ilanlarının {share} {m.skill} istiyor."


def percent_suffix(n: int) -> str:
    """0-100 arası tam sayıya gelen iyelik eki (Türkçe ses uyumu, okunuştaki son kelimeye göre)."""
    if not 0 <= n <= 100:
        raise ValueError("yüzde 0-100 olmalı")
    if n == 100:
        return "ü"
    return _UNIT_SUFFIX[n % 10] if n % 10 else _TENS_SUFFIX[n // 10]


def rule_reason(r: Resource) -> str:
    parts = ["Türkçe" if r.language == "tr" else "İngilizce", _LEVEL_PHRASE[r.level]]
    if r.is_free:
        parts.append("ücretsiz")
    text = ", ".join(parts)
    if r.duration_min:
        text += f" ve yaklaşık {_duration(r.duration_min)} süren"
    return f"{text[0].upper()}{text[1:]} bir kaynak; {r.skill} için iyi bir başlangıç."


def recommend(
    missing: Sequence[Missing],
    candidates: dict[str, list[Resource]],
    *,
    role_name: str,
    postings_analyzed: int,
    present: Sequence[str] = (),
    transport: Transport | None = None,
    model: str | None = None,
    prompt: Prompt | None = None,
    per_skill: int = PER_SKILL,
    llm_skills: int = LLM_SKILLS,
    use_llm: bool = True,
) -> Recommendation:
    """`candidates`: yetkinlik → aday kaynaklar (`load_candidates`). Adayı olmayan yetkinliğin `resources`'ı boş kalır.

    `use_llm=False` veya LLM hatası: sadece kurallı seçim ve gerekçe (`llm_error` hata kodunu taşır).
    """
    if per_skill < 1:
        raise ValueError("per_skill en az 1 olmalı")
    model = model or os.environ.get("OLLAMA_MODEL") or DEFAULT_MODEL
    prompt = prompt or get_prompt("recommendation")
    ranked = {s: sorted(rs, key=rank_key)[:CANDIDATES_PER_SKILL] for s, rs in candidates.items()}

    llm_targets = [m for m in missing if ranked.get(m.skill)][: max(llm_skills, 0)]
    chosen: dict[str, list[Pick]] = {}
    error: LlmErrorCode | None = None
    rejected = 0
    if use_llm and llm_targets:
        try:
            raw = _ask_llm(llm_targets, ranked, role_name, present, per_skill, transport, model, prompt)
            chosen, rejected = _validate(raw, ranked, {m.skill for m in llm_targets}, per_skill)
        except LlmError as e:
            error = e.code

    picks: dict[str, list[Pick]] = {}
    for m in missing:
        own = chosen.get(m.skill, [])
        used = {p.resource.resource_id for p in own}
        fill = [Pick(r, rule_reason(r), "rule") for r in ranked.get(m.skill, []) if r.resource_id not in used]
        stat = stat_sentence(m, role_name, postings_analyzed)
        picks[m.skill] = [replace(p, reason=f"{stat} {p.reason}") for p in (own + fill)[:per_skill]]
    return Recommendation(list(missing), picks, model_info(model, prompt), error, rejected)


def _ask_llm(
    targets: Sequence[Missing],
    ranked: dict[str, list[Resource]],
    role_name: str,
    present: Sequence[str],
    per_skill: int,
    transport: Transport | None,
    model: str,
    prompt: Prompt,
) -> Any:
    lines = [f"Hedef pozisyon: {role_name}"]
    if present:
        lines.append("Öğrencinin bildiği yetkinlikler: " + ", ".join(dict.fromkeys(present)))
    lines.append(f"Her yetkinlik için en fazla {per_skill} kaynak seç.")
    for m in targets:
        lines.append(f"\nEksik yetkinlik: {m.skill}")
        for r in ranked[m.skill]:
            lines.append("- " + _describe(r))
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": prompt.text}, {"role": "user", "content": "\n".join(lines)}],
        "stream": False,
        "format": SCHEMA,
        "options": {"temperature": TEMPERATURE, "seed": 42, "num_ctx": NUM_CTX},
    }
    response = (transport or ollama_transport())(body)
    try:
        return json.loads(response["message"]["content"])["picks"]
    except (KeyError, TypeError, ValueError):
        raise LlmError("INTERNAL") from None


def _validate(
    raw: Any, ranked: dict[str, list[Resource]], targets: set[str], per_skill: int
) -> tuple[dict[str, list[Pick]], int]:
    if not isinstance(raw, list):
        raise LlmError("INTERNAL")
    # Numara → kaynak; sadece LLM'e gösterilen adaylar. Yetkinlik numaradan bulunur, LLM'in yazdığı ad kullanılmaz.
    by_id = {r.resource_id: r for s in targets for r in ranked.get(s, [])}
    out: dict[str, list[Pick]] = {}
    seen: set[int] = set()
    rejected = 0
    for item in raw:
        rid = item.get("resource_id") if isinstance(item, dict) else None
        reason = _clean_reason(item.get("reason")) if isinstance(item, dict) else None
        resource = by_id.get(rid) if isinstance(rid, int) and not isinstance(rid, bool) else None
        if resource is None or rid in seen or len(out.get(resource.skill, [])) >= per_skill:
            rejected += 1
            continue
        seen.add(resource.resource_id)
        if reason is None:
            rejected += 1  # kaynak geçerli, gerekçe değil: kaynak kalır, gerekçe kurallı olur
            reason_text, by = rule_reason(resource), "rule"
        else:
            reason_text, by = reason, "llm"
        out.setdefault(resource.skill, []).append(Pick(resource, reason_text, by))  # type: ignore[arg-type]
    return out, rejected


def _clean_reason(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text or len(text) > MAX_REASON_CHARS or _LINK.search(text) or "%" in text:
        return None
    return text if text.endswith((".", "!")) else text + "."


def _describe(r: Resource) -> str:
    title = " ".join(r.title.split())[:120]
    parts = [
        f"[{r.resource_id}] {title}",
        "Türkçe" if r.language == "tr" else "İngilizce",
        _LEVEL_TR[r.level],
        "ücretsiz" if r.is_free else "ücretli",
        r.provider,
    ]
    if r.duration_min:
        parts.append(_duration(r.duration_min))
    return " | ".join(parts)


def _duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} dakika"
    hours, rest = divmod(minutes, 60)
    return f"{hours} saat" if rest == 0 else f"{hours} saat {rest} dakika"
