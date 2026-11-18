"""Panelde yapılan her ekleme/düzenleme/silme `audit_logs`'a yazılır: kim, ne zaman, hangi kayıt.

Değişen değerler yazılmaz (tabloda sütun yok); kaynak/ilan kaynağı ayarları kişisel veri değil, kaydın kendisi
sorulduğunda tablodan bakılır.
"""

import uuid
from typing import Any

from sqladmin.audit import AuditEntry, DBAuditBackend
from starlette.requests import Request

from app.db.models import AuditLog


class AdminAuditBackend(DBAuditBackend):
    def build_row(self, entry: AuditEntry, actor: Any, request: Request) -> AuditLog:
        return AuditLog(
            user_id=actor if isinstance(actor, uuid.UUID) else None,
            action=f"admin.{entry.action}",  # admin.create / admin.update / admin.delete
            entity=entry.identity,
            entity_id=entry.pk,
        )
