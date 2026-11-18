"""CV yetkinlikleri ↔ pozisyon talebi eşleştirmesi (T-042).

Girdi: CV yetkinlikleri (extraction v1/v2, `present_skills`) ve pozisyonun talep istatistikleri (`role_skill_stats`).
Çıktı: 0-100 uyum skoru ve talep oranına göre sıralı eksik yetkinlikler
(contracts/analysis_result.schema.json: match_score, postings_analyzed, missing_skills).

Talep ağırlığı = ilan frekansı (pozisyondaki talep oranı) × IDF. IDF tüm pozisyonların ilanları üzerinden hesaplanır:
her ilanda istenen yetkinlik (Git, İngilizce) skoru az, pozisyona özgü yetkinlik çok etkiler.
    ağırlık(s) = talep_oranı(pozisyon, s) × (ln((1 + N) / (1 + df(s))) + 1)
N: istatistikteki toplam ilan, df(s): s'yi isteyen ilan (scikit-learn'deki yumuşatılmış IDF; hiçbir ağırlık 0 olmaz).

Eşleşme:
- Taksonomideki yetkinlik (`verified`) sadece adıyla eşleşir. İki farklı taksonomi yetkinliği vektörle eşlenmez:
  vektör benzerliği Redux–Redis, Vite–Vitest gibi farklı yetkinlikleri de çok yakın buluyor (ai/README.md, T-041).
- Taksonomide olmayan ad (`verified=False`, ör. "Express") kosinüs benzerliğiyle pozisyondaki en yakın yetkinliğe
  bağlanır; benzerlik eşiğin altındaysa eşleşmez. Eşleşme kısmi sayılır: katkı = ağırlık × benzerlik.
- Eşik ayarlanabilir; varsayılan 0,90 multilingual-e5-small için ölçüldü (0,80 bu modelde neredeyse her şeyi eşler).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

Vector = Sequence[float]
Embed = Callable[[Sequence[str]], list[list[float]]]

SIMILARITY_THRESHOLD = 0.90
# Pozisyonun uzun kuyruğu (birkaç ilanda geçen yetkinlik) skoru sulandırmasın.
MIN_DEMAND_RATIO = 0.05
MIN_POSTINGS = 50  # karar #23; scraper/etl/stats.py MIN_POSTINGS ile aynı olmalı (test denetliyor)


@dataclass(frozen=True)
class Demand:
    """Pozisyondaki bir yetkinliğin talebi (role_skill_stats satırı + IDF için genel ilan sayısı)."""

    skill: str  # taksonomideki standart ad
    posting_count: int
    total_postings: int
    demand_ratio: float
    df: int  # tüm pozisyonlarda bu yetkinliği isteyen ilan sayısı
    vector: Vector | None = None  # skills.embedding (T-041); yoksa anlamsal eşleşme yapılmaz


@dataclass(frozen=True)
class CvSkill:
    skill: str
    verified: bool = True


@dataclass(frozen=True)
class Match:
    demand: str  # pozisyondaki yetkinlik
    by: str  # CV'deki ad
    similarity: float  # tam eşleşmede 1.0


@dataclass(frozen=True)
class Missing:
    skill: str
    demand_ratio: float
    priority: int
    weight: float


@dataclass
class MatchResult:
    match_score: float
    postings_analyzed: int
    low_data: bool  # karar #23: ilan sayısı az, oranlar yanıltıcı olabilir
    matched: list[Match] = field(default_factory=list)
    missing: list[Missing] = field(default_factory=list)

    def missing_skills(self) -> list[dict[str, object]]:
        """contracts → missing_skills; `resources` T-043'te doldurulur."""
        return [
            {"skill": m.skill, "demand_ratio": round(m.demand_ratio, 4), "priority": m.priority, "resources": []}
            for m in self.missing
        ]


def idf(df: int, total: int) -> float:
    return math.log((1 + total) / (1 + df)) + 1


def match(
    cv_skills: Sequence[CvSkill],
    demands: Sequence[Demand],
    *,
    corpus_postings: int,
    embed: Embed | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
    min_demand_ratio: float = MIN_DEMAND_RATIO,
) -> MatchResult:
    """`corpus_postings`: IDF'teki N (istatistikteki tüm pozisyonların toplam ilanı).
    `embed`: taksonomide olmayan CV adlarını vektöre çevirir (embedding.default_encoder()); None: anlamsal eşleşme yok.
    """
    if not 0 < threshold <= 1:
        raise ValueError("eşik 0 ile 1 arasında olmalı")
    considered = [d for d in demands if d.demand_ratio >= min_demand_ratio]
    total = max((d.total_postings for d in demands), default=0)
    weights = {d.skill: d.demand_ratio * idf(d.df, corpus_postings) for d in considered}

    credit: dict[str, Match] = {}
    verified = {_key(s.skill): s.skill for s in cv_skills if s.verified}
    for d in considered:
        if _key(d.skill) in verified:
            credit[d.skill] = Match(d.skill, verified[_key(d.skill)], 1.0)

    unverified = list(dict.fromkeys(s.skill for s in cv_skills if not s.verified))
    open_demands = [d for d in considered if d.skill not in credit and d.vector is not None]
    if embed is not None and unverified and open_demands:
        for name, vec in zip(unverified, embed(unverified), strict=True):
            best = max(open_demands, key=lambda d: _cosine(vec, d.vector or ()))
            sim = _cosine(vec, best.vector or ())
            current = credit.get(best.skill)
            if sim >= threshold and (current is None or sim > current.similarity):
                credit[best.skill] = Match(best.skill, name, sim)

    total_weight = sum(weights.values())
    gained = sum(weights[s] * m.similarity for s, m in credit.items())
    score = round(100 * gained / total_weight, 1) if total_weight else 0.0

    # Kriter: eksikler talep oranına göre; eşitlikte ağırlık (pozisyona özgü olan önce), sonra ad.
    missing_demands = sorted(
        (d for d in considered if d.skill not in credit), key=lambda d: (-d.demand_ratio, -weights[d.skill], d.skill)
    )
    missing = [
        Missing(d.skill, d.demand_ratio, i, round(weights[d.skill], 4)) for i, d in enumerate(missing_demands, start=1)
    ]
    matched = sorted(credit.values(), key=lambda m: -weights[m.demand])
    return MatchResult(score, total, total < MIN_POSTINGS, matched, missing)


def _key(name: str) -> str:
    return " ".join(name.casefold().split())


def _cosine(a: Vector, b: Vector) -> float:
    # Vektörler normalize (T-041); yine de güvenli olsun diye bölüyoruz.
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
