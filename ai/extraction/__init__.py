"""CV metninden yetkinlik çıkarımı. v1 (T-031): `extract_skills(text, lang)`, sözlük + kural, LLM'siz yedek yol.

v2 (T-032) burada içe aktarılmaz: `from extraction.llm import extract_skills_v2`. Scraper bu paketi sadece
ortak yetkinlik eşleyicisi için kullanıyor; imajında LLM kodu ve `prompts` yok (#78).
"""

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
