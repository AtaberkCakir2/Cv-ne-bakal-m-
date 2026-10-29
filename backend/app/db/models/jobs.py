"""İlan toplama: kaynaklar, temizlenmiş ilanlar, ilan-yetkinlik etiketleri ve toplama çalışmaları."""

from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import CHAR, BigInteger, ForeignKey, Identity, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import LangCode, ScrapeStatus, SkillImportance, SourceType, pg_enum
from app.db.models.catalog import EMBEDDING_DIM, hnsw_index


class JobSource(TimestampMixin, Base):
    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)  # contracts: source
    type: Mapped[SourceType] = mapped_column(pg_enum(SourceType, "source_type"))
    base_url: Mapped[str | None] = mapped_column(Text)
    tos_checked: Mapped[bool] = mapped_column(server_default=text("false"))  # scraper/kaynak-uygunluk.md
    rate_limit_sec: Mapped[Decimal] = mapped_column(Numeric(4, 1), server_default=text("4"))
    # Sadece uygunluk tablosunda ✅ olan kaynak açılır.
    is_active: Mapped[bool] = mapped_column(server_default=text("false"))


class JobPosting(TimestampMixin, Base):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("source_id", "external_id"), hnsw_index())

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # contracts: id
    # Kaynak silinirse (ör. izin bitti) ilanları da silinir.
    source_id: Mapped[int] = mapped_column(ForeignKey("job_sources.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    title_raw: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), index=True)
    company: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    # ETL, İK kişisinin adı / e-posta / telefonunu buraya yazmadan önce siler.
    description_clean: Mapped[str] = mapped_column(Text)
    language: Mapped[LangCode] = mapped_column(pg_enum(LangCode, "lang_code"))
    posted_at: Mapped[date | None] = mapped_column(index=True)
    content_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)  # tekrar kayıt engeli
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    source: Mapped[JobSource] = relationship()
    skills: Mapped[list["JobPostingSkill"]] = relationship(back_populates="posting", passive_deletes=True)


class JobPostingSkill(TimestampMixin, Base):
    __tablename__ = "job_posting_skills"

    posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True, index=True)
    importance: Mapped[SkillImportance] = mapped_column(pg_enum(SkillImportance, "skill_importance"))

    posting: Mapped[JobPosting] = relationship(back_populates="skills")


class ScrapeRun(TimestampMixin, Base):
    __tablename__ = "scrape_runs"
    __table_args__ = (Index(None, "source_id", "started_at"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("job_sources.id", ondelete="CASCADE"))
    started_at: Mapped[datetime]
    finished_at: Mapped[datetime | None]
    status: Mapped[ScrapeStatus] = mapped_column(pg_enum(ScrapeStatus, "scrape_status"), index=True)
    fetched: Mapped[int] = mapped_column(server_default=text("0"))
    inserted: Mapped[int] = mapped_column(server_default=text("0"))
    duplicates: Mapped[int] = mapped_column(server_default=text("0"))
    errors: Mapped[int] = mapped_column(server_default=text("0"))
    error_log: Mapped[str | None] = mapped_column(Text)
