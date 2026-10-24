import asyncio
import hashlib
import io
import tempfile
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.core.uploads import MAX_PDF_BYTES, UploadSizeLimitMiddleware

URL = "/api/v1/analyses"
PROBLEM = "application/problem+json"


def make_pdf(pages: int = 1, password: str | None = None, owner_only: bool = False) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    if password:
        writer.encrypt(user_password="" if owner_only else password, owner_password=password)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def upload(client: TestClient, content: bytes, content_type: str = "application/pdf", role: str | None = "1"):  # type: ignore[no-untyped-def]
    data = {"target_role_id": role} if role is not None else {}
    return client.post(URL, files={"file": ("ozgecmis.pdf", content, content_type)}, data=data)


def assert_problem(response, status: int, code: str) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["request_id"] == response.headers["x-request-id"]


def test_valid_pdf_is_accepted_and_result_is_available(client: TestClient) -> None:
    response = upload(client, make_pdf(2))
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    analysis_id = uuid.UUID(body["analysis_id"])

    result = client.get(f"{URL}/{analysis_id}")
    assert result.status_code == 200
    data = result.json()
    assert data["analysis_id"] == str(analysis_id)
    assert data["status"] == "done"
    assert data["missing_skills"][0]["skill"] == "Docker"  # contracts/examples sahte sonucu


def test_only_hash_and_page_count_are_stored_not_the_cv(app: FastAPI, client: TestClient) -> None:
    pdf = make_pdf(3)
    analysis_id = uuid.UUID(upload(client, pdf).json()["analysis_id"])
    record = app.state.analysis_service.repository.get(analysis_id)
    assert record.cv_sha256 == hashlib.sha256(pdf).hexdigest()
    assert record.cv_pages == 3
    assert pdf not in repr(vars(record)).encode()  # kayıtta CV baytları yok


def test_upload_is_never_written_to_disk(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Starlette varsayılanında 1 MB'ı aşan dosya geçici diske yazılırdı (rollover).
    rolled: list[int] = []
    original = tempfile.SpooledTemporaryFile.rollover

    def spy(self: tempfile.SpooledTemporaryFile) -> None:  # type: ignore[type-arg]
        rolled.append(1)
        original(self)

    monkeypatch.setattr(tempfile.SpooledTemporaryFile, "rollover", spy)
    almost_max = b"%PDF-1.4\n" + b"0" * (MAX_PDF_BYTES - 100)
    response = upload(client, almost_max)
    assert response.status_code == 422  # içerik bozuk PDF; önemli olan diske yazılmaması
    assert rolled == []


@pytest.mark.parametrize(
    ("content", "content_type"),
    [
        (b"\x89PNG\r\n\x1a\n" + b"0" * 100, "application/pdf"),  # PDF diye gönderilmiş PNG
        (b"PK\x03\x04" + b"0" * 100, "application/pdf"),  # PDF diye gönderilmiş DOCX/ZIP
        (make_pdf(1), "image/png"),  # PDF ama türü yanlış bildirilmiş
    ],
)
def test_non_pdf_is_rejected(client: TestClient, content: bytes, content_type: str) -> None:
    assert_problem(upload(client, content, content_type), 415, "PDF_UNREADABLE")


def test_octet_stream_pdf_is_accepted(client: TestClient) -> None:
    # Bazı tarayıcı/mobil istemciler türü bildirmez; imza PDF ise kabul edilir.
    assert upload(client, make_pdf(1), "application/octet-stream").status_code == 202


def test_more_than_five_pages_is_rejected(client: TestClient) -> None:
    assert upload(client, make_pdf(5)).status_code == 202
    response = upload(client, make_pdf(6))
    assert_problem(response, 422, "PDF_TOO_LARGE")
    assert "5 sayfa" in response.json()["detail"]


def test_encrypted_pdf_is_rejected(client: TestClient) -> None:
    response = upload(client, make_pdf(1, password="gizli"))
    assert_problem(response, 422, "PDF_UNREADABLE")
    assert "Şifreli" in response.json()["detail"]  # kod sözleşmedeki gibi genel, mesaj nedeni söylüyor


def test_edit_restricted_pdf_without_open_password_is_accepted(client: TestClient) -> None:
    # Boş kullanıcı şifreli ("sadece düzenleme kısıtlı") PDF herkesçe açılabilir; reddedilmemeli.
    assert upload(client, make_pdf(1, password="sahip", owner_only=True)).status_code == 202


@pytest.mark.parametrize("content", [b"%PDF-1.4\nbozuk dosya", b""])
def test_corrupt_or_empty_pdf_is_rejected(client: TestClient, content: bytes) -> None:
    assert_problem(upload(client, content), 422, "PDF_UNREADABLE")


def test_file_over_5mb_is_rejected_by_validation(client: TestClient) -> None:
    # İstek sınırının altında ama dosya 5 MB'tan büyük
    assert_problem(upload(client, b"%PDF-1.4\n" + b"0" * MAX_PDF_BYTES), 413, "PDF_TOO_LARGE")


def test_request_over_limit_is_rejected_before_reading_body(client: TestClient) -> None:
    assert_problem(upload(client, b"%PDF-1.4\n" + b"0" * (MAX_PDF_BYTES + 100_000)), 413, "PDF_TOO_LARGE")


def test_missing_content_length_is_rejected() -> None:
    sent: list[dict[str, object]] = []

    async def downstream(scope, receive, send):  # type: ignore[no-untyped-def]
        raise AssertionError("gövde okunmamalıydı")

    async def receive():  # type: ignore[no-untyped-def]
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):  # type: ignore[no-untyped-def]
        sent.append(message)

    middleware = UploadSizeLimitMiddleware(downstream, paths=(URL,))
    scope = {"type": "http", "method": "POST", "path": URL, "headers": [], "query_string": b""}
    asyncio.run(middleware(scope, receive, send))
    assert sent[0]["status"] == 411


def test_missing_target_role_is_validation_error(client: TestClient) -> None:
    response = upload(client, make_pdf(1), role=None)
    assert response.status_code == 422
    assert [e["field"] for e in response.json()["errors"]] == ["target_role_id"]


def test_unknown_analysis_is_404(client: TestClient) -> None:
    response = client.get(f"{URL}/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Analiz bulunamadı."
    assert client.get(f"{URL}/uuid-degil").status_code == 422
