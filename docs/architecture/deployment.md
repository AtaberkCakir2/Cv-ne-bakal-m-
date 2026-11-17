# Deployment: production (PC + Cloudflare Tunnel)

Karar #30 ve [ADR-0004](adr/0004-barindirma-pc-cloudflare-tunnel.md). Production, Ataberk'in bilgisayarında `careerai-prod` adlı Docker Compose projesidir (`infra/pc/compose.yml`). Dışarıdan tek giriş Cloudflare Tunnel; hiçbir servis host'a port açmaz (Grafana yalnızca `127.0.0.1`).

```mermaid
flowchart LR
    user(["Kullanıcı<br/>tarayıcı · Electron · Android"])
    admin(["Ataberk<br/>PC başında"])

    subgraph cf["Cloudflare (ücretsiz plan)"]
        edge["api.cvnebakalim.com<br/>DNS · TLS · HSTS · güvenlik başlıkları"]
        pages["Cloudflare Pages<br/>tanıtım · aydınlatma · gizlilik"]
    end

    subgraph pc["Production PC · Windows 10 Pro · Docker Desktop (WSL2, ≤ 20 GB)"]
        subgraph prod["careerai-prod · iç ağ (COMPOSE_SUBNET) · host'a port yok"]
            cfd["cloudflared<br/>128 MB<br/>sadece dışarı bağlanır"]
            api["api<br/>FastAPI · :8000 · 1 GB"]
            wai["worker-ai<br/>Celery · analysis · eşzamanlılık 1<br/>2 GB"]
            wdata["worker-data<br/>Celery beat · data · 03:00<br/>1,5 GB"]
            ollama["ollama<br/>Llama 3.1 8B · :11434 · 8 GB"]
            pg[("postgres 16 + pgvector<br/>:5432 · 2 GB")]
            redis[("redis<br/>kuyruk · AOF · 256 MB")]
            cvredis[("cv-redis<br/>CV baytları · tmpfs · 256 MB")]
            backup["backup<br/>pg_dump + restic · 512 MB"]
            subgraph mon["monitoring profili"]
                prom["prometheus<br/>+ exporter'lar"]
                loki["loki + alloy<br/>loglar · 14 gün"]
                graf["grafana<br/>127.0.0.1:3000"]
            end
        end
    end

    b2[("Backblaze B2<br/>şifreli yedek")]
    ghcr[("GHCR<br/>CI imajları")]
    sources["İlan kaynakları<br/>resmi API · açık veri · YouTube API"]

    user -->|HTTPS| edge
    user -->|HTTPS| pages
    edge ==>|tünel, PC dışarı bağlanır| cfd
    cfd --> api
    api --> pg
    api --> redis
    api --> cvredis
    redis --> wai
    cvredis --> wai
    wai --> ollama
    wai --> pg
    wdata --> pg
    wdata --> redis
    wdata -->|gece| sources
    backup --> pg
    backup -->|S3 API · her gece| b2
    prom -.-> api & pg & redis
    prom -.->|dış prob| edge
    loki -.-> api & wdata & pg
    graf --> prom & loki
    admin -->|127.0.0.1| graf
    admin -->|deploy.sh vX.Y.Z| ghcr
```

`worker-ai` ve `cv-redis`, Burak'ın `ai/Dockerfile`'ı ve analiz işçisi `main`'e girince compose'a eklenir (`infra/pc/deploy.md`, "Henüz eksik"); diyagram hedef durumu gösterir.

## Ağ sınırları

| Sınır | Kural | Nerede |
|---|---|---|
| İnternet → PC | Gelen port yok. `cloudflared` Cloudflare'e dışarıya bağlanır; istek tünelden `api:8000`'e gelir. Ev IP'si görünmez. | `infra/pc/compose.yml`, `infra/pc/deploy.md` 3. bölüm |
| Tünel → api | Sadece `api.cvnebakalim.com` yayınlanır. Grafana, veritabanı ve Ollama için public hostname eklenmez. Yönetim paneli (`/admin`) Cloudflare Access ile ayrıca korunur. | Cloudflare Zero Trust paneli |
| İstemci IP'si | api `X-Forwarded-For`'a yalnızca projenin alt ağından (`FORWARDED_ALLOW_IPS=COMPOSE_SUBNET`) güvenir; istek sınırları sahte başlıkla aşılamaz. | `infra/pc/compose.yml` (api) |
| PC → dışarı | Yedek (B2), ilan kaynakları, imaj çekme (GHCR) ve Cloudflare. Başka çıkış yok. | — |
| Host → konteyner | Sadece Grafana `127.0.0.1:3000`. Sunum B planında api geçici olarak `127.0.0.1:8100` (`make prod-local`). | `compose.local.yml` |
| Veritabanı rolleri | Uygulama en az yetkili `careerai_app` rolüyle bağlanır; migration sahip rolle; izleme salt okunur `careerai_monitor` (sadece izleme sütunları). | `infra/pc/app-role.sql`, `deploy.sh` (T-075) |

## Deploy akışı

```mermaid
flowchart LR
    pr["PR → main<br/>CI yeşil + 1 onay"] --> ci["GitHub Actions<br/>imaj build"]
    ci --> ghcr[("GHCR<br/>careerai-api:sha<br/>careerai-worker-data:sha")]
    tag["vX.Y.Z etiketi"] --> deploy
    ghcr --> deploy["PC'de elle:<br/>bash infra/pc/deploy.sh vX.Y.Z"]
    deploy --> s1["imajları çek"] --> s2["postgres/redis/ollama"] --> s3["DB dökümü<br/>~/careerai-yedek"] --> s4["alembic upgrade"] --> s5["DB rolleri"] --> s6["servisleri yenile"] --> s7{"/health/ready"}
    s7 -->|başarısız| rb["önceki imajlara dön"]
```

PC'ye dışarıdan deploy erişimi yoktur; CI sadece imaj üretir. Prova için aynı betik `staging` ortamıyla çalışır (`careerai-staging`, ayrı volume'lar).

## Yedek ve geri dönüş

| Ne | Nasıl | Hedef |
|---|---|---|
| Gece yedeği | `backup` konteyneri: `pg_dump` → restic → B2 (şifreli, artımlı) | RPO < 24 saat |
| Deploy öncesi döküm | `deploy.sh` → `~/careerai-yedek/deploy-*.dump` (son 5) | Hatalı migration'dan dönüş |
| Geri yükleme testi | `bash infra/backup/restore-test.sh` (geçici konteynerde) | Aylık |
| Felaket kurtarma | Başka bir ekip bilgisayarında yedekten kurulum + tüneli taşıma (T-087) | RTO < 4 saat |

CV dosyası ve ham CV metni hiçbir yedekte yoktur (karar #9); yedek sadece veritabanıdır.

## Bellek bütçesi

| Servis | Sınır |
|---|---|
| ollama | 8 GB |
| worker-ai | 2 GB |
| postgres | 2 GB |
| worker-data | 1,5 GB |
| api | 1 GB |
| izleme (prometheus, grafana, loki, alloy, exporter'lar) | ~1,8 GB sınır (ölçülen çok daha az) |
| backup | 512 MB |
| redis, cv-redis | 256 MB + 256 MB |
| cloudflared | 128 MB |

Docker Desktop'a (WSL2) en fazla 20 GB verilir; production açıkken geliştirme ortamının Ollama'sı kapatılır. RAM %85'i aşınca Grafana panosunda uyarı görünür (R-09).
