"""Kimlik doğrulama uçları (contracts/api.md, "Kimlik doğrulama"). Giriş/kayıt/sıfırlama uçlarında IP başına sınır var
(T-050, app/api/rate_limits.py)."""

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from app.api.deps import AppSettings, DbSession, get_email_sender
from app.api.rate_limits import AuthRateLimit
from app.schemas.auth import (
    EmailIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    RegisterOut,
    ResetPasswordIn,
    TokenIn,
    TokenOut,
)
from app.services.auth import AuthError, AuthService, ConsentInput, TokenPair
from app.services.email import EmailSender

router = APIRouter(prefix="/auth", tags=["Kimlik doğrulama"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}
UserAgent = Annotated[str | None, Header()]


def get_auth_service(
    db: DbSession, settings: AppSettings, email: Annotated[EmailSender, Depends(get_email_sender)]
) -> AuthService:
    return AuthService(db, settings, email)


Auth = Annotated[AuthService, Depends(get_auth_service)]


def _raise(exc: AuthError) -> NoReturn:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
    raise HTTPException(exc.status, exc.detail, headers=headers) from exc


def _tokens(pair: TokenPair) -> TokenOut:
    return TokenOut(access_token=pair.access_token, refresh_token=pair.refresh_token, expires_in=pair.expires_in)


@router.post(
    "/register",
    dependencies=[AuthRateLimit],
    status_code=201,
    response_model=RegisterOut,
    summary="Kayıt + KVKK rızaları",
    responses={409: {"description": "E-posta kayıtlı", **_PROBLEM}, 422: {"description": "Eksik onay", **_PROBLEM}},
)
def register(body: RegisterIn, request: Request, auth: Auth) -> RegisterOut:
    """Doğrulama bağlantısı e-postayla gönderilir. Üç onay da zorunludur."""
    try:
        user = auth.register(
            email=str(body.email),
            password=body.password,
            full_name=body.full_name,
            consents=[ConsentInput(c.consent_type, c.version) for c in body.consents],
            ip=request.client.host if request.client else None,
        )
    except AuthError as exc:
        _raise(exc)
    return RegisterOut(user_id=user.id)


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Giriş",
    dependencies=[AuthRateLimit],
    responses={401: {"description": "Hatalı bilgi", **_PROBLEM}, 429: {"description": "Çok fazla deneme", **_PROBLEM}},
)
def login(body: LoginIn, auth: Auth, user_agent: UserAgent = None) -> TokenOut:
    try:
        return _tokens(auth.login(email=str(body.email), password=body.password, user_agent=user_agent))
    except AuthError as exc:
        _raise(exc)


@router.post(
    "/refresh",
    response_model=TokenOut,
    summary="Token yenileme (rotasyonlu)",
    responses={401: {"description": "Geçersiz / kullanılmış / süresi dolmuş", **_PROBLEM}},
)
def refresh(body: RefreshIn, auth: Auth, user_agent: UserAgent = None) -> TokenOut:
    """Her refresh token tek kullanımlıktır; kullanılmış bir token tekrar gelirse bütün oturumlar kapatılır."""
    try:
        return _tokens(auth.refresh(refresh_token=body.refresh_token, user_agent=user_agent))
    except AuthError as exc:
        _raise(exc)


@router.post("/logout", status_code=204, summary="Çıkış (refresh token iptali)")
def logout(body: RefreshIn, auth: Auth) -> Response:
    auth.logout(body.refresh_token)
    return Response(status_code=204)


@router.post(
    "/verify-email",
    dependencies=[AuthRateLimit],
    status_code=204,
    summary="E-posta doğrulama",
    responses={400: {"description": "Bağlantı geçersiz", **_PROBLEM}},
)
def verify_email(body: TokenIn, auth: Auth) -> Response:
    try:
        auth.verify_email(body.token)
    except AuthError as exc:
        _raise(exc)
    return Response(status_code=204)


@router.post("/forgot-password", status_code=202, summary="Şifre sıfırlama e-postası", dependencies=[AuthRateLimit])
def forgot_password(body: EmailIn, auth: Auth) -> Response:
    """E-posta kayıtlı olsun olmasın 202 döner (hesap var mı yok mu belli edilmez)."""
    auth.forgot_password(str(body.email))
    return Response(status_code=202)


@router.post(
    "/reset-password",
    dependencies=[AuthRateLimit],
    status_code=204,
    summary="Yeni şifre belirleme",
    responses={400: {"description": "Bağlantı geçersiz", **_PROBLEM}},
)
def reset_password(body: ResetPasswordIn, auth: Auth) -> Response:
    """Başarılı olursa kullanıcının bütün oturumları kapatılır."""
    try:
        auth.reset_password(token=body.token, new_password=body.new_password)
    except AuthError as exc:
        _raise(exc)
    return Response(status_code=204)
