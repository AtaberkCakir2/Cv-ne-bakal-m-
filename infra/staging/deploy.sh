#!/usr/bin/env bash
# Verilen commit'in imajlarını staging'e alır; başarısız olursa önceki imajlara döner (T-036).
#   bash infra/staging/deploy.sh <commit-sha>
# Normalde .github/workflows/deploy.yml çalıştırır. Elle kullanılacaksa önce `docker login ghcr.io`.
#
# Geri dönüş migration'ları geri almaz: migration'lar önceki sürümle uyumlu yazılmalı (sütun silme ayrı PR'da).
set -euo pipefail

SHA="${1:?Kullanım: deploy.sh <commit-sha>}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/ataberkcakir2/careerai}"
SERVICES=(api worker-data)

cd "$(dirname "$0")"
[[ -f .env ]] || { echo "infra/staging/.env yok: infra/server/README.md 3. adım" >&2; exit 1; }

# compose.yml sabit `careerai/<servis>:staging` adını kullanır; deploy bu adı doğru imaja bağlar.
use_images() {  # $1: new (bu commit) veya previous
  for s in "${SERVICES[@]}"; do
    if [[ "$1" == previous ]]; then
      docker tag "careerai/$s:previous" "careerai/$s:staging"
    else
      local image="$IMAGE_PREFIX-$s:$SHA"
      docker image inspect "$image" >/dev/null 2>&1 || docker pull --quiet "$image"
      docker tag "$image" "careerai/$s:staging"
    fi
  done
}

# `if roll_out` içinde `set -e` çalışmaz: her adım && ile bağlı, yoksa hatalı migration başarı sayılır.
roll_out() {
  docker compose up -d --no-build --wait postgres redis ollama \
    && docker compose run --rm --no-deps api alembic -c app/db/alembic.ini upgrade head \
    && docker compose up -d --no-build --wait --remove-orphans \
    && docker compose exec -T api python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=5)"
}

have_previous=false
if docker image inspect "careerai/api:staging" >/dev/null 2>&1 \
  && docker image inspect "careerai/worker-data:staging" >/dev/null 2>&1; then
  for s in "${SERVICES[@]}"; do docker tag "careerai/$s:staging" "careerai/$s:previous"; done
  have_previous=true
fi

use_images new
if roll_out; then
  docker image prune --force >/dev/null
  echo "Deploy tamam: $SHA"
  exit 0
fi

echo "Deploy başarısız: $SHA" >&2
if [[ "$have_previous" == true ]]; then
  echo "Önceki imajlara dönülüyor" >&2
  use_images previous
  docker compose up -d --no-build --wait --remove-orphans
  echo "Önceki sürüme dönüldü" >&2
fi
exit 1
