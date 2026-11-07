"""Dosya yükleme sınırları ve "diske yazmama" garantisi (karar #9, T-038).

Starlette, multipart dosyaları SpooledTemporaryFile'da tutar ve 1 MB'ı aşınca **geçici disk dosyasına**
yazar. CV'ler 5 MB'a kadar olabildiği için bu eşik izin verilen en büyük istek boyutunun üstüne çekilir;
böylece CV hiçbir zaman diske dokunmaz. Belleği korumak için de büyük istekler gövde okunmadan
Content-Length'e bakılarak reddedilir (UploadSizeLimitMiddleware).
"""

from starlette.formparsers import MultiPartParser
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.errors import problem

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 5
# Multipart zarfı (sınırlar, başlıklar, form alanları) için pay
MAX_UPLOAD_REQUEST_BYTES = MAX_PDF_BYTES + 64 * 1024


def keep_uploads_in_memory() -> None:
    MultiPartParser.spool_max_size = MAX_UPLOAD_REQUEST_BYTES


class UploadSizeLimitMiddleware:
    """Belirtilen yollara gelen POST isteklerinde Content-Length zorunlu ve üst sınırlıdır."""

    def __init__(self, app: ASGIApp, paths: tuple[str, ...], max_bytes: int = MAX_UPLOAD_REQUEST_BYTES) -> None:
        self.app = app
        self.paths = paths
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "POST" and scope["path"] in self.paths:
            raw = dict(scope["headers"]).get(b"content-length")
            if raw is None or not raw.isdigit():
                response = problem(411, "İstekte Content-Length başlığı olmalı.", None, instance=scope["path"])
                await response(scope, receive, send)
                return
            if int(raw) > self.max_bytes:
                response = problem(
                    413, "Dosya en fazla 5 MB olabilir.", None, instance=scope["path"], code="PDF_TOO_LARGE"
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
