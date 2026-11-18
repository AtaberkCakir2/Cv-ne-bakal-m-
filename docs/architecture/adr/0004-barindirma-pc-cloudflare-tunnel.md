# ADR-0004 · Barındırma: PC + Docker Compose + Cloudflare Tunnel

- **Durum:** Öneri, uygulamada (karar #30, Burak ve Anıl onayı bekleniyor; eski karar #13 "tek VPS + Caddy" değişti → #30). İzleme kısmı karar #32, PC ayarları karar #31.
- **Tarih:** 06.11.2026
- **Sahibi:** Ataberk (altyapı)

## Bağlam

Fizibilite planı 6 aylık bir VPS (8 vCPU / 16 GB, ~4.200 TL) öngörüyordu. Bitirme projesinin amacı jüriye ve hocalara çalışan sistemi göstermek; sürekli trafik beklenmiyor. Ataberk'in bilgisayarı (i7-9750H, 32 GB RAM, GTX 1650) VPS'in iki katı bellek sunuyor. Ev/okul ağında sabit IP yok, modemde port açmak istenmiyor. Mobil uygulamanın Play Store'da gizlilik politikası URL'si PC kapalıyken de açık olmalı.

## Seçenekler

| Seçenek | Artı | Eksi |
|---|---|---|
| VPS + Caddy + Let's Encrypt (eski #13) | Hep açık; veri merkezinde | Aylık maliyet; 16 GB'ta 8B model + Postgres sıkışık; GPU yok |
| **PC + Cloudflare Tunnel** | Maliyet 0 (sadece alan adı); 32 GB RAM; port açmadan, IP göstermeden HTTPS; ağ değişse de çalışır | PC tek hata noktası (elektrik, internet, güncelleme); geliştirme ile aynı makine |
| PC + port yönlendirme + Caddy | Ek servis yok | Sabit IP / DDNS gerekir, ev IP'si görünür, modem erişimi gerekir |
| Tailscale Funnel | Kolay | Alan adı ve ölçek sınırlı, hocalara sunumda kendi alan adımız yok |

## Karar

- Production, PC'de ayrı bir compose projesidir: `careerai-prod`, kendi volume'ları, **hiçbir servis host'a port açmaz** (tek istisna Grafana, sadece `127.0.0.1:3000`).
- Dış erişim yalnızca `cloudflared` konteyneri üzerinden: `api.cvnebakalim.com` → `http://api:8000`. TLS, HSTS ve güvenlik başlıkları Cloudflare'de. API `X-Forwarded-For`'a yalnızca projenin kendi ağından (`COMPOSE_SUBNET`) güvenir.
- Tanıtım ve yasal sayfalar Cloudflare Pages'te (statik, PC'den bağımsız).
- Prova ortamı aynı PC'de geçici `careerai-staging` projesi; ayrı sunucu yok.
- İmajları CI üretir (GHCR, `main`'deki her commit); production **elle**, `bash infra/pc/deploy.sh vX.Y.Z` ile güncellenir. PC'ye dışarıdan deploy erişimi açılmaz.
- Yedek: her gece `pg_dump` + restic, şifreli olarak PC dışına (Backblaze B2). PC bozulursa başka bir ekip bilgisayarına geri kurulur (T-087).
- İzleme PC içinde: Prometheus + Grafana + Loki; uyarılar sadece panoda, dış izleyici ve bildirim yok (#32).

## Sonuçlar

**İyi:** Kira yok; bellek bütçesi rahat (Docker'a en fazla 20 GB, production ~15,5 GB); modem/IP bağımlılığı yok; saldırı yüzeyi tek giriş (tünel).

**Bedeli:**
- Sistem sadece PC açıkken erişilebilir; SLO'lar buna göre gevşetildi (`docs/go-live.md`). Kesinti, panoya veya siteye bakılana kadar fark edilmez (#32).
- PC'nin sunucu gibi davranması için ayarlar gerekir: uyku kapalı, kapak kapanınca bir şey yapma, Docker Desktop elle açılır, güncellemeler sunum haftası durdurulur (#31, `infra/pc/README.md`).
- Gece toplaması PC kapalıysa kaçar; açılışta telafi edilir (T-075).
- Geliştirme ve production aynı makinede: production açıkken geliştirme ortamının Ollama'sı kapatılır.
- Riskler: R-09, R-10, R-17, R-18 (`docs/riskler.md`).

## Ne zaman yeniden bakılır

- Canlıya çıkıştan sonra gerçek kullanıcı sayısı veya erişilebilirlik beklentisi artarsa (ör. TÜBİTAK dönemi, karar #22): VPS veya okul sunucusu. Compose dosyası taşınabilir; değişen sadece tünelin bağlandığı makine.
