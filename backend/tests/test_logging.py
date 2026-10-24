import json
import logging

import pytest

from app.core.logging import JsonFormatter, mask_pii, request_id_var


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("kullanıcı ali.veli@ornek.com.tr giriş yaptı", "kullanıcı [E-POSTA] giriş yaptı"),
        ("tel: 0532 123 45 67", "tel: [TELEFON]"),
        ("tel: +90 532-123-45-67", "tel: [TELEFON]"),
        ("tel: 5321234567", "tel: [TELEFON]"),
        ("analiz süresi 61234 ms, 150 ilan", "analiz süresi 61234 ms, 150 ilan"),
    ],
)
def test_mask_pii(raw: str, expected: str) -> None:
    assert mask_pii(raw) == expected


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
