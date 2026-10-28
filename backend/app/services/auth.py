"""Kimlik doğrulama iş mantığı (T-037).

Kurallar:
- Hata mesajları e-postanın kayıtlı olup olmadığını belli etmez (giriş ve şifremi unuttum).
- Refresh token tek kullanımlıktır (rotasyon). Daha önce kullanılmış / iptal edilmiş bir token tekrar gelirse
  token çalınmış olabilir: kullanıcının bütün oturumları kapatılır.
- Şifre sıfırlanınca bütün oturumlar kapatılır.

Bilinen ve kabul edilen sınırlar (kod incelemesi, T-037):
- Aynı refresh token'la aynı anda iki istek gelirse (ör. iki sekme) ikincisi "tekrar kullanım" sayılır ve
  oturumlar kapanır. İstemciler (web/mobil) token yenilemeyi tek seferde yapmalı (tek uçuşlu yenileme).
- "Şifremi unuttum" kayıtlı e-postada veritabanına yazdığı için biraz daha uzun sürer; yanıt süresinden
  e-postanın kayıtlı olduğu tahmin edilebilir. Rate limit (T-050) bunu pratikte zorlaştırır; gerekirse iş
  arka plan görevine taşınır.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import Settings
from app.db.enums import ConsentType, TokenPurpose, UserRole
from app.db.models import Consent, RefreshToken, User, UserToken
from app.repositories.users import UserRepository
from app.services.email import EmailMessage, EmailSender

REQUIRED_CONSENTS = frozenset(ConsentType)


class AuthError(Exception):
    """İstemciye gösterilecek kimlik doğrulama hatası. `status` HTTP durum kodudur."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


# Her raise'da yeni nesne: ortak bir istisna nesnesine eşzamanlı isteklerin traceback'i (ve yerel değişkenleri,
# ör. düz metin parola) yazılmasın.
def invalid_credentials() -> AuthError:
    return AuthError(401, "E-posta veya şifre hatalı.")


def invalid_refresh() -> AuthError:
    return AuthError(401, "Oturum geçersiz veya süresi dolmuş. Lütfen tekrar giriş yapın.")


def invalid_link() -> AuthError:
    return AuthError(400, "Bağlantı geçersiz, kullanılmış veya süresi dolmuş.")


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int  # access token ömrü (saniye)


@dataclass(frozen=True)
class ConsentInput:
    consent_type: ConsentType
    version: str


class AuthService:
    def __init__(self, session: Session, settings: Settings, email: EmailSender) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.settings = settings
        self.email = email

    # --- kayıt
    def register(
        self, *, email: str, password: str, full_name: str | None, consents: list[ConsentInput], ip: str | None
    ) -> User:
        given = {c.consent_type for c in consents}
        if missing := REQUIRED_CONSENTS - given:
            names = ", ".join(sorted(m.value for m in missing))
            raise AuthError(422, f"Zorunlu onaylar eksik: {names}.")
        if self.repo.email_exists(email):
            raise AuthError(409, "Bu e-posta ile kayıtlı bir hesap var. Giriş yapın veya şifrenizi sıfırlayın.")

        now = datetime.now(UTC)
        user = User(email=email, password_hash=security.hash_password(password), full_name=full_name)
        try:
            self.repo.add_user(user)
        except IntegrityError as exc:  # aynı anda iki kayıt isteği
            self.session.rollback()
            raise AuthError(409, "Bu e-posta ile kayıtlı bir hesap var.") from exc
        ip_hash = security.hash_ip(ip, self.settings)
        self.repo.add_consents(
            [
                Consent(
                    user_id=user.id, consent_type=c.consent_type, version=c.version, accepted_at=now, ip_hash=ip_hash
                )
                for c in consents
            ]
        )
        message = self._verification_email(user, now)
        self.session.commit()
        # E-posta ancak kayıt kalıcı olunca gider: commit düşerse elde karşılıksız bağlantı kalmasın.
        self.email.send(message)
        return user

    def _verification_email(self, user: User, now: datetime) -> EmailMessage:
        token = self._issue_user_token(
            user, TokenPurpose.VERIFY_EMAIL, now + timedelta(hours=self.settings.verify_email_ttl_hours), now
        )
        link = f"{self.settings.frontend_url}/e-posta-dogrula?token={token}"
        return EmailMessage(
            to=user.email,
            subject="CareerAI: e-posta adresini doğrula",
            body=(
                f"Hesabını doğrulamak için bağlantıyı aç: {link}\n"
                f"Bağlantı {self.settings.verify_email_ttl_hours} saat geçerlidir."
            ),
            link=link,
        )

    def verify_email(self, token: str) -> None:
        user_token = self._consume_user_token(token, TokenPurpose.VERIFY_EMAIL)
        user = self.repo.get_active_by_id(user_token.user_id)
        if user is None:
            raise invalid_link()
        user.is_verified = True
        self.session.commit()

    # --- giriş / oturum
    def login(self, *, email: str, password: str, user_agent: str | None) -> TokenPair:
        user = self.repo.get_active_by_email(email)
        # Kullanıcı yoksa da parola doğrulaması çalışır (zamanlama eşitleme, security._DUMMY_HASH).
        if not security.verify_password(user.password_hash if user else None, password) or user is None:
            raise invalid_credentials()
        if security.password_needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)
        pair = self._issue_pair(user, user_agent)
        self.session.commit()
        return pair

    def refresh(self, *, refresh_token: str, user_agent: str | None) -> TokenPair:
        now = datetime.now(UTC)
        stored = self.repo.get_refresh_token_for_update(security.hash_token(refresh_token))
        if stored is None:
            raise invalid_refresh()
        if stored.revoked_at is not None:
            # Kullanılmış token tekrar geldi: çalınmış olabilir, bütün oturumları kapat.
            self.repo.revoke_all_refresh_tokens(stored.user_id, now)
            self.session.commit()
            raise invalid_refresh()
        if stored.expires_at <= now:
            raise invalid_refresh()
        user = self.repo.get_active_by_id(stored.user_id)
        if user is None:
            raise invalid_refresh()
        stored.revoked_at = now
        pair = self._issue_pair(user, user_agent, now)
        self.session.commit()
        return pair

    def logout(self, refresh_token: str) -> None:
        stored = self.repo.get_refresh_token_for_update(security.hash_token(refresh_token))
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            self.session.commit()

    def _issue_pair(self, user: User, user_agent: str | None, now: datetime | None = None) -> TokenPair:
        now = now or datetime.now(UTC)
        refresh = security.new_opaque_token()
        self.repo.add_refresh_token(
            RefreshToken(
                user_id=user.id,
                token_hash=security.hash_token(refresh),
                expires_at=now + timedelta(days=self.settings.refresh_token_ttl_days),
                user_agent=(user_agent or "")[:300] or None,
            )
        )
        role = user.role.value if isinstance(user.role, UserRole) else str(user.role)
        return TokenPair(
            access_token=security.create_access_token(user.id, role, self.settings, now),
            refresh_token=refresh,
            expires_in=self.settings.access_token_ttl_minutes * 60,
        )

    # --- şifre sıfırlama
    def forgot_password(self, email: str) -> None:
        """Kayıtlı olsun olmasın aynı yanıt verilir; sadece kayıtlıysa e-posta gider."""
        user = self.repo.get_active_by_email(email)
        if user is None:
            return
        now = datetime.now(UTC)
        token = self._issue_user_token(
            user,
            TokenPurpose.RESET_PASSWORD,
            now + timedelta(minutes=self.settings.reset_password_ttl_minutes),
            now,
        )
        link = f"{self.settings.frontend_url}/sifre-sifirla?token={token}"
        message = EmailMessage(
            to=user.email,
            subject="CareerAI: şifre sıfırlama",
            body=(
                f"Şifreni sıfırlamak için bağlantıyı aç: {link}\n"
                f"Bağlantı {self.settings.reset_password_ttl_minutes} dakika geçerlidir. "
                "Bu isteği sen yapmadıysan bu e-postayı yok sayabilirsin."
            ),
            link=link,
        )
        self.session.commit()
        self.email.send(message)

    def reset_password(self, *, token: str, new_password: str) -> None:
        user_token = self._consume_user_token(token, TokenPurpose.RESET_PASSWORD)
        user = self.repo.get_active_by_id(user_token.user_id)
        if user is None:
            raise invalid_link()
        now = datetime.now(UTC)
        user.password_hash = security.hash_password(new_password)
        # Sıfırlama bağlantısını açabilen kişi e-postaya sahiptir; doğrulanmış sayılır.
        user.is_verified = True
        self.repo.revoke_all_refresh_tokens(user.id, now)
        self.session.commit()

    # --- tek kullanımlık token
    def _issue_user_token(self, user: User, purpose: TokenPurpose, expires_at: datetime, now: datetime) -> str:
        self.repo.invalidate_user_tokens(user.id, purpose, now)
        token = security.new_opaque_token()
        self.repo.add_user_token(
            UserToken(user_id=user.id, purpose=purpose, token_hash=security.hash_token(token), expires_at=expires_at)
        )
        return token

    def _consume_user_token(self, token: str, purpose: TokenPurpose) -> UserToken:
        now = datetime.now(UTC)
        user_token = self.repo.get_user_token_for_update(security.hash_token(token), purpose)
        if user_token is None or user_token.used_at is not None or user_token.expires_at <= now:
            raise invalid_link()
        user_token.used_at = now
        return user_token
