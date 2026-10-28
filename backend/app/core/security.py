"""Parola hash'i, JWT ve tek kullanımlık token yardımcıları (T-037).

- Parolalar argon2id ile hash'lenir; parametreler değişince girişte kendiliğinden yeniden hash'lenir.
- Access token: kısa ömürlü JWT (varsayılan 15 dk), sunucuda saklanmaz.
- Refresh / doğrulama / sıfırlama token'ları rastgeledir; veritabanında sadece SHA-256 hash'i tutulur.
"""

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings

_hasher = PasswordHasher()
# Kullanıcı yokken de aynı süre harcansın (e-posta var mı yok mu, yanıt süresinden anlaşılmasın).
_DUMMY_HASH = _hasher.hash("careerai-zamanlama-esitleme")

ACCESS_TOKEN_TYPE = "access"  # noqa: S105 — JWT tür alanı, şifre değil


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_opaque_token() -> str:
    """URL'de taşınabilen 256 bit rastgele token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_ip(ip: str | None, settings: Settings) -> str | None:
    """KVKK rızası için IP'nin anahtarlı hash'i; açık IP saklanmaz (docs/veritabani.md, consents)."""
    if not ip:
        return None
    return hmac.new(settings.jwt_secret.encode(), ip.encode(), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class AccessClaims:
    user_id: uuid.UUID
    role: str


def create_access_token(user_id: uuid.UUID, role: str, settings: Settings, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str, settings: Settings) -> AccessClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],  # "none" ve başka algoritmalar reddedilir
            options={"require": ["sub", "exp", "iat", "type"]},
        )
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise InvalidTokenError("access token değil")
        return AccessClaims(user_id=uuid.UUID(payload["sub"]), role=str(payload.get("role", "")))
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise InvalidTokenError(type(exc).__name__) from exc
