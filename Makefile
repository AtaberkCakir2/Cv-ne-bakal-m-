# Lokal geliştirme komutları (T-007). Windows'ta make yoksa: winget install ezwinports.make
# Her hedefin make'siz karşılığı yanında yazılı.

-include .env

# backend/ veya ai/ altında Dockerfile varsa api / worker servisleri de başlatılır.
PROFILES := $(if $(wildcard backend/Dockerfile),--profile api) $(if $(wildcard ai/Dockerfile),--profile worker)
COMPOSE  := docker compose $(PROFILES)
MODEL    ?= $(or $(OLLAMA_MODEL),llama3.1:8b)

.PHONY: help up down restart ps logs model psql redis-cli reset check-env prod-ps prod-logs prod-local prod-model staging-ps staging-down backup-init backup-now backup-list

# $(info) kabuk kullanmaz; Windows (cmd) ve macOS/Linux'ta aynı çıktıyı verir.
help:
	$(info make up        Tum servisleri baslatir ve saglikli olmalarini bekler)
	$(info make model     Ollama modelini indirir ($(MODEL), ilk seferde ~5 GB))
	$(info make ps        Servis durumlari)
	$(info make logs      Canli loglar (cikis: Ctrl+C))
	$(info make psql      PostgreSQL konsolu)
	$(info make redis-cli Redis konsolu)
	$(info make down      Servisleri durdurur (veriler kalir))
	$(info make reset     Servisleri durdurur ve TUM lokal veriyi siler)
	$(info Production / prova (karar #30, infra/pc/deploy.md). Deploy Git Bash'te: bash infra/pc/deploy.sh v1.0.0)
	$(info make prod-ps   make prod-logs   make prod-model   make prod-local (sunum B plani))
	$(info make staging-ps   make staging-down)
	$(info make backup-init (bir kez)   make backup-now   make backup-list   Geri yukleme testi: bash infra/backup/restore-test.sh)
	@cd .

check-env:
	$(if $(wildcard .env),,$(error .env dosyasi yok. Once: cp .env.example .env))

# docker compose up -d --wait
up: check-env
	$(COMPOSE) up -d --build --wait

# docker compose down
down:
	$(COMPOSE) down

restart: down up

# docker compose ps
ps:
	$(COMPOSE) ps

# docker compose logs -f --tail=100
logs:
	$(COMPOSE) logs -f --tail=100

# docker compose exec ollama ollama pull llama3.1:8b
model:
	docker compose exec ollama ollama pull $(MODEL)

# docker compose exec postgres psql -U careerai -d careerai
psql:
	docker compose exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# docker compose exec redis redis-cli
redis-cli:
	docker compose exec redis redis-cli

# docker compose down -v  (Postgres verisi ve indirilen modeller silinir)
reset:
	$(COMPOSE) down -v

# --- Production ve prova ortamı (bu PC'de, karar #30). Ayrıntı: infra/pc/deploy.md ---
PC_PROD    := docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml
PC_STAGING := docker compose -p careerai-staging --env-file infra/pc/.env.staging -f infra/pc/compose.yml

prod-ps:
	$(PC_PROD) ps

prod-logs:
	$(PC_PROD) logs -f --tail=100

# Model dosyaları iki ortamda ortak volume'da (careerai-ollama-models): bir kez indirmek yeter.
prod-model:
	$(PC_PROD) exec ollama ollama pull $(MODEL)

# Sunum B planı: api'yi sadece bu PC'ye açar (127.0.0.1:8100).
prod-local:
	$(PC_PROD) -f infra/pc/compose.local.yml up -d --no-build --wait api

staging-ps:
	$(PC_STAGING) ps

# Prova bitince kapatılır; verisi kalır. Veriyi de silmek için sonuna -v (ortak Ollama modeli silinmez).
staging-down:
	$(PC_STAGING) down

# --- Yedek (T-068, infra/backup/README.md). backup servisi production'da açıktır. ---
# Depoyu bir kez oluşturur (restic init).
backup-init:
	$(PC_PROD) run --rm --no-deps backup restic init

# Zamanlayıcıyı beklemeden şimdi yedek alır.
backup-now:
	$(PC_PROD) exec backup backup.sh

backup-list:
	$(PC_PROD) exec backup restic snapshots
