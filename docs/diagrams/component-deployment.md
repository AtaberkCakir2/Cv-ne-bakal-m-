# Component ve Deployment diyagramları

## Component: bileşenler ve sorumluları

Her kutu bir modül; parantez içinde repodaki klasörü ve sahibi var. Oklar veri akışının yönünü gösterir.

```mermaid
flowchart TB
    subgraph istemci["İstemciler"]
        web["Web arayüzü<br/>React + Vite<br/>(web/ · Anıl)"]
        desk["Masaüstü<br/>Electron<br/>(web/ · Anıl)"]
        mob["Mobil<br/>React Native · Expo<br/>(mobile/ · Burak)"]
    end

    subgraph api["Backend (backend/ · Anıl)"]
        auth["Kimlik doğrulama<br/>JWT + argon2"]
        routes["Analiz · katalog · KVKK<br/>endpoint'leri"]
        sse["İlerleme (SSE)"]
    end

    subgraph ai["AI worker (ai/ · Burak)"]
        parse["PDF / OCR<br/>pdfplumber · PyMuPDF · Tesseract"]
        pii["Kişisel veri maskeleme"]
        extract["Yetkinlik çıkarımı<br/>sözlük + LLM"]
        match["Eşleştirme<br/>TF-IDF + embedding"]
        rec["Kaynak önerisi (RAG)"]
    end

    subgraph data["Veri toplama (scraper/ · Ataberk)"]
        collect["İlan toplama<br/>API · açık veri · Playwright"]
        etl["Temizleme + yetkinlik etiketleme"]
        stats["Talep istatistikleri"]
    end

    queue[("Redis<br/>kuyruk")]
    db[("PostgreSQL 16<br/>+ pgvector<br/>(backend/app/db · Ataberk)")]
    llm["Ollama<br/>yerel LLM"]
    emb["sentence-transformers<br/>embedding (384)"]

    web & desk & mob -->|HTTPS · REST| api
    routes -->|iş| queue
    queue --> parse
    parse --> pii --> extract --> match --> rec
    extract & rec -->|maskelenmiş metin| llm
    match --> emb
    api <--> db
    ai <--> db
    collect --> etl --> stats --> db
    etl --> emb
```

**Sınırlar:** İstemciler sadece API ile konuşur. AI worker'a kuyruk üzerinden iş gelir, sonucu veritabanına yazar. Modüller arası veri formatları `contracts/` altındadır (`job_posting` Ataberk → Burak, `analysis_result` Burak → Anıl).

## Deployment: production sunucusu

Tek Linux VPS (8 vCPU / 16 GB RAM), Docker Compose (karar #13). Sadece Caddy dışarıya açıktır.

```mermaid
flowchart LR
    user(["Kullanıcı<br/>tarayıcı · Electron · Android"])

    subgraph vps["Linux VPS · Ubuntu 24.04 · 8 vCPU / 16 GB RAM"]
        subgraph compose["Docker Compose · iç ağ"]
            caddy["caddy<br/>:80 / :443<br/>256 MB"]
            apic["api<br/>FastAPI + Gunicorn ×4<br/>:8000 · 1 GB"]
            wai["worker-ai<br/>Celery · eşzamanlılık 1<br/>2 GB"]
            wdata["worker-data<br/>Celery beat + Playwright<br/>1,5 GB"]
            ollama["ollama<br/>:11434 · 8 GB"]
            pg[("postgres<br/>pgvector · :5432 · 2 GB")]
            redis[("redis<br/>:6379 · 256 MB")]
            mon["uptime-kuma · grafana<br/>512 MB"]
        end
    end

    backup[("Sunucu dışı yedek<br/>restic · şifreli")]
    sites["İlan kaynakları<br/>API · açık veri"]

    user -->|HTTPS| caddy
    caddy --> apic
    caddy -.->|status sayfası| mon
    apic --> pg
    apic --> redis
    redis --> wai
    wai --> ollama
    wai --> pg
    wdata --> pg
    wdata -->|gece 03:00| sites
    pg -.->|pg_dump · günlük| backup
```

| Container | Dışa açık mı? | Bellek limiti | Sorumlu |
|---|---|---|---|
| caddy | **Evet** (tek giriş noktası, otomatik HTTPS) | 256 MB | Ataberk |
| api | Hayır | 1 GB | Anıl |
| worker-ai | Hayır | 2 GB | Burak |
| worker-data | Hayır | 1,5 GB | Ataberk |
| ollama | **Kesinlikle hayır** | 8 GB | Burak |
| postgres | Hayır | 2 GB | Ataberk |
| redis | Hayır | 256 MB | Ataberk |
| uptime-kuma / grafana | Sadece status sayfası | 512 MB | Ataberk |

Toplam ~15,5 GB / 16 GB. Ayrıntılar ve ortamlar (lokal / staging / production): `docs/mimari.md`.
