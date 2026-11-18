"""Pozisyon talebini veritabanından okur: role_skill_stats (T-045) + skills.embedding (T-041).

psycopg bağlantısıyla düz SQL; değerler parametre, tablo/sütun adları sabit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from matching.score import Demand


class Connection(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] = ..., /) -> Any: ...


@dataclass(frozen=True)
class RoleDemand:
    slug: str
    name: str
    demands: list[Demand]
    corpus_postings: int  # IDF'teki N: tüm pozisyonların toplam ilanı


_ROLE = "SELECT name FROM roles WHERE slug = %s"
_CORPUS = (
    "SELECT coalesce(sum(total_postings), 0) FROM (SELECT DISTINCT role_id, total_postings FROM role_skill_stats) t"
)
_DEMANDS = """
WITH df AS (SELECT skill_id, sum(posting_count)::int AS df FROM role_skill_stats GROUP BY skill_id)
SELECT s.canonical_name, r.posting_count, r.total_postings, r.demand_ratio, df.df, s.embedding::text
FROM role_skill_stats r
JOIN roles ro ON ro.id = r.role_id
JOIN skills s ON s.id = r.skill_id
JOIN df ON df.skill_id = r.skill_id
WHERE ro.slug = %s
ORDER BY r.demand_ratio DESC, s.canonical_name
"""


def load_role_demand(conn: Connection, role_slug: str) -> RoleDemand:
    """Pozisyon yoksa `LookupError`. İlanı olmayan pozisyon boş talep listesiyle döner (skor 0, low_data)."""
    row = conn.execute(_ROLE, (role_slug,)).fetchone()
    if row is None:
        raise LookupError(f"pozisyon yok: {role_slug}")
    corpus = int(conn.execute(_CORPUS).fetchone()[0])
    demands = [
        Demand(
            skill=name,
            posting_count=int(count),
            total_postings=int(total),
            demand_ratio=float(ratio),
            df=int(df),
            vector=parse_vector(vec) if vec else None,
        )
        for name, count, total, ratio, df, vec in conn.execute(_DEMANDS, (role_slug,)).fetchall()
    ]
    return RoleDemand(role_slug, row[0], demands, corpus)


def parse_vector(text: str) -> list[float]:
    """pgvector metin biçimi "[0.1,0.2,...]" → liste."""
    return [float(x) for x in text.strip("[] ").split(",")]
