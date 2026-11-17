# İzleme (T-066)

Production PC'sinde Prometheus + Grafana: CPU, RAM, disk, kuyruklar, analiz süresi ve hataları, gece toplaması ve sitenin alan adından (tünel) erişilebilirliği tek panoda. Eşik aşılınca uyarı panonun en üstünde görünür, kimseye gönderilmez.

PC dışı uptime izleyici, status sayfası ve Sentry **kullanılmaz** (karar #32). Bedeli: PC tamamen kapanırsa (elektrik, internet, güncelleme) pano da kapanır ve otomatik uyarı gelmez; kesinti siteye girmeye çalışan biri fark edince anlaşılır. Sunum ve hypercare döneminde nöbetçi günde bir kez panoya ve siteye bakar.

## PC'deki servisler

`infra/pc/compose.yml` içinde `monitoring` profiliyle açılır, sadece production'da (`COMPOSE_PROFILES=tunnel,backup,monitoring`).

| Servis | Ne yapar | Dışa açık mı |
|---|---|---|
| prometheus | Metrikleri 30 sn'de bir toplar, 30 gün / 2 GB saklar, `prometheus/alerts.yml` kurallarını değerlendirir | Hayır |
| grafana | Pano: http://127.0.0.1:3000 (kullanıcı `admin`) | Sadece bu PC (127.0.0.1) |
| node-exporter | Docker'ın WSL2 makinesi: CPU, RAM (`.wslconfig` sınırı, 20 GB); Windows C: boş alanı | Hayır |
| redis-exporter | Celery kuyruk uzunlukları (`analysis`, `data`), Redis belleği | Hayır |
| postgres-exporter | Bağlantılar, analiz hata oranı ve süresi, son başarılı toplama (`postgres-exporter/queries.yaml`) | Hayır |
| blackbox-exporter | `/api/v1/health/ready`: içeriden (`api:8000`) ve dışarıdan (`api.cvnebakalim.com`, tünel) | Hayır |

Toplam bellek sınırı ~1 GB; 12.11.2026 denemesinde toplam ~170 MB kullandı. Grafana'ya tünelden public hostname **eklenmez** (`infra/pc/deploy.md`).

Grafana ve postgres-exporter veri tabanına `careerai_monitor` rolüyle bağlanır. Rol salt okunurdur ve sadece şu sütunları görür: `analyses(status, duration_ms, created_at, completed_at)`, `scrape_runs` sayaçları, `job_sources(id, name)`. Kullanıcı, CV hash'i ve yetkinlik verisi okunamaz (karar #5). Rolü `deploy.sh` her deploy'da oluşturur veya şifresini günceller.

### Uyarılar

Tetiklenen uyarılar panonun en üstündeki **Aktif uyarılar** tablosunda görünür; bildirim (Telegram, e-posta) gönderilmez (karar #32). Panoya göz atmak yeterli; sunum ve hypercare döneminde nöbetçi günde bir kez bakar.

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

## Günlük kullanım

| Ne | Nasıl |
|---|---|
| Panoyu aç | http://127.0.0.1:3000 → Cv'ne Bakalım! panosu (giriş sayfası) |
| Aktif uyarılar | Panonun en üstündeki tablo |
| Kural/ayar değişikliğini uygula | `make prod-monitoring-reload` |
| Kuralları kontrol et | `make monitoring-check` (promtool; CI'a gerek yok) |

## Bilinen sınırlar

- CPU ve RAM, Windows'un tamamını değil Docker Desktop'ın WSL2 makinesini gösterir (`.wslconfig` ile 20 GB). Bellek bütçesi de bu sınıra göre (docs/mimari.md).
- C: diski Docker Desktop'ın `/run/desktop/mnt/host/c` bağlama noktasından okunur; Docker Desktop dışında (ör. Linux sunucuya taşınırsa) bu satır kaldırılır, kök dosya sistemi kullanılır.
- Analiz süresi `analyses.duration_ms` sütunundan okunur; worker'a ayrıca metrik eklenmedi. API istek süresi (SLO p95 < 300 ms) API'nin istek loglarındaki `duration_ms`'ten okunur (T-067); `/health/ready` süresi sadece kaba bir göstergedir.
- Yedeğin başarılı olup olmadığı henüz burada izlenmiyor; T-068 tamamlanınca eklenecek.
