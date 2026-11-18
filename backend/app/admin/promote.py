"""Bir kullanıcıya admin rolü verir veya geri alır. Varsayılan admin hesabı yoktur (go-live #14).

Kullanıcı önce uygulamadan normal kayıt olur (parolayı kendisi belirler), sonra sunucuda:
    python -m app.admin.promote ad@ornek.com            # admin yap
    python -m app.admin.promote ad@ornek.com --revoke   # normal kullanıcıya döndür
Production'da: make prod-admin EMAIL=ad@ornek.com (infra/pc/deploy.md).
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.db.enums import UserRole
from app.db.models import AuditLog
from app.db.session import get_sessionmaker
from app.repositories.users import UserRepository


def set_role(session: Session, email: str, role: UserRole) -> bool:
    repo = UserRepository(session)
    user = repo.get_active_by_email(email)
    if user is None:
        return False
    if user.role != role:
        user.role = role
        action = "admin.grant" if role == UserRole.ADMIN else "admin.revoke"
        repo.add_audit(AuditLog(user_id=user.id, action=action, entity="users", entity_id=str(user.id)))
        session.commit()
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kullanıcıya admin rolü ver / geri al")
    parser.add_argument("email")
    parser.add_argument("--revoke", action="store_true", help="admin rolünü geri al")
    args = parser.parse_args(argv)

    role = UserRole.USER if args.revoke else UserRole.ADMIN
    with get_sessionmaker()() as session:
        if not set_role(session, args.email.strip(), role):
            print("Bu e-postayla aktif kullanıcı yok. Önce uygulamadan kayıt olunmalı.", file=sys.stderr)
            return 1
    print(f"Rol: {role.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
