#!/usr/bin/env bash
# Production'da vektörü boş yetkinlik ve ilanlara embedding üretir (T-057 gelene kadar; infra/pc/deploy.md "7. Vektörler").
#   make prod-embed            yeni ilanlar (gece toplamasından sonra)
#   make prod-embed HEPSI=1    model değiştiyse bütün vektörler baştan
# İmaj (~3,3 GB, model içinde) bir kez derlenir ve PC'de kalır; ai/ değişince Docker önbelleği yeniden derler.
# Kaldırmak: docker rmi careerai/embedding-gecici:local
set -euo pipefail

cd "$(dirname "$0")/../.."
ENV_FILE=infra/pc/.env.prod
PROJECT=careerai-prod
IMAGE=careerai/embedding-gecici:local
[[ -f "$ENV_FILE" ]] || { echo "$ENV_FILE yok" >&2; exit 1; }
compose() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f infra/pc/compose.yml "$@"; }
env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r'; }

compose ps --status running --services | grep -qx postgres || { echo "Production postgres çalışmıyor" >&2; exit 1; }

echo "Önce yedek (backup.sh)"
compose exec -T backup backup.sh

echo "İmaj: $IMAGE"
docker build -q -t "$IMAGE" -f infra/pc/embedding/Dockerfile ai >/dev/null

args=()
[[ -n "${HEPSI:-}" ]] && args+=(--hepsi)

# Uygulama rolüyle (careerai_app) bağlanır; parola ortam değişkeniyle geçer, komut satırında görünmez.
DATABASE_URL="postgresql+psycopg://careerai_app:$(env_value APP_DB_PASSWORD)@postgres:5432/$(env_value POSTGRES_DB)"
export DATABASE_URL
docker run --rm --network "${PROJECT}_default" -e DATABASE_URL "$IMAGE" python -m embedding "${args[@]}"
unset DATABASE_URL

# shellcheck disable=SC2016  # değişkenler konteynerin içinde açılmalı
compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F " " -c "
  select '"'"'yetkinlik'"'"', count(*) filter (where embedding is null), count(*) from skills
  union all select '"'"'ilan'"'"', count(*) filter (where embedding is null), count(*) from job_postings"' \
  | tr -d '\r' | while read -r ad bos toplam; do echo "$ad: vektörü boş $bos / $toplam"; done
