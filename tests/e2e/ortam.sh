#!/usr/bin/env bash
# E2E test ortamı (T-071): docker compose ile geçici, boş bir yığın kurar veya kaldırır. CI (.github/workflows/e2e.yml)
# ve yerel çalıştırma (tests/e2e/README.md) aynı betiği kullanır. Karar #30: ayrı staging sunucusu yok.
#
#   bash tests/e2e/ortam.sh up     # api + analiz işçisi + postgres + redis'ler; migration; taksonomi ve kaynaklar
#   bash tests/e2e/ortam.sh psql   # (testler kullanır) stdin'deki SQL'i e2e veritabanında çalıştırır
#   bash tests/e2e/ortam.sh down   # her şeyi volume'larıyla siler
#
# Geliştirme ortamıyla aynı portları (127.0.0.1:5432, 8000…) kullanır: yerelde önce `make down`.
# ENVIRONMENT=test: analiz, AI modülü yerine sözleşmedeki örnek sonucu döner (backend/app/services/analyzer.py).
set -euo pipefail

cd "$(dirname "$0")/../.."
export MSYS_NO_PATHCONV=1  # Git Bash: /yollar Windows yoluna çevrilmesin
ENV_FILE=tests/e2e/.env.e2e
compose() {
  docker compose -p careerai-e2e --env-file "$ENV_FILE" -f docker-compose.yml -f tests/e2e/compose.e2e.yml \
    --profile api --profile analysis --profile data "$@"
}

write_env() {
  # Sadece bu geçici ortam için; sır değildir, her çalıştırmada yeniden yazılır (gitignore: .env.*).
  sed -e 's/^ENVIRONMENT=.*/ENVIRONMENT=test/' -e 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=e2e/' .env.example >"$ENV_FILE"
  # docker-compose.yml servisleri `env_file: .env` ister; CI'da yoksa aynı içerik konur. Test ortamına özgü
  # değerler (ENVIRONMENT, CORS) compose.e2e.yml'de sabit, geliştiricinin .env'i onları değiştirmez.
  [[ -f .env ]] || cp "$ENV_FILE" .env
}

case "${1:-}" in
  up)
    write_env
    compose build --quiet api worker-data
    compose up -d --wait postgres redis cv-redis
    compose run --rm --no-deps api alembic -c app/db/alembic.ini upgrade head
    # Pozisyonlar ve yetkinlikler (yükleme ekranındaki liste), elle derlenmiş kaynaklar (sonuçtaki öneriler).
    compose run --rm --no-deps worker-data python -m collector seed-taxonomy
    compose run --rm --no-deps worker-data python -m collector resources-seed
    compose up -d --no-build --wait api worker-analysis
    echo "E2E ortamı hazır: http://127.0.0.1:8000"
    ;;
  psql)
    # shellcheck disable=SC2016  # değişkenler konteynerin içinde açılır
    compose exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    ;;
  logs)
    compose logs --no-color --tail 200 api worker-analysis
    ;;
  down)
    [[ -f "$ENV_FILE" ]] || write_env
    compose down -v --remove-orphans
    ;;
  *)
    echo "Kullanım: bash tests/e2e/ortam.sh up|psql|logs|down" >&2
    exit 2
    ;;
esac
