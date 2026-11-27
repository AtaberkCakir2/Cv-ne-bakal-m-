#!/usr/bin/env bash
# Yavaş sorgu ölçümü, tek oturumda (go-live #18, karar #40). Production'ın son deploy dökümü prova ortamına
# (`careerai-staging`) yüklenir, sayaçlar sıfırlanır, slow-queries-load.py yük verir, slow-queries.sql raporlar.
#   make staging-slow-queries                 (son döküm, 5 tur ≈ 4 dk)
#   bash infra/pc/slow-queries-staging.sh ~/careerai-yedek/deploy-….dump 5
# worker-data BAŞLATILMAZ: açılışta gece toplamasını kaçmış sayar ve gerçek sitelerden ilan çeker. api imajı
# production'dakiyle aynıdır (döküm de o sürümden). Bitince prova ortamı verisiyle silinir (döküm PC'de kalır).
set -euo pipefail
cd "$(dirname "$0")"

DUMP="${1:-$(find "${BACKUP_DIR:-$HOME/careerai-yedek}" -maxdepth 1 -name 'deploy-*.dump' | sort | tail -n 1)}"
ROUNDS="${2:-5}"
[[ -f "$DUMP" ]] || { echo "Döküm yok: $DUMP (production deploy'u döküm alır)" >&2; exit 1; }
[[ -f .env.staging ]] || { echo "infra/pc/.env.staging yok: infra/pc/deploy.md 2. adım" >&2; exit 1; }

compose() { docker compose -p careerai-staging --env-file .env.staging -f compose.yml "$@"; }
# shellcheck disable=SC2016  # değişkenler konteynerin içinde açılmalı
psql_owner() { compose exec -T postgres sh -c 'psql -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' "$@"; }

echo "Döküm: $DUMP"
docker tag careerai/api:production careerai/api:staging
compose up -d --wait postgres redis
# shellcheck disable=SC2016
compose exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
# shellcheck disable=SC2016
compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges --exit-on-error' < "$DUMP"

# Uygulama rolü (deploy.sh setup_app_role ile aynı): şifre psql değişkeniyle girişten verilir.
pw="$(sed -n 's/^APP_DB_PASSWORD=//p' .env.staging | tail -n 1 | tr -d '\r')"
{ printf '\\set app_pw %s\n' "$pw"; cat app-role.sql; } | psql_owner
unset pw
psql_owner <<<"SET client_min_messages = warning; CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

compose up -d --wait api
psql_owner -At <<<"SELECT pg_stat_statements_reset() IS NOT NULL;" >/dev/null
compose exec -T -e ROUNDS="$ROUNDS" api python - < slow-queries-load.py
# shellcheck disable=SC2016
compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < slow-queries.sql

compose down -v
echo "Prova ortamı kapatıldı, verisi silindi."
