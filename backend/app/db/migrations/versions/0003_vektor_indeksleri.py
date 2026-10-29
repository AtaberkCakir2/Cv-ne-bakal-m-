"""Vektör indeksleri (T-013): skills.embedding ve job_postings.embedding için HNSW (kosinüs).

İndeks boş sütunda da kurulur; vektörler sonradan yazıldıkça güncellenir. Parametreler pgvector varsayılanları
(m=16, ef_construction=64); ölçüm docs/veritabani.md "Vektör indeksleri" bölümünde.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-29 21:00:00+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("skills", "job_postings")


def upgrade() -> None:
    for table in TABLES:
        op.create_index(
            op.f(f"ix_{table}_embedding"),
            table,
            ["embedding"],
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(op.f(f"ix_{table}_embedding"), table_name=table)
