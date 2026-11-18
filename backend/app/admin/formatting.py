"""Panelde tarih gösterimi: Türkiye saati, saniyesiz. Türkiye yaz saati uygulamadığı için sabit UTC+3 yeterli
(zoneinfo Windows'ta ayrıca tzdata paketi ister)."""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

TR = timezone(timedelta(hours=3), "TRT")

ANALYSIS_STATUS_TR = {"queued": "kuyrukta", "processing": "işleniyor", "done": "bitti", "failed": "hata"}


def fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(TR).strftime("%d.%m.%Y %H:%M")


def dt_column(model: Any, attribute: str) -> str:
    """SQLAdmin `column_formatters` imzası: (model, sütun adı)."""
    return fmt_dt(getattr(model, attribute))
