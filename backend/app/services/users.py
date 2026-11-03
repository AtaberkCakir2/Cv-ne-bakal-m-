"""Profil ve KVKK iş mantığı (T-049): profil güncelleme, sürümlü rıza kaydı, verilerimi indir, hesabımı sil.

Hesap silme iki aşamalıdır (docs/veritabani.md, "Soft delete"):
1. Hemen: kişiyi tanımlayan alanlar anonimleştirilir (e-posta, ad, şifre), bütün oturumlar ve tek kullanımlık
   bağlantılar geçersiz olur, analizler gizlenir. E-posta serbest kalır; aynı adresle yeniden kayıt olunabilir.
2. 30 gün sonra: `purge_deleted_users` kullanıcıyı kalıcı siler; bağlı kayıtlar CASCADE ile gider.

Açık rızanın geri alınması henüz yok: consents tablosunda geri alma alanı yok (model Ataberk'te; öneri PR'da).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import Settings
from app.db.enums import TokenPurpose
from app.db.models import Analysis, AuditLog, Consent, RefreshToken, Resource, User
from app.repositories.users import UserRepository
from app.schemas.users import (
    ConsentOut,
    ExportActivity,
    ExportAnalysis,
    ExportOut,
    ExportRecommendation,
    ExportSession,
    ExportSkill,
    ProfileOut,
    RoleRef,
)
from app.services.auth import ConsentInput

PURGE_AFTER = timedelta(days=30)


class UserError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


@dataclass(frozen=True)
class ProfileChanges:
    full_name: str | None
    target_role_id: int | None
    fields: frozenset[str]  # istemcinin gönderdiği alanlar; gönderilmeyen alan değişmez


def anonymized_email(user_id: uuid.UUID) -> str:
    # .invalid alan adı hiçbir zaman gerçek bir adrese çözülmez (RFC 2606); kullanıcı id'si tekilliği sağlar.
    return f"silindi-{user_id}@silinmis.invalid"


def profile_out(user: User) -> ProfileOut:
    role = user.target_role
    return ProfileOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_verified=user.is_verified,
        target_role=RoleRef(id=role.id, slug=role.slug, name=role.name) if role else None,
    )


class UserService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repo = UserRepository(session)

    def _lock_active(self, user: User) -> None:
        """Satırı kilitleyip tazeler: eşzamanlı bir silme isteği commit ettiyse silinmiş hesaba veri yazılmasın."""
        self.session.refresh(user, with_for_update=True)
        if user.deleted_at is not None:
            raise UserError(401, "Oturum geçersiz veya süresi dolmuş.")

    def update_profile(self, user: User, changes: ProfileChanges) -> User:
        self._lock_active(user)
        if "target_role_id" in changes.fields:
            if changes.target_role_id is not None and self.repo.get_active_role(changes.target_role_id) is None:
                raise UserError(422, "Seçilen pozisyon bulunamadı.")
            user.target_role_id = changes.target_role_id
        if "full_name" in changes.fields:
            user.full_name = changes.full_name
        self.session.commit()
        self.session.refresh(user, ["target_role"])
        return user

    # --- rıza
    def consents(self, user: User) -> list[ConsentOut]:
        return [
            ConsentOut(consent_type=c.consent_type, version=c.version, accepted_at=c.accepted_at)
            for c in self.repo.list_consents(user.id)
        ]

    def accept_consents(self, user: User, consents: list[ConsentInput], ip: str | None) -> list[ConsentOut]:
        """Yeni metin sürümlerini kaydeder. Onaylanmış (tür, sürüm) tekrar eklenmez; eski sürümler silinmez."""
        self._lock_active(user)
        existing = {(c.consent_type, c.version) for c in self.repo.list_consents(user.id)}
        now = datetime.now(UTC)
        ip_hash = security.hash_ip(ip, self.settings)
        self.repo.add_consents(
            [
                Consent(
                    user_id=user.id, consent_type=c.consent_type, version=c.version, accepted_at=now, ip_hash=ip_hash
                )
                for c in consents
                if (c.consent_type, c.version) not in existing
            ]
        )
        try:
            self.session.commit()
        except IntegrityError:  # aynı sürüm eşzamanlı iki istekle geldi; istek tekrarlanabilir, sonuç aynı
            self.session.rollback()
        return self.consents(user)

    # --- verilerimi indir
    def export(self, user: User, ip: str | None) -> ExportOut:
        analyses = self.repo.list_analyses(user.id)
        skill_ids = {s.skill_id for a in analyses for s in a.skills} | {
            r.skill_id for a in analyses for r in a.recommendations
        }
        names = self.repo.skill_names(skill_ids)
        resources = self.repo.resources({r.resource_id for a in analyses for r in a.recommendations})
        out = ExportOut(
            exported_at=datetime.now(UTC),
            profile=profile_out(user),
            created_at=user.created_at,
            consents=self.consents(user),
            sessions=[
                ExportSession(
                    created_at=t.created_at, expires_at=t.expires_at, revoked_at=t.revoked_at, user_agent=t.user_agent
                )
                for t in self.repo.list_refresh_tokens(user.id)
            ],
            analyses=[self._export_analysis(a, names, resources) for a in analyses],
            activity=[ExportActivity(action=e.action, created_at=e.created_at) for e in self.repo.list_audit(user.id)],
        )
        self.repo.add_audit(
            AuditLog(user_id=user.id, action="data.export", ip_hash=security.hash_ip(ip, self.settings))
        )
        self.session.commit()
        return out

    @staticmethod
    def _export_analysis(a: Analysis, names: dict[int, str], resources: dict[int, Resource]) -> ExportAnalysis:
        return ExportAnalysis(
            id=a.id,
            created_at=a.created_at,
            target_role=a.target_role.slug,
            status=a.status,
            cv_sha256=a.cv_sha256,
            cv_pages=a.cv_pages,
            match_score=a.match_score,
            postings_analyzed=a.postings_analyzed,
            completed_at=a.completed_at,
            deleted_at=a.deleted_at,
            duration_ms=a.duration_ms,
            error_code=a.error_code.value if a.error_code else None,
            model_name=a.model_name,
            prompt_version=a.prompt_version,
            skills=[
                ExportSkill(
                    skill=names.get(s.skill_id, str(s.skill_id)),
                    kind=s.kind.value,
                    level=s.level.value,
                    confidence=s.confidence,
                    demand_ratio=s.demand_ratio,
                    priority=s.priority,
                )
                for s in a.skills
            ],
            unverified_skills=[
                {"name": u.name, "level": u.level.value, "confidence": u.confidence} for u in a.unverified_skills
            ],
            recommendations=[
                ExportRecommendation(
                    skill=names.get(r.skill_id, str(r.skill_id)),
                    title=resources[r.resource_id].title,
                    url=resources[r.resource_id].url,
                    rank=r.rank,
                    reason_text=r.reason_text,
                )
                for r in sorted(a.recommendations, key=lambda r: r.rank)
                if r.resource_id in resources
            ],
            feedback={"rating": a.feedback.rating, "comment": a.feedback.comment} if a.feedback else None,
        )

    # --- hesabımı sil
    def delete_account(self, user: User, password: str, ip: str | None) -> None:
        self._lock_active(user)
        ip_hash = security.hash_ip(ip, self.settings)
        if not security.verify_password(user.password_hash, password):
            # Çalınmış bir oturumla şifre denemesi izlenebilsin (rate limit T-050).
            self.repo.add_audit(AuditLog(user_id=user.id, action="account.delete_failed", ip_hash=ip_hash))
            self.session.commit()
            # 401 değil: istemci 401'de oturumu yenilemeye çalışır, burada sorun oturum değil şifre.
            raise UserError(403, "Şifre hatalı.")
        now = datetime.now(UTC)
        user.deleted_at = now
        user.email = anonymized_email(user.id)
        user.full_name = None
        user.target_role_id = None
        user.is_verified = False
        # Bilinen bir şifreyle eşleşmeyen, rastgele bir değerin hash'i: hesap hiçbir şifreyle açılamaz.
        user.password_hash = security.hash_password(security.new_opaque_token())
        self.repo.revoke_all_refresh_tokens(user.id, now)
        # Oturumların cihaz bilgisi de kişisel veri; iptal edilmiş oturumda tutmanın bir gereği yok.
        self.session.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(user_agent=None))
        for purpose in TokenPurpose:
            self.repo.invalidate_user_tokens(user.id, purpose, now)
        self.session.execute(
            update(Analysis).where(Analysis.user_id == user.id, Analysis.deleted_at.is_(None)).values(deleted_at=now)
        )
        self.repo.add_audit(AuditLog(user_id=user.id, action="account.delete", ip_hash=ip_hash))
        self.session.commit()


def purge_deleted_users(session: Session, now: datetime | None = None) -> int:
    """30 günü geçmiş silinmiş hesapları ve tek tek silinmiş analizleri kalıcı siler (günlük iş;
    docs/go-live.md, "Rutin operasyonlar"). Silinen hesap sayısını döner."""
    now = now or datetime.now(UTC)
    repo = UserRepository(session)
    count = repo.purge_deleted_users(now - PURGE_AFTER)
    repo.purge_deleted_analyses(now - PURGE_AFTER)
    if count:
        repo.add_audit(AuditLog(action="account.purge", entity="users"))
    session.commit()
    return count
