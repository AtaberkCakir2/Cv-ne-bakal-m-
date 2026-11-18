"""İstatistik sayfasının sorguları. Sadece sayımlar: kişi, CV veya ilan metni dönmez."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Row, func, select, text
from sqlalchemy.orm import Session

from app.db.enums import AnalysisStatus
from app.db.models import Analysis, JobPosting, JobSource, Resource, ScrapeRun, Skill, User

MIN_RESOURCES_PER_SKILL = 3  # T-046 kabul kriteri


@dataclass(frozen=True)
class Stats:
    sources: Sequence[Row[Any]]  # ad, açık mı, aktif ilan, son 7 gün, son çalışma durumu, son çalışma zamanı
    postings_active: int
    postings_last_7d: int
    resources_alive: int
    resources_dead: int
    resources_by_provider: Sequence[Row[Any]]  # sağlayıcı, sayı
    skills_active: int
    skills_under_min: int
    analyses: dict[str, dict[str, int]]
    analysis_avg_s_7d: float | None
    users_active: int
    stats_computed_at: datetime | None


def collect(session: Session, now: datetime | None = None) -> Stats:
    now = now or datetime.now(UTC)
    week_ago, day_ago = now - timedelta(days=7), now - timedelta(days=1)

    last_run = (
        select(ScrapeRun.source_id, ScrapeRun.status, ScrapeRun.started_at)
        .distinct(ScrapeRun.source_id)
        .order_by(ScrapeRun.source_id, ScrapeRun.started_at.desc())
        .subquery()
    )
    active_postings = (
        select(func.count())
        .where(JobPosting.source_id == JobSource.id, JobPosting.is_active)
        .correlate(JobSource)
        .scalar_subquery()
    )
    new_postings = (
        select(func.count())
        .where(JobPosting.source_id == JobSource.id, JobPosting.created_at >= week_ago)
        .correlate(JobSource)
        .scalar_subquery()
    )
    sources = list(
        session.execute(
            select(
                JobSource.name,
                JobSource.is_active,
                active_postings,
                new_postings,
                last_run.c.status,
                last_run.c.started_at,
            )
            .outerjoin(last_run, last_run.c.source_id == JobSource.id)
            .order_by(JobSource.name)
        ).all()
    )

    alive_per_skill = (
        select(func.count()).where(Resource.skill_id == Skill.id, Resource.is_alive).correlate(Skill).scalar_subquery()
    )

    analyses: dict[str, dict[str, int]] = {"24 saat": {}, "7 gün": {}}
    for label, since in (("24 saat", day_ago), ("7 gün", week_ago)):
        rows = session.execute(
            select(Analysis.status, func.count()).where(Analysis.created_at >= since).group_by(Analysis.status)
        ).all()
        counts: dict[Any, int] = {status: n for status, n in rows}
        analyses[label] = {s.value: int(counts.get(s, 0)) for s in AnalysisStatus}

    avg_ms = session.scalar(
        select(func.avg(Analysis.duration_ms)).where(
            Analysis.status == AnalysisStatus.DONE, Analysis.created_at >= week_ago
        )
    )

    return Stats(
        sources=sources,
        postings_active=session.scalar(select(func.count()).where(JobPosting.is_active)) or 0,
        postings_last_7d=session.scalar(select(func.count()).where(JobPosting.created_at >= week_ago)) or 0,
        resources_alive=session.scalar(select(func.count()).where(Resource.is_alive)) or 0,
        resources_dead=session.scalar(select(func.count()).where(Resource.is_alive.is_(False))) or 0,
        resources_by_provider=list(
            session.execute(
                select(Resource.provider, func.count())
                .where(Resource.is_alive)
                .group_by(Resource.provider)
                .order_by(func.count().desc())
            ).all()
        ),
        skills_active=session.scalar(select(func.count()).where(Skill.is_active)) or 0,
        skills_under_min=session.scalar(
            select(func.count()).where(Skill.is_active, alive_per_skill < MIN_RESOURCES_PER_SKILL)
        )
        or 0,
        analyses=analyses,
        analysis_avg_s_7d=float(avg_ms) / 1000 if avg_ms is not None else None,
        users_active=session.scalar(select(func.count()).where(User.deleted_at.is_(None))) or 0,
        stats_computed_at=session.scalar(text("SELECT max(computed_at) FROM role_skill_stats")),
    )
