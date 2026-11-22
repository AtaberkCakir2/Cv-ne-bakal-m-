# Yedek konteyneri (T-068, karar #30): restic + Postgres 16 istemcisi. infra/pc/compose.yml'deki `backup` servisi.
# Windows'ta systemd/cron olmadığı için zamanlayıcı da bu konteynerin içindedir (scheduler.sh).
FROM restic/restic:0.20.0

# pg_dump sunucuyla aynı ana sürüm olmalı (pgvector/pgvector:pg16).
# apk upgrade: taban imajdaki OpenSSL/musl yamaları (T-064 Trivy taraması).
RUN apk upgrade --no-cache && apk add --no-cache bash postgresql16-client tzdata

COPY backup.sh scheduler.sh /usr/local/bin/
RUN chmod 0755 /usr/local/bin/backup.sh /usr/local/bin/scheduler.sh

ENV TZ=Europe/Istanbul STATE_DIR=/state
ENTRYPOINT []
CMD ["/usr/local/bin/scheduler.sh"]
