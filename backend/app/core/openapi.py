"""OpenAPI tanımının son rötuşları (T-080).

FastAPI hata yanıtlarını kendi biçimiyle (HTTPValidationError) belgeler; bu API ise her hatayı RFC 7807 biçiminde
döner (app/core/errors.py). Burada tek bir `Problem` şeması tanımlanır ve tüm 4xx/5xx yanıtları ona bağlanır.
Böylece /docs ve web'in ürettiği tipler gerçek yanıtla aynı olur.
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.errors import PROBLEM_JSON

PROBLEM_SCHEMA: dict[str, Any] = {
    "title": "Problem",
    "type": "object",
    "description": "RFC 7807 hata biçimi. Tüm 4xx/5xx yanıtları bu şemadadır.",
    "required": ["type", "title", "status"],
    "properties": {
        "type": {"type": "string", "example": "about:blank"},
        "title": {"type": "string", "description": "Durum koduna göre Türkçe başlık"},
        "status": {"type": "integer"},
        "detail": {"type": "string", "description": "Kullanıcıya gösterilebilecek Türkçe açıklama"},
        "instance": {"type": "string", "description": "İsteğin yolu"},
        "request_id": {"type": "string", "description": "Destek için; X-Request-ID başlığıyla aynı"},
        "code": {"type": "string", "description": "Bazı hatalarda makine okunur kod, ör. PDF_TOO_LARGE"},
        "errors": {
            "type": "array",
            "description": "Sadece 422: geçersiz alanlar",
            "items": {
                "type": "object",
                "required": ["field", "message"],
                "properties": {"field": {"type": "string"}, "message": {"type": "string"}},
            },
        },
    },
    "example": {
        "type": "about:blank",
        "title": "Doğrulama hatası",
        "status": 422,
        "detail": "İstekteki bazı alanlar geçersiz.",
        "instance": "/api/v1/auth/register",
        "request_id": "7f9c2b1e4a5d4c3b8e6f0a1b2c3d4e5f",
        "errors": [{"field": "email", "message": "value is not a valid email address"}],
    },
}
_PROBLEM_REF = {"$ref": "#/components/schemas/Problem"}


def _use_problem_schema(schema: dict[str, Any]) -> None:
    for path, operations in schema.get("paths", {}).items():
        for operation in operations.values():
            _fix_responses(path, operation["responses"])
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    for unused in ("HTTPValidationError", "ValidationError"):
        components.pop(unused, None)
    components["Problem"] = PROBLEM_SCHEMA


def _has_own_model(response: dict[str, Any]) -> bool:
    """Hata kodunda kendi gövdesini dönen uçlar (ör. /health/ready 503 → ReadinessResponse) olduğu gibi kalır."""
    ref = response.get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
    return bool(ref) and not ref.endswith("/HTTPValidationError")


def _fix_responses(path: str, responses: dict[str, Any]) -> None:
    # Genel sınır (100/dk/IP) sadece tam `/health` yolunu muaf tutar; `/health/ready` dahil (app/main.py).
    if not path.endswith("/health"):
        responses.setdefault(
            "429", {"description": "İstek sınırı aşıldı; `Retry-After` kaç saniye sonra denenebileceğini söyler"}
        )
    for status, response in responses.items():
        if status[:1] not in {"4", "5"} or _has_own_model(response):
            continue
        if status == "422" and response.get("description") == "Validation Error":
            response["description"] = "Geçersiz alanlar (`errors` listesinde)"
        response["content"] = {PROBLEM_JSON: {"schema": _PROBLEM_REF}}


def install_openapi(app: FastAPI) -> None:
    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
                tags=app.openapi_tags,
                servers=app.servers,
            )
            _use_problem_schema(schema)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
