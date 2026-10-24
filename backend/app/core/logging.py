"""Yapılandırılmış (JSON) log, istek kimliği ve kişisel veri maskeleme.

Kural (karar #9): loglara e-posta, telefon veya CV içeriği yazılmaz. Maskeleme filtresi
yanlışlıkla yazılan e-posta ve telefon numaralarını ikinci bir güvenlik katmanı olarak gizler.
"""

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?90[\s-]?)?0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)")


def mask_pii(text: str) -> str:
    return _PHONE.sub("[TELEFON]", _EMAIL.sub("[E-POSTA]", text))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
        }
        request_id = request_id_var.get()
        if request_id:
            entry["request_id"] = request_id
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            entry.update({k: mask_pii(v) if isinstance(v, str) else v for k, v in extra.items()})
        if record.exc_info:
            entry["exception"] = mask_pii(self.formatException(record.exc_info))
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # uvicorn'un kendi erişim logu yerine istek logunu middleware yazar
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
