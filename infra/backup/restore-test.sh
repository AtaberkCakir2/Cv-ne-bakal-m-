#!/usr/bin/env bash
# Geri yükleme testi (T-068; go-live.md: aylık). Son yedeği geçici bir Postgres kapsayıcısına yükler, tabloların satır
# sayılarını canlı veritabanıyla yan yana yazar ve kapsayıcıyı siler. Canlı veritabanına yazmaz.
#   restore-test.sh <ortam> <compose-klasörü> [snapshot]     snapshot verilmezse en son yedek
set -euo pipefail

ENV_NAME="${1:?Kullanım: restore-test.sh <ortam> <compose-klasörü> [snapshot]}"
COMPOSE_DIR="${2:?Kullanım: restore-test.sh <ortam> <compose-klasörü> [snapshot]}"
SNAPSHOT="${3:-latest}"
RESTIC="${RESTIC:-restic}"
PG_IMAGE="${PG_IMAGE:-pgvector/pgvector:pg16}"
CONTAINER="careerai-restore-test-$$"
TABLES="users consents analyses job_sources job_postings job_posting_skills skills roles role_skill_stats resources"

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY tanımlı değil (backup.env)}"

# -v: imajın anonim veri birimi geri yüklenen veritabanının kendisi; silinmezse kişisel veri diskte kalır.
cleanup() { docker rm -fv "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

counts() {  # $@: psql komutu (bağlantı dahil); her satır "tablo sayı"
  local sql="" t
  for t in $TABLES; do sql+="select '$t', (select count(*) from $t) union all "; done
  sql+="select 'alembic_version', (select count(*) from alembic_version);"
  "$@" -At -F ' ' -c "$sql"
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
"$RESTIC" dump --tag "$ENV_NAME" "$SNAPSHOT" "/careerai-$ENV_NAME.dump" \
  | docker exec -i "$CONTAINER" pg_restore -U postgres -d restore --no-owner --no-privileges --exit-on-error
echo "Yükleme süresi: $(( $(date +%s) - start )) sn"

restored="$(counts docker exec -i "$CONTAINER" psql -U postgres -d restore)"
# shellcheck disable=SC2016 # değişkenler kapsayıcının içinde açılmalı
live="$(counts docker compose --project-directory "$COMPOSE_DIR" exec -T postgres \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' psql)"

printf '\n%-20s %10s %10s\n' tablo yedek canlı
join -j 1 <(sort <<<"$restored") <(sort <<<"$live") | awk '{ printf "%-20s %10s %10s\n", $1, $2, $3 }'
# Canlı veri yedekten sonra değişmiş olabilir (gece toplaması); boş tablo ise yükleme sorunudur.
if awk '$1 == "skills" || $1 == "alembic_version" { if ($2 == 0) bad = 1 } END { exit !bad }' <<<"$restored"; then
  echo "Geri yükleme başarısız: temel tablolar boş" >&2
  exit 1
fi
echo "Geri yükleme testi tamam"
