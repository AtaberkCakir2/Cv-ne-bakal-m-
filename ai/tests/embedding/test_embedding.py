"""Embedding servisi (T-041).

- Birim testleri sahte model ve sahte bağlantıyla.
- Gerçek model testi: CAREERAI_EMBEDDING_TEST=1 (model ilk çalışmada indirilir, ~470 MB).
- Veritabanı testi: TEST_DATABASE_URL (pgvector'lü Postgres; geçici tablolarla, gerçek tablolara dokunmaz).
"""

from __future__ import annotations

import math
import os
from collections.abc import Iterator, Sequence
from typing import Any

import pytest

from embedding import DIM, check, cosine, embed_table, posting_text, skill_text, to_literal
from embedding.__main__ import psycopg_url
from embedding.texts import POSTING_MAX_CHARS


def unit(i: int) -> list[float]:
    v = [0.0] * DIM
    v[i % DIM] = 1.0
    return v


class FakeEncoder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [unit(len(t)) for t in texts]


class FakeCursor:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def executemany(self, query: str, params: list[tuple[str, int]]) -> None:
        for literal, row_id in params:
            self.conn.vectors[row_id] = literal


class FakeResult:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class FakeConn:
    """skills tablosunun bellekteki taklidi: id > son id, LIMIT, embedding IS NULL süzgeci."""

    def __init__(self, names: dict[int, str], vectors: dict[int, str] | None = None) -> None:
        self.names = names
        self.vectors = dict(vectors or {})
        self.commits = 0
        self.queries: list[str] = []

    def execute(self, query: str, params: tuple[int, int]) -> FakeResult:
        self.queries.append(query)
        last_id, limit = params
        ids = sorted(i for i in self.names if i > last_id)
        if "embedding IS NULL" in query:
            ids = [i for i in ids if i not in self.vectors]
        return FakeResult([(i, self.names[i], ["eş"]) for i in ids[:limit]])

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1


def test_texts() -> None:
    assert skill_text("  Spring   Boot ") == "Spring Boot"
    assert skill_text("JavaScript", ["js", "ecmascript", "JavaScript", " "]) == "JavaScript, js, ecmascript"
    text = posting_text("Backend  Geliştirici", "Python\n ve  " + "x" * 5000)
    assert text.startswith("Backend Geliştirici. Python ve x")
    assert len(text) <= len("Backend Geliştirici. ") + POSTING_MAX_CHARS
    assert posting_text("Data Engineer", "  ") == "Data Engineer"


def test_check_and_literal() -> None:
    v = unit(3)
    lit = to_literal(v)
    assert lit.startswith("[0,0,0,1,0") and lit.endswith("]") and lit.count(",") == DIM - 1
    for bad in ([1.0] * 10, [0.5] * DIM, [math.nan] + [0.0] * (DIM - 1)):
        with pytest.raises(ValueError):
            check(bad)
    assert cosine(unit(1), unit(1)) == 1.0 and cosine(unit(1), unit(2)) == 0.0


def test_only_missing_rows_are_written_in_batches() -> None:
    conn = FakeConn({i: f"skill{i}" for i in range(1, 8)}, vectors={2: "eski", 5: "eski"})
    enc = FakeEncoder()
    n = embed_table(conn, enc, "skills", batch=2)
    assert n == 5
    assert set(conn.vectors) == set(range(1, 8)) and conn.vectors[2] == "eski"
    assert [len(c) for c in enc.calls] == [2, 2, 1]
    assert conn.commits == 3  # her parti ayrı commit: yarıda kesilen iş kaldığı yerden sürer


def test_all_rows_are_rewritten_when_asked() -> None:
    conn = FakeConn({1: "Python", 2: "Go"}, vectors={1: "eski"})
    assert embed_table(conn, FakeEncoder(), "skills", only_missing=False) == 2
    assert conn.vectors[1] != "eski"
    assert all("embedding IS NULL" not in q for q in conn.queries)


def test_wrong_vector_count_is_an_error() -> None:
    def broken(texts: Sequence[str]) -> list[list[float]]:
        return [unit(0)]

    with pytest.raises(ValueError):
        embed_table(FakeConn({1: "a", 2: "b"}), broken, "skills")


def test_psycopg_url() -> None:
    assert psycopg_url("postgresql+psycopg://u:p@h:5432/db") == "postgresql://u:p@h:5432/db"


# --- gerçek model ---

real_model = pytest.mark.skipif(os.environ.get("CAREERAI_EMBEDDING_TEST") != "1", reason="gerçek model testi kapalı")


@real_model
def test_real_model_is_multilingual_and_normalized() -> None:
    from embedding import default_encoder

    enc = default_encoder()
    py, py_tr, accounting, react, react_js, express_js, express = enc(
        [
            skill_text("Python", ["python3", "py"]),
            "Python programlama",
            "Muhasebe",
            skill_text("React", ["react.js", "reactjs"]),
            "React.js",
            skill_text("Express.js", ["expressjs"]),
            "Express",
        ]
    )
    for v in (py, py_tr, accounting):
        check(v)
    assert cosine(py, py_tr) > cosine(py, accounting)
    assert cosine(react, react_js) > cosine(react, express)
    assert cosine(express_js, express) > cosine(react, express)


# --- veritabanı ---

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db() -> Iterator[Any]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL verilmedi")
    import psycopg

    with psycopg.connect(psycopg_url(TEST_DATABASE_URL)) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # Geçici tablolar pg_temp'te: arama yolunda public'ten önce gelir, gerçek tablolar etkilenmez.
        conn.execute(
            "CREATE TEMP TABLE skills (id int PRIMARY KEY, canonical_name text, synonyms text[], embedding vector(384))"
        )
        conn.execute(
            "CREATE TEMP TABLE job_postings (id bigint PRIMARY KEY, title_raw text, description_clean text,"
            " is_active boolean, embedding vector(384))"
        )
        yield conn


def test_vectors_are_written_to_pgvector(db: Any) -> None:
    db.execute("INSERT INTO skills (id, canonical_name) VALUES (1, 'Python'), (2, 'Go')")
    db.execute(
        "INSERT INTO job_postings (id, title_raw, description_clean, is_active) VALUES"
        " (10, 'Backend', 'Python', true), (11, 'Eski', 'Go', false)"
    )
    enc = FakeEncoder()
    assert embed_table(db, enc, "skills") == 2
    assert embed_table(db, enc, "job_postings") == 1  # pasif ilan atlanır
    assert embed_table(db, enc, "skills") == 0  # ikinci çalışma: eksik yok
    dist = db.execute(
        "SELECT a.embedding <=> b.embedding FROM skills a, skills b WHERE a.id = 1 AND b.id = 1"
    ).fetchone()
    assert dist[0] == pytest.approx(0.0)
    assert db.execute("SELECT embedding IS NULL FROM job_postings WHERE id = 11").fetchone()[0] is True
