# İzleme ve uyarılar (T-066)

Üç katman var. Her biri farklı bir soruyu cevaplar:

| Katman | Nerede | Ne söyler | Kim kurar |
|---|---|---|---|
| Dış uptime izleyici (UptimeRobot) | PC dışı (bulut) | Site dışarıdan açılıyor mu? PC kapansa da çalışır, status sayfası buradan | Ataberk (hesap) |
| Prometheus + Grafana + Alertmanager | Production PC'si, `careerai-prod` projesi | CPU, RAM, disk, kuyruk, analiz süresi, toplama; eşik aşılınca Telegram | Bu klasör |
| Sentry | Bulut (ücretsiz katman) | Uygulama hataları (backend, web, mobil) | Hesap: Ataberk · kod: Anıl (backend, web), Burak (mobil) |

PC içindeki izleme, PC kapanınca kendisi de kapanır; "site çöktü" uyarısını bu yüzden dış izleyici verir (karar #30).

## PC'deki servisler

`infra/pc/compose.yml` içinde `monitoring` profiliyle açılır, sadece production'da (`COMPOSE_PROFILES=tunnel,backup,monitoring`).

| Servis | Ne yapar | Dışa açık mı |
|---|---|---|
| prometheus | Metrikleri 30 sn'de bir toplar, 30 gün / 2 GB saklar, `prometheus/alerts.yml` kurallarını değerlendirir | Hayır |
| alertmanager | Uyarıları gruplar, Telegram'a gönderir (4 saatte bir hatırlatır, düzelince "resolved" yazar) | Hayır |
| grafana | Pano: http://127.0.0.1:3000 (kullanıcı `admin`) | Sadece bu PC (127.0.0.1) |
| node-exporter | Docker'ın WSL2 makinesi: CPU, RAM (`.wslconfig` sınırı, 20 GB); Windows C: boş alanı | Hayır |
| redis-exporter | Celery kuyruk uzunlukları (`analysis`, `data`), Redis belleği | Hayır |
| postgres-exporter | Bağlantılar, analiz hata oranı ve süresi, son başarılı toplama (`postgres-exporter/queries.yaml`) | Hayır |
| blackbox-exporter | `/api/v1/health/ready`: içeriden (`api:8000`) ve dışarıdan (`api.cvnebakalim.com`, tünel) | Hayır |

Toplam bellek sınırı ~1,1 GB; 12.11.2026 denemesinde toplam ~180 MB kullandı. Grafana'ya tünelden public hostname **eklenmez** (`infra/pc/deploy.md`).

Grafana ve postgres-exporter veri tabanına `careerai_monitor` rolüyle bağlanır. Rol salt okunurdur ve sadece şu sütunları görür: `analyses(status, duration_ms, created_at, completed_at)`, `scrape_runs` sayaçları, `job_sources(id, name)`. Kullanıcı, CV hash'i ve yetkinlik verisi okunamaz (karar #5). Rolü `deploy.sh` her deploy'da oluşturur veya şifresini günceller.

### Uyarılar

| Uyarı | Koşul | Önem |
|---|---|---|
| ApiHazirDegil | `/health/ready` içeriden 2 dk başarısız | kritik |
| DisErisimYok | api içeride ayakta ama alan adından 5 dk erişilemiyor (tünel / internet) | kritik |
| PostgresKapali | 2 dk bağlantı yok | kritik |
| DiskAz | C: boş alan < %10, 10 dk | kritik |
| RamYuksek | Docker RAM'i > %85, 10 dk (docs/mimari.md bellek bütçesi) | uyarı |
| CpuYuksek | > %90, 15 dk | uyarı |
| ApiYavas | `/health/ready` ortalaması > 1 sn, 10 dk | uyarı |
| AnalizKuyruguBirikti | analiz kuyruğunda ≥ 6 iş, 10 dk (sınır 8) | uyarı |
| VeriKuyruguBirikti | toplama kuyruğunda > 50 iş, 30 dk | uyarı |
| AnalizHatalari | son 1 saatte ≥ 3 hata ve hata oranı > %20 | uyarı |
| ToplamaGecikti | 30 saattir başarılı ilan toplaması yok | uyarı |
| IzlemeHedefiKapali | bir exporter 5 dk okunamıyor | uyarı |

Eşik değiştirmek için `prometheus/alerts.yml` düzenlenir, sonra `make prod-monitoring-reload`.

## Kurulum (bir kez)

### 1. Şifreler

`infra/pc/.env.prod` içinde (Git Bash'te `openssl rand -hex 32` ile üretin):

```
GRAFANA_ADMIN_PASSWORD=<rastgele>
MONITOR_DB_PASSWORD=<rastgele, sadece harf/rakam>
COMPOSE_PROFILES=tunnel,backup,monitoring
```

Sonra normal deploy: `bash infra/pc/deploy.sh <sürüm> production`. Deploy rolü oluşturur ve izleme servislerini açar.

### 2. Telegram uyarıları

1. Telegram'da **@BotFather**'a yazın → `/newbot` → isim: `CareerAI Uyarı`, kullanıcı adı: `cvnebakalim_uyari_bot` (alınmışsa başka bir `_bot` ile biten ad).
2. BotFather'ın verdiği token'ı `.env.prod` içine `TELEGRAM_BOT_TOKEN=` satırına yapıştırın. Token'ı sohbete, terminale veya repoya yazmayın.
3. Ekip için bir Telegram grubu açın (ör. `CareerAI Nöbet`), Burak ve Anıl'ı ve botu gruba ekleyin. Grupta bir mesaj yazın (ör. `/start`).
4. Tarayıcıda şu adresi açın (TOKEN yerine token'ı yazın): `https://api.telegram.org/botTOKEN/getUpdates`. Çıkan metinde `"chat":{"id":-100...` gibi eksiyle başlayan sayıyı bulun.
5. Bu sayıyı `.env.prod` içine `TELEGRAM_CHAT_ID=` satırına yazın.
6. `make prod-monitoring-reload` → `make prod-test-alert`. Gruba bir dakika içinde "TestUyarisi" mesajı gelmeli.

### 3. Dış uptime izleyici ve status sayfası (UptimeRobot, ücretsiz)

1. https://uptimerobot.com → **Register for FREE** ile hesap açın (ekibin ortak e-postası varsa onunla).
2. **+ New monitor** → Monitor type: **HTTP(s)**.
   - Friendly name: `CareerAI API`
   - URL: `https://api.cvnebakalim.com/api/v1/health/ready`
   - Monitoring interval: **5 minutes** (ücretsiz katmandaki en kısa süre)
3. **Integrations & Team** (veya Alert contacts) → ekip üyelerinin e-postalarını ekleyin; Telegram entegrasyonu sunuluyorsa 2. adımdaki grubu da bağlayın. Monitörde bu kişileri işaretleyin → **Create monitor**.
4. Web arayüzü yayına çıkınca aynı şekilde `https://app.cvnebakalim.com` için ikinci monitör.
5. **Status pages** → **+ New status page** → ad: `CareerAI Durum`, monitörleri seçin → oluşturun. Linki `docs/go-live.md` iletişim planına ekleyin.
6. Bildirimi deneme: go-live provasında (T-091) tüneli 6 dakika durdurun (`docker compose -p careerai-prod stop cloudflared`). E-posta geldikten sonra `docker compose -p careerai-prod start cloudflared`. Aynı sırada Telegram'a da `DisErisimYok` uyarısı gelmeli.

### 4. Sentry

1. https://sentry.io → ücretsiz hesap → organizasyon `cvnebakalim`.
2. Üç proje açın: `api` (Python / FastAPI), `web` (React), `mobile` (React Native).
3. DSN'leri ekibe parola yöneticisinden iletin. Entegrasyon kodu modül sahiplerinde: backend ve web Anıl, mobil Burak (go-live #22). DSN repoya yazılmaz; production'da `.env.prod` üzerinden verilir.
4. Gönderilen olaylarda kişisel veri olmamalı (`send_default_pii=False`, CV metni ve dosya adı loglanmaz; T-067).

## Günlük kullanım

| Ne | Nasıl |
|---|---|
| Panoyu aç | http://127.0.0.1:3000 → CareerAI panosu (giriş sayfası) |
| Aktif uyarılar | `make prod-alerts` |
| Kural/ayar değişikliğini uygula | `make prod-monitoring-reload` |
| Telegram'ı dene | `make prod-test-alert` |
| Kuralları kontrol et | `make monitoring-check` (promtool; CI'a gerek yok) |

## Bilinen sınırlar

- CPU ve RAM, Windows'un tamamını değil Docker Desktop'ın WSL2 makinesini gösterir (`.wslconfig` ile 20 GB). Bellek bütçesi de bu sınıra göre (docs/mimari.md).
- C: diski Docker Desktop'ın `/run/desktop/mnt/host/c` bağlama noktasından okunur; Docker Desktop dışında (ör. Linux sunucuya taşınırsa) bu satır kaldırılır, kök dosya sistemi kullanılır.
- Analiz süresi `analyses.duration_ms` sütunundan okunur; worker'a ayrıca metrik eklenmedi. API istek süresi (SLO p95 < 300 ms) Sentry Performance'tan izlenir; `/health/ready` süresi sadece kaba bir göstergedir.
- Yedeğin başarılı olup olmadığı henüz burada izlenmiyor; T-068 tamamlanınca eklenecek.
