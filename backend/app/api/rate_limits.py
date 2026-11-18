"""Uçlara bağlanan istek sınırları (T-050). Genel sınır middleware'de (app/core/rate_limit.py)."""

from fastapi import Depends, HTTPException, Request

from app.api.deps import CurrentUser
from app.core.rate_limit import TOO_MANY, Limit, RateLimiter, too_many_requests_headers


def _limiter(request: Request) -> RateLimiter | None:
    limiter: RateLimiter | None = getattr(request.app.state, "rate_limiter", None)
    return limiter


async def _enforce(limiter: RateLimiter, limit: Limit, subject: str) -> None:
    retry = await limiter.retry_after(limit, subject)
    if retry is not None:
        raise HTTPException(429, TOO_MANY, headers=too_many_requests_headers(retry))


async def limit_auth(request: Request) -> None:
    """Giriş, kayıt, e-posta doğrulama ve şifre sıfırlama: IP başına ortak sayaç (kaba kuvvet denemelerine karşı)."""
    limiter = _limiter(request)
    if limiter is not None:
        limit = Limit("auth", limiter.settings.rate_limit_auth_per_minute, 60)
        await _enforce(limiter, limit, limiter.ip_subject(request.client.host if request.client else None))


def _analyses_limit(limiter: RateLimiter) -> Limit:
    return Limit("analyses", limiter.settings.rate_limit_analyses_per_hour, 3600)


async def limit_analyses(request: Request, user: CurrentUser) -> None:
    """Kullanıcı başına saatlik analiz sınırı. Başlatılamayan analiz `release_analysis` ile geri düşülür."""
    limiter = _limiter(request)
    if limiter is not None:
        retry, counted = await limiter.check(_analyses_limit(limiter), str(user.id))
        if retry is not None:
            raise HTTPException(429, TOO_MANY, headers=too_many_requests_headers(retry))
        request.state.analysis_counted = counted


async def release_analysis(request: Request, user_id: object) -> None:
    """Reddedilen yükleme (bozuk/büyük PDF, kuyruk dolu…) saatlik hakkı harcamasın: sadece başlayan analiz sayılır.
    Reddedilen istekler yine de IP başına genel sınıra takılır."""
    limiter = _limiter(request)
    if limiter is not None and getattr(request.state, "analysis_counted", False):
        await limiter.release(_analyses_limit(limiter), str(user_id))


AuthRateLimit = Depends(limit_auth)
AnalysesRateLimit = Depends(limit_analyses)
