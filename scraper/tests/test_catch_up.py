"""Kaçan gece toplamasının açılışta telafisi (T-075, R-18)."""

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from collector import tasks

IST = ZoneInfo("Europe/Istanbul")


def ist(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=IST)


@pytest.mark.parametrize(
    ("last", "now", "missed"),
    [
        # Dün 03:00'te çalıştı, bugün 03:00'te PC kapalıydı, 09:00'da açıldı → kaçmış.
        (ist(14, 3, 1), ist(15, 9), True),
        # Bugün 03:00'te çalıştı → kaçmamış.
        (ist(15, 3, 1), ist(15, 9), False),
        # Gece 02:00, bugünün 03:00'ü henüz gelmedi; dünkü yapılmış → kaçmamış.
        (ist(14, 3, 1), ist(15, 2), False),
        # Gece 02:00, dünkü de yapılmamış → kaçmış.
        (ist(13, 3, 1), ist(15, 2), True),
        # 03:05'te açıldı: beat tetikleyecek, ikinci kez kuyruğa konmaz.
        (ist(14, 3, 1), ist(15, 3, 5), False),
        # Hiç toplama yok (yeni kurulum) → başlatılır.
        (None, ist(15, 9), True),
        # Veritabanından UTC gelir: 00:01 UTC = 03:01 İstanbul, bugün yapılmış.
        (datetime(2026, 11, 15, 0, 1, tzinfo=UTC), ist(15, 9), False),
    ],
)
def test_missed_nightly(last: datetime | None, now: datetime, missed: bool) -> None:
    assert tasks.missed_nightly(last, now) is missed


class _FakeSession:
    def __init__(self, last: datetime | None) -> None:
        self.last = last

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def scalar(self, _query: Any) -> datetime | None:
        return self.last


def test_worker_start_queues_missed_nightly(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[dict[str, Any]] = []
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: lambda: _FakeSession(None))
    monkeypatch.setattr(tasks.nightly, "apply_async", lambda **kw: queued.append(kw))

    tasks._catch_up_missed_nightly()

    assert queued == [{"expires": 6 * 3600}]


def test_worker_start_survives_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> Any:
        raise OSError("veritabanı yok")

    queued: list[object] = []
    monkeypatch.setattr(tasks, "get_sessionmaker", broken)
    monkeypatch.setattr(tasks.nightly, "apply_async", lambda **kw: queued.append(kw))

    tasks._catch_up_missed_nightly()  # hata fırlatmaz

    assert queued == []
