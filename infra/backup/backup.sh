#!/usr/bin/env bash
# Postgres'in günlük yedeği (T-068): pg_dump → restic (şifreli, sunucu dışı depo), 7 günlük + 4 haftalık saklama.
#   backup.sh <ortam> <compose-klasörü>      ör. backup.sh staging /home/deploy/careerai/infra/staging
# Normalde systemd zamanlayıcısı her gece 02:00'de çalıştırır (README.md). Depo ve parola ortam değişkenlerinden gelir:
# RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE (+ deponun kendi değişkenleri), örnek: backup.env.example.
#
# Döküm diske yazılmaz, doğrudan restic'e akar. pg_dump yarıda kalırsa restic snapshot oluşturmaz
# (--stdin-from-command, restic >= 0.17). CV dosyası ve ham metni veritabanında olmadığı için yedekte de yoktur.
set -euo pipefail

ENV_NAME="${1:?Kullanım: backup.sh <ortam> <compose-klasörü>}"
COMPOSE_DIR="${2:?Kullanım: backup.sh <ortam> <compose-klasörü>}"
RESTIC="${RESTIC:-restic}"
STATE_DIR="${STATE_DIR:-/var/lib/careerai}"
DUMP_NAME="careerai-$ENV_NAME.dump"

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY tanımlı değil (backup.env)}"
[[ -n "${RESTIC_PASSWORD_FILE:-}${RESTIC_PASSWORD:-}" ]] || { echo "RESTIC_PASSWORD_FILE tanımlı değil" >&2; exit 1; }
[[ -f "$COMPOSE_DIR/compose.yml" || -f "$COMPOSE_DIR/docker-compose.yml" ]] \
  || { echo "$COMPOSE_DIR içinde compose dosyası yok" >&2; exit 1; }

version="$("$RESTIC" version | awk '{print $2}')"
[[ "$(printf '%s\n' 0.17.0 "$version" | sort -V | head -1)" == 0.17.0 ]] \
  || { echo "restic $version eski: en az 0.17 gerekli (sudo restic self-update)" >&2; exit 1; }

log() { printf '%s %s\n' "$(date '+%F %T')" "$*"; }

# Aynı anda iki yedek çalışmasın (elle çalıştırma + zamanlayıcı).
exec 9>"/tmp/careerai-backup-$ENV_NAME.lock"
flock -n 9 || { echo "Başka bir yedek çalışıyor" >&2; exit 1; }

log "Yedek başlıyor: $ENV_NAME"
# Kullanıcı ve veritabanı adı kapsayıcının kendi ortamından okunur; parola gerekmez (yerel soket).
# shellcheck disable=SC2016 # değişkenler kapsayıcının içinde açılmalı
"$RESTIC" backup --quiet --host "$(hostname)" --tag "$ENV_NAME" --tag postgres \
  --stdin-filename "$DUMP_NAME" --stdin-from-command -- \
  docker compose --project-directory "$COMPOSE_DIR" exec -T postgres \
  sh -c 'pg_dump --format=custom --compress=6 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

log "Eski yedekler temizleniyor (7 günlük + 4 haftalık)"
"$RESTIC" forget --quiet --tag "$ENV_NAME" --group-by host,tags --keep-daily 7 --keep-weekly 4 --prune

# Pazar günleri depodaki verinin %10'u okunup doğrulanır; bozulma geri yükleme gününe kalmasın.
if [[ "$(date +%u)" == 7 ]]; then
  log "Depo kontrolü"
  "$RESTIC" check --read-data-subset=10%
fi

# İzleme (T-066) bu dosyanın yaşına bakar: 26 saatten eskiyse yedek çalışmıyor demektir.
mkdir -p "$STATE_DIR"
date '+%FT%T%z' > "$STATE_DIR/backup-$ENV_NAME.last-success"
log "Yedek tamam: $ENV_NAME"
