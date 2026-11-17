"""Yetkinlik ve ilan vektörlerini toplu üretip pgvector sütunlarına yazar (skills.embedding, job_postings.embedding).

Varsayılan sadece vektörü olmayan satırlar işlenir (gece toplamasındaki yeni ilanlar); model değişince
`only_missing=False` ile hepsi yeniden üretilir. Her parti ayrı commit'lenir:
yarıda kesilen çalışma kaldığı yerden sürer.
İlan metni loglanmaz; sadece sayılar döner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from embedding.model import Encoder, Vector, check
from embedding.texts import posting_text, skill_text

Table = Literal["skills", "job_postings"]
BATCH = 256


class Connection(Protocol):
    """psycopg.Connection'ın burada kullanılan kısmı."""

    def execute(self, query: str, params: tuple[int, int], /) -> Any: ...
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...


@dataclass(frozen=True)
class _Spec:
    columns: str
    where: str


# Sabit SQL; kullanıcı girdisi sorguya sadece parametre olarak girer.
_SPECS: dict[Table, _Spec] = {
    "skills": _Spec("id, canonical_name, synonyms", "TRUE"),
    # Pasif ilanlar (eski / benzer kopya) eşleştirmede kullanılmıyor.
    "job_postings": _Spec("id, title_raw, description_clean", "is_active"),
}


def to_literal(vector: Vector) -> str:
    """pgvector metin biçimi: [0.1,0.2,...]. `pgvector` Python paketi gerekmesin diye elle."""
    check(vector)
    return "[" + ",".join(f"{x:.7g}" for x in vector) + "]"


def _text(table: Table, row: tuple[Any, ...]) -> str:
    if table == "skills":
        return skill_text(row[1], row[2] or ())
    return posting_text(row[1] or "", row[2] or "")


def embed_table(
    conn: Connection, encoder: Encoder, table: Table, *, only_missing: bool = True, batch: int = BATCH
) -> int:
    """Tablodaki satırların vektörünü yazar; yazılan satır sayısını döner."""
    spec = _SPECS[table]
    missing = " AND embedding IS NULL" if only_missing else ""
    select = f"SELECT {spec.columns} FROM {table} WHERE {spec.where}{missing} AND id > %s ORDER BY id LIMIT %s"  # noqa: S608 (sabit tablo/sütun adları)
    update = f"UPDATE {table} SET embedding = %s::vector WHERE id = %s"  # noqa: S608
    last_id = 0
    written = 0
    while True:
        rows = conn.execute(select, (last_id, batch)).fetchall()
        if not rows:
            return written
        vectors = encoder([_text(table, r) for r in rows])
        if len(vectors) != len(rows):
            raise ValueError("model satır sayısı kadar vektör döndürmedi")
        with conn.cursor() as cur:
            cur.executemany(update, [(to_literal(v), r[0]) for v, r in zip(vectors, rows, strict=True)])
        conn.commit()
        written += len(rows)
        last_id = rows[-1][0]
