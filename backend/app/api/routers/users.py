"""Kullanıcı uçları. Şimdilik sadece GET /users/me (oturum kontrolü).

Güncelleme, KVKK dışa aktarma ve hesap silme T-049.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.auth import MeOut

router = APIRouter(prefix="/users", tags=["Kullanıcı"])


@router.get("/me", response_model=MeOut, summary="Profil")
def me(user: CurrentUser) -> MeOut:
    return MeOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role, is_verified=user.is_verified)
