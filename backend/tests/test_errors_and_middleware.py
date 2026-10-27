from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

PROBLEM = "application/problem+json"


class _Item(BaseModel):
    name: str
    count: int


def _add_test_routes(app: FastAPI) -> None:
    router = APIRouter()

    @router.post("/_test/validate")
    async def validate(item: _Item) -> _Item:
        return item

    @router.get("/_test/forbidden")
    async def forbidden() -> None:
        raise HTTPException(status_code=403, detail="Bu analiz size ait değil.")

    @router.get("/_test/limited")
    async def limited() -> None:
        raise HTTPException(status_code=429, headers={"Retry-After": "60"})

    @router.get("/_test/crash")
    async def crash() -> None:
        raise RuntimeError("SELECT * FROM users WHERE email='gizli@ornek.com'")

    app.include_router(router)


def test_not_found_is_problem_json(client: TestClient) -> None:
    response = client.get("/yok-boyle-bir-yer")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Bulunamadı"
    assert body["instance"] == "/yok-boyle-bir-yer"
    assert body["request_id"] == response.headers["x-request-id"]
    assert "detail" not in body  # "Not Found" gibi varsayılan İngilizce ifade tekrar edilmez


def test_http_exception_keeps_custom_detail(app: FastAPI, client: TestClient) -> None:
    _add_test_routes(app)
    response = client.get("/_test/forbidden")
    assert response.status_code == 403
    assert response.json()["detail"] == "Bu analiz size ait değil."


def test_http_exception_headers_are_kept(app: FastAPI, client: TestClient) -> None:
    _add_test_routes(app)
    response = client.get("/_test/limited")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert response.json()["title"] == "Çok fazla istek"


def test_validation_error_lists_fields(app: FastAPI, client: TestClient) -> None:
    _add_test_routes(app)
    response = client.post("/_test/validate", json={"name": "x", "count": "çok"})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body["title"] == "Doğrulama hatası"
    assert [e["field"] for e in body["errors"]] == ["count"]


def test_unhandled_error_is_generic_500_with_request_id(app: FastAPI, client: TestClient) -> None:
    _add_test_routes(app)
    response = client.get("/_test/crash", headers={"X-Request-ID": "test-kimlik-123"})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body == {
        "type": "about:blank",
        "title": "Beklenmeyen bir hata oluştu",
        "status": 500,
        "request_id": "test-kimlik-123",
        "instance": "/_test/crash",
    }
    assert "SELECT" not in response.text and "gizli@ornek.com" not in response.text


def test_request_id_is_generated_and_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 32


def test_safe_incoming_request_id_is_reused_unsafe_is_replaced(client: TestClient) -> None:
    assert client.get("/api/v1/health", headers={"X-Request-ID": "abc-12345678"}).headers["x-request-id"] == (
        "abc-12345678"
    )
    unsafe = client.get("/api/v1/health", headers={"X-Request-ID": "<script>"}).headers["x-request-id"]
    assert unsafe != "<script>" and len(unsafe) == 32


def test_openapi_is_served_under_api_prefix(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths and "/api/v1/health/ready" in paths
    assert client.get("/docs").status_code == 200
