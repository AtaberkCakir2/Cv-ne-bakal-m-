"""Katalog endpoint'leri (T-048), gerçek PostgreSQL ile. role_skill_stats materialized view'u testte yenilenir."""

import hashlib
from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import LangCode, ResourceLevel, ResourceProvider, SkillCategory, SkillImportance, SourceType
from app.db.models import JobPosting, JobPostingSkill, JobSource, Resource, Role, Skill
from tests.auth.test_auth_flow import API


@pytest.fixture
def client(auth_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(auth_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def sessions(db_sessionmaker: sessionmaker[Session]) -> sessionmaker[Session]:
    with db_sessionmaker() as session:
        session.execute(text("TRUNCATE roles, skills, resources, job_sources RESTART IDENTITY CASCADE"))
        session.commit()
    return db_sessionmaker


def add_skill(session: Session, name: str, active: bool = True) -> Skill:
    row = Skill(canonical_name=name, slug=name.lower(), category=SkillCategory.DIL, synonyms=[], is_active=active)
    session.add(row)
    session.flush()
    return row


def add_posting(
    session: Session, source: JobSource, role: Role, skills: list[Skill], posted_at: date | None = None
) -> None:
    key = f"{role.slug}-{len(skills)}-{[s.slug for s in skills]}-{posted_at}-{id(skills)}"
    posting = JobPosting(
        source_id=source.id,
        external_id=key,
        title_raw="İlan",
        role_id=role.id,
        description_clean="sahte ilan",
        language=LangCode.TR,
        posted_at=posted_at,
        content_hash=hashlib.sha256(key.encode()).hexdigest(),
    )
    session.add(posting)
    session.flush()
    session.add_all(
        [JobPostingSkill(posting_id=posting.id, skill_id=s.id, importance=SkillImportance.REQUIRED) for s in skills]
    )


def test_roles_lists_active_roles_by_name(client: TestClient, sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        session.add_all(
            [
                Role(name="Veri Analisti", slug="veri-analisti", synonyms=[], description="Veri"),
                Role(name="Backend Developer", slug="backend-developer", synonyms=[]),
                Role(name="Eski", slug="eski", synonyms=[], is_active=False),
            ]
        )
        session.commit()

    response = client.get(f"{API}/roles")

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public")
    assert [(r["slug"], r["description"]) for r in response.json()] == [
        ("backend-developer", None),
        ("veri-analisti", "Veri"),
    ]
    assert all(isinstance(r["id"], int) for r in response.json())


def test_role_skills_ranks_by_demand(client: TestClient, sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        role = Role(name="Backend Developer", slug="backend-developer", synonyms=[])
        source = JobSource(name="test", type=SourceType.API)
        session.add_all([role, source])
        session.flush()
        python, sql, docker = add_skill(session, "Python"), add_skill(session, "SQL"), add_skill(session, "Docker")
        hidden = add_skill(session, "Eski", active=False)
        add_posting(session, source, role, [python, sql, hidden])
        add_posting(session, source, role, [python, docker])
        add_posting(session, source, role, [python, sql])
        add_posting(session, source, role, [docker], posted_at=date.today() - timedelta(days=400))  # 6 aydan eski
        session.commit()
        session.execute(text("REFRESH MATERIALIZED VIEW role_skill_stats"))
        session.commit()

    response = client.get(f"{API}/roles/backend-developer/skills")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == {"slug": "backend-developer", "name": "Backend Developer"}
    assert body["total_postings"] == 3
    assert body["computed_at"] is not None
    assert [(s["skill"], s["posting_count"], s["demand_ratio"]) for s in body["skills"]] == [
        ("Python", 3, 1.0),
        ("SQL", 2, 0.6667),
        ("Docker", 1, 0.3333),
    ]
    assert body["skills"][0] == {
        "skill": "Python",
        "slug": "python",
        "category": "dil",
        "demand_ratio": 1.0,
        "posting_count": 3,
    }
    limited = client.get(f"{API}/roles/backend-developer/skills", params={"limit": 1}).json()
    assert [s["skill"] for s in limited["skills"]] == ["Python"]


def test_role_without_postings_has_empty_skills(client: TestClient, sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        session.add(Role(name="Yeni", slug="yeni", synonyms=[]))
        session.commit()

    body = client.get(f"{API}/roles/yeni/skills").json()

    assert body == {"role": {"slug": "yeni", "name": "Yeni"}, "total_postings": 0, "computed_at": None, "skills": []}


def test_unknown_or_inactive_role_is_404(client: TestClient, sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        session.add(Role(name="Eski", slug="eski", synonyms=[], is_active=False))
        session.commit()

    for slug in ("yok", "eski"):
        response = client.get(f"{API}/roles/{slug}/skills")
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/problem+json")


def test_skill_resources_lists_alive_ones_free_first(client: TestClient, sessions: sessionmaker[Session]) -> None:
    def resource(skill: Skill, title: str, **values: object) -> Resource:
        fields: dict[str, object] = {
            "provider": ResourceProvider.DOCS,
            "language": LangCode.EN,
            "level": ResourceLevel.BEGINNER,
            "is_free": True,
        }
        fields.update(values)
        return Resource(skill_id=skill.id, title=title, url=f"https://example.com/{title}", **fields)

    with sessions() as session:
        docker, other = add_skill(session, "Docker"), add_skill(session, "SQL")
        session.add_all(
            [
                resource(docker, "ucretli", is_free=False),
                resource(docker, "ileri", level=ResourceLevel.ADVANCED),
                resource(docker, "baslangic", language=LangCode.TR, duration_min=30),
                resource(docker, "kirik", is_alive=False),
                resource(other, "baska"),
            ]
        )
        session.commit()

    response = client.get(f"{API}/skills/docker/resources")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["skill"] == {"slug": "docker", "name": "Docker"}
    assert [r["title"] for r in body["resources"]] == ["baslangic", "ileri", "ucretli"]
    assert body["resources"][0]["duration_min"] == 30
    assert "duration_min" not in body["resources"][1]  # null değil, hiç yok (analiz sonucuyla aynı şekil)
    turkish = client.get(f"{API}/skills/docker/resources", params={"language": "tr"}).json()
    assert [r["title"] for r in turkish["resources"]] == ["baslangic"]
    assert client.get(f"{API}/skills/docker/resources", params={"language": "de"}).status_code == 422
    assert client.get(f"{API}/skills/yok/resources").status_code == 404


def test_inactive_skill_resources_is_404(client: TestClient, sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        add_skill(session, "Eski", active=False)
        session.commit()

    assert client.get(f"{API}/skills/eski/resources").status_code == 404
