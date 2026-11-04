"""Kuyruk parçaları (T-039): servis gerekmez. Veritabanı isteyen senaryolar tests/auth/test_analyses_queue.py'de."""

import uuid

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import Settings
from app.services.analysis_queue import CeleryAnalysisQueue, QueueUnavailable, build_analysis_queue
from app.services.analyzer import AnalysisFailed, ExampleAnalyzer, UnavailableAnalyzer, build_analyzer


class Store:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, bytes] = {}
        self.fail = False

    def put(self, analysis_id: uuid.UUID, content: bytes) -> None:
        if self.fail:
            raise RedisConnectionError
        self.items[analysis_id] = content

    def get(self, analysis_id: uuid.UUID) -> bytes | None:
        return self.items.get(analysis_id)

    def delete(self, analysis_id: uuid.UUID) -> None:
        self.items.pop(analysis_id, None)

    def count(self) -> int:
        return len(self.items)


def settings(**values: object) -> Settings:
    return Settings(_env_file=None, redis_url="redis://cache:6379/0", jwt_secret="x" * 40, **values)  # type: ignore[arg-type]


def test_message_has_only_the_id_and_the_cv_goes_to_the_store() -> None:
    store = Store()
    sent: list[uuid.UUID] = []
    queue = CeleryAnalysisQueue(store, sent.append, 5)
    analysis_id = uuid.uuid4()
    queue.enqueue(analysis_id, b"%PDF icerik")
    assert sent == [analysis_id]
    assert store.items[analysis_id] == b"%PDF icerik"


def test_no_cv_store_refuses_instead_of_using_the_persistent_redis() -> None:
    sent: list[uuid.UUID] = []
    with pytest.raises(QueueUnavailable):
        CeleryAnalysisQueue(None, sent.append, 5).enqueue(uuid.uuid4(), b"x")
    assert sent == []


def test_full_queue_is_refused() -> None:
    store = Store()
    queue = CeleryAnalysisQueue(store, lambda _: None, 1)
    queue.enqueue(uuid.uuid4(), b"x")
    with pytest.raises(QueueUnavailable):
        queue.enqueue(uuid.uuid4(), b"y")
    assert len(store.items) == 1


def test_publish_failure_removes_the_cv() -> None:
    store = Store()

    def fail(_: uuid.UUID) -> None:
        raise OSError("broker yok")

    with pytest.raises(QueueUnavailable):
        CeleryAnalysisQueue(store, fail, 5).enqueue(uuid.uuid4(), b"x")
    assert store.items == {}


def test_store_failure_is_unavailable() -> None:
    store = Store()
    store.fail = True
    with pytest.raises(QueueUnavailable):
        CeleryAnalysisQueue(store, lambda _: None, 5).enqueue(uuid.uuid4(), b"x")


def test_cv_store_url_needs_explicit_setting_outside_dev() -> None:
    assert settings(environment="staging").cv_store_url is None
    assert settings(environment="staging", cv_redis_url="redis://cv:6379/0").cv_store_url == "redis://cv:6379/0"
    assert settings(environment="local").cv_store_url == "redis://cache:6379/1"


def test_build_queue_without_store_is_refused() -> None:
    with pytest.raises(QueueUnavailable):
        build_analysis_queue(settings(environment="staging")).enqueue(uuid.uuid4(), b"x")


def test_example_result_only_in_dev() -> None:
    assert isinstance(build_analyzer(settings(environment="local")), ExampleAnalyzer)
    analyzer = build_analyzer(settings(environment="production"))
    assert isinstance(analyzer, UnavailableAnalyzer)
    with pytest.raises(AnalysisFailed):
        analyzer.analyze(b"x", 1)
