"""Kullanıcı, oturum (refresh) token'ı, tek kullanımlık token ve rıza kayıtlarına erişim (T-037).

Modeller app/db/models/user.py'de (sahibi: Ataberk). Silinmiş (deleted_at dolu) kullanıcılar yok sayılır.
"""

import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.db.enums import TokenPurpose
from app.db.models import Analysis, AuditLog, Consent, RefreshToken, Resource, Role, Skill, User, UserToken


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
        # Silinen hesabın e-postası silme anında anonimleştirilir (T-049), yani adres yeniden kayıt için serbest kalır.
        return self.session.scalar(select(User.id).where(User.email == email)) is not None

    def add_user(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def add_consents(self, consents: list[Consent]) -> None:
        self.session.add_all(consents)

    def list_consents(self, user_id: uuid.UUID) -> list[Consent]:
        return list(
            self.session.scalars(
                select(Consent).where(Consent.user_id == user_id).order_by(Consent.accepted_at, Consent.consent_type)
            )
        )

    # --- profil ve KVKK (T-049)
    def get_active_role(self, role_id: int) -> Role | None:
        return self.session.scalar(select(Role).where(Role.id == role_id, Role.is_active))

    def list_refresh_tokens(self, user_id: uuid.UUID) -> list[RefreshToken]:
        return list(
            self.session.scalars(
                select(RefreshToken).where(RefreshToken.user_id == user_id).order_by(RefreshToken.created_at)
            )
        )

    def list_analyses(self, user_id: uuid.UUID) -> list[Analysis]:
        """Kullanıcının analizleri, bağlı kayıtlarıyla (dışa aktarma için). Silinmiş ama henüz kalıcı silinmemiş
        analizler de dahil: o süre boyunca hâlâ işlenen veridir (KVKK md. 11)."""
        return list(
            self.session.scalars(
                select(Analysis)
                .where(Analysis.user_id == user_id)
                .options(
                    selectinload(Analysis.target_role),
                    selectinload(Analysis.skills),
                    selectinload(Analysis.unverified_skills),
                    selectinload(Analysis.recommendations),
                    selectinload(Analysis.feedback),
                )
                .order_by(Analysis.created_at)
            )
        )

    def skill_names(self, skill_ids: set[int]) -> dict[int, str]:
        if not skill_ids:
            return {}
        rows = self.session.execute(select(Skill.id, Skill.canonical_name).where(Skill.id.in_(skill_ids)))
        return dict(rows.tuples().all())

    def resources(self, resource_ids: set[int]) -> dict[int, Resource]:
        if not resource_ids:
            return {}
        return {r.id: r for r in self.session.scalars(select(Resource).where(Resource.id.in_(resource_ids)))}

    def list_audit(self, user_id: uuid.UUID) -> list[AuditLog]:
        return list(self.session.scalars(select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.id)))

    def purge_deleted_analyses(self, before: datetime) -> None:
        self.session.execute(delete(Analysis).where(Analysis.deleted_at.is_not(None), Analysis.deleted_at < before))

    def add_audit(self, entry: AuditLog) -> None:
        self.session.add(entry)

    def purge_deleted_users(self, before: datetime) -> int:
        """deleted_at'i `before`'dan eski kullanıcıları kalıcı siler; bağlı kayıtlar CASCADE ile gider,
        audit_logs.user_id NULL olur. Silinen kullanıcı sayısını döner."""
        result = self.session.execute(delete(User).where(User.deleted_at.is_not(None), User.deleted_at < before))
        return int(getattr(result, "rowcount", 0) or 0)

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
