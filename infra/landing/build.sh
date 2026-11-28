#!/usr/bin/env bash
# Tanıtım sayfasını (T-070) Cloudflare Pages çıktısının köküne koyar. Yasal sayfalar (Anıl, T-065) aynı Pages projesinde
# alt yollarda durur (/aydinlatma/, /gizlilik/…); bu betik onların derlemesinden SONRA çalışır ve ana sayfayı değiştirir.
#
#   bash infra/landing/build.sh [çıktı klasörü]     (varsayılan web/yasal-site/dist)
#
# Cloudflare Pages derleme komutu (README.md): cd web && npm ci && npm run build:yasal && cd .. && bash infra/landing/build.sh
# Yasal site henüz yoksa (çıktı klasörü boş) sayfa tek başına üretilir; yasal bağlantılar o zaman 404 verir.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/infra/landing"
OUT="${1:-$ROOT/web/yasal-site/dist}"
mkdir -p "$OUT/img"

cp "$SRC/index.html" "$SRC/landing.css" "$SRC/favicon.svg" "$OUT/"
cp "$SRC"/img/*.png "$OUT/img/"
# Renkler uygulamayla aynı dosyadan; yasal site zaten kopyaladıysa aynı içerik.
cp "$ROOT/web/src/ui/tokens.css" "$OUT/tokens.css"

# Güvenlik başlıkları: yasal site derlemesi yazdıysa onunki geçerli (taslakken noindex dahil). Yoksa aynı kurallar.
if [[ ! -f "$OUT/_headers" ]]; then
  cat >"$OUT/_headers" <<'EOF'
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
EOF
fi

echo "Tanıtım sayfası: $OUT/index.html"
