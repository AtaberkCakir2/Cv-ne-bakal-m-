import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.enums import ConsentType, UserRole

# NIST 800-63B: en az 8 karakter; üst sınır argon2'ye aşırı uzun girdi verilmesini engeller.
Password = Field(min_length=8, max_length=128)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class ConsentIn(BaseModel):
    consent_type: ConsentType
    version: str = Field(min_length=1, max_length=20, description="Kabul edilen metnin sürümü, ör. 2026-12")


class RegisterIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "ogrenci@example.com",
                    "password": "ornek-sifre-123",
                    "full_name": "Örnek Öğrenci",
                    "consents": [
                        {"consent_type": "kvkk_aydinlatma", "version": "2026-12"},
                        {"consent_type": "acik_riza", "version": "2026-12"},
                        {"consent_type": "kullanim_kosullari", "version": "2026-12"},
                    ],
                }
            ]
        }
    )

    email: EmailStr
    password: str = Password
    full_name: str | None = Field(default=None, max_length=120)
    consents: list[ConsentIn] = Field(description="Üç onay da zorunlu: kvkk_aydinlatma, acik_riza, kullanim_kosullari")

    _email = field_validator("email")(_normalize_email)

    @field_validator("consents")
    @classmethod
    def _no_duplicate_consents(cls, value: list[ConsentIn]) -> list[ConsentIn]:
        # Aynı onay iki kez gelirse consents tablosundaki tekillik kısıtı commit'te 500 verirdi; burada 422 olur.
        types = [c.consent_type for c in value]
        if len(types) != len(set(types)):
            raise ValueError("Her onay türü bir kez gönderilmeli.")
        return value


class RegisterOut(BaseModel):
    user_id: uuid.UUID


class LoginIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "ogrenci@example.com", "password": "ornek-sifre-123"}]}
    )

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    _email = field_validator("email")(_normalize_email)


class TokenOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "kX3v9...",
                    "token_type": "bearer",
                    "expires_in": 900,
                }
            ]
        }
    )

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 — OAuth2 tür adı, şifre değil
    expires_in: int = Field(description="Access token ömrü (saniye)")


class RefreshIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"refresh_token": "kX3v9..."}]})

    refresh_token: str = Field(min_length=1, max_length=200)


class EmailIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "ogrenci@example.com"}]})

    email: EmailStr

    _email = field_validator("email")(_normalize_email)


class TokenIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"token": "e-postadaki-bağlantıdaki-token"}]})

    token: str = Field(min_length=1, max_length=200)


class ResetPasswordIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"token": "e-postadaki-bağlantıdaki-token", "new_password": "yeni-ornek-sifre-456"}]
        }
    )

    token: str = Field(min_length=1, max_length=200)
    new_password: str = Password


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    is_verified: bool
