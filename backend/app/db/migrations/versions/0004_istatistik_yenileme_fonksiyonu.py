"""role_skill_stats yenileme fonksiyonu (T-075): uygulama rolü view'ın sahibi olmadan yenileyebilsin.

REFRESH MATERIALIZED VIEW sadece sahibine izinli. Production'da API ve veri işçisi en az yetkili `careerai_app`
rolüyle bağlanır (infra/pc/deploy.sh, setup_app_role); view'ın sahibi migration'ı çalıştıran rol. Bu fonksiyon
SECURITY DEFINER: sahibinin yetkisiyle sadece bu tek işi yapar. Herkese açık değil; EXECUTE yetkisini deploy.sh
uygulama rolüne verir (rol adı ortama bağlı olduğu için migration'da yazılmaz).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-15 21:30:00+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # search_path sabit: SECURITY DEFINER fonksiyonda çağıranın şemasından nesne çözülmesin.
    op.execute(
        """
        CREATE FUNCTION refresh_role_skill_stats(concurrent boolean) RETURNS void
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
        BEGIN
          IF concurrent THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY public.role_skill_stats;
          ELSE
            REFRESH MATERIALIZED VIEW public.role_skill_stats;
          END IF;
        END $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION refresh_role_skill_stats(boolean) FROM PUBLIC")


def downgrade() -> None:
    op.execute("DROP FUNCTION refresh_role_skill_stats(boolean)")
