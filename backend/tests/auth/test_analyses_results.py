"""Analiz listesi, sonuç ayrıntısı ve silme (T-048), gerçek PostgreSQL ile. Kullanıcı sadece kendi analizini görür."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import (
    AnalysisErrorCode,
    AnalysisStatus,
    LangCode,
    ResourceLevel,
    ResourceProvider,
    SkillCategory,
    SkillKind,
    SkillLevel,
)
from app.db.models import (
    Analysis,
    AnalysisRecommendation,
    AnalysisSkill,
    AnalysisUnverifiedSkill,
    Resource,
    Role,
    Skill,
)
from tests.auth.test_auth_flow import API, bearer, login, register

URL = f"{API}/analyses"


@pytest.fixture
def client(auth_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(auth_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def sessions(db_sessionmaker: sessionmaker[Session]) -> sessionmaker[Session]:
    with db_sessionmaker() as session:
        session.execute(text("TRUNCATE roles, skills, resources RESTART IDENTITY CASCADE"))
        session.commit()
    return db_sessionmaker


@pytest.fixture
def role(sessions: sessionmaker[Session]) -> int:
    with sessions() as session:
        row = Role(name="Backend Developer", slug="backend-developer", synonyms=[])
        session.add(row)
        session.commit()
        return row.id


def user(client: TestClient, email: str) -> tuple[uuid.UUID, dict[str, str]]:
    user_id = uuid.UUID(register(client, email))
    return user_id, bearer(login(client, email)["access_token"])


def add_analysis(
    sessions: sessionmaker[Session],
    user_id: uuid.UUID,
    role_id: int,
    status: AnalysisStatus = AnalysisStatus.DONE,
    created_at: datetime | None = None,
    **values: object,
) -> uuid.UUID:
    with sessions() as session:
        row = Analysis(user_id=user_id, target_role_id=role_id, status=status, cv_sha256="0" * 64, cv_pages=1, **values)
        if created_at is not None:
            row.created_at = created_at
        session.add(row)
        session.commit()
        return row.id


def skill(session: Session, name: str) -> Skill:
    row = Skill(canonical_name=name, slug=name.lower(), category=SkillCategory.DIL, synonyms=[])
    session.add(row)
    session.flush()
    return row


def test_list_shows_only_own_analyses_newest_first(
    client: TestClient, sessions: sessionmaker[Session], role: int
) -> None:
    me, headers = user(client, "liste@example.com")
    other, _ = user(client, "baska@example.com")
    now = datetime.now(UTC)
    old = add_analysis(sessions, me, role, created_at=now - timedelta(days=2), match_score=Decimal("40.00"))
    new = add_analysis(sessions, me, role, created_at=now - timedelta(minutes=1))
    add_analysis(sessions, other, role)

    response = client.get(URL, headers=headers)

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["total"] == 2
    assert [item["analysis_id"] for item in body["items"]] == [str(new), str(old)]
    assert body["items"][1]["match_score"] == 40.0
    assert "match_score" not in body["items"][0]  # null değil, hiç yok (sözleşme)
    assert body["items"][0]["target_role"] == {"slug": "backend-developer", "name": "Backend Developer"}


def test_list_paginates(client: TestClient, sessions: sessionmaker[Session], role: int) -> None:
    me, headers = user(client, "sayfa@example.com")
    now = datetime.now(UTC)
    ids = [add_analysis(sessions, me, role, created_at=now - timedelta(minutes=i)) for i in range(3)]

    body = client.get(URL, headers=headers, params={"limit": 2, "offset": 1}).json()

    assert body["total"] == 3
    assert [item["analysis_id"] for item in body["items"]] == [str(ids[1]), str(ids[2])]
    assert client.get(URL, headers=headers, params={"limit": 101}).status_code == 422


def test_list_fails_stale_analyses(client: TestClient, sessions: sessionmaker[Session], role: int) -> None:
    me, headers = user(client, "askida@example.com")
    stale = add_analysis(
        sessions, me, role, status=AnalysisStatus.PROCESSING, created_at=datetime.now(UTC) - timedelta(hours=2)
    )
    fresh = add_analysis(sessions, me, role, status=AnalysisStatus.QUEUED)

    items = {i["analysis_id"]: i for i in client.get(URL, headers=headers).json()["items"]}

    assert items[str(stale)]["status"] == "failed"
    assert items[str(stale)]["error"]["code"] == "INTERNAL"
    assert items[str(fresh)]["status"] == "queued"
    with sessions() as session:
        saved = session.get(Analysis, stale)
        assert saved is not None and saved.completed_at is not None


def test_list_needs_login(client: TestClient) -> None:
    assert client.get(URL).status_code == 401


def test_result_has_skills_and_recommended_resources(
    client: TestClient, sessions: sessionmaker[Session], role: int
) -> None:
    me, headers = user(client, "sonuc@example.com")
    analysis_id = add_analysis(
        sessions,
        me,
        role,
        match_score=Decimal("62.50"),
        postings_analyzed=150,
        model_name="llama3.1:8b",
        prompt_version="v1",
        completed_at=datetime.now(UTC),
    )
    with sessions() as session:
        python, docker, sql, k8s = (skill(session, n) for n in ("Python", "Docker", "SQL", "Kubernetes"))
        video = Resource(
            skill_id=docker.id,
            title="Docker'a giriş",
            url="https://example.com/docker",
            provider=ResourceProvider.YOUTUBE,
            language=LangCode.TR,
            level=ResourceLevel.BEGINNER,
            duration_min=45,
            is_free=True,
        )
        course = Resource(
            skill_id=docker.id,
            title="Docker kursu",
            url="https://example.com/docker-kurs",
            provider=ResourceProvider.UDEMY,
            language=LangCode.EN,
            level=ResourceLevel.INTERMEDIATE,
            is_free=False,
        )
        dead = Resource(
            skill_id=docker.id,
            title="Kırık link",
            url="https://example.com/kirik",
            provider=ResourceProvider.BLOG,
            language=LangCode.TR,
            level=ResourceLevel.BEGINNER,
            is_free=True,
            is_alive=False,
        )
        session.add_all([video, course, dead])
        session.flush()
        session.add(AnalysisRecommendation(analysis_id=analysis_id, skill_id=docker.id, resource_id=dead.id, rank=3))
        session.add_all(
            [
                AnalysisSkill(
                    analysis_id=analysis_id,
                    skill_id=python.id,
                    kind=SkillKind.PRESENT,
                    level=SkillLevel.ADVANCED,
                    confidence=Decimal("0.90"),
                ),
                AnalysisSkill(
                    analysis_id=analysis_id,
                    skill_id=docker.id,
                    kind=SkillKind.MISSING,
                    demand_ratio=Decimal("0.7500"),
                    priority=1,
                ),
                AnalysisSkill(  # öncelik yok: sıra numarası verilir
                    analysis_id=analysis_id, skill_id=k8s.id, kind=SkillKind.MISSING, demand_ratio=Decimal("0.3000")
                ),
                AnalysisSkill(
                    analysis_id=analysis_id,
                    skill_id=sql.id,
                    kind=SkillKind.MISSING,
                    demand_ratio=Decimal("0.5000"),
                    priority=5,  # AI'ın numarasında boşluk: yanıtta yine sıra numarası (2)
                ),
                AnalysisUnverifiedSkill(
                    analysis_id=analysis_id, name="Figma", level=SkillLevel.UNKNOWN, confidence=Decimal("0.40")
                ),
                AnalysisRecommendation(
                    analysis_id=analysis_id, skill_id=docker.id, resource_id=course.id, rank=2, reason_text=None
                ),
                AnalysisRecommendation(
                    analysis_id=analysis_id,
                    skill_id=docker.id,
                    resource_id=video.id,
                    rank=1,
                    reason_text="Kısa ve Türkçe.",
                ),
            ]
        )
        session.commit()
        video_id, course_id = video.id, course.id

    response = client.get(f"{URL}/{analysis_id}", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["match_score"] == 62.5
    assert body["postings_analyzed"] == 150
    assert body["present_skills"] == [
        {"skill": "Python", "level": "advanced", "confidence": 0.9, "verified": True},
        {"skill": "Figma", "level": "unknown", "confidence": 0.4, "verified": False},
    ]
    assert [(m["skill"], m["priority"], m["demand_ratio"]) for m in body["missing_skills"]] == [
        ("Docker", 1, 0.75),
        ("SQL", 2, 0.5),
        ("Kubernetes", 3, 0.3),
    ]
    docker_resources = body["missing_skills"][0]["resources"]
    assert docker_resources == [
        {
            "resource_id": video_id,
            "title": "Docker'a giriş",
            "url": "https://example.com/docker",
            "provider": "youtube",
            "language": "tr",
            "level": "beginner",
            "duration_min": 45,
            "is_free": True,
            "reason": "Kısa ve Türkçe.",
        },
        {
            "resource_id": course_id,
            "title": "Docker kursu",
            "url": "https://example.com/docker-kurs",
            "provider": "udemy",
            "language": "en",
            "level": "intermediate",
            "is_free": False,
        },
    ]
    assert body["missing_skills"][1]["resources"] == []


def test_unfinished_result_has_no_optional_fields(
    client: TestClient, sessions: sessionmaker[Session], role: int
) -> None:
    me, headers = user(client, "bekliyor@example.com")
    analysis_id = add_analysis(sessions, me, role, status=AnalysisStatus.PROCESSING)

    body = client.get(f"{URL}/{analysis_id}", headers=headers).json()

    assert body["status"] == "processing"
    assert body["present_skills"] == [] and body["missing_skills"] == []
    assert {"match_score", "postings_analyzed", "model"}.isdisjoint(body)


def test_stale_result_is_failed(client: TestClient, sessions: sessionmaker[Session], role: int) -> None:
    me, headers = user(client, "eski@example.com")
    created = datetime.now(UTC) - timedelta(hours=2)
    analysis_id = add_analysis(sessions, me, role, status=AnalysisStatus.QUEUED, created_at=created)

    body = client.get(f"{URL}/{analysis_id}", headers=headers).json()

    assert body["status"] == "failed"
    assert body["error"]["code"] == "INTERNAL"
    with sessions() as session:
        saved = session.get(Analysis, analysis_id)
        assert saved is not None and saved.status is AnalysisStatus.FAILED


def test_result_of_another_user_is_404(client: TestClient, sessions: sessionmaker[Session], role: int) -> None:
    other, _ = user(client, "sahip@example.com")
    _, headers = user(client, "saldirgan@example.com")
    analysis_id = add_analysis(sessions, other, role)

    for response in (
        client.get(f"{URL}/{analysis_id}", headers=headers),
        client.delete(f"{URL}/{analysis_id}", headers=headers),
    ):
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/problem+json")
    assert client.get(URL, headers=headers).json()["total"] == 0
    with sessions() as session:
        saved = session.get(Analysis, analysis_id)
        assert saved is not None and saved.deleted_at is None


def test_delete_hides_the_analysis_and_keeps_it_for_purge(
    client: TestClient, sessions: sessionmaker[Session], role: int
) -> None:
    me, headers = user(client, "sil@example.com")
    analysis_id = add_analysis(sessions, me, role, status=AnalysisStatus.FAILED, error_code=AnalysisErrorCode.INTERNAL)

    response = client.delete(f"{URL}/{analysis_id}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{URL}/{analysis_id}", headers=headers).status_code == 404
    assert client.get(URL, headers=headers).json() == {"items": [], "total": 0}
    assert client.delete(f"{URL}/{analysis_id}", headers=headers).status_code == 404
    with sessions() as session:
        saved = session.get(Analysis, analysis_id)
        assert saved is not None and saved.deleted_at is not None  # 30 gün sonra purge_deleted_users.py siler


def test_delete_needs_login(client: TestClient) -> None:
    assert client.delete(f"{URL}/{uuid.uuid4()}").status_code == 401
