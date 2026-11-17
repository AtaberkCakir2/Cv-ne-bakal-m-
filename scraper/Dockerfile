# CareerAI veri işçisi (worker-data, docs/mimari.md): Celery beat + gece ilan toplama (T-034).
# Modeller backend paketinden geldiği için bağlam repo kökü: docker build -f scraper/Dockerfile .
FROM python:3.12-slim

# Taban imajdaki Debian paketlerinin güvenlik yamaları: Docker Hub imajı yenilenene kadar Trivy HIGH buluyor
# (ör. zlib CVE-2026-85091, 17.11.2026). infra/backup/Dockerfile'daki apk upgrade ile aynı amaç.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Önce sadece bağımlılıklar: kod değişince bu katman yeniden kurulmaz.
COPY backend/pyproject.toml backend/
COPY ai/pyproject.toml ai/
COPY scraper/pyproject.toml scraper/
RUN mkdir -p backend/app ai/pii ai/extraction scraper/collector scraper/etl \
    && touch backend/app/__init__.py ai/pii/__init__.py ai/extraction/__init__.py scraper/collector/__init__.py \
       scraper/etl/__init__.py \
    && pip install -e backend -e ai -e scraper

# Editable kurulum: taksonomi CSV'leri paketin yanındaki scraper/taxonomy/'den okunur (pii de aynı dosyayı bulur).
# ai/'den sadece ilan maskeleme (pii) ve CV ile ortak yetkinlik eşleyicisi (extraction) gerekir; NER (torch)
# kurulmaz, ilanlar kurallarla maskelenir.
COPY backend/app backend/app
COPY ai/pii ai/pii
COPY ai/extraction ai/extraction
COPY scraper/collector scraper/collector
COPY scraper/etl scraper/etl
COPY scraper/taxonomy scraper/taxonomy

# data/: YouTube arama durumu (T-046), compose'da kalıcı volume.
RUN useradd --create-home --uid 10001 careerai \
    && mkdir -p scraper/data && chown careerai scraper/data
USER careerai
WORKDIR /srv/scraper

HEALTHCHECK --interval=60s --timeout=20s --start-period=30s --retries=3 \
    CMD celery -A collector.tasks inspect ping --timeout 10 || exit 1

# Tek süreç: işçi + beat (-B), tek eşzamanlılık. Beat durum dosyası konteyner içinde; yeniden başlayınca
# zamanlama crontab'dan tekrar hesaplanır.
CMD ["celery", "-A", "collector.tasks", "worker", "-B", "-Q", "data", "--concurrency", "1", \
     "--loglevel", "INFO", "-s", "/tmp/celerybeat-schedule"]
