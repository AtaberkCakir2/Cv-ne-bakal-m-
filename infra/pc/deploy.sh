#!/usr/bin/env bash
# Bir sürümü bu PC'deki production veya prova ortamına alır; başarısız olursa önceki imajlara döner (T-036, karar #30).
#   bash infra/pc/deploy.sh <etiket-veya-commit> [production|staging]
#   ör. bash infra/pc/deploy.sh v1.0.0            bash infra/pc/deploy.sh origin/main staging
# Windows'ta Git Bash ile çalışır. İmajları CI üretir (.github/workflows/deploy.yml, main'deki her commit için);
# ilk kullanımdan önce bir kez `docker login ghcr.io` (infra/pc/deploy.md).
#
# Geri dönüş migration'ları geri almaz: migration'lar önceki sürümle uyumlu yazılmalı (sütun silme ayrı PR'da).
# Production'da migration'dan önce veri tabanı dökümü alınır (geri dönüş gerekirse elle yüklenir).
set -euo pipefail

REF="${1:?Kullanım: deploy.sh <etiket-veya-commit> [production|staging]}"
ENV_NAME="${2:-production}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/ataberkcakir2/careerai}"
SERVICES=(api worker-data)

case "$ENV_NAME" in
  production) PROJECT=careerai-prod; ENV_FILE=.env.prod ;;
  staging) PROJECT=careerai-staging; ENV_FILE=.env.staging ;;
  *) echo "Ortam production veya staging olmalı: $ENV_NAME" >&2; exit 2 ;;
esac

cd "$(dirname "$0")"
[[ -f "$ENV_FILE" ]] || { echo "infra/pc/$ENV_FILE yok: infra/pc/deploy.md 2. adım" >&2; exit 1; }
grep -qx "APP_ENVIRONMENT=$ENV_NAME" "$ENV_FILE" \
  || { echo "infra/pc/$ENV_FILE içinde APP_ENVIRONMENT=$ENV_NAME olmalı" >&2; exit 1; }

# İmajlar commit'e göre adlandırılır: etiket (v1.0.0) veya dal adı tam commit'e çevrilir.
SHA="$(git rev-parse --verify --quiet "$REF^{commit}")" || { echo "Bulunamadı: $REF (önce git fetch --tags)" >&2; exit 1; }

compose() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f compose.yml "$@"; }

# compose.yml sabit `careerai/<servis>:<ortam>` adını kullanır; deploy bu adı doğru imaja bağlar.
use_images() {  # $1: new (bu commit) veya previous
  local s
  if [[ "$1" == previous ]]; then
    for s in "${SERVICES[@]}"; do docker tag "careerai/$s:$ENV_NAME-previous" "careerai/$s:$ENV_NAME"; done
    return
  fi
  # Önce hepsi indirilir: biri inmezse hiçbir etiket değişmeden durulur, yarım sürüm kalmaz.
  for s in "${SERVICES[@]}"; do
    docker image inspect "$IMAGE_PREFIX-$s:$SHA" >/dev/null 2>&1 || docker pull --quiet "$IMAGE_PREFIX-$s:$SHA"
  done
  for s in "${SERVICES[@]}"; do docker tag "$IMAGE_PREFIX-$s:$SHA" "careerai/$s:$ENV_NAME"; done
}

# `docker image prune` etiketli imajları silmez: her servisin en yeni 3 <sha> etiketi kalır, gerisi silinir.
# İki ortam aynı imajları paylaşır; kullanımdaki imaj silinemez, hata yok sayılır.
prune_images() {
  local s
  for s in "${SERVICES[@]}"; do
    docker image ls "$IMAGE_PREFIX-$s" --format '{{.Repository}}:{{.Tag}}' | tail -n +4 \
      | xargs -r docker image rm >/dev/null 2>&1 || true
  done
  docker image prune --force >/dev/null
}

# Production'da migration öncesi döküm (PC'de, repo dışında). Son 5 döküm tutulur. CV verisi içermez (karar #5).
backup_db() {
  [[ "$ENV_NAME" == production ]] || return 0
  compose ps --status running --services 2>/dev/null | grep -qx postgres || return 0
  local dir="${BACKUP_DIR:-$HOME/careerai-yedek}"
  mkdir -p "$dir"
  local file
  file="$dir/deploy-$(date +%Y%m%d-%H%M%S)-${SHA:0:7}.dump"
  # shellcheck disable=SC2016  # değişkenler konteynerin içinde açılmalı
  compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$file" \
    || { rm -f "$file"; return 1; }
  echo "Döküm: $file"
  # Ad tarihle başladığı için ada göre sıralama = zamana göre sıralama.
  find "$dir" -maxdepth 1 -name 'deploy-*.dump' | sort -r | tail -n +6 | xargs -r rm -f
}

# `if roll_out` içinde `set -e` çalışmaz: her adım && ile bağlı, yoksa hatalı migration başarı sayılır.
roll_out() {
  compose up -d --no-build --wait postgres redis ollama \
    && backup_db \
    && compose run --rm --no-deps api alembic -c app/db/alembic.ini upgrade head \
    && compose up -d --no-build --wait --remove-orphans \
    && compose exec -T api python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=5)"
}

have_previous=false
if docker image inspect "careerai/api:$ENV_NAME" >/dev/null 2>&1 \
  && docker image inspect "careerai/worker-data:$ENV_NAME" >/dev/null 2>&1; then
  for s in "${SERVICES[@]}"; do docker tag "careerai/$s:$ENV_NAME" "careerai/$s:$ENV_NAME-previous"; done
  have_previous=true
fi

echo "Deploy: $REF ($SHA) → $PROJECT"
docker volume create careerai-ollama-models >/dev/null  # iki ortamın ortak model volume'u (varsa dokunmaz)
use_images new
if roll_out; then
  prune_images
  echo "Deploy tamam: $REF → $PROJECT"
  exit 0
fi

echo "Deploy başarısız: $REF" >&2
if [[ "$have_previous" == true ]]; then
  echo "Önceki imajlara dönülüyor" >&2
  use_images previous
  compose up -d --no-build --wait --remove-orphans
  echo "Önceki sürüme dönüldü" >&2
fi
exit 1
