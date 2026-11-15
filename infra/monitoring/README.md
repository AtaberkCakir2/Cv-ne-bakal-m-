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
| loki | Merkezi log deposu: tüm production konteynerlerinin logları, **14 gün** saklanır (`loki/loki.yml`) | Hayır |
| alloy | Konteyner loglarını Docker'dan okur, e-posta / telefon / TC kimlik no'yu maskeler, Loki'ye yazar (`alloy/config.alloy`) | Hayır |

Toplam bellek sınırı ~1,8 GB (Loki + Alloy dahil); 12.11.2026 denemesinde toplam ~170 MB kullandı. Grafana'ya tünelden public hostname **eklenmez** (`infra/pc/deploy.md`).

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

## Loglar (T-067)

Grafana → sol menü **Explore** → üstte veri kaynağı **Loglar**. Örnek sorgular (**Code** sekmesine yapıştırın):

| Ne | Sorgu |
|---|---|
| Bir servisin logları | `{service="api"}` (diğerleri: `worker-data`, `postgres`, `redis`, `cloudflared`, `backup`…) |
| Tüm hatalar | `{level="ERROR"}` |
| Bir isteğin izi (hata bildirimindeki istek kimliği) | `{service="api"} \|= "<X-Request-ID>"` |
| 5xx oranı, son 1 saat (SLO < %1; sonuç boşsa hiç 5xx yok) | `sum(count_over_time({service="api"} \| json \| status >= 500 [1h])) / sum(count_over_time({service="api"} \| json \| message="istek" [1h]))` |
| API p95 süresi, son 1 saat (SLO < 300 ms) | `quantile_over_time(0.95, {service="api"} \| json \| message="istek" \| path !~ "/api/v1/(analyses\|health).*" \| unwrap duration_ms [1h]) by (service)` |

Nasıl çalışıyor:

- **Format:** API ve veri işçisi JSON yazar (`time`, `level`, `logger`, `message`, API'de `request_id` ve istek alanları). Ortak biçimlendirici `backend/app/core/logging.py`; veri işçisi Celery'nin kendi logunu kapatıp bunu kullanır (`scraper/collector/tasks.py`).
- **Maskeleme, iki katman:** (1) uygulama yazarken `mask_pii` (e-posta → `[E-POSTA]`, telefon → `[TELEFON]`, TC kimlik no → `[TCKN]`); (2) Alloy aynı desenlerle bütün konteynerlerin satırlarını Loki'ye yazmadan önce tekrar maskeler (Postgres, Redis, cloudflared gibi bizim yazmadığımız servisler için). Postgres ayrıca hata satırına değer yazmaz (`log_error_verbosity=terse`, `log_min_error_statement=panic`, `infra/pc/compose.yml`).
- **Saklama ve rotasyon:** Loki 14 gün tutar, compactor eskileri siler. Docker'ın kendi log dosyaları da döner: konteyner başına 3 × 10 MB (`x-logging`, json-file). Bu yerel dosyalar Alloy'dan önceki ham hâldir; uygulamalar zaten maskeli yazdığı için kişisel veri içermemeli, en geç birkaç gün içinde üzerine yazılır.
- **Erişim:** Loki ve Alloy'un portu yok; loglar sadece Grafana'dan (127.0.0.1) okunur. Alloy, konteyner loglarını okumak için Docker soketine salt okunur bağlanır.

Doğrulama (15.11.2026): Postgres'e sahte e-posta ve telefon içeren bir benzersizlik hatası yaptırıldı; Loki'de `[E-POSTA]`, `[TELEFON]`, `[TCKN]` olarak göründü, `terse` sonrası ham Docker logunda değer satırı kalmadı. API istek logları `service` ve `level` etiketleriyle, `request_id` ile geldi.

## Bilinen sınırlar

- CPU ve RAM, Windows'un tamamını değil Docker Desktop'ın WSL2 makinesini gösterir (`.wslconfig` ile 20 GB). Bellek bütçesi de bu sınıra göre (docs/mimari.md).
- C: diski Docker Desktop'ın `/run/desktop/mnt/host/c` bağlama noktasından okunur; Docker Desktop dışında (ör. Linux sunucuya taşınırsa) bu satır kaldırılır, kök dosya sistemi kullanılır.
- Analiz süresi `analyses.duration_ms` sütunundan okunur; worker'a ayrıca metrik eklenmedi. API istek süresi (SLO p95 < 300 ms) ve 5xx oranı Loki'deki istek loglarından okunur (yukarıdaki "Loglar" sorguları); `/health/ready` süresi sadece kaba bir göstergedir.
- Yedeğin başarılı olup olmadığı henüz burada izlenmiyor; T-068 tamamlanınca eklenecek.
