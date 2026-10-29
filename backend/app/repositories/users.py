"""Kullanıcı, oturum (refresh) token'ı, tek kullanımlık token ve rıza kayıtlarına erişim (T-037).

Modeller app/db/models/user.py'de (sahibi: Ataberk). Silinmiş (deleted_at dolu) kullanıcılar yok sayılır.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.enums import TokenPurpose
from app.db.models import Consent, RefreshToken, User, UserToken


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # --- kullanıcı
    def get_active_by_email(self, email: str) -> User | None:
        # email sütunu CITEXT: büyük/küçük harf duyarsız karşılaştırma veritabanında yapılır.
        return self.session.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))

    def get_active_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.session.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))

    def email_exists(self, email: str) -> bool:
        # Silinmiş hesap da e-postayı tutar (unique); kalıcı silme işi gelene kadar yeniden kayıt olunamaz.
        return self.session.scalar(select(User.id).where(User.email == email)) is not None

    def add_user(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def add_consents(self, consents: list[Consent]) -> None:
        self.session.add_all(consents)

    # --- refresh token
    def add_refresh_token(self, token: RefreshToken) -> None:
        self.session.add(token)

    def get_refresh_token_for_update(self, token_hash: str) -> RefreshToken | None:
        # FOR UPDATE: aynı token'la eşzamanlı iki yenileme isteği iki yeni oturum üretemesin.
        return self.session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update())

    def revoke_all_refresh_tokens(self, user_id: uuid.UUID, now: datetime) -> None:
        self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    # --- tek kullanımlık token (e-posta doğrulama / şifre sıfırlama)
    def add_user_token(self, token: UserToken) -> None:
        self.session.add(token)

    def get_user_token_for_update(self, token_hash: str, purpose: TokenPurpose) -> UserToken | None:
        return self.session.scalar(
            select(UserToken).where(UserToken.token_hash == token_hash, UserToken.purpose == purpose).with_for_update()
        )

    def invalidate_user_tokens(self, user_id: uuid.UUID, purpose: TokenPurpose, now: datetime) -> None:
        """Aynı amaçla verilmiş eski, kullanılmamış token'ları geçersiz kılar (yeni bağlantı istenince)."""
        self.session.execute(
            update(UserToken)
            .where(UserToken.user_id == user_id, UserToken.purpose == purpose, UserToken.used_at.is_(None))
            .values(used_at=now)
        )
