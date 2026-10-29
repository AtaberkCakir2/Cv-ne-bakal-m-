"""Kullanıcı, oturum token'ları ve KVKK rızaları."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.db.enums import ConsentType, TokenPurpose, UserRole, pg_enum

if TYPE_CHECKING:
    from app.db.models.analysis import Analysis
    from app.db.models.catalog import Role

UUID_DEFAULT = text("gen_random_uuid()")


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_DEFAULT)
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)  # argon2
    full_name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole, "user_role"), server_default=UserRole.USER.value)
    target_role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    is_verified: Mapped[bool] = mapped_column(server_default=text("false"))

    target_role: Mapped["Role | None"] = relationship()
    # passive_deletes: silmeyi DB'deki ON DELETE CASCADE yapar, ORM tek tek yüklemez.
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user", passive_deletes=True)
    consents: Mapped[list["Consent"]] = relationship(back_populates="user", passive_deletes=True)


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_DEFAULT)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)  # SHA-256; token kendisi saklanmaz
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(Text)


class UserToken(TimestampMixin, Base):
    """Tek kullanımlık e-posta doğrulama / şifre sıfırlama token'ı (T-037 için öneri)."""

    __tablename__ = "user_tokens"
    __table_args__ = (Index(None, "user_id", "purpose"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_DEFAULT)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[TokenPurpose] = mapped_column(pg_enum(TokenPurpose, "token_purpose"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class Consent(TimestampMixin, Base):
    __tablename__ = "consents"
    # Aynı metin sürümünün yürürlükteki tek onayı olur. Geri alınan onay satırı silinmez (ispat için kalır);
    # kullanıcı aynı sürümü yeniden onaylarsa yeni satır eklenir.
    __table_args__ = (
        Index(
            "uq_consents_active_version",
            "user_id",
            "consent_type",
            "version",
            unique=True,
            postgresql_where=text("withdrawn_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_DEFAULT)
    # Kısmi tekillik indeksi geri alınmış satırları kapsamaz; kullanıcının bütün onayları (export, CASCADE) için ayrı.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    consent_type: Mapped[ConsentType] = mapped_column(pg_enum(ConsentType, "consent_type"))
    version: Mapped[str] = mapped_column(String(20))  # metin sürümü, ör. 2026-12
    accepted_at: Mapped[datetime]
    ip_hash: Mapped[str | None] = mapped_column(Text)  # tuzlu hash; açık IP saklanmaz
    # KVKK md. 11: rıza her zaman geri alınabilir. Dolu ise bu onay artık geçerli değil.
    withdrawn_at: Mapped[datetime | None]

    user: Mapped[User] = relationship(back_populates="consents")
