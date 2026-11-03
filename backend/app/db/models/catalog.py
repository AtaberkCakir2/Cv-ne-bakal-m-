"""Katalog: hedef pozisyonlar, yetkinlik taksonomisi ve eğitim kaynakları."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, ForeignKey, Identity, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import LangCode, ResourceLevel, ResourceProvider, SkillCategory, pg_enum

EMBEDDING_DIM = 384  # sentence-transformers paraphrase-multilingual-MiniLM-L12-v2


def hnsw_index(column: str = "embedding") -> Index:
    """Kosinüs benzerliği için HNSW indeksi (T-013). Sorgu `<=>` operatörüyle yazılmalı, yoksa indeks kullanılmaz.

    m / ef_construction pgvector'un varsayılanları; ölçüm ve gerekçe docs/veritabani.md "Vektör indeksleri".
    """
    return Index(
        None,
        column,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={column: "vector_cosine_ops"},
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (Index(None, "synonyms", postgresql_using="gin"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # contracts: role_slug
    synonyms: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (Index(None, "synonyms", postgresql_using="gin"), hnsw_index())

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True)  # contracts: skills[].skill
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[SkillCategory] = mapped_column(pg_enum(SkillCategory, "skill_category"), index=True)
    synonyms: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    esco_uri: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    resources: Mapped[list["Resource"]] = relationship(back_populates="skill")


class Resource(TimestampMixin, Base):
    """Eğitim kaynağı. Öneri linkleri sadece buradan gelir; LLM link üretmez (karar #10)."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)  # contracts: resource_id
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, unique=True)
    provider: Mapped[ResourceProvider] = mapped_column(pg_enum(ResourceProvider, "resource_provider"))
    language: Mapped[LangCode] = mapped_column(pg_enum(LangCode, "lang_code"))
    level: Mapped[ResourceLevel] = mapped_column(pg_enum(ResourceLevel, "resource_level"))
    duration_min: Mapped[int | None]
    is_free: Mapped[bool]
    is_alive: Mapped[bool] = mapped_column(server_default=text("true"))  # haftalık link kontrolü
    last_checked_at: Mapped[datetime | None]

    skill: Mapped[Skill] = relationship(back_populates="resources")
