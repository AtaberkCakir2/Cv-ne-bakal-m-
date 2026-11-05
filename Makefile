# Lokal geliştirme komutları (T-007). Windows'ta make yoksa: winget install ezwinports.make
# Her hedefin make'siz karşılığı yanında yazılı.

-include .env

# backend/ veya ai/ altında Dockerfile varsa api / worker servisleri de başlatılır.
# Analiz işçisi (T-039) backend/app/worker/ main'e gelince eklenir.
PROFILES := $(if $(wildcard backend/Dockerfile),--profile api) $(if $(wildcard ai/Dockerfile),--profile worker) \
            $(if $(wildcard backend/app/worker/celery_app.py),--profile analysis)
COMPOSE  := docker compose $(PROFILES)
MODEL    ?= $(or $(OLLAMA_MODEL),llama3.1:8b)

.PHONY: help up down restart ps logs model psql redis-cli reset check-env

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
