"""Ortak FastAPI bağımlılıkları: veritabanı oturumu, e-posta gönderici, oturum açmış kullanıcı ve rol kontrolü."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import Settings, get_settings
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import get_sessionmaker
from app.repositories.users import UserRepository
from app.services.email import EmailSender

_bearer = HTTPBearer(auto_error=False, description="Access token (POST /auth/login)")
_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_db() -> Iterator[Session]:
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def get_email_sender(request: Request) -> EmailSender:
    sender: EmailSender = request.app.state.email_sender
    return sender


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DbSession,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(401, "Giriş yapmanız gerekiyor.", headers=_UNAUTHORIZED_HEADERS)
    try:
        claims = security.decode_access_token(credentials.credentials, settings)
    except security.InvalidTokenError as exc:
        raise HTTPException(401, "Oturum geçersiz veya süresi dolmuş.", headers=_UNAUTHORIZED_HEADERS) from exc
    # Rol token'dan değil veritabanından okunur: rolü düşürülen kullanıcı yeni token beklemeden yetkisini kaybeder.
    user = UserRepository(db).get_active_by_id(claims.user_id)
    if user is None:
        raise HTTPException(401, "Oturum geçersiz veya süresi dolmuş.", headers=_UNAUTHORIZED_HEADERS)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "Bu işlem için yönetici yetkisi gerekiyor.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
