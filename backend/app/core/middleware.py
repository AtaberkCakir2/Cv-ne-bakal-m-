"""İstek kimliği ve istek logu.

Her isteğe bir kimlik verilir (istemci X-Request-ID gönderdiyse o kullanılır) ve yanıta eklenir.
Hata bildirimlerinde bu kimlik sorulur; loglarda aynı kimlikle aranır.
"""

import logging
import re
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import problem
from app.core.logging import request_id_var

logger = logging.getLogger("careerai.request")

_SAFE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status = 500
        started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status, started
            if message["type"] == "http.response.start":
                status = message["status"]
                started = True
                message.setdefault("headers", []).append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # Beklenmeyen hata: istek kimliği hâlâ geçerliyken logla ve RFC 7807 yanıtı dön.
            # (FastAPI'nin kendi 500 işleyicisi bu middleware'in dışında çalışır, kimliği göremez.)
            if started:
                raise
            logger.exception("Beklenmeyen hata", extra={"fields": {"path": scope["path"]}})
            response = problem(500, None, None, instance=scope["path"])
            await response(scope, receive, send_wrapper)
        finally:
            logger.info(
                "istek",
                extra={
                    "fields": {
                        "method": scope["method"],
                        "path": scope["path"],
                        "status": status,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                    }
                },
            )
            request_id_var.reset(token)
