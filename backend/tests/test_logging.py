import json
import logging

import pytest

from app.core.config import Settings
from app.core.logging import JsonFormatter, configure_logging, mask_pii, request_id_var


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("kullanıcı ali.veli@ornek.com.tr giriş yaptı", "kullanıcı [E-POSTA] giriş yaptı"),
        ("tel: 0532 123 45 67", "tel: [TELEFON]"),
        ("tel: +90 532-123-45-67", "tel: [TELEFON]"),
        ("tel: 5321234567", "tel: [TELEFON]"),
        ("tckn 12345678901 girildi", "tckn [TCKN] girildi"),
        ("tel 05321234567", "tel [TELEFON]"),  # 11 hane ama 0 ile başlıyor → TCKN değil, telefon
        ("analiz süresi 61234 ms, 150 ilan", "analiz süresi 61234 ms, 150 ilan"),
        (
            "analiz 3f6c2a9e8d1b4c7a9e2f1a2b3c4d5e6f",
            "analiz 3f6c2a9e8d1b4c7a9e2f1a2b3c4d5e6f",
        ),  # istek kimliği bozulmaz
    ],
)
def test_mask_pii(raw: str, expected: str) -> None:
    assert mask_pii(raw) == expected


def test_noisy_library_loggers_are_quiet() -> None:
    configure_logging("INFO")
    assert logging.getLogger("httpx").getEffectiveLevel() == logging.WARNING


def test_default_service_urls_use_ipv4_not_localhost() -> None:
    # Windows'ta localhost → ::1; compose portları 127.0.0.1'de. localhost kullanılırsa Redis zaman aşımına uğrar.
    settings = Settings(_env_file=None)
    for url in (settings.database_url, settings.redis_url, settings.ollama_url):
        assert "localhost" not in url and "127.0.0.1" in url


def test_json_formatter_includes_request_id_and_fields_and_masks() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "giriş: %s", ("a@b.co",), None)
    record.fields = {"path": "/api/v1/health", "status": 200}
    token = request_id_var.set("kimlik-1")
    try:
        line = JsonFormatter().format(record)
    finally:
        request_id_var.reset(token)
    data = json.loads(line)
    assert data["message"] == "giriş: [E-POSTA]"
    assert data["request_id"] == "kimlik-1"
    assert data["path"] == "/api/v1/health" and data["status"] == 200
    assert data["level"] == "INFO"
