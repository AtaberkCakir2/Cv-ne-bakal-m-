"""CV analizleri ve sonuçları. CV dosyası ve ham CV metni hiçbir sütunda yok (karar #9)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.db.enums import AnalysisErrorCode, AnalysisStatus, SkillKind, SkillLevel, pg_enum
from app.db.models.catalog import Role
from app.db.models.user import UUID_DEFAULT

if TYPE_CHECKING:
    from app.db.models.user import User


class Analysis(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index(None, "user_id", "created_at"),
        CheckConstraint("match_score BETWEEN 0 AND 100", name="match_score_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_DEFAULT)  # contracts: analysis_id
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Analiz anındaki hedef; users.target_role_id sonradan değişebilir.
    target_role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
    status: Mapped[AnalysisStatus] = mapped_column(
        pg_enum(AnalysisStatus, "analysis_status"), server_default=AnalysisStatus.QUEUED.value, index=True
    )
    cv_sha256: Mapped[str] = mapped_column(CHAR(64), index=True)  # önbellek anahtarı; dosya/metin saklanmaz
    cv_pages: Mapped[int | None] = mapped_column(SmallInteger)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    postings_analyzed: Mapped[int | None]
    model_name: Mapped[str | None] = mapped_column(String(60))
    prompt_version: Mapped[str | None] = mapped_column(String(60))
    duration_ms: Mapped[int | None]
    # Hata mesajı API'de koddan üretilir; ham hata metni (CV parçası içerebilir) saklanmaz.
    error_code: Mapped[AnalysisErrorCode | None] = mapped_column(pg_enum(AnalysisErrorCode, "analysis_error_code"))
    completed_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="analyses")
    target_role: Mapped[Role] = relationship()
    skills: Mapped[list["AnalysisSkill"]] = relationship(back_populates="analysis", passive_deletes=True)
    unverified_skills: Mapped[list["AnalysisUnverifiedSkill"]] = relationship(
        back_populates="analysis", passive_deletes=True
    )
    recommendations: Mapped[list["AnalysisRecommendation"]] = relationship(
        back_populates="analysis", passive_deletes=True, order_by="AnalysisRecommendation.rank"
    )
    feedback: Mapped["Feedback | None"] = relationship(back_populates="analysis", passive_deletes=True)


class AnalysisSkill(TimestampMixin, Base):
    __tablename__ = "analysis_skills"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("demand_ratio BETWEEN 0 AND 1", name="demand_ratio_range"),
        CheckConstraint("priority IS NULL OR kind = 'missing'", name="priority_only_missing"),
    )

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True, index=True)
    kind: Mapped[SkillKind] = mapped_column(pg_enum(SkillKind, "skill_kind"))
    level: Mapped[SkillLevel] = mapped_column(
        pg_enum(SkillLevel, "skill_level"), server_default=SkillLevel.UNKNOWN.value
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    # Analiz anındaki talep oranı: bilinçli anlık görüntü (3NF istisnası, docs/veritabani.md).
    demand_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    priority: Mapped[int | None] = mapped_column(SmallInteger)  # contracts: missing_skills[].priority

    analysis: Mapped[Analysis] = relationship(back_populates="skills")


class AnalysisUnverifiedSkill(TimestampMixin, Base):
    """Taksonomide olmayan, LLM tahmini yetkinlik (contracts: present_skills[].verified = false)."""

    __tablename__ = "analysis_unverified_skills"
    __table_args__ = (
        UniqueConstraint("analysis_id", "name"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))  # sadece yetkinlik adı, CV metni değil
    level: Mapped[SkillLevel] = mapped_column(
        pg_enum(SkillLevel, "skill_level"), server_default=SkillLevel.UNKNOWN.value
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))

    analysis: Mapped[Analysis] = relationship(back_populates="unverified_skills")


class AnalysisRecommendation(TimestampMixin, Base):
    __tablename__ = "analysis_recommendations"
    __table_args__ = (UniqueConstraint("analysis_id", "skill_id", "rank"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    # İndeks gerekmez: (analysis_id, skill_id, rank) unique kısıtı analysis_id ile başlıyor.
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"))
    # Sadece DB'deki kaynaklar; öneride kullanılan kaynak silinemez (karar #10).
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id", ondelete="RESTRICT"))
    rank: Mapped[int] = mapped_column(SmallInteger)
    reason_text: Mapped[str | None] = mapped_column(Text)  # LLM'in Türkçe gerekçesi

    analysis: Mapped[Analysis] = relationship(back_populates="recommendations")


class Feedback(TimestampMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    # unique: analiz başına tek geri bildirim (1:1).
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="feedback")
