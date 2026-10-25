"""ESCO eşlemesi; uydurma, küçük bir skills_en.csv ile (gerçek dosyadaki sütun adları ve örnek kalıplar)."""

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


def test_only_preferred_labels_match(tmp_path: Path) -> None:
    rows = [
        "KnowledgeSkillCompetence,http://e/py,knowledge,cross-sector,Python (computer programming),,released\n",
        "KnowledgeSkillCompetence,http://e/jenkins,knowledge,cross-sector,"
        "Jenkins (tools for software configuration management),,released\n",
        "KnowledgeSkillCompetence,http://e/sqlserver,knowledge,cross-sector,SQL Server,,released\n",
        # Gerçek ESCO'daki gibi geniş kavram: alternatif adları bash, tensorflow içeriyor → kullanılmamalı.
        'KnowledgeSkillCompetence,http://e/prog,knowledge,cross-sector,computer programming,"bash\nOCaml",released\n',
        'KnowledgeSkillCompetence,http://e/cv,knowledge,cross-sector,computer vision,"tensorflow\nkeras",released\n',
        "KnowledgeSkillCompetence,http://e/go1,knowledge,cross-sector,Go,,released\n",
        "KnowledgeSkillCompetence,http://e/go2,knowledge,cross-sector,Go (board game),,released\n",
        "KnowledgeSkillCompetence,http://e/sparkjava,knowledge,cross-sector,SPARK,,released\n",
        "KnowledgeSkillCompetence,http://e/old,knowledge,cross-sector,Rust,,obsolete\n",
    ]
    index = load_esco_index(esco_csv(tmp_path, rows))
    skills = [
        skill("python", "Python"),
        skill("jenkins", "Jenkins"),  # parantezli not yok sayılır
        skill("mssql", "Microsoft SQL Server", "sql server"),  # eş anlamlı tercih edilen adla eşleşir
        skill("bash", "Bash"),
        skill("tensorflow", "TensorFlow"),
        skill("go", "Go", "golang"),  # iki kavrama gidiyor → belirsiz
        skill("spark", "Apache Spark", "spark"),  # aynı adlı başka kavram (HOMONYMS)
        skill("rust", "Rust"),  # sadece kullanımdan kalkmış kavram var
        skill("cobol", "COBOL", uri="http://manual/cobol"),  # elle girilen korunur
    ]
    uris = {s.slug: s.esco_uri for s in map_skills(skills, index)}
    assert uris == {
        "python": "http://e/py",
        "jenkins": "http://e/jenkins",
        "mssql": "http://e/sqlserver",
        "bash": None,
        "tensorflow": None,
        "go": None,
        "spark": None,
        "rust": None,
        "cobol": "http://manual/cobol",
    }


def test_write_skills_round_trips(tmp_path: Path) -> None:
    out = tmp_path / "skills.csv"
    original = load_skills()
    write_skills(original, out)
    assert load_skills(out) == original
