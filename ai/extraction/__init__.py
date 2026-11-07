"""CV metninden yetkinlik çıkarımı (T-031 v1: sözlük + kural). Kullanım: `extract_skills(text, lang)`."""

from extraction.extract import ExtractedSkill, extract_skills, to_present_skills
from extraction.taxonomy import Matcher, Skill, default_matcher, load_skills

__all__ = [
    "ExtractedSkill",
    "Matcher",
    "Skill",
    "default_matcher",
    "extract_skills",
    "load_skills",
    "to_present_skills",
]
