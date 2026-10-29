"""Engine ve oturum fabrikası. Repository'ler oturumu buradan alır; FastAPI bağımlılığı backend tarafında yazılır."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping: Postgres yeniden başlarsa kopmuş bağlantı ilk sorguda fark edilip yenilenir.
    # hide_parameters: hata mesajlarına ve loglara SQL parametreleri (ilan metni, e-posta vb.) girmez (karar #9).
    return create_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
