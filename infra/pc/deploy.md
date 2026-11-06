# Production ve prova ortamı: kurulum ve deploy (T-035, T-036, T-075)

Karar #30: production Ataberk'in PC'sinde Docker Compose ile çalışır, dışarıya Cloudflare Tunnel ile açılır. PC hazırlığı (uyku, BitLocker, Docker Desktop): [`README.md`](README.md).

| Ortam | Compose projesi | Ayar dosyası (repoda yok) | Dış erişim |
|---|---|---|---|
| Production | `careerai-prod` | `infra/pc/.env.prod` | Cloudflare Tunnel (`api.cvnebakalim.com`) |
| Prova (staging) | `careerai-staging` | `infra/pc/.env.staging` | Yok (gerekirse geçici tünel) |
| Geliştirme | `careerai` | `.env` (kök) | Yok, 127.0.0.1 |

Üçü aynı PC'de ayrı volume'larla çalışır; sadece Ollama model dosyaları ortak (`careerai-ollama-models`). Hiçbir production servisi host'a port açmaz.

Komutlar **Git Bash**'te, repo kökünde çalıştırılır.

## 1. GHCR girişi (bir kez)

İmajları CI üretir (`.github/workflows/deploy.yml`); PC onları GitHub Container Registry'den çeker. Repo özel olduğu için giriş gerekir:

1. GitHub → sağ üst profil → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**.
2. Not: `careerai-pc-ghcr`; süre: 90 gün; yetki: sadece **read:packages**. **Generate token**.
3. Git Bash: `docker login ghcr.io -u AtaberkCakir2`. Şifre sorulunca token'ı yapıştırın. Token'ı başka bir yere kaydetmeyin.

## 2. Ayar dosyaları (bir kez)

```bash
cp infra/pc/.env.example infra/pc/.env.prod
cp infra/pc/.env.example infra/pc/.env.staging
```

- `.env.prod`: `APP_ENVIRONMENT=production`; şifreler için her satıra ayrı `openssl rand -hex 32` çıktısı; `TUNNEL_TOKEN` 3. adımdan; yedek ayarları (`RESTIC_*`, `B2_*`) `infra/backup/README.md`'den.
- `.env.staging`: `APP_ENVIRONMENT=staging`; production'dan **farklı** şifreler; `TUNNEL_TOKEN=`, `RESTIC_*` ve `COMPOSE_PROFILES=` boş.

Postgres şifresi ilk açılışta veri tabanına yazılır; sonradan dosyada değiştirmek yetmez.

## 3. Cloudflare Tunnel (T-010, bir kez)

Alan adı Cloudflare'e eklendikten (ad sunucuları Cloudflare'de) sonra:

1. Cloudflare paneli → **Zero Trust** → **Networks** → **Tunnels** → **Create a tunnel** → **Cloudflared** → ad: `careerai-pc`.
2. Kurulum ekranında **Docker** seçin; gösterilen komuttaki `--token` sonrasındaki uzun değeri `.env.prod` içindeki `TUNNEL_TOKEN=` satırına yazın. Komutu çalıştırmayın (cloudflared compose'da).
3. **Public Hostname** → **Add a public hostname**: Subdomain `api`, Domain `cvnebakalim.com`, Type `HTTP`, URL `api:8000`. Kaydedin.
4. Cloudflare paneli → alan adı → **SSL/TLS** → **Edge Certificates**: **Always Use HTTPS** açık, **Minimum TLS Version** 1.2, **HSTS** açık.

Admin paneli, Grafana ve veri tabanı için public hostname **eklenmez**.

## 4. Deploy

Sürüm etiketi `main`'deki bir commit'e basılır (imajı CI'da üretilmiş olmalı; son 20 birleştirme):

```bash
git fetch --tags origin
bash infra/pc/deploy.sh v1.0.0
```

Betik sırayla: imajları çeker → postgres/redis/ollama'yı başlatır → veri tabanı dökümü alır (`~/careerai-yedek`, son 5) → `alembic upgrade head` → servisleri yeniler → `/health/ready` ile kontrol eder. Bir adım başarısız olursa önceki imajlara döner ve hata koduyla çıkar. Migration geri alınmaz; gerekirse döküm `pg_restore` ile yüklenir.

İlk kurulumda modeli bir kez indirin: `make prod-model` (~5 GB). Yedek deposunu bir kez oluşturun: `make backup-init` (`infra/backup/README.md`).

Durum ve loglar: `make prod-ps`, `make prod-logs`.

## 5. Prova ortamı

```bash
bash infra/pc/deploy.sh origin/main staging    # main'in son hâli
make staging-ps
make staging-down                              # iş bitince (veri kalır)
```

Go-live provası (T-091) ve aylık yedekten geri yükleme testi burada yapılır.

## 6. Sunum B planı

Alan adı açılmazsa api'yi sadece bu PC'ye açın: `make prod-local` → `http://127.0.0.1:8100`. Ağdaki başka cihazlar erişemez. Olay adımları: `docs/go-live.md`.

## Henüz eksik

- `worker-ai` / analiz işçisi ve CV Redis'i: `ai/Dockerfile` (Burak) ve #58/#60 main'e girince eklenecek; o zamana kadar analizler çalışmaz.
- Web arayüzü (`app.cvnebakalim.com`): Cloudflare Pages'te mi tünelde mi yayınlanacağı Anıl'la kararlaştırılacak.
- Güvenlik başlıkları (nosniff, X-Frame-Options): eskiden Caddy veriyordu; şimdi api'de (Anıl) veya Cloudflare **Rules → Transform Rules** ile eklenmeli (go-live #12).
- Dış uptime izleme ve yedek uyarısı (T-066).
