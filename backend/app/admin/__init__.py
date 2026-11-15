"""Yönetim paneli (T-063): SQLAdmin ile kaynak havuzu, ilan kaynakları, toplama çalışmaları ve istatistikler.

`/admin` altında açılır, sadece `role = admin` kullanıcılar girer (go-live #14). Production'da ayrıca Cloudflare
Access arkasındadır (app/admin/README.md). Kişisel veri gösterilmez: kullanıcı, analiz ve CV tabloları panelde yok.
"""

from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin
from sqladmin.i18n import I18nConfig
from sqlalchemy.orm import Session, sessionmaker

from app.admin.audit import AdminAuditBackend
from app.admin.auth import AdminAuth
from app.admin.views import JobSourceAdmin, ResourceAdmin, ScrapeRunAdmin, StatsView
from app.core.config import Settings
from app.core.rate_limit import RateLimiter

BASE_URL = "/admin"
TEMPLATES = Path(__file__).parent / "templates"


def mount_admin(app: FastAPI, settings: Settings, maker: sessionmaker[Session]) -> Admin:
    """Paneli `app`'e bağlar. Veritabanına ilk istekte bağlanılır (engine tembel kurulur)."""

    def limiter() -> RateLimiter | None:
        # Sınırlayıcı create_app'te app.state'e konur; panel ayrı bir alt uygulama olduğu için buradan okunur.
        found: RateLimiter | None = getattr(app.state, "rate_limiter", None)
        return found

    admin = Admin(
        app,
        session_maker=maker,
        base_url=BASE_URL,
        title="CareerAI Yönetim",
        templates_dir=str(TEMPLATES),
        authentication_backend=AdminAuth(settings, maker, limiter),
        audit_backend=AdminAuditBackend(maker),
        # Arayüz her zaman Türkçe: tarayıcı dili ve dil çerezi dikkate alınmaz.
        i18n_config=I18nConfig(default_locale="tr", language_cookie_name=None, language_header_name=None),
    )
    admin.add_view(StatsView)
    admin.add_view(ResourceAdmin)
    admin.add_view(JobSourceAdmin)
    admin.add_view(ScrapeRunAdmin)
    return admin
