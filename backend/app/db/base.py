"""Ortak model tabanı: kısıt adlandırma kuralı ve zaman damgası sütunları."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Alembic'in ürettiği kısıt adları sabit olsun; downgrade ve sonraki migration'lar adla çalışır.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Tüm zaman damgaları timestamptz (varsayılan DateTime saat dilimsizdir).
    type_annotation_map = {datetime: DateTime(timezone=True)}


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TimestampMixin(CreatedAtMixin):
    # onupdate ORM üzerinden yapılan güncellemelerde çalışır; elle SQL ile güncellerken updated_at'i siz verin.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    # Silinen kayıt sorgularda filtrelenir; 30 gün sonra kalıcı silme işi CASCADE ile temizler (docs/veritabani.md).
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
