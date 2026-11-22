"""Kaçan gece toplamasının ve haftalık link kontrolünün açılışta telafisi (T-075, R-18, go-live #35)."""

from datetime import UTC, datetime, timedelta
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


@pytest.mark.parametrize(
    ("last", "now", "missed"),
    [
        # Hiç kontrol yok (production'daki durum) → başlatılır.
        (None, ist(18, 9), True),
        # 3 gün önce kontrol edildi → kaçmamış.
        (ist(15, 7, 1), ist(18, 9), False),
        # Geçen pazar 07:00 yapıldı, bu pazar 07:05'te açıldı: 7 gün + 10 dk dolmadı → beat'e bırakılır.
        (ist(8, 7, 0), ist(15, 7, 5), False),
        # Geçen pazar yapıldı, bu pazar PC kapalıydı, pazartesi açıldı → kaçmış.
        (ist(8, 7, 0), ist(16, 9), True),
        # Veritabanından saat dilimsiz gelirse UTC sayılır.
        (datetime(2026, 11, 1, 4, 0), ist(18, 9), True),
    ],
)
def test_missed_link_check(last: datetime | None, now: datetime, missed: bool) -> None:
    assert tasks.missed_link_check(last, now) is missed


def test_worker_start_queues_missed_link_check(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[dict[str, Any]] = []
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: lambda: _FakeSession(None))
    monkeypatch.setattr(tasks.resources_check, "apply_async", lambda **kw: queued.append(kw))

    tasks._catch_up_missed_link_check()

    assert queued == [{"expires": 12 * 3600}]


def test_worker_start_skips_recent_link_check(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[object] = []
    recent = datetime.now(UTC)
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: lambda: _FakeSession(recent))
    monkeypatch.setattr(tasks.resources_check, "apply_async", lambda **kw: queued.append(kw))

    tasks._catch_up_missed_link_check()

    assert queued == []


def test_link_check_catch_up_survives_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> Any:
        raise OSError("veritabanı yok")

    queued: list[object] = []
    monkeypatch.setattr(tasks, "get_sessionmaker", broken)
    monkeypatch.setattr(tasks.resources_check, "apply_async", lambda **kw: queued.append(kw))

    tasks._catch_up_missed_link_check()  # hata fırlatmaz

    assert queued == []


# --- Aynı gecenin ikinci kez toplanmaması (22.11.2026: beat + açılış telafisi aynı geceyi iki kez kuyruğa koydu) ---


@pytest.mark.parametrize(
    ("now", "slot"),
    [
        (ist(22, 3, 23), ist(22, 3)),
        (ist(22, 3, 0), ist(22, 3)),
        (ist(22, 2, 59), ist(21, 3)),
        # UTC verilse de İstanbul 03:00'ü bulunur: 23:30 UTC = 02:30 İstanbul.
        (datetime(2026, 11, 21, 23, 30, tzinfo=UTC), ist(21, 3)),
    ],
)
def test_nightly_slot(now: datetime, slot: datetime) -> None:
    assert tasks.nightly_slot(now) == slot


class _FakeLock:
    def __init__(self, free: bool = True) -> None:
        self.free = free
        self.released = False

    def acquire(self) -> bool:
        return self.free

    def release(self) -> None:
        self.released = True


class _FakeReport:
    ok = True
    inserted = 3
    stats_rows = 7

    def summary(self) -> str:
        return "özet"


@pytest.fixture
def nightly_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    env: dict[str, Any] = {"lock": _FakeLock(), "runs": 0, "last": None}

    class _FakeRedis:
        @staticmethod
        def from_url(_url: str) -> Any:
            return type("R", (), {"lock": lambda self, *a, **kw: env["lock"]})()

    def fake_run(_sessionmaker: Any) -> _FakeReport:
        env["runs"] += 1
        return _FakeReport()

    monkeypatch.setattr(tasks, "Redis", _FakeRedis)
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: None)
    monkeypatch.setattr(tasks, "run_nightly", fake_run)
    monkeypatch.setattr(tasks, "_last_nightly_start", lambda: env["last"])
    return env


def test_nightly_skips_when_tonight_already_collected(nightly_env: dict[str, Any]) -> None:
    # Telafi 03:23'te bu geceyi topladı; beat'in görevi ardından gelince tekrar toplamaz.
    nightly_env["last"] = datetime.now(UTC)

    assert tasks.nightly() == {"skipped": True}
    assert nightly_env["runs"] == 0
    assert nightly_env["lock"].released


def test_nightly_runs_when_last_collection_is_before_slot(nightly_env: dict[str, Any]) -> None:
    nightly_env["last"] = tasks.nightly_slot(datetime.now(UTC)) - timedelta(minutes=1)

    assert tasks.nightly() == {"inserted": 3, "stats_rows": 7, "ok": True}
    assert nightly_env["runs"] == 1
    assert nightly_env["lock"].released


def test_nightly_runs_on_fresh_install(nightly_env: dict[str, Any]) -> None:
    assert tasks.nightly()["inserted"] == 3
    assert nightly_env["runs"] == 1


def test_nightly_force_collects_again(nightly_env: dict[str, Any]) -> None:
    nightly_env["last"] = datetime.now(UTC)

    assert tasks.nightly(force=True)["inserted"] == 3
    assert nightly_env["runs"] == 1


def test_nightly_skips_when_locked(nightly_env: dict[str, Any]) -> None:
    nightly_env["lock"] = _FakeLock(free=False)

    assert tasks.nightly() == {"skipped": True}
    assert nightly_env["runs"] == 0
