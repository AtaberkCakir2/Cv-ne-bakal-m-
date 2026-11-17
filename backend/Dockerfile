# CareerAI API (FastAPI). docker-compose'daki `api` servisi bu dosyayla derlenir (T-007).
# Lokal: `make up` (backend/Dockerfile varsa api profili otomatik eklenir) → http://localhost:8000/docs
FROM python:3.12-slim

# Taban imajdaki Debian paketlerinin güvenlik yamaları: Docker Hub imajı yenilenene kadar Trivy HIGH buluyor
# (ör. zlib CVE-2026-85091, 17.11.2026; G-4). scraper/Dockerfile ile aynı.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Önce sadece bağımlılıklar: kod değişince bu katman yeniden kurulmaz.
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py && pip install . && rm -rf app build *.egg-info

COPY app ./app

# Root olmayan kullanıcı
RUN useradd --create-home --uid 10001 careerai
USER careerai

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2)"

# --proxy-headers: gerçek istemci IP'si X-Forwarded-For'dan okunur (IP başına istek sınırları, T-050).
# Güvenilen vekil burada verilmez: production'da compose FORWARDED_ALLOW_IPS=${COMPOSE_SUBNET} verir (sadece
# projenin ağı, yani cloudflared; infra/pc/compose.yml). Bayrak ortam değişkenini ezeceği için eklenmez; "*" verilmez.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
