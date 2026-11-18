#!/usr/bin/env bash
# Yedek zamanlayıcısı (T-068, karar #30, risk R-18). Her gün BACKUP_HOUR'da (varsayılan 02:00) yedek alır.
# PC o saatte kapalıysa veya uykudaysa, açıldıktan sonraki ilk kontrolde (en geç CHECK_SECONDS) kaçan yedeği alır.
# Başarısız yedek RETRY_SECONDS sonra yeniden denenir.
set -uo pipefail

STATE_DIR="${STATE_DIR:-/state}"
BACKUP_HOUR="${BACKUP_HOUR:-02}"
CHECK_SECONDS="${CHECK_SECONDS:-600}"
RETRY_SECONDS="${RETRY_SECONDS:-1800}"

# En son geçmiş "BACKUP_HOUR:00" anı (epoch). Ondan sonra başarılı yedek yoksa yedek zamanı gelmiştir.
last_slot() {
  local today now
  today="$(date -d "$(date +%F) $BACKUP_HOUR:00" +%s)"
  now="$(date +%s)"
  if (( now >= today )); then echo "$today"; else echo $(( today - 86400 )); fi
}

last_success() { cat "$STATE_DIR/last-success" 2>/dev/null || echo 0; }

echo "$(date '+%F %T') Zamanlayıcı başladı: her gün $BACKUP_HOUR:00, kontrol aralığı ${CHECK_SECONDS} sn"
while true; do
  if (( $(last_success) < $(last_slot) )); then
    if backup.sh; then
      sleep "$CHECK_SECONDS"
    else
      echo "$(date '+%F %T') Yedek başarısız; ${RETRY_SECONDS} sn sonra yeniden denenecek" >&2
      sleep "$RETRY_SECONDS"
    fi
  else
    sleep "$CHECK_SECONDS"
  fi
done
