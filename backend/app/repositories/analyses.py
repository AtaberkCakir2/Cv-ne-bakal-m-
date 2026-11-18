"""Analiz kayıtları (T-039, T-048). CV içeriği yok: sadece SHA-256 özeti ve sayfa sayısı (karar #9)."""

import uuid
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.enums import AnalysisErrorCode, AnalysisStatus, ConsentType
from app.db.models import Analysis, Consent, Feedback, Resource, Role, Skill

_UNFINISHED = (AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING)


class AnalysisRepository(Protocol):
    def has_explicit_consent(self, user_id: uuid.UUID) -> bool: ...
    def role_exists(self, role_id: int) -> bool: ...
    def add(self, user_id: uuid.UUID, target_role_id: int, cv_sha256: str, cv_pages: int) -> uuid.UUID: ...
    def mark_failed(self, analysis_id: uuid.UUID, code: AnalysisErrorCode) -> None: ...
    def get_owned(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> Analysis | None: ...
    def fail_stale(self, user_id: uuid.UUID, created_before: datetime) -> None: ...
    def list_owned(self, user_id: uuid.UUID, limit: int, offset: int) -> tuple[list[Analysis], int]: ...
    def soft_delete(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> bool: ...
    def skill_names(self, skill_ids: set[int]) -> dict[int, str]: ...
    def resources(self, resource_ids: set[int]) -> dict[int, Resource]: ...
    def save_feedback(self, analysis_id: uuid.UUID, rating: int, comment: str | None) -> None: ...


def _owned(user_id: uuid.UUID) -> tuple[ColumnElement[bool], ...]:
    """Kullanıcının silinmemiş analizleri. Her sorgu bu koşulla yazılır: başkasının analizi görünmez (IDOR)."""
    return (Analysis.user_id == user_id, Analysis.deleted_at.is_(None))


class SqlAnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def has_explicit_consent(self, user_id: uuid.UUID) -> bool:
        """Yürürlükte (geri alınmamış) açık rıza var mı? Geri alınınca yeni analiz başlatılmaz (KVKK md. 11)."""
        stmt = select(Consent.id).where(
            Consent.user_id == user_id,
            Consent.consent_type == ConsentType.ACIK_RIZA,
            Consent.withdrawn_at.is_(None),
        )
        return self.session.scalar(stmt.limit(1)) is not None

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
            .options(
                joinedload(Analysis.target_role),
                selectinload(Analysis.skills),
                selectinload(Analysis.unverified_skills),
                selectinload(Analysis.recommendations),
                selectinload(Analysis.feedback),
            )
            .where(Analysis.id == analysis_id, *_owned(user_id))
        )

    def fail_stale(self, user_id: uuid.UUID, created_before: datetime) -> None:
        """Askıda kalan (işçi öldü, sert süre sınırı) analizleri başarısız sayar; liste de sonsuza dek beklemesin."""
        result = self.session.execute(
            update(Analysis)
            .where(*_owned(user_id), Analysis.status.in_(_UNFINISHED), Analysis.created_at < created_before)
            .values(status=AnalysisStatus.FAILED, error_code=AnalysisErrorCode.INTERNAL, completed_at=func.now())
            # fetch: oturumdaki nesneler sadece veritabanında gerçekten değişen satırlar için güncellenir
            # (işçi arada DONE yazdıysa satır koşula uymaz ve nesne de değişmez).
            .execution_options(synchronize_session="fetch")
        )
        if getattr(result, "rowcount", 0):
            self.session.commit()

    def list_owned(self, user_id: uuid.UUID, limit: int, offset: int) -> tuple[list[Analysis], int]:
        total = self.session.scalar(select(func.count()).select_from(Analysis).where(*_owned(user_id))) or 0
        rows = self.session.scalars(
            select(Analysis)
            .options(joinedload(Analysis.target_role))
            .where(*_owned(user_id))
            .order_by(Analysis.created_at.desc(), Analysis.id)
            .limit(limit)
            .offset(offset)
        )
        return list(rows), total

    def soft_delete(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Analiz listeden ve sonuçtan hemen kalkar; 30 gün sonra kalıcı silinir (purge_deleted_users.py).
        Kuyrukta veya işlenirken silinirse işçi sonucu yazmaz (analysis_runner, deleted_at kontrolü)."""
        result = self.session.execute(
            update(Analysis).where(Analysis.id == analysis_id, *_owned(user_id)).values(deleted_at=func.now())
        )
        self.session.commit()
        return bool(getattr(result, "rowcount", 0))

    def skill_names(self, skill_ids: set[int]) -> dict[int, str]:
        if not skill_ids:
            return {}
        rows = self.session.execute(select(Skill.id, Skill.canonical_name).where(Skill.id.in_(skill_ids)))
        return dict(rows.tuples().all())

    def resources(self, resource_ids: set[int]) -> dict[int, Resource]:
        if not resource_ids:
            return {}
        return {r.id: r for r in self.session.scalars(select(Resource).where(Resource.id.in_(resource_ids)))}

    def save_feedback(self, analysis_id: uuid.UUID, rating: int, comment: str | None) -> None:
        """Analiz başına tek geri bildirim; tekrar gönderilirse güncellenir (aynı anda iki istek de güvenli)."""
        values = {"rating": rating, "comment": comment}
        self.session.execute(
            pg_insert(Feedback)
            .values(analysis_id=analysis_id, **values)
            .on_conflict_do_update(index_elements=[Feedback.analysis_id], set_={**values, "updated_at": func.now()})
        )
        self.session.commit()
        self.session.expire_all()  # ilişkili Analysis.feedback yeniden okunsun
