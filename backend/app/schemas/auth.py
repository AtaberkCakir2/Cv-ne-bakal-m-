import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.enums import ConsentType, UserRole

# NIST 800-63B: en az 8 karakter; üst sınır argon2'ye aşırı uzun girdi verilmesini engeller.
Password = Field(min_length=8, max_length=128)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class ConsentIn(BaseModel):
    consent_type: ConsentType
    version: str = Field(min_length=1, max_length=20, description="Kabul edilen metnin sürümü, ör. 2026-12")


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Password
    full_name: str | None = Field(default=None, max_length=120)
    consents: list[ConsentIn] = Field(description="Üç onay da zorunlu: kvkk_aydinlatma, acik_riza, kullanim_kosullari")

    _email = field_validator("email")(_normalize_email)


class RegisterOut(BaseModel):
    user_id: uuid.UUID


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    _email = field_validator("email")(_normalize_email)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 — OAuth2 tür adı, şifre değil
    expires_in: int = Field(description="Access token ömrü (saniye)")


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=200)


class EmailIn(BaseModel):
    email: EmailStr

    _email = field_validator("email")(_normalize_email)


class TokenIn(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=1, max_length=200)
    new_password: str = Password


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    is_verified: bool
