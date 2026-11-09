"""Analiz akışı (T-039), gerçek PostgreSQL ile. Kuyruk ve CV deposu test çiftleri; analiz görevi Celery ile eager."""

import hashlib
import logging
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import AnalysisErrorCode, AnalysisStatus
from app.db.models import Analysis, Role
from app.services import analysis_runner
from app.services.analysis_queue import QueueUnavailable
from app.services.analysis_runner import AnalysisRunner, RetryLater
from app.services.analyzer import AnalysisFailed, AnalysisOutput
from app.worker import tasks
from tests.auth.test_auth_flow import API, bearer, login, register
from tests.test_analyses_upload import make_pdf
from tests.test_analysis_worker import Store

URL = f"{API}/analyses"
OUTPUT = AnalysisOutput(Decimal("62.50"), 150, "llama3.1:8b", "v1")


class Queue:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, bytes]] = []
        self.fail = False

    def enqueue(self, analysis_id: uuid.UUID, pdf: bytes) -> None:
        if self.fail:
            raise QueueUnavailable
        self.calls.append((analysis_id, pdf))


class Analyzer:
    def __init__(self, *results: object) -> None:
        self.results = list(results) or [OUTPUT]
        self.calls = 0

    def analyze(self, pdf: bytes, target_role_id: int) -> AnalysisOutput:
        self.calls += 1
        result = self.results[min(self.calls, len(self.results)) - 1]
        if isinstance(result, Exception):
            raise result
        assert isinstance(result, AnalysisOutput)
        return result


@pytest.fixture
def queue(auth_app: FastAPI) -> Queue:
    fake = Queue()
    auth_app.state.analysis_queue = fake
    return fake


@pytest.fixture
def client(auth_app: FastAPI, queue: Queue) -> Iterator[TestClient]:
    with TestClient(auth_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def role(db_sessionmaker: sessionmaker[Session]) -> Iterator[int]:
    with db_sessionmaker() as session:
        row = Role(name=f"Rol {uuid.uuid4().hex[:6]}", slug=f"rol-{uuid.uuid4().hex[:6]}", synonyms=[])
        session.add(row)
        session.commit()
        yield row.id


def signed_in(client: TestClient, email: str = "kuyruk@example.com") -> dict[str, str]:
    register(client, email)
    return bearer(login(client, email)["access_token"])


def upload(client: TestClient, headers: dict[str, str], role_id: int, pdf: bytes | None = None):  # type: ignore[no-untyped-def]
    files = {"file": ("ozgecmis.pdf", pdf or make_pdf(2), "application/pdf")}
    return client.post(URL, headers=headers, files=files, data={"target_role_id": str(role_id)})


def queued(client: TestClient, queue: Queue, role: int) -> uuid.UUID:
    response = upload(client, signed_in(client), role)
    assert response.status_code == 202, response.text
    return uuid.UUID(response.json()["analysis_id"])


def row(sessions: sessionmaker[Session], analysis_id: uuid.UUID) -> Analysis:
    with sessions() as session:
        found = session.get(Analysis, analysis_id)
        assert found is not None
        return found


def test_upload_needs_login(client: TestClient, role: int) -> None:
    assert upload(client, {}, role).status_code == 401


def test_upload_saves_only_hash_and_pages_then_queues(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    pdf = make_pdf(3)
    response = upload(client, signed_in(client), role, pdf)
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    analysis_id = uuid.UUID(response.json()["analysis_id"])
    assert queue.calls == [(analysis_id, pdf)]
    saved = row(db_sessionmaker, analysis_id)
    assert saved.status is AnalysisStatus.QUEUED
    assert saved.cv_sha256 == hashlib.sha256(pdf).hexdigest()
    assert saved.cv_pages == 3


def test_unknown_role_is_rejected(client: TestClient, queue: Queue) -> None:
    assert upload(client, signed_in(client), 999_999).status_code == 422
    assert queue.calls == []


def test_queue_down_answers_503_and_marks_failed(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    queue.fail = True
    response = upload(client, signed_in(client), role)
    assert response.status_code == 503
    assert response.headers["retry-after"]
    assert response.headers["content-type"].startswith("application/problem+json")
    with db_sessionmaker() as session:
        saved = session.scalars(select(Analysis)).one()
        assert saved.status is AnalysisStatus.FAILED
        assert saved.error_code is AnalysisErrorCode.INTERNAL


def test_status_is_visible_only_to_the_owner(client: TestClient, queue: Queue, role: int) -> None:
    analysis_id = queued(client, queue, role)
    owner = bearer(login(client, "kuyruk@example.com")["access_token"])
    response = client.get(f"{URL}/{analysis_id}", headers=owner)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["status"] == "queued"
    assert body["target_role"]["slug"].startswith("rol-")
    # Sözleşmede null olamayan alanlar değer yokken yanıtta da yok.
    assert not {"match_score", "postings_analyzed", "model"} & set(body)
    assert body["error"] is None and body["completed_at"] is None
    assert client.get(f"{URL}/{analysis_id}", headers=signed_in(client, "diger@example.com")).status_code == 404
    assert client.get(f"{URL}/{analysis_id}").status_code == 401
    assert client.get(f"{URL}/{uuid.uuid4()}", headers=owner).status_code == 404


def runner(sessions: sessionmaker[Session], analyzer: Analyzer) -> tuple[AnalysisRunner, Store]:
    store = Store()
    return AnalysisRunner(sessions, store, analyzer), store


def test_success_writes_result_and_deletes_the_cv(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer())
    store.put(analysis_id, b"%PDF")
    work.run(analysis_id, last_attempt=False)
    saved = row(db_sessionmaker, analysis_id)
    assert saved.status is AnalysisStatus.DONE
    assert saved.match_score == Decimal("62.50")
    assert saved.completed_at is not None and saved.duration_ms is not None
    assert store.items == {}
    owner = bearer(login(client, "kuyruk@example.com")["access_token"])
    body = client.get(f"{URL}/{analysis_id}", headers=owner).json()
    assert body["status"] == "done"
    assert body["match_score"] == 62.5
    assert body["model"] == {"name": "llama3.1:8b", "prompt_version": "v1"}
    assert body["error"] is None


def test_timeout_retries_then_fails_with_llm_timeout(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer(TimeoutError()))
    store.put(analysis_id, b"%PDF")
    with pytest.raises(RetryLater):
        work.run(analysis_id, last_attempt=False)
    assert row(db_sessionmaker, analysis_id).status is AnalysisStatus.QUEUED
    assert store.items  # tekrar deneme için duruyor
    work.run(analysis_id, last_attempt=True)
    saved = row(db_sessionmaker, analysis_id)
    assert saved.status is AnalysisStatus.FAILED
    assert saved.error_code is AnalysisErrorCode.LLM_TIMEOUT
    assert store.items == {}


def test_permanent_failure_is_not_retried(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer(AnalysisFailed(AnalysisErrorCode.NO_TEXT_FOUND)))
    store.put(analysis_id, b"%PDF")
    work.run(analysis_id, last_attempt=False)
    assert row(db_sessionmaker, analysis_id).error_code is AnalysisErrorCode.NO_TEXT_FOUND
    assert store.items == {}


def test_expired_cv_fails_without_calling_the_analyzer(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    analyzer = Analyzer()
    work, _ = runner(db_sessionmaker, analyzer)
    work.run(analysis_id, last_attempt=False)
    assert row(db_sessionmaker, analysis_id).status is AnalysisStatus.FAILED
    assert analyzer.calls == 0


def test_error_text_is_never_logged(
    client: TestClient,
    queue: Queue,
    role: int,
    db_sessionmaker: sessionmaker[Session],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer(ValueError("Ayse Yilmaz 05321234567")))
    store.put(analysis_id, b"%PDF")
    # Alembic fileConfig var olan logger'ları kapatır; kapalı kalırsa bu test bir şey kanıtlamaz.
    monkeypatch.setattr(analysis_runner.logger, "disabled", False)
    with caplog.at_level(logging.DEBUG):
        work.run(analysis_id, last_attempt=True)
    assert "Ayse" not in caplog.text
    assert "ValueError" in caplog.text
    assert row(db_sessionmaker, analysis_id).error_code is AnalysisErrorCode.INTERNAL


def test_later_error_does_not_chain_the_original_error(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer(ValueError("Ayse Yilmaz")))
    store.put(analysis_id, b"%PDF")
    with pytest.raises(RetryLater) as raised:
        work.run(analysis_id, last_attempt=False)
    assert raised.value.__context__ is None


def test_database_error_on_finish_still_removes_the_cv(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    work, store = runner(db_sessionmaker, Analyzer())
    store.put(analysis_id, b"%PDF")
    calls = {"n": 0}

    def flaky() -> Session:
        calls["n"] += 1
        if calls["n"] > 1:
            raise OperationalError("x", {}, Exception("baglanti"))
        return db_sessionmaker()

    work.sessions = flaky  # type: ignore[assignment]
    with pytest.raises(OperationalError):
        work.run(analysis_id, last_attempt=False)
    assert store.items == {}


def test_stuck_analysis_fails_on_the_next_poll(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    with db_sessionmaker() as session:
        saved = session.get(Analysis, analysis_id)
        assert saved is not None
        saved.status = AnalysisStatus.PROCESSING
        saved.created_at = datetime.now(UTC) - timedelta(hours=2)
        session.commit()
    owner = bearer(login(client, "kuyruk@example.com")["access_token"])
    body = client.get(f"{URL}/{analysis_id}", headers=owner).json()
    assert body["status"] == "failed"
    assert body["error"]["code"] == "INTERNAL"
    assert row(db_sessionmaker, analysis_id).status is AnalysisStatus.FAILED


def test_deleted_analysis_is_skipped_and_cv_removed(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    with db_sessionmaker() as session:
        saved = session.get(Analysis, analysis_id)
        assert saved is not None
        saved.deleted_at = datetime.now(UTC)
        session.commit()
    analyzer = Analyzer()
    work, store = runner(db_sessionmaker, analyzer)
    store.put(analysis_id, b"%PDF")
    work.run(analysis_id, last_attempt=False)
    assert analyzer.calls == 0
    assert store.items == {}


def test_finished_analysis_is_not_run_again(
    client: TestClient, queue: Queue, role: int, db_sessionmaker: sessionmaker[Session]
) -> None:
    analysis_id = queued(client, queue, role)
    analyzer = Analyzer()
    work, store = runner(db_sessionmaker, analyzer)
    store.put(analysis_id, b"%PDF")
    work.run(analysis_id, last_attempt=False)
    store.put(analysis_id, b"%PDF")  # işçi ölüp mesaj tekrar geldi
    work.run(analysis_id, last_attempt=False)
    assert analyzer.calls == 1
    assert store.items == {}


def test_celery_task_retries_once_then_records_failure(
    client: TestClient,
    queue: Queue,
    role: int,
    db_sessionmaker: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis_id = queued(client, queue, role)
    analyzer = Analyzer(TimeoutError())
    work, store = runner(db_sessionmaker, analyzer)
    store.put(analysis_id, b"%PDF")
    monkeypatch.setattr(tasks, "build_runner", lambda: work)
    monkeypatch.setattr(tasks, "RETRY_DELAY_S", 0)
    tasks.run_analysis.apply(args=[str(analysis_id)])
    assert analyzer.calls == 2
    assert row(db_sessionmaker, analysis_id).error_code is AnalysisErrorCode.LLM_TIMEOUT
    assert store.items == {}
