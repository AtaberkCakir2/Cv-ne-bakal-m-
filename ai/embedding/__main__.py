"""python -m embedding [--hepsi] [--tablo skills|job_postings]. Adres DATABASE_URL ortam değişkeninden okunur."""

from __future__ import annotations

import argparse
import os
import sys
import time

from embedding.model import SentenceEncoder
from embedding.store import Table, embed_table


def psycopg_url(url: str) -> str:
    """SQLAlchemy biçimi (postgresql+psycopg://) → libpq biçimi."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m embedding", description="Yetkinlik ve ilan vektörlerini yazar.")
    parser.add_argument("--hepsi", action="store_true", help="vektörü olanları da yeniden üret (model değişince)")
    parser.add_argument("--tablo", choices=["skills", "job_postings"], action="append", help="varsayılan: ikisi")
    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL yok", file=sys.stderr)
        return 2

    import psycopg

    tables: list[Table] = args.tablo or ["skills", "job_postings"]
    encoder = SentenceEncoder()
    with psycopg.connect(psycopg_url(url)) as conn:
        for table in tables:
            start = time.perf_counter()
            n = embed_table(conn, encoder, table, only_missing=not args.hepsi)
            print(f"{table}: {n} satır, {time.perf_counter() - start:.1f} sn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
