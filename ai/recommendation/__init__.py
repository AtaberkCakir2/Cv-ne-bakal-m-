"""Kaynak önerisi (T-043): eksik yetkinlik → veritabanındaki aday kaynaklar → LLM seçer ve Türkçe gerekçe yazar.

from recommendation import load_candidates, recommend
candidates = load_candidates(conn, [m.skill for m in result.missing])
rec = recommend(result.missing, candidates, role_name=role.name, postings_analyzed=result.postings_analyzed)
rec.missing_skills()
"""

from recommendation.db import load_candidates
from recommendation.recommend import (
    LLM_SKILLS,
    PER_SKILL,
    Pick,
    Recommendation,
    Resource,
    percent_suffix,
    rank_key,
    recommend,
    rule_reason,
    stat_sentence,
)

__all__ = [
    "LLM_SKILLS",
    "PER_SKILL",
    "Pick",
    "Recommendation",
    "Resource",
    "load_candidates",
    "percent_suffix",
    "rank_key",
    "recommend",
    "rule_reason",
    "stat_sentence",
]
