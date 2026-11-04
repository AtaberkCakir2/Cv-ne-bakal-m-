"""Analiz kayıtları (T-039). CV içeriği yok: sadece SHA-256 özeti ve sayfa sayısı (karar #9)."""

import uuid
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.enums import AnalysisErrorCode, AnalysisStatus
from app.db.models import Analysis, Role


class AnalysisRepository(Protocol):
    def role_exists(self, role_id: int) -> bool: ...
    def add(self, user_id: uuid.UUID, target_role_id: int, cv_sha256: str, cv_pages: int) -> uuid.UUID: ...
    def mark_failed(self, analysis_id: uuid.UUID, code: AnalysisErrorCode) -> None: ...
    def get_owned(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> Analysis | None: ...


class SqlAnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def role_exists(self, role_id: int) -> bool:
        return self.session.scalar(select(Role.id).where(Role.id == role_id, Role.is_active)) is not None

    def add(self, user_id: uuid.UUID, target_role_id: int, cv_sha256: str, cv_pages: int) -> uuid.UUID:
        analysis = Analysis(user_id=user_id, target_role_id=target_role_id, cv_sha256=cv_sha256, cv_pages=cv_pages)
        self.session.add(analysis)
        # Kuyruğa vermeden önce commit: işçi kaydı hemen okuyabilmeli.
        self.session.commit()
        return analysis.id

    def mark_failed(self, analysis_id: uuid.UUID, code: AnalysisErrorCode) -> None:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is not None:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_code = code
            analysis.completed_at = datetime.now(UTC)
            self.session.commit()

    def get_owned(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> Analysis | None:
        return self.session.scalar(
            select(Analysis)
            .options(joinedload(Analysis.target_role))
            .where(Analysis.id == analysis_id, Analysis.user_id == user_id, Analysis.deleted_at.is_(None))
        )
