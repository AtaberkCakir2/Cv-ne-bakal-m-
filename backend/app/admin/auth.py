"""Panel girişi: e-posta + parola, sadece `role = admin` (go-live #14).

Oturum imzalı çerezde sadece kullanıcı kimliğini taşır; rol her istekte veritabanından okunur. Rolü düşürülen veya
silinen kullanıcı bir sonraki tıklamada dışarı atılır (API'deki `require_admin` ile aynı ilke).
"""

import hashlib
import hmac
import uuid
from collections.abc import Callable

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from app.core import security
from app.core.config import Settings
from app.core.rate_limit import Limit, RateLimiter
from app.db.enums import UserRole
from app.db.models import AuditLog, User
from app.repositories.users import UserRepository

SESSION_KEY = "admin_user_id"
SESSION_MAX_AGE_S = 8 * 3600  # bir iş günü; sonra yeniden giriş


def session_secret(settings: Settings) -> str:
    # Ayrı bir sır eklememek için JWT_SECRET'ten türetilir; amaç etiketi farklı olduğu için JWT imzasıyla karışmaz.
    return hmac.new(settings.jwt_secret.encode(), b"careerai-admin-session", hashlib.sha256).hexdigest()


class AdminAuth(AuthenticationBackend):
    def __init__(
        self,
        settings: Settings,
        maker: sessionmaker[Session],
        limiter: Callable[[], RateLimiter | None],
    ) -> None:
        super().__init__(
            secret_key=session_secret(settings),
            session_cookie="careerai_admin",
            max_age=SESSION_MAX_AGE_S,
            path="/admin",
            # strict: başka siteden gelen form/link çerezi taşımaz (panelin formlarında CSRF jetonu yok).
            same_site="strict",
            https_only=not settings.is_explicit_dev,
        )
        self.settings = settings
        self.maker = maker
        self.limiter = limiter

    async def login(self, request: Request) -> Response | bool:
        ip = request.client.host if request.client else None
        limiter = self.limiter()
        if limiter is not None:
            limit = Limit("admin_login", self.settings.rate_limit_auth_per_minute, 60)
            retry = await limiter.retry_after(limit, limiter.ip_subject(ip))
            if retry is not None:
                return PlainTextResponse(
                    "Çok fazla deneme. Biraz sonra tekrar deneyin.",
                    status_code=429,
                    headers={"Retry-After": str(retry)},
                )

        form = await request.form()
        email, password = str(form.get("username", "")).strip(), str(form.get("password", ""))
        user_id = await run_in_threadpool(self._check_credentials, email, password, ip)
        if user_id is None:
            return False
        request.session.clear()
        request.session[SESSION_KEY] = str(user_id)
        return True

    def _check_credentials(self, email: str, password: str, ip: str | None) -> uuid.UUID | None:
        with self.maker() as session:
            repo = UserRepository(session)
            user = repo.get_active_by_email(email) if email else None
            # Kullanıcı yoksa da parola doğrulaması çalışır (zamanlama eşitleme, AuthService.login ile aynı).
            if not security.verify_password(user.password_hash if user else None, password) or user is None:
                return None
            # Admin olmayan kullanıcıya da aynı hata: hangi e-postanın admin olduğu sızmaz.
            if user.role != UserRole.ADMIN:
                return None
            repo.add_audit(AuditLog(user_id=user.id, action="admin.login", ip_hash=security.hash_ip(ip, self.settings)))
            session.commit()
            return user.id

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        raw = request.session.get(SESSION_KEY)
        try:
            user_id = uuid.UUID(str(raw))
        except ValueError:
            return False
        if not await run_in_threadpool(self._is_admin, user_id):
            request.session.clear()
            return False
        return True

    def _is_admin(self, user_id: uuid.UUID) -> bool:
        with self.maker() as session:
            user: User | None = UserRepository(session).get_active_by_id(user_id)
            return user is not None and user.role == UserRole.ADMIN

    async def get_user_id(self, request: Request) -> uuid.UUID | None:
        raw = request.session.get(SESSION_KEY)
        return uuid.UUID(raw) if raw else None
