"""Eşleştirme (T-042): CV yetkinlikleri ↔ pozisyon talebi → uyum skoru ve eksik yetkinlikler.

from matching import CvSkill, load_role_demand, match
role = load_role_demand(conn, "backend-developer")
result = match([CvSkill("Python"), CvSkill("Express", verified=False)], role.demands,
               corpus_postings=role.corpus_postings, embed=embedding.default_encoder())
result.match_score, result.missing_skills()
"""

from matching.db import RoleDemand, load_role_demand, parse_vector
from matching.score import (
    MIN_DEMAND_RATIO,
    MIN_POSTINGS,
    SIMILARITY_THRESHOLD,
    CvSkill,
    Demand,
    Match,
    MatchResult,
    Missing,
    idf,
    match,
)

__all__ = [
    "MIN_DEMAND_RATIO",
    "MIN_POSTINGS",
    "SIMILARITY_THRESHOLD",
    "CvSkill",
    "Demand",
    "Match",
    "MatchResult",
    "Missing",
    "RoleDemand",
    "idf",
    "load_role_demand",
    "match",
    "parse_vector",
]
