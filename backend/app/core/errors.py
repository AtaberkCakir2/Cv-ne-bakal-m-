"""Global hata formatı: RFC 7807 (application/problem+json).

Tüm hatalar aynı biçimde döner; istemciler sadece bu şemayı bilir:
    {"type", "title", "status", "detail", "instance", "request_id", "errors"?}
Beklenmeyen hatalarda iç ayrıntı (stack trace, SQL vb.) kullanıcıya gösterilmez, sadece loglanır.
"""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var

PROBLEM_JSON = "application/problem+json"

_TITLES = {
    400: "Geçersiz istek",
    401: "Kimlik doğrulama gerekli",
    403: "Bu işlem için yetkiniz yok",
    404: "Bulunamadı",
    405: "Bu yöntem desteklenmiyor",
    409: "Çakışma",
    411: "Content-Length gerekli",
    413: "Dosya çok büyük",
    415: "Desteklenmeyen dosya türü",
    422: "Doğrulama hatası",
    429: "Çok fazla istek",
    500: "Beklenmeyen bir hata oluştu",
    503: "Servis şu an kullanılamıyor",
}


def problem(status: int, detail: str | None = None, request: Request | None = None, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": _TITLES.get(status, "Hata"),
        "status": status,
    }
    if detail:
        body["detail"] = detail
    if request is not None:
        body["instance"] = request.url.path
    request_id = request_id_var.get()
    if request_id:
        body["request_id"] = request_id
    body.update(extra)
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


async def _http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    detail = exc.detail if isinstance(exc.detail, str) and exc.detail != _default_phrase(exc.status_code) else None
    response = problem(exc.status_code, detail, request)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _validation_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"field": ".".join(str(p) for p in err.get("loc", ()) if p != "body"), "message": err.get("msg", "")}
        for err in exc.errors()
    ]
    return problem(422, "İstekteki bazı alanlar geçersiz.", request, errors=errors)


def _default_phrase(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return ""


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception)
    app.add_exception_handler(RequestValidationError, _validation_exception)
    # Beklenmeyen hatalar (500) app.core.middleware.RequestContextMiddleware içinde yakalanır.
