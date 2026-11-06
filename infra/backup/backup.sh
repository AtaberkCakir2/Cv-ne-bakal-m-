#!/usr/bin/env bash
# Postgres'in günlük yedeği (T-068): pg_dump → restic (şifreli, PC dışı depo), 7 günlük + 4 haftalık saklama.
# `backup` konteynerinin içinde çalışır; normalde scheduler.sh çağırır. Elle: make backup-now (infra/backup/README.md).
#
# Ayarlar konteyner ortamından gelir (infra/pc/.env.prod):
#   RESTIC_REPOSITORY, RESTIC_PASSWORD (+ deponun kendi değişkenleri, ör. B2_ACCOUNT_ID / B2_ACCOUNT_KEY)
#   PGHOST, PGUSER, PGPASSWORD, PGDATABASE (compose doldurur), BACKUP_TAG (ortam adı)
#
# Döküm diske yazılmaz, doğrudan restic'e akar. pg_dump yarıda kalırsa restic snapshot oluşturmaz
# (--stdin-from-command, restic >= 0.17). CV dosyası ve ham metni veritabanında olmadığı için yedekte de yoktur.
set -euo pipefail

TAG="${BACKUP_TAG:?BACKUP_TAG tanımlı değil}"
STATE_DIR="${STATE_DIR:-/state}"
DUMP_NAME="careerai-$TAG.dump"

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY tanımlı değil (infra/pc/.env.prod)}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD tanımlı değil (infra/pc/.env.prod)}"

log() { printf '%s %s\n' "$(date '+%F %T')" "$*"; }

# Aynı anda iki yedek çalışmasın (zamanlayıcı + make backup-now).
exec 9>"/tmp/careerai-backup.lock"
flock -n 9 || { echo "Başka bir yedek çalışıyor" >&2; exit 1; }

log "Yedek başlıyor: $TAG"
# --host sabit: konteyner adı her yeniden oluşturmada değişir, saklama kuralı (group-by host) bozulmasın.
restic backup --quiet --host careerai-pc --tag "$TAG" --tag postgres \
  --stdin-filename "$DUMP_NAME" --stdin-from-command -- \
  pg_dump --format=custom --compress=6

log "Eski yedekler temizleniyor (7 günlük + 4 haftalık)"
restic forget --quiet --tag "$TAG" --group-by host,tags --keep-daily 7 --keep-weekly 4 --prune

# Pazar günleri depodaki verinin %10'u okunup doğrulanır; bozulma geri yükleme gününe kalmasın.
if [[ "$(date +%u)" == 7 ]]; then
  log "Depo kontrolü"
  restic check --read-data-subset=10%
fi

# Zamanlayıcı ve izleme (T-066) bu dosyaya bakar: 26 saatten eskiyse yedek çalışmıyor demektir.
mkdir -p "$STATE_DIR"
date +%s > "$STATE_DIR/last-success"
log "Yedek tamam: $TAG"
