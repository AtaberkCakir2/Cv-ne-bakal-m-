"""Kullanıcı uçları (contracts/api.md, "Kullanıcı (KVKK)"; T-049).

Profil, rıza kayıtları, verilerimi indir, hesabımı sil.
"""

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.rate_limits import AuthRateLimit
from app.db.enums import ConsentType
from app.schemas.users import ConsentOut, ConsentsIn, DeleteAccountIn, ExportOut, ProfileOut, ProfileUpdateIn
from app.services.auth import ConsentInput
from app.services.users import ProfileChanges, UserError, UserService, profile_out

router = APIRouter(prefix="/users", tags=["Kullanıcı"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}


def get_user_service(db: DbSession, settings: AppSettings) -> UserService:
    return UserService(db, settings)


Users = Annotated[UserService, Depends(get_user_service)]


def _raise(exc: UserError) -> NoReturn:
    raise HTTPException(exc.status, exc.detail) from exc


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/me", response_model=ProfileOut, summary="Profil")
def me(user: CurrentUser) -> ProfileOut:
    return profile_out(user)


@router.patch(
    "/me",
    response_model=ProfileOut,
    summary="Profil / hedef pozisyon güncelleme",
    responses={422: {"description": "Pozisyon bulunamadı", **_PROBLEM}},
)
def update_me(body: ProfileUpdateIn, user: CurrentUser, users: Users) -> ProfileOut:
    """Sadece gönderilen alanlar değişir. `target_role_id: null` hedef pozisyonu temizler."""
    changes = ProfileChanges(body.full_name, body.target_role_id, frozenset(body.model_fields_set))
    try:
        return profile_out(users.update_profile(user, changes))
    except UserError as exc:
        _raise(exc)


@router.get("/me/consents", response_model=list[ConsentOut], summary="Onay kayıtlarım (sürümlü)")
def my_consents(user: CurrentUser, users: Users) -> list[ConsentOut]:
    return users.consents(user)


@router.post("/me/consents", response_model=list[ConsentOut], summary="Metnin yeni sürümünü onayla")
def accept_consents(body: ConsentsIn, request: Request, user: CurrentUser, users: Users) -> list[ConsentOut]:
    """Yasal metin değişince istemci yeni sürümü burada onaylatır. Eski onay kayıtları silinmez."""
    try:
        return users.accept_consents(
            user, [ConsentInput(c.consent_type, c.version) for c in body.consents], _ip(request)
        )
    except UserError as exc:
        _raise(exc)


@router.delete(
    "/me/consents/{consent_type}",
    response_model=list[ConsentOut],
    summary="Açık rızayı geri al",
    responses={422: {"description": "Bu onay türü geri alınamaz", **_PROBLEM}},
)
def withdraw_consent(consent_type: ConsentType, request: Request, user: CurrentUser, users: Users) -> list[ConsentOut]:
    """KVKK md. 11. Onay kaydı silinmez, `withdrawn_at` dolar. Tekrar çağrılırsa bir şey değişmez."""
    try:
        return users.withdraw_consent(user, consent_type, _ip(request))
    except UserError as exc:
        _raise(exc)


@router.get("/me/export", response_model=ExportOut, summary="Verilerimi indir (JSON)")
def export_me(request: Request, user: CurrentUser, users: Users, response: Response) -> ExportOut:
    """KVKK md. 11: hesaba bağlı bütün kişisel veriler. CV dosyası ve metni saklanmadığı için yoktur."""
    response.headers["Content-Disposition"] = 'attachment; filename="careerai-verilerim.json"'
    response.headers["Cache-Control"] = "no-store"
    return users.export(user, _ip(request))


@router.delete(
    "/me",
    status_code=204,
    summary="Hesabımı sil",
    # Şifre denemesine açık: giriş uçlarıyla aynı IP sayacı
    dependencies=[AuthRateLimit],
    responses={403: {"description": "Şifre hatalı", **_PROBLEM}, 429: {"description": "Çok fazla deneme", **_PROBLEM}},
)
def delete_me(body: DeleteAccountIn, request: Request, user: CurrentUser, users: Users) -> Response:
    """Şifre tekrar istenir. Kişisel bilgiler hemen anonimleştirilir, oturumlar kapanır; hesap 30 gün sonra kalıcı
    olarak silinir."""
    try:
        users.delete_account(user, body.password, _ip(request))
    except UserError as exc:
        _raise(exc)
    return Response(status_code=204)
