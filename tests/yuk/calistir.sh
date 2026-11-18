#!/usr/bin/env bash
# Yük testi (T-072): E2E ortamını (tests/e2e/ortam.sh) istek sınırı kapalı kurar, k6'yı Docker'da aynı ağda çalıştırır,
# özeti tests/yuk/sonuclar/ altına yazar ve ortamı kaldırır.
#
#   bash tests/yuk/calistir.sh                 # kabul kriteri: 20 kullanıcı, 30 dk
#   SURE=3m bash tests/yuk/calistir.sh         # kısa deneme
#   VUS=40 SURE=10m bash tests/yuk/calistir.sh
#   ORTAMI_BIRAK=1 bash tests/yuk/calistir.sh  # bittiğinde ortamı kaldırma (loglara bakmak için)
#
# Geliştirme ortamıyla aynı portları kullanır: önce `make down`. Production'a dokunmaz (ayrı compose projesi).
set -euo pipefail

cd "$(dirname "$0")/../.."
export MSYS_NO_PATHCONV=1
K6_IMAGE="${K6_IMAGE:-grafana/k6:1.3.0}"
SURE="${SURE:-30m}"
VUS="${VUS:-20}"
CIKTI="tests/yuk/sonuclar/$(date +%Y%m%d-%H%M)-${VUS}vu-${SURE}"
mkdir -p "$CIKTI"

kaldir() { [[ -n "${ORTAMI_BIRAK:-}" ]] || bash tests/e2e/ortam.sh down >/dev/null 2>&1 || true; }
trap kaldir EXIT

RATE_LIMIT_ENABLED=false bash tests/e2e/ortam.sh up

# Ortamın kaynak kullanımı test süresince 30 sn'de bir kaydedilir (RAM < %85 kriteri için).
( while sleep 30; do
    docker stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' \
      | grep careerai-e2e | sed "s/^/$(date +%H:%M:%S)\t/"
  done >"$CIKTI/kaynak.tsv" ) &
IZLEYICI=$!

set +e
docker run --rm -i --network careerai-e2e_default \
  -e BASE_URL=http://api:8000 -e VUS="$VUS" -e SURE="$SURE" \
  -e ANALIZ_ARALIK_SN="${ANALIZ_ARALIK_SN:-300}" \
  -v "$PWD/tests/yuk:/yuk" "$K6_IMAGE" run --quiet --summary-export "/yuk/${CIKTI#tests/yuk/}/ozet.json" /yuk/api.js \
  | tee "$CIKTI/k6.txt"
SONUC=${PIPESTATUS[0]}
set -e
kill "$IZLEYICI" 2>/dev/null || true

echo "Sonuç: $CIKTI (k6 çıkış kodu $SONUC; 99 = eşik aşıldı)"
exit "$SONUC"
