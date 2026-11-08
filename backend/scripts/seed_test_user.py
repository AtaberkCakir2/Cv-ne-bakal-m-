"""Uçtan uca testler için kalıcı, sahte test kullanıcısını lokal veritabanında oluşturur (T-037).

Kullanım (backend/ klasöründe, servisler `make up` ile açıkken):
    python scripts/seed_test_user.py

Bilgiler ortam değişkenlerinden (.env) okunur: E2E_TEST_EMAIL, E2E_TEST_PASSWORD.
- E-posta @example.com ile bitmelidir (gerçek bir adrese e-posta gitmesin).
- Kullanıcı varsa şifresi bu değere çekilir; e-postası doğrulanmış ve üç KVKK onayı verilmiş olur.
- Sadece local/test ortamında çalışır.
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ (app paketi)

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.enums import ConsentType  # noqa: E402
from app.db.models import Consent, User  # noqa: E402
from app.db.session import get_sessionmaker  # noqa: E402

CONSENT_VERSION = "test"


def main() -> int:
    settings = get_settings()
    if not settings.is_explicit_dev:  # ENVIRONMENT hiç verilmemişse de çalışmaz (canlı veri tabanına yazmasın)
        print(f"Sadece ENVIRONMENT=local/test açıkça verildiğinde çalışır (şu an: {settings.environment}).")
        return 1
    email = os.environ.get("E2E_TEST_EMAIL", "").strip().lower()
    password = os.environ.get("E2E_TEST_PASSWORD", "")
    if not email.endswith("@example.com"):
        print("E2E_TEST_EMAIL ayarlanmalı ve @example.com ile bitmeli (ör. e2e@example.com).")
        return 1
    if len(password) < 8:
        print("E2E_TEST_PASSWORD en az 8 karakter olmalı.")
        return 1

    with get_sessionmaker()() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name="E2E Test Kullanıcısı", password_hash=hash_password(password))
            session.add(user)
            session.flush()
            action = "oluşturuldu"
        else:
            user.password_hash = hash_password(password)
            user.deleted_at = None
            action = "güncellendi"
        user.is_verified = True
        existing = {c.consent_type for c in user.consents if c.withdrawn_at is None}
        now = datetime.now(UTC)
        session.add_all(
            Consent(user_id=user.id, consent_type=t, version=CONSENT_VERSION, accepted_at=now)
            for t in ConsentType
            if t not in existing
        )
        session.commit()
    print(f"Test kullanıcısı {action}: {email} (doğrulanmış, KVKK onayları verilmiş).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
