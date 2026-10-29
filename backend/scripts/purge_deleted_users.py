"""Silineli 30 günü geçmiş hesapları kalıcı siler (T-049; docs/go-live.md, "Rutin operasyonlar", günlük).

Kullanım (backend/ klasöründe):
    python scripts/purge_deleted_users.py

Bağlı kayıtlar (oturumlar, onaylar, analizler) CASCADE ile silinir; audit_logs kayıtları kalır, kişi bağı kopar.
Zamanlama Celery beat'e (T-039) bağlanana kadar sunucuda günlük cron ile çalıştırılır.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ (app paketi)

from app.db.session import get_sessionmaker  # noqa: E402
from app.services.users import purge_deleted_users  # noqa: E402


def main() -> int:
    with get_sessionmaker()() as session:
        count = purge_deleted_users(session)
    print(f"Kalıcı silinen hesap: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
