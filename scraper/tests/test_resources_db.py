"""Kaynak havuzu: yazma, kaldığı yerden devam, link kontrolü. Sadece TEST_DATABASE_URL verilince çalışır."""

import argparse
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from app.db.enums import LangCode, ResourceLevel, ResourceProvider
from app.db.models import Resource, Skill
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session

from collector import resources
from collector.http import PoliteClient
from collector.taxonomy_rows import SkillRow

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
REPO = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO / "backend" / "app" / "db" / "alembic.ini"
SKILLS = [SkillRow("Docker", "docker", "devops", (), None)]

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL verilmedi")


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    assert TEST_DATABASE_URL
    cfg = Config(str(ALEMBIC_INI))
    cfg.cmd_opts = argparse.Namespace(x=[f"url={TEST_DATABASE_URL}"])
    command.upgrade(cfg, "head")
    eng = create_engine(TEST_DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as conn:
        trans = conn.begin()
        s = Session(bind=conn, join_transaction_mode="create_savepoint")
        s.add(Skill(canonical_name="Docker", slug="docker", category="devops"))
        s.flush()
        yield s
        s.close()
        trans.rollback()


def row(url: str, provider: ResourceProvider = ResourceProvider.DOCS) -> dict[str, Any]:
    return {
        "slug": "docker",
        "title": "Docker belgeleri",
        "url": url,
        "provider": provider,
        "language": LangCode.EN,
        "level": ResourceLevel.BEGINNER,
        "duration_min": None,
        "is_free": True,
    }


def api(request: httpx.Request, ids: list[str]) -> httpx.Response:
    if request.url.path.endswith("/search"):
        return httpx.Response(200, json={"items": [{"id": {"videoId": i}} for i in ids]})
    wanted = request.url.params["id"].split(",")
    return httpx.Response(
        200,
        json={
            "items": [
                {
                    "id": i,
                    "snippet": {"title": "Docker Eğitimi", "defaultAudioLanguage": "tr"},
                    "contentDetails": {"duration": "PT1H"},
                    "statistics": {"viewCount": "50000"},
                }
                for i in wanted
                if i in ids
            ]
        },
    )


def client(handler: Any) -> PoliteClient:
    return PoliteClient(delay_s=0, transport=httpx.MockTransport(handler), max_retries=0)


def test_seed_is_idempotent_and_rejects_unknown_skill(session: Session) -> None:
    assert resources.seed(session, [row("https://docs.docker.com/")]) == 1
    assert resources.seed(session, [row("https://docs.docker.com/")]) == 0
    with pytest.raises(ValueError, match="yok-boyle"):
        resources.seed(session, [{**row("https://x.dev/"), "slug": "yok-boyle"}])


def test_search_stores_top_results_and_resumes(session: Session, tmp_path: Path) -> None:
    state = tmp_path / "searched.json"
    yt = client(lambda r: api(r, ["a", "b", "c", "d"]))
    first = resources.search_youtube(session, yt, "k", SKILLS, limit=1, searched_file=state)
    assert (first.searches, first.added, first.remaining) == (1, 3, 1)  # tr: en iyi 3 video
    rows = session.scalars(select(Resource).order_by(Resource.url)).all()
    assert [r.url[-1] for r in rows] == ["a", "b", "c"]
    assert rows[0].provider == ResourceProvider.YOUTUBE
    assert rows[0].language == LangCode.TR
    # Kalan: sadece en. Türkçe sesli videolar elenir, arama yine "yapıldı" sayılır ve tekrarlanmaz.
    second = resources.search_youtube(session, yt, "k", SKILLS, searched_file=state)
    assert (second.searches, second.added, second.remaining) == (1, 0, 0)
    assert resources.search_youtube(session, yt, "k", SKILLS, searched_file=state).searches == 0


def test_quota_stops_without_marking_search_done(session: Session, tmp_path: Path) -> None:
    state = tmp_path / "searched.json"
    quota = client(lambda _: httpx.Response(403, text="quotaExceeded"))
    r = resources.search_youtube(session, quota, "k", SKILLS, searched_file=state)
    assert (r.quota_hit, r.searches, r.remaining) == (True, 0, 2)
    assert not state.exists()


def test_check_links_marks_dead_keeps_blocked_and_refreshes_videos(session: Session) -> None:
    urls = {"https://a.dev/ok": 200, "https://a.dev/yok": 404, "https://a.dev/engel": 403}
    resources.seed(session, [row(u) for u in urls])
    resources.seed(
        session,
        [
            row("https://www.youtube.com/watch?v=var", ResourceProvider.YOUTUBE),
            row("https://www.youtube.com/watch?v=silindi", ResourceProvider.YOUTUBE),
        ],
    )
    web = client(lambda r: httpx.Response(urls[str(r.url)]))
    r = resources.check_links(session, web, client(lambda q: api(q, ["var"])), "k")
    assert (r.checked, r.dead) == (4, 2)  # 403 sayılmaz, silinen video ölü
    by_url = {x.url: x for x in session.scalars(select(Resource))}
    assert not by_url["https://a.dev/yok"].is_alive
    assert by_url["https://a.dev/engel"].is_alive
    assert by_url["https://a.dev/engel"].last_checked_at is None
    assert by_url["https://www.youtube.com/watch?v=var"].title == "Docker Eğitimi"
    assert by_url["https://www.youtube.com/watch?v=var"].last_checked_at is not None
    assert not by_url["https://www.youtube.com/watch?v=silindi"].is_alive


def test_report_counts_only_live(session: Session) -> None:
    resources.seed(session, [row("https://a.dev/1"), row("https://a.dev/2"), row("https://a.dev/3")])
    rep = resources.report(session)
    assert rep["total"] == 3
    assert rep["short"] == []
