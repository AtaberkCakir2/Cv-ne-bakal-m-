"""Açık rızanın geri alınması: consents.withdrawn_at ve yürürlükteki onay için kısmi tekillik.

KVKK md. 11 gereği rıza her zaman geri alınabilir. Geri alınan onay satırı silinmez (ne zaman verilip ne zaman geri
alındığının ispatı); aynı metin sürümü yeniden onaylanırsa yeni satır eklenir. Bu yüzden UNIQUE(user_id,
consent_type, version) kısıtı yalnızca yürürlükteki (withdrawn_at IS NULL) satırlara uygulanan bir indekse dönüşür.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29 12:00:00+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("consents", sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("uq_consents_user_id_consent_type_version", "consents", type_="unique")
    op.create_index(
        "uq_consents_active_version",
        "consents",
        ["user_id", "consent_type", "version"],
        unique=True,
        postgresql_where=sa.text("withdrawn_at IS NULL"),
    )
    # Eski UNIQUE kısıtı user_id için indeks görevi de görüyordu; kısmi indeks geri alınmış satırları kapsamaz.
    op.create_index(op.f("ix_consents_user_id"), "consents", ["user_id"])


def downgrade() -> None:
    # Eski şemada "geri alındı" bilgisi tutulamaz. Geri alınmış satırlar kalırsa yürürlükteki onay gibi görünür ve
    # aynı sürümün ikinci satırı UNIQUE'i bozar; rızası geri alınmış kişinin verisi işlenmesin diye silinir.
    op.execute("DELETE FROM consents WHERE withdrawn_at IS NOT NULL")
    op.drop_index(op.f("ix_consents_user_id"), table_name="consents")
    op.drop_index("uq_consents_active_version", table_name="consents")
    op.create_unique_constraint(
        "uq_consents_user_id_consent_type_version", "consents", ["user_id", "consent_type", "version"]
    )
    op.drop_column("consents", "withdrawn_at")
