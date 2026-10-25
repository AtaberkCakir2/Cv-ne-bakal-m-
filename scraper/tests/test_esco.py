"""ESCO eşlemesi; uydurma, küçük bir skills_en.csv ile (gerçek dosyadaki sütun adları)."""

from pathlib import Path

from collector.esco import load_esco_index, map_skills, write_skills
from collector.taxonomy import SkillRow, load_skills

ESCO_HEADER = "conceptType,conceptUri,skillType,reuseLevel,preferredLabel,altLabels,status\n"


def esco_csv(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "skills_en.csv"
    path.write_text(ESCO_HEADER + "".join(rows), encoding="utf-8")
    return path


def skill(slug: str, name: str, *synonyms: str, uri: str | None = None) -> SkillRow:
    return SkillRow(canonical_name=name, slug=slug, category="dil", synonyms=synonyms, esco_uri=uri)


def test_exact_matches_only_and_ambiguous_terms_are_skipped(tmp_path: Path) -> None:
    rows = [
        'KnowledgeSkillCompetence,http://e/py,knowledge,cross-sector,Python (computer programming),"Python",released\n',
        'KnowledgeSkillCompetence,http://e/js,knowledge,cross-sector,JavaScript,"ECMAScript\nJS",released\n',
        "KnowledgeSkillCompetence,http://e/go1,knowledge,cross-sector,Go,,released\n",
        "KnowledgeSkillCompetence,http://e/go2,knowledge,cross-sector,go (board game),go,released\n",
        "KnowledgeSkillCompetence,http://e/old,knowledge,cross-sector,Rust,,obsolete\n",
    ]
    index = load_esco_index(esco_csv(tmp_path, rows))
    skills = [
        skill("python", "Python"),
        skill("javascript", "JavaScript", "js"),
        skill("go", "Go", "golang"),  # "go" iki kavrama gidiyor → belirsiz, atlanır
        skill("rust", "Rust"),  # sadece kullanımdan kalkmış kavram var
        skill("cobol", "COBOL", uri="http://manual/cobol"),  # elle girilen korunur
        skill("react", "React"),  # ESCO'da yok
    ]
    uris = {s.slug: s.esco_uri for s in map_skills(skills, index)}
    assert uris == {
        "python": "http://e/py",
        "javascript": "http://e/js",
        "go": None,
        "rust": None,
        "cobol": "http://manual/cobol",
        "react": None,
    }


def test_write_skills_round_trips(tmp_path: Path) -> None:
    out = tmp_path / "skills.csv"
    original = load_skills()
    write_skills(original, out)
    assert load_skills(out) == original
