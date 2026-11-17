"""Veri işçisinin logu JSON ve maskeli (T-067)."""

import json
import logging
from collections.abc import Iterator

import pytest

from collector import tasks


@pytest.fixture
def restore_root_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def test_celery_logging_is_json_and_masked(restore_root_logging: None, capsys: pytest.CaptureFixture[str]) -> None:
    tasks._json_logging()

    logging.getLogger("collector.nightly").warning("ilan sahibi ali.veli@example.com, tel 0532 123 45 67")

    line = capsys.readouterr().out.strip().splitlines()[-1]
    entry = json.loads(line)
    assert entry["level"] == "WARNING"
    assert entry["logger"] == "collector.nightly"
    assert entry["message"] == "ilan sahibi [E-POSTA], tel [TELEFON]"


def test_celery_does_not_hijack_logging() -> None:
    from celery.signals import setup_logging

    assert setup_logging.receivers, "setup_logging sinyaline bağlı fonksiyon yok: Celery düz metin log kurar"
