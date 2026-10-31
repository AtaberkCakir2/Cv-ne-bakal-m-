#!/usr/bin/env bash
# Staging'i `main`'in son haline getirir (T-035). T-036 bu adımları GitHub Actions'tan çalıştıracak.
# Sunucuda deploy kullanıcısıyla: bash infra/staging/deploy.sh
set -euo pipefail

cd "$(dirname "$0")"
[[ -f .env ]] || { echo "infra/staging/.env yok: README'deki 3. adım" >&2; exit 1; }

git fetch --quiet origin
git merge --ff-only --quiet origin/main

docker compose build --pull
docker compose up -d postgres redis ollama --wait
docker compose run --rm --no-deps api alembic -c app/db/alembic.ini upgrade head
docker compose up -d --wait --remove-orphans

docker compose ps
