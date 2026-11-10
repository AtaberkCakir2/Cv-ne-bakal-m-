#!/usr/bin/env bash
# Geri yükleme testi (T-068; go-live.md: aylık). Son yedeği geçici bir Postgres kapsayıcısına yükler, tabloların satır
# sayılarını canlı veritabanıyla yan yana yazar ve kapsayıcıyı siler. Canlı veritabanına yazmaz.
#   bash infra/backup/restore-test.sh [production|staging] [snapshot]     (Git Bash; snapshot verilmezse en son yedek)
# Depo ayarları ortamın env dosyasından (infra/pc/.env.prod) `backup` konteyneri üzerinden okunur.
set -euo pipefail

ENV_NAME="${1:-production}"
SNAPSHOT="${2:-latest}"
PG_IMAGE="${PG_IMAGE:-pgvector/pgvector:pg16}"
CONTAINER="careerai-restore-test-$$"
TABLES="users consents analyses job_sources job_postings job_posting_skills skills roles role_skill_stats resources"

case "$ENV_NAME" in
  production) PROJECT=careerai-prod; ENV_FILE=.env.prod ;;
  staging) PROJECT=careerai-staging; ENV_FILE=.env.staging ;;
  *) echo "Ortam production veya staging olmalı: $ENV_NAME" >&2; exit 2 ;;
esac

cd "$(dirname "$0")/../pc"
[[ -f "$ENV_FILE" ]] || { echo "infra/pc/$ENV_FILE yok" >&2; exit 1; }
compose() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f compose.yml "$@"; }

# -v: imajın anonim veri birimi geri yüklenen veritabanının kendisi; silinmezse kişisel veri diskte kalır.
cleanup() { docker rm -fv "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

counts() {  # $@: psql komutu (bağlantı dahil); her satır "tablo sayı"
  local sql="" t
  for t in $TABLES; do sql+="select '$t', (select count(*) from $t) union all "; done
  sql+="select 'alembic_version', (select count(*) from alembic_version);"
  "$@" -At -F ' ' -c "$sql" | tr -d '\r'
}

start=$(date +%s)
echo "Geçici Postgres açılıyor"
docker run -d --rm --name "$CONTAINER" -e POSTGRES_PASSWORD=restore -e POSTGRES_DB=restore "$PG_IMAGE" >/dev/null
for _ in $(seq 60); do
  # -h 127.0.0.1: ilk kurulumdaki geçici sunucu sadece soketi dinler, "hazır" sanılıp pg_restore kopmasın.
  docker exec "$CONTAINER" pg_isready -h 127.0.0.1 -U postgres -d restore >/dev/null 2>&1 && break
  sleep 1
done

echo "Yedek yükleniyor: $ENV_NAME, $SNAPSHOT"
# shellcheck disable=SC2016 # değişken konteynerin içinde açılmalı
compose exec -T backup sh -c 'restic dump --tag "$BACKUP_TAG" "$1" "/careerai-$BACKUP_TAG.dump"' sh "$SNAPSHOT" \
  | docker exec -i "$CONTAINER" pg_restore -U postgres -d restore --no-owner --no-privileges --exit-on-error
echo "Yükleme süresi: $(( $(date +%s) - start )) sn"

restored="$(counts docker exec -i "$CONTAINER" psql -U postgres -d restore)"
# shellcheck disable=SC2016 # değişkenler konteynerin içinde açılmalı
live="$(counts compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' psql)"

printf '\n%-20s %10s %10s\n' tablo yedek canlı
join -j 1 <(sort <<<"$restored") <(sort <<<"$live") | awk '{ printf "%-20s %10s %10s\n", $1, $2, $3 }'
# Canlı veri yedekten sonra değişmiş olabilir (gece toplaması); boş tablo ise yükleme sorunudur.
if awk '$1 == "skills" || $1 == "alembic_version" { if ($2 == 0) bad = 1 } END { exit !bad }' <<<"$restored"; then
  echo "Geri yükleme başarısız: temel tablolar boş" >&2
  exit 1
fi
echo "Geri yükleme testi tamam"
