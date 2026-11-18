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

## Deployment

Eski VPS + Caddy diyagramı karar #30 ile geçersiz oldu. Güncel production deployment diyagramı, ağ sınırları, deploy ve yedek akışı: [`docs/architecture/deployment.md`](../architecture/deployment.md).
