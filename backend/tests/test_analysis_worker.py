"""Kuyruk parçaları (T-039): servis gerekmez. Veritabanı isteyen senaryolar tests/auth/test_analyses_queue.py'de."""

import json
import sys
import types
import uuid
from contextlib import contextmanager
from typing import Any

import pytest
from celery.exceptions import SoftTimeLimitExceeded
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import Settings
from app.db.enums import AnalysisErrorCode
from app.services import analyzer as analyzer_module
from app.services.analysis_queue import CeleryAnalysisQueue, QueueUnavailable, build_analysis_queue
from app.services.analyzer import (
    EXAMPLE_RESULT,
    AiAnalyzer,
    AnalysisFailed,
    ExampleAnalyzer,
    MissingSkill,
    PresentSkill,
    SuggestedResource,
    UnavailableAnalyzer,
    build_analyzer,
    output_from_result,
)


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


def test_unexpected_publish_error_also_removes_the_cv() -> None:
    store = Store()

    def fail(_: uuid.UUID) -> None:
        raise RuntimeError("beklenmedik")

    with pytest.raises(QueueUnavailable):
        CeleryAnalysisQueue(store, fail, 5).enqueue(uuid.uuid4(), b"x")
    assert store.items == {}


@pytest.mark.parametrize(
    "cv_url",
    ["redis://cache:6379/0", "redis://cache:6379/1", "redis://cache:6379", "redis://CACHE", "redis://:pw@cache/2"],
)
def test_cv_redis_must_differ_from_the_broker_outside_dev(cv_url: str) -> None:
    # Veritabanı numarası farklı olsa da aynı (kalıcı) Redis sunucusudur.
    with pytest.raises(ValueError, match="CV_REDIS_URL"):
        settings(environment="production", cv_redis_url=cv_url)


def test_cv_redis_on_another_server_is_accepted() -> None:
    assert settings(environment="staging", cv_redis_url="redis://cache:6380/0").cv_store_url == "redis://cache:6380/0"


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


def test_example_result_only_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(analyzer_module, "pipeline_available", lambda: False)
    assert isinstance(build_analyzer(settings(environment="local")), ExampleAnalyzer)
    analyzer = build_analyzer(settings(environment="production"))
    assert isinstance(analyzer, UnavailableAnalyzer)
    with pytest.raises(AnalysisFailed):
        analyzer.analyze(b"x", 1)


def test_example_result_carries_skills_and_resources() -> None:
    output = ExampleAnalyzer().analyze(b"%PDF", 1)
    assert [p.skill for p in output.present_skills] == ["Python", "SQL", "Git"]
    assert output.present_skills[0] == PresentSkill("Python", "advanced", 0.94, True)
    assert [(m.skill, m.priority) for m in output.missing_skills] == [("Docker", 1), ("PostgreSQL", 2)]
    assert output.missing_skills[0].resources[0].resource_id == 101


def test_result_parsing_tolerates_optional_fields() -> None:
    output = output_from_result(
        {
            "match_score": 40,
            "postings_analyzed": 12,
            "model": {"name": "m", "prompt_version": "skill_extraction:v1,recommendation:v1"},
            "present_skills": [{"skill": "Express", "verified": False}],
            "missing_skills": [{"skill": "Docker", "demand_ratio": 0.5, "resources": [{"resource_id": 3}]}],
        }
    )
    assert output.present_skills == (PresentSkill("Express", "unknown", None, False),)
    assert output.missing_skills == (MissingSkill("Docker", 0.5, None, (SuggestedResource(3, None),)),)


class FakeAiError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(f"CV metni: {code}")  # gerçek mesaj CV parçası içerebilir; sızmamalı
        self.code = code


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Sahte ai/pipeline ve psycopg.connect: AiAnalyzer'ın çağrı biçimini ve hata eşlemesini denetler."""
    calls: dict[str, Any] = {"raise": None}

    def analyze_cv(
        pdf: bytes, *, role_id: int, conn: object, embed: object = None, budget_s: float = 165.0
    ) -> types.SimpleNamespace:
        calls.update(pdf=pdf, role_id=role_id, conn=conn, embed=embed, budget_s=budget_s)
        if calls["raise"] is not None:
            raise FakeAiError(calls["raise"])
        return types.SimpleNamespace(result=json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8")), stats={})

    pipeline = types.ModuleType("pipeline")
    pipeline.BUDGET_SECONDS = 165.0  # type: ignore[attr-defined]
    pipeline.AnalysisError = FakeAiError  # type: ignore[attr-defined]
    pipeline.analyze_cv = analyze_cv  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pipeline", pipeline)

    @contextmanager
    def connect(url: str, **kwargs: Any) -> Any:
        calls.update(url=url, connect_kwargs=kwargs)
        yield "conn"

    import psycopg

    monkeypatch.setattr(psycopg, "connect", connect)
    return calls


def test_ai_analyzer_calls_pipeline_read_only(fake_ai: dict[str, Any]) -> None:
    embed = lambda texts: [[0.0] for _ in texts]  # noqa: E731
    out = AiAnalyzer("postgresql+psycopg://u:p@db:5432/careerai", embed=embed).analyze(b"%PDF", 3)
    assert out.present_skills and out.missing_skills
    assert fake_ai["url"] == "postgresql://u:p@db:5432/careerai"
    assert fake_ai["connect_kwargs"]["options"] == "-c default_transaction_read_only=on"
    assert fake_ai["connect_kwargs"]["autocommit"] is True
    assert 160 < fake_ai["budget_s"] <= 165.0
    assert (fake_ai["pdf"], fake_ai["role_id"], fake_ai["conn"], fake_ai["embed"]) == (b"%PDF", 3, "conn", embed)


@pytest.mark.parametrize(
    ("ai_code", "expected"),
    [
        ("NO_TEXT_FOUND", AnalysisErrorCode.NO_TEXT_FOUND),
        ("PDF_UNREADABLE", AnalysisErrorCode.PDF_UNREADABLE),
        ("INTERNAL", AnalysisErrorCode.INTERNAL),
        ("PDF_TOO_LARGE", AnalysisErrorCode.PDF_TOO_LARGE),
        ("LLM_TIMEOUT", AnalysisErrorCode.LLM_TIMEOUT),
        ("BILINMEYEN", AnalysisErrorCode.INTERNAL),
    ],
)
def test_ai_analyzer_maps_errors_without_message(
    fake_ai: dict[str, Any], ai_code: str, expected: AnalysisErrorCode
) -> None:
    fake_ai["raise"] = ai_code
    with pytest.raises(AnalysisFailed) as info:
        AiAnalyzer("postgresql://x", load_embed=False).analyze(b"%PDF", 1)
    assert info.value.code is expected
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert "CV metni" not in str(info.value)


def test_ai_analyzer_continues_without_embedding(fake_ai: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "embedding", None)  # import edilemez
    analyzer = AiAnalyzer("postgresql://x")
    analyzer.analyze(b"%PDF", 1)
    assert fake_ai["embed"] is None
    analyzer.analyze(b"%PDF", 1)  # bir kez denenir, her analizde tekrar yüklenmez
    assert analyzer._load_embed is False


def test_build_analyzer_uses_pipeline_when_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(analyzer_module, "pipeline_available", lambda: True)
    assert isinstance(build_analyzer(settings(environment="production")), AiAnalyzer)
    assert isinstance(build_analyzer(settings(environment="local")), AiAnalyzer)


def _fake_embedding(monkeypatch: pytest.MonkeyPatch, default_encoder: Any) -> None:
    module = types.ModuleType("embedding")
    module.default_encoder = default_encoder  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "embedding", module)


def test_ai_analyzer_loads_embedding_once(fake_ai: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    loads: list[int] = []
    encoder = lambda texts: [[0.0] for _ in texts]  # noqa: E731

    def load() -> Any:
        loads.append(1)
        return encoder

    _fake_embedding(monkeypatch, load)
    analyzer = AiAnalyzer("postgresql://x")
    analyzer.analyze(b"%PDF", 1)
    analyzer.analyze(b"%PDF", 1)
    assert fake_ai["embed"] is encoder and loads == [1]


def test_ai_analyzer_does_not_swallow_time_limit(fake_ai: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    def slow() -> None:
        raise SoftTimeLimitExceeded

    _fake_embedding(monkeypatch, slow)
    analyzer = AiAnalyzer("postgresql://x")
    with pytest.raises(SoftTimeLimitExceeded):
        analyzer.analyze(b"%PDF", 1)
    assert "pdf" not in fake_ai  # analiz bütçesine baştan başlanmadı
    assert analyzer._load_embed is True  # sonraki analiz modeli yeniden dener


def test_pipeline_available_needs_importable_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pipeline", None)
    assert analyzer_module.pipeline_available() is False
