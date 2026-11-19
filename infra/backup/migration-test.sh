#!/usr/bin/env bash
# Gerçek veriyle migration geri alma testi (go-live #15, #49). Son yedeği geçici bir Postgres kapsayıcısına yükler ve
# o kopya üzerinde:
#   1) rollback provası: bir adım geri (downgrade -1) + tekrar ileri (upgrade head); temel tabloların satır sayıları
#      değişmemeli (deploy geri alınırken migration'ı da geri almak gerekirse olacak olan budur),
#   2) tam geri alma: her migration tek tek base'e kadar geri alınır, sonra head'e çıkılır.
# Canlı veritabanına ve production konteynerlerine dokunmaz: yedek `backup` imajıyla tek seferlik okunur (prod kapalıyken
# de çalışır). Kapsayıcı birimiyle birlikte silinir (içinde kişisel veri var).
#   bash infra/backup/migration-test.sh [production|staging] [snapshot]     (Git Bash; snapshot verilmezse en son yedek)
# Alembic yerel Python'la çalışır (repodaki migration'lar); PY ile değiştirilebilir: PY=/c/venv/careerai/Scripts/python
set -euo pipefail

ENV_NAME="${1:-production}"
SNAPSHOT="${2:-latest}"
PG_IMAGE="${PG_IMAGE:-pgvector/pgvector:pg16}"
PY="${PY:-python}"
CONTAINER="careerai-migration-test-$$"
# Rollback provasında sayısı korunması gereken tablolar (yedekte boş olabilenler de sayılır, eşitlik aranır).
TABLES="users consents analyses job_sources job_postings job_posting_skills skills roles resources"

case "$ENV_NAME" in
  production) PROJECT=careerai-prod; ENV_FILE=.env.prod ;;
  staging) PROJECT=careerai-staging; ENV_FILE=.env.staging ;;
  *) echo "Ortam production veya staging olmalı: $ENV_NAME" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ALEMBIC_INI="$ROOT/backend/app/db/alembic.ini"
cd "$ROOT/infra/pc"
[[ -f "$ENV_FILE" ]] || { echo "infra/pc/$ENV_FILE yok" >&2; exit 1; }
compose() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f compose.yml "$@"; }

cleanup() { docker rm -fv "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

start=$(date +%s)
echo "Geçici Postgres açılıyor (sadece 127.0.0.1)"
docker run -d --rm --name "$CONTAINER" -p 127.0.0.1::5432 \
  -e POSTGRES_PASSWORD=restore -e POSTGRES_DB=restore "$PG_IMAGE" >/dev/null
for _ in $(seq 60); do
  docker exec "$CONTAINER" pg_isready -h 127.0.0.1 -U postgres -d restore >/dev/null 2>&1 && break
  sleep 1
done
PORT="$(docker port "$CONTAINER" 5432/tcp | head -1 | sed 's/.*://' | tr -d '\r')"
URL="postgresql+psycopg://postgres:restore@127.0.0.1:$PORT/restore"

echo "Yedek yükleniyor: $ENV_NAME, $SNAPSHOT"
# shellcheck disable=SC2016 # değişken konteynerin içinde açılmalı
compose run --rm --no-deps -T backup sh -c 'restic dump --tag "$BACKUP_TAG" "$1" "/careerai-$BACKUP_TAG.dump"' sh "$SNAPSHOT" \
  | docker exec -i "$CONTAINER" pg_restore -U postgres -d restore --no-owner --no-privileges --exit-on-error
echo "Yükleme süresi: $(( $(date +%s) - start )) sn"

alembic() { "$PY" -m alembic -c "$ALEMBIC_INI" -x "url=$URL" "$@"; }
current() { alembic current 2>/dev/null | awk 'NF { print $1 }' | tail -1; }
counts() {
  local sql="" t
  for t in $TABLES; do sql+="select '$t', (select count(*) from $t) union all "; done
  docker exec -i "$CONTAINER" psql -U postgres -d restore -At -F ' ' -c "${sql% union all };" | tr -d '\r'
}

HEAD="$(current)"
echo "Yedekteki sürüm: $HEAD"
[[ -n "$HEAD" ]] || { echo "alembic_version boş: yedek yüklenmemiş" >&2; exit 1; }
before="$(counts)"

echo
echo "== 1) Rollback provası: downgrade -1 → upgrade head"
t=$(date +%s)
alembic downgrade -1
echo "   geri alındı: $(current)"
alembic upgrade head
after="$(counts)"
echo "   tekrar ileri: $(current) ($(( $(date +%s) - t )) sn)"
printf '\n   %-20s %10s %10s\n' tablo önce sonra
join -j 1 <(sort <<<"$before") <(sort <<<"$after") | awk '{ printf "   %-20s %10s %10s\n", $1, $2, $3 }'
if [[ "$before" != "$after" ]]; then
  echo "Rollback provası BAŞARISIZ: satır sayıları değişti" >&2
  exit 1
fi
[[ "$(current)" == "$HEAD" ]] || { echo "Rollback provası BAŞARISIZ: head'e dönülmedi" >&2; exit 1; }

echo
echo "== 2) Tam geri alma: base'e kadar tek tek, sonra head"
t=$(date +%s)
while [[ -n "$(current)" ]]; do
  rev="$(current)"
  alembic downgrade -1
  echo "   $rev geri alındı"
done
alembic upgrade head
[[ "$(current)" == "$HEAD" ]] || { echo "Tam geri alma BAŞARISIZ: head'e dönülmedi" >&2; exit 1; }
echo "   base → $HEAD ($(( $(date +%s) - t )) sn)"

echo
echo "Migration geri alma testi tamam (toplam $(( $(date +%s) - start )) sn)"
