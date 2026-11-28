"""Yavaş sorgu ölçümü için tek oturumluk yük (go-live #18, karar #40). Prova ortamının api kapsayıcısında çalışır:

    make staging-slow-queries      (dökümü yükler, sayaçları sıfırlar, bunu çalıştırır, raporu basar)

İki kısım:
1. Katalog uçları (giriş gerektirmeyen, veri tabanına giden GET'ler) HTTP ile; genel hız sınırı (100/dk) aşılmasın
   diye istekler aralıklı gönderilir.
2. Analiz akışının sorguları (`ai/matching/db.py`, `ai/recommendation/db.py`) doğrudan uygulama rolüyle. Analiz
   işçisi production'da henüz yok (T-057); sorgu metinleri o dosyalardan kopyadır, değişirse burası da güncellenir.

Sadece okuma yapar; kullanıcı verisine dokunmaz. Standart kütüphane + api imajındaki psycopg yeterlidir.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

import psycopg

BASE = "http://127.0.0.1:8000/api/v1"
ROUNDS = int(os.environ.get("ROUNDS", "5"))
REQ_PER_MIN = 90  # genel sınır 100/dk

_ROLE = "SELECT name FROM roles WHERE slug = %s"
_CORPUS = "SELECT coalesce(sum(total_postings), 0) FROM (SELECT DISTINCT role_id, total_postings FROM role_skill_stats) t"
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
_CANDIDATES = """
SELECT r.id, s.canonical_name, r.title, r.url, r.provider::text, r.language::text, r.level::text,
       r.duration_min, r.is_free
FROM resources r
JOIN skills s ON s.id = r.skill_id
WHERE s.canonical_name = ANY(%s) AND r.is_alive
ORDER BY s.canonical_name, r.id
"""

_last = 0.0


def get(path: str) -> object:
    global _last
    wait = 60 / REQ_PER_MIN - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    _last = time.monotonic()
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.load(r)


def main() -> int:
    roles = get("/roles")
    assert isinstance(roles, list)
    slugs = [r["slug"] for r in roles]
    role_skills: dict[str, list[dict]] = {
        s: get(f"/roles/{s}/skills?limit=20")["skills"] for s in slugs
    }  # type: ignore[index]
    skill_slugs = sorted({k["slug"] for v in role_skills.values() for k in v[:10]})
    print(
        f"{len(slugs)} pozisyon, {len(skill_slugs)} yetkinlik, {ROUNDS} tur", flush=True
    )

    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url, autocommit=True) as conn:
        for i in range(ROUNDS):
            t = time.monotonic()
            for s in slugs:  # analiz akışı: pozisyon başına bir eşleştirme + öneri
                conn.execute(_ROLE, (s,)).fetchone()
                conn.execute(_CORPUS).fetchone()
                demands = conn.execute(_DEMANDS, (s,)).fetchall()
                conn.execute(_CANDIDATES, ([d[0] for d in demands[:15]],)).fetchall()
            get("/roles")
            for s in slugs:
                get(f"/roles/{s}/skills?limit=20")
            for k in skill_slugs:
                try:
                    get(f"/skills/{k}/resources")
                except urllib.error.HTTPError as e:
                    if e.code != 404:
                        raise
            print(f"tur {i + 1}/{ROUNDS}: {time.monotonic() - t:.0f} sn", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
