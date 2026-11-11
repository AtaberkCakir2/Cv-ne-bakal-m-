#!/bin/sh
# Alertmanager ayarını env'den üretir: TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID doluysa uyarılar ekibin Telegram
# grubuna gider, boşsa sadece Alertmanager'da kalır. Token konteynerin içindeki dosyada kalır, loglanmaz.
set -eu
CONFIG=/tmp/alertmanager.yml
umask 077
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  printf '%s' "$TELEGRAM_BOT_TOKEN" > /tmp/telegram_token
  cat > "$CONFIG" <<CFG
route:
  receiver: telegram
  group_by: [alertname]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
receivers:
  - name: telegram
    telegram_configs:
      - bot_token_file: /tmp/telegram_token
        chat_id: ${TELEGRAM_CHAT_ID}
        send_resolved: true
CFG
  echo "Uyarılar Telegram'a gönderilecek"
else
  cat > "$CONFIG" <<CFG
route:
  receiver: bos
receivers:
  - name: bos
CFG
  echo "TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID boş: uyarılar sadece Alertmanager'da görünür"
fi
exec /bin/alertmanager --config.file="$CONFIG" --storage.path=/alertmanager "$@"
