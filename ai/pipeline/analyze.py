"""CV analizinin AI zinciri (T-057): PDF → metin → kişisel veri maskeleme → yetkinlik çıkarımı → eşleştirme → öneri.

    from pipeline import analyze_cv, AnalysisError
    try:
        out = analyze_cv(pdf_bytes, role_id=3, conn=psycopg_conn)
    except AnalysisError as e:
        e.code  # contracts → error.code: PDF_UNREADABLE | PDF_TOO_LARGE | NO_TEXT_FOUND | INTERNAL
    out.result  # contracts/analysis_result.schema.json alanları: target_role, postings_analyzed, match_score,
                # present_skills, missing_skills, model (analysis_id, status, tarih alanları backend'de)

Analiz işçisi (backend/app/worker, T-039) bunu çağırır; eşzamanlılık 1 ve görev zaman aşımı oradadır.

Gizlilik (CLAUDE.md kural 5, karar #9):
- PDF ve ham metin sadece bu fonksiyonun içinde bellekte durur; hiçbir yere yazılmaz, loglanmaz, sonuçta yoktur.
- LLM'e (yerel Ollama) sadece maskelenmiş metin gider; öneri adımına sadece yetkinlik adları.
- Log ve `stats` sadece sayı ve kod içerir.

Süre: analiz işçisinin sınırı 180 sn. Zincir `budget_s` içinde kalmaya çalışır: çıkarım en fazla
`EXTRACT_MAX_SECONDS` bekler (öneriye süre kalsın; bozuk yanıttaki ikinci deneme de bu sınırın içindedir), her LLM
çağrısının zaman aşımı kalan süreye göre kısalır; öneri
için yeterli süre kalmadıysa LLM atlanır, kurallı öneri yapılır. LLM düşerse (zaman aşımı, Ollama kapalı)
çıkarım v1 sözlük sonucuyla, öneri kurallı sıralamayla devam eder; analiz yine `done` olur.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from extraction.llm import TIMEOUT_SECONDS, ExtractionResult, Transport, extract_skills_v2, ollama_transport
from extraction.taxonomy import Lang
from matching import CvSkill, MatchResult, load_role_demand, match
from parsing import PdfError, extract_text
from pii import mask
from prompts import ModelInfo
from recommendation import Recommendation, load_candidates, recommend

log = logging.getLogger(__name__)

ErrorCode = Literal["PDF_UNREADABLE", "PDF_TOO_LARGE", "NO_TEXT_FOUND", "LLM_TIMEOUT", "INTERNAL"]
Embed = Callable[[Sequence[str]], list[list[float]]]

BUDGET_SECONDS = 165.0  # işçinin 180 sn sınırının altında; veritabanına yazma payı
MIN_LLM_SECONDS = 20.0  # bundan az süre kaldıysa LLM çağrılmaz
# Çıkarımın en fazla bekleyeceği süre: yavaş makinede (production PC, Ollama CPU'da) çıkarım bütçeyi tek başına
# yiyordu ve öneri LLM'i hiç çalışamıyordu (#155 incelemesi: çıkarım 145 sn bekleyip zaman aşımına düşüyordu).
# Böylece öneriye en az ~70 sn kalır; çıkarım bu sürede bitmezse v1 sözlük sonucu kullanılır.
EXTRACT_MAX_SECONDS = 90.0
_SAFETY_SECONDS = 5.0
MIN_CALL_SECONDS = 10.0  # çıkarımda bundan az süre kaldıysa (ör. ikinci deneme) LLM çağrılmaz

_TR_LETTERS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_TR_WORDS = frozenset({"ve", "ile", "için", "bir", "bu", "olarak", "deneyim", "eğitim", "üniversitesi", "yıl"})
_EN_WORDS = frozenset({"and", "the", "with", "for", "of", "experience", "education", "university", "years", "in"})
_WORD = re.compile(r"[^\W\d_]+")


class AnalysisError(Exception):
    """Kullanıcıya hata koduyla gösterilecek, tekrar denemenin işe yaramayacağı hata. Mesajında CV parçası yoktur."""

    def __init__(self, code: ErrorCode) -> None:
        super().__init__(code)
        self.code: ErrorCode = code


class Connection(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] = ..., /) -> Any: ...


@dataclass
class AnalysisOutput:
    result: dict[str, Any]  # sözleşme biçiminde sonuç
    stats: dict[str, Any] = field(default_factory=dict)  # loglanabilir: süreler, sayılar, LLM hata kodları


def analyze_cv(
    pdf: bytes,
    *,
    role_id: int,
    conn: Connection,
    transport_factory: Callable[[float], Transport] | None = None,
    embed: Embed | None = None,
    budget_s: float = BUDGET_SECONDS,
    clock: Callable[[], float] = time.monotonic,
) -> AnalysisOutput:
    """`transport_factory(timeout)`: Ollama istemcisi (testte sahtesi). `embed`: taksonomide olmayan adları vektöre
    çevirir (ör. `embedding.default_encoder()`, çağrılabilir nesne); None ise anlamsal eşleşme yapılmaz."""
    start = clock()
    factory = transport_factory or (lambda timeout: ollama_transport(timeout=timeout))
    stats: dict[str, Any] = {}

    def remaining() -> float:
        return budget_s - (clock() - start)

    # 1. PDF → metin
    try:
        parsed = extract_text(pdf)
    except PdfError as e:
        raise AnalysisError(e.code.value) from None
    if parsed.needs_ocr:
        # Taranmış PDF: OCR yedek akışı (T-029) gelene kadar metin yok sayılır.
        raise AnalysisError("NO_TEXT_FOUND")
    stats.update(pages=parsed.page_count, multi_column_pages=parsed.multi_column_pages)

    # 2. Maskeleme: bundan sonra ham metin kullanılmaz.
    lang = guess_lang(parsed.text)
    masked = mask(parsed.text, lang, detector=_name_detector())
    del parsed
    stats.update(lang=lang, masked={k.value: v for k, v in masked.counts.items()})

    # 3. Yetkinlik çıkarımı (v1 + LLM; LLM düşerse v1)
    t = clock()
    extraction = _extract(masked.text, lang, factory, remaining(), clock)
    del masked
    stats.update(extract_s=round(clock() - t, 1), extraction_llm_error=extraction.llm_error)

    # 4. Eşleştirme
    try:
        slug, name = _role(conn, role_id)
        role = load_role_demand(conn, slug)
    except LookupError:
        raise AnalysisError("INTERNAL") from None
    cv = [CvSkill(s.skill, s.verified) for s in extraction.skills]
    result = match(cv, role.demands, corpus_postings=role.corpus_postings, embed=embed if _has_unverified(cv) else None)

    # 5. Kaynak önerisi (LLM sadece süre kaldıysa)
    t = clock()
    rec = _recommend(conn, result, name, [s.skill for s in extraction.skills if s.verified], factory, remaining())
    stats.update(
        recommend_s=round(clock() - t, 1),
        recommendation_llm_error=rec.llm_error,
        present=len(extraction.skills),
        missing=len(result.missing),
        low_data=result.low_data,
        total_s=round(clock() - start, 1),
    )
    log.info("analiz tamam %s", {k: v for k, v in stats.items() if k != "masked"})
    return AnalysisOutput(_result(slug, name, result, extraction, rec), stats)


def guess_lang(text: str) -> Lang:
    """CV dili: Türkçe harf ve sık kelimelere göre; karar verilemezse Türkçe (hedef kitle)."""
    words = [w.casefold() for w in _WORD.findall(text[:5000])]
    tr = sum(w in _TR_WORDS for w in words) + len(_TR_LETTERS.findall(text[:5000])) / 4
    en = sum(w in _EN_WORDS for w in words)
    return "en" if en > tr * 1.5 and en >= 5 else "tr"


def prompt_version(extraction: ModelInfo, recommendation: ModelInfo) -> str:
    """Analizdeki iki prompt sürümü tek alanda: "skill_extraction:v1,recommendation:v1".

    Sözleşmede tek `model.prompt_version` alanı var (`analyses.prompt_version` varchar(60)); karar önerisi #38.
    """
    return f"skill_extraction:{extraction['prompt_version']},recommendation:{recommendation['prompt_version']}"


def _extract(
    text: str, lang: Lang, factory: Callable[[float], Transport], left: float, clock: Callable[[], float]
) -> ExtractionResult:
    if left < MIN_LLM_SECONDS:
        return extract_skills_v2(text, lang, transport=_timeout_transport)
    end = clock() + min(TIMEOUT_SECONDS, EXTRACT_MAX_SECONDS, left - MIN_LLM_SECONDS)

    def send(body: dict[str, Any]) -> dict[str, Any]:
        # Her çağrı (bozuk yanıttaki ikinci deneme dahil) sadece çıkarımın bitiş zamanına kalan süreyi bekler (#158).
        timeout = end - clock()
        if timeout < MIN_CALL_SECONDS:
            return _timeout_transport(body)
        return factory(timeout)(body)

    return extract_skills_v2(text, lang, transport=send)


def _recommend(
    conn: Connection,
    result: MatchResult,
    role_name: str,
    present: list[str],
    factory: Callable[[float], Transport],
    left: float,
) -> Recommendation:
    candidates = load_candidates(conn, [m.skill for m in result.missing])
    use_llm = left - _SAFETY_SECONDS >= MIN_LLM_SECONDS
    return recommend(
        result.missing,
        candidates,
        role_name=role_name,
        postings_analyzed=result.postings_analyzed,
        present=present,
        transport=factory(left - _SAFETY_SECONDS) if use_llm else None,
        use_llm=use_llm,
    )


def _result(
    slug: str, name: str, result: MatchResult, extraction: ExtractionResult, rec: Recommendation
) -> dict[str, Any]:
    return {
        "target_role": {"slug": slug, "name": name},
        "postings_analyzed": result.postings_analyzed,
        "match_score": result.match_score,
        "present_skills": extraction.present_skills(),
        "missing_skills": rec.missing_skills(),
        "model": {
            "name": extraction.model["name"],
            "prompt_version": prompt_version(extraction.model, rec.model),
        },
    }


def _role(conn: Connection, role_id: int) -> tuple[str, str]:
    row = conn.execute("SELECT slug, name FROM roles WHERE id = %s", (role_id,)).fetchone()
    if row is None:
        raise LookupError(role_id)
    return str(row[0]), str(row[1])


def _has_unverified(cv: Sequence[CvSkill]) -> bool:
    return any(not s.verified for s in cv)


def _timeout_transport(body: dict[str, Any]) -> dict[str, Any]:
    from extraction.llm import LlmError

    raise LlmError("LLM_TIMEOUT")


def _name_detector() -> Any:
    from pii.ner import default_detector

    return default_detector()
