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
- `.env.staging`: `APP_ENVIRONMENT=staging`; `COMPOSE_SUBNET=172.31.11.0/24`; production'dan **farklı** şifreler; `TUNNEL_TOKEN=`, `RESTIC_*` ve `COMPOSE_PROFILES=` boş.

`COMPOSE_SUBNET` projenin Docker ağıdır; api yalnızca bu ağdan (cloudflared) gelen `X-Forwarded-For` başlığına güvenir, istek sınırları istemcinin uydurduğu adresle aşılamaz. Değiştirirseniz ağın yeniden kurulması gerekir: `docker compose -p <proje> --env-file <dosya> -f infra/pc/compose.yml down` (`-v` olmadan), sonra deploy.

Postgres şifresi ilk açılışta veri tabanına yazılır; sonradan dosyada değiştirmek yetmez.

**Dosya izinleri:** iki dosyayı da sadece kendi Windows kullanıcınız okusun (varsayılan izinde PC'deki her kullanıcı okuyabilir). PowerShell'de, repo kökünde:

```powershell
icacls infra\pc\.env.prod /inheritance:r /grant:r "$($env:USERNAME):F" "SYSTEM:F" "Administrators:F"
icacls infra\pc\.env.staging /inheritance:r /grant:r "$($env:USERNAME):F" "SYSTEM:F" "Administrators:F"
```

Kontrol: `icacls infra\pc\.env.prod` çıktısında `BUILTIN\Users` satırı olmamalı.

### Veri tabanı rolleri (T-075)

| Rol | Kim kullanır | Yetki |
|---|---|---|
| `POSTGRES_USER` (`careerai`) | Migration (deploy.sh), yedek, elle bakım | Sahip (süper kullanıcı) |
| `careerai_app` | api, worker-data (`APP_DB_PASSWORD`) | Tablolarda okuma/yazma; tablo oluşturamaz, silemez, `TRUNCATE` yok; `audit_logs`'ta sadece ekleme/okuma; istatistik yenileme sadece `refresh_role_skill_stats()` ile |
| `careerai_monitor` | Grafana, postgres-exporter (`MONITOR_DB_PASSWORD`) | Salt okunur, sadece izleme sütunları |

Rolleri deploy.sh her deploy'da migration'dan sonra kurar ve yetkileri yeniler (`infra/pc/app-role.sql`, `setup_monitor_role`); yeni tablolar da otomatik yetki alır. Şifreyi değiştirmek için dosyadaki değeri değiştirip yeniden deploy etmek yeter.

## 3. Cloudflare Tunnel (T-010, bir kez)

Alan adı Cloudflare'e eklendikten (ad sunucuları Cloudflare'de) sonra:

1. Cloudflare paneli → **Zero Trust** → **Networks** → **Tunnels** → **Create a tunnel** → **Cloudflared** → ad: `careerai-pc`.
2. Kurulum ekranında **Docker** seçin; gösterilen komuttaki `--token` sonrasındaki uzun değeri `.env.prod` içindeki `TUNNEL_TOKEN=` satırına yazın. Komutu çalıştırmayın (cloudflared compose'da).
3. **Public Hostname** → **Add a public hostname**: Subdomain `api`, Domain `cvnebakalim.com`, Type `HTTP`, URL `api:8000`. Kaydedin.
4. Cloudflare paneli → alan adı → **SSL/TLS** → **Edge Certificates**: **Always Use HTTPS** açık, **Minimum TLS Version** 1.2, **HSTS** açık.

Grafana ve veri tabanı için public hostname **eklenmez**. Yönetim paneli api'nin içinde (`/admin`) olduğu için
tünelden erişilir; o yol ayrıca Cloudflare Access ile korunur (`backend/app/admin/README.md`, "Cloudflare Access").

## 4. Deploy

Sürüm etiketi `main`'deki bir commit'e basılır (imajı CI'da üretilmiş olmalı; son 20 birleştirme):

```bash
git fetch --tags origin
bash infra/pc/deploy.sh v1.0.0
```

Betik sırayla: imajları çeker → postgres/redis/ollama'yı başlatır → veri tabanı dökümü alır (`~/careerai-yedek`, son 5) → `alembic upgrade head` (sahip rolle) → uygulama ve izleme rollerini kurar → servisleri yeniler → `/health/ready` ile kontrol eder. Bir adım başarısız olursa önceki imajlara döner ve hata koduyla çıkar. Migration geri alınmaz; gerekirse döküm `pg_restore` ile yüklenir.

İlk kurulumda modeli bir kez indirin: `make prod-model` (~5 GB). Yedek deposunu bir kez oluşturun: `make backup-init` (`infra/backup/README.md`).

Durum ve loglar: `make prod-ps`, `make prod-logs`.

Yönetim paneline admin vermek (kişi önce uygulamadan kayıt olur): `make prod-admin EMAIL=ad@ornek.com`.

Yavaş sorgu raporu (go-live #18): `make prod-slow-queries`. Uygulama rolünün (`careerai_app`) en az 5 kez çalışmış sorgularını ortalama, yaklaşık p95 (ortalama + 1,645 × standart sapma) ve en yüksek süreyle listeler; hedef 50 ms üstü sorgu 0. Kaynak `pg_stat_statements`: `compose.yml`'de postgres'e yüklenir, eklentiyi `deploy.sh` (`setup_stats`) kurar. Sorgu metinleri normalleştirilmiştir (değerler `$1`), kişisel veri görünmez. Yeni ölçüm dönemi başlatmak (sayaçları sıfırlar): Git Bash'te `docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_stat_statements_reset()"'`.

**Kaçan gece toplaması (R-18):** PC 03:00'te kapalıysa veri işçisi açılışta son toplamanın zamanına bakar, kaçmışsa hemen başlatır (`scraper/collector/tasks.py`, `missed_nightly`). Logda `Gece toplaması kaçmış (…), şimdi başlatılıyor` görünür; elle bir şey yapmak gerekmez.

## 5. Prova ortamı

```bash
bash infra/pc/deploy.sh origin/main staging    # main'in son hâli
make staging-ps
make staging-down                              # iş bitince (veri kalır)
```

Go-live provası (T-091) ve aylık yedekten geri yükleme testi burada yapılır.

## 6. Sunum B planı

Alan adı açılmazsa sunum aynı PC'de, aynı veriyle yerelden sürer. Ağdaki başka cihazlar erişemez (her şey 127.0.0.1). Git Bash'te, repo kökünde:

```bash
make prod-local          # api ayrıca 127.0.0.1:8100'de; yerel web'in kökenine CORS izni (tünel çalışmaya devam eder)
make prod-local-web      # web arayüzü bu api'ye bağlı derlenir: http://127.0.0.1:5173 (Ctrl+C ile durur)
# sunum bittikten sonra:
make prod-local-down     # api normal ayarlarına döner, 8100 kapanır
```

Tarayıcıda `http://127.0.0.1:5173` → Durum sayfasında db/redis/ollama ✓ olmalı. Olay adımları: `docs/go-live.md` "Sunum sırasında dış erişim yok"; telefondan internet paylaşımıyla tünel de geri gelebilir (PC'yi telefonun ağına bağlayın, `cloudflared` kendiliğinden yeniden bağlanır).

**Prova (21.11.2026, T-091 / go-live #51):** `make prod-local` 11 sn, `make prod-local-web` 35 sn (ilk `npm ci` dahil) → yaklaşık 1 dk'da yerel arayüz hazır. Gerçek tarayıcıda yerel arayüz production verisini okudu (12 pozisyon, kaynaklar, Durum sayfası), konsol hatası yok; tünel bu sırada da 200 verdi. `make prod-local-down` 9 sn; sonra 8100 kapalı, CORS eski hâlinde. Eskiden `compose.local.yml` sadece portu açıyordu: production'da `CORS_ORIGINS=[]` olduğu için tarayıcıdaki arayüz api'yi çağıramazdı; yerel web için derleme komutu da yoktu. Telefondan internet paylaşımı ve analiz akışı (analiz işçisi production'da yok, T-057) bu provada denenmedi.

## 7. Vektörler (T-057 gelene kadar elle)

Eşleştirme `skills.embedding` ve `job_postings.embedding` sütunlarını kullanır (pgvector, karar #35). AI işçisi production'a girene kadar bunları üreten servis yok; gece toplamasının eklediği yeni ilanların vektörü boş kalır. Gece toplamasından sonra (veya Grafana'da yeni ilan görünce) Git Bash'te, repo kökünde:

```bash
make prod-embed            # önce yedek alır, sadece vektörü boş satırlar
make prod-embed HEPSI=1    # model değiştiyse hepsi baştan
```

Betik `infra/pc/embed.sh`: yedek (`backup.sh`) → geçici imajı derler (`infra/pc/embedding/Dockerfile`, ~3,3 GB, model içinde; ilk seferde ~5 dk, sonra önbellekten) → `python -m embedding` → kalan boş vektör sayısını yazar (pasif ilanlar vektör almaz, sayılmaz). İmaj PC'de kalır; kaldırmak: `docker rmi careerai/embedding-gecici:local`. Her parti ayrı kaydedilir (yarıda kesilirse kaldığı yerden sürer). Uygulama rolüyle (`careerai_app`) bağlanır; parola komut satırında görünmez. İlk çalışma 20.11.2026: 374 yetkinlik 3 sn, 2.213 ilan 4 dk (CPU). T-057 (Burak) analiz işçisini production'a alınca bu adım ve imaj kaldırılır.

## 8. Ollama GPU (GTX 1650)

`compose.yml`'de `ollama` servisi `gpus: all` ile açılır. Şartlar: Windows'ta NVIDIA sürücüsü **550 veya üstü** (Ollama 0.40 CUDA 13 ister) ve Docker Desktop WSL2 altyapısı. Sürücü güncellendikten sonra PC yeniden başlatılmadıysa WSL eski sürücü dosyalarını tutar ve GPU'lu konteyner açılırken çöker (`nvidia-container-runtime-hook … SIGSEGV`): Docker Desktop'ı kapatıp PowerShell'de `wsl --shutdown`, sonra Docker Desktop'ı açın.

Kontrol: `docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml exec ollama ollama ps` → `PROCESSOR` sütununda GPU payı görünmeli. Loglarda `msg="inference compute" … library=CUDA` olmalı; `NVIDIA driver too old` görünüyorsa sürücü eski, Ollama CPU'da çalışıyordur.

Ölçüm (24.11.2026, `llama3.1:8b`, ~750 token prompt, sürücü 621.24): model 4 GB'a sığmadığı için katmanların bir kısmı GPU'da (13/33).

| | Sadece CPU | GPU ile |
|---|---|---|
| Prompt işleme | 14,8 token/sn (~50 sn) | 82 token/sn (~9 sn) |
| Üretim | 3,1 token/sn | 4,8 token/sn |

## Henüz eksik

- `worker-ai` / analiz işçisi ve CV Redis'i: `ai/Dockerfile` (Burak) ve #58/#60 main'e girince eklenecek; o zamana kadar analizler çalışmaz.
- Web arayüzü (`app.cvnebakalim.com`): Cloudflare Pages'te mi tünelde mi yayınlanacağı Anıl'la kararlaştırılacak.
