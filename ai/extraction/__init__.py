"""CV metninden yetkinlik çıkarımı. v1 (T-031): `extract_skills(text, lang)`, sözlük + kural, LLM'siz yedek yol.
v2 (T-032): `extract_skills_v2(text, lang)`, yerel LLM sonucu v1 ile birleştirilir."""

from extraction.extract import ExtractedSkill, extract_skills, to_present_skills
from extraction.llm import ExtractionResult, LlmError, MergedSkill, extract_skills_v2
from extraction.taxonomy import Matcher, Skill, default_matcher, load_skills

__all__ = [
    "ExtractedSkill",
    "ExtractionResult",
    "LlmError",
    "Matcher",
    "MergedSkill",
    "Skill",
    "default_matcher",
    "extract_skills",
    "extract_skills_v2",
    "load_skills",
    "to_present_skills",
]
