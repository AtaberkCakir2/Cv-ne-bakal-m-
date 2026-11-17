"""Aday kaynakları veritabanından okur: `resources` (T-046), sadece canlı link (`is_alive`)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from recommendation.recommend import Resource


class Connection(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] = ..., /) -> Any: ...


_CANDIDATES = """
SELECT r.id, s.canonical_name, r.title, r.url, r.provider::text, r.language::text, r.level::text,
       r.duration_min, r.is_free
FROM resources r
JOIN skills s ON s.id = r.skill_id
WHERE s.canonical_name = ANY(%s) AND r.is_alive
ORDER BY s.canonical_name, r.id
"""


def load_candidates(conn: Connection, skills: Sequence[str]) -> dict[str, list[Resource]]:
    """Yetkinlik (taksonomideki standart ad) → aday kaynaklar. Kaynağı olmayan yetkinlik sözlükte yer almaz."""
    if not skills:
        return {}
    out: dict[str, list[Resource]] = {}
    for rid, skill, title, url, provider, language, level, duration, free in conn.execute(
        _CANDIDATES, (list(dict.fromkeys(skills)),)
    ).fetchall():
        out.setdefault(skill, []).append(
            Resource(
                resource_id=int(rid),
                skill=skill,
                title=title,
                url=url,
                provider=provider,
                language=language,
                level=level,
                duration_min=int(duration) if duration is not None else None,
                is_free=bool(free),
            )
        )
    return out
