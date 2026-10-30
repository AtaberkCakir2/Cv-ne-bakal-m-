# Sistem Mimarisi

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

## Akış

```
İstemci (Web / Electron / React Native)
   │ HTTPS
   ▼
Caddy (reverse proxy, otomatik SSL)
   ▼
FastAPI (backend/)  ──►  PostgreSQL 16 + pgvector
   │ iş kuyruğa atılır          ▲
   ▼                            │
Redis kuyruğu ──► AI worker (ai/)
                   PDF → kişisel veri maskeleme → yetkinlik çıkarımı
                   → embedding → eşleştirme → kaynak önerisi (Ollama)

Toplayıcı (scraper/, Celery beat, her gece 03:00)
   ilanları toplar → temizler → yetkinlik etiketler → istatistikleri yeniler
```

### Bir analizin yaşam döngüsü

1. Kullanıcı hedef pozisyonu seçer ve CV'sini (PDF, ≤ 5 MB, ≤ 5 sayfa) yükler.
2. API dosyayı diske yazmadan kuyruğa atar ve hemen `202 {analysis_id}` döner. İstemci ilerlemeyi SSE veya polling ile izler.
3. AI worker metni çıkarır (gerekirse OCR), kişisel verileri maskeler, yetkinlikleri çıkarır (sözlük + LLM), pozisyonun talep istatistikleriyle karşılaştırır.
4. Eksik yetkinlikler için kaynaklar **veri tabanından** seçilir; LLM sadece bu listeden seçip Türkçe gerekçe yazar.
5. Sonuç `contracts/analysis_result.schema.json` formatında kaydedilir; CV dosyası ve ham metin hiçbir yerde saklanmaz.

CPU'lu sunucuda bir analiz yaklaşık 1–2 dakika sürer; bu yüzden işlem senkron istek değil kuyruk işidir.

## Teknoloji kararları

| Katman | Bileşen | Teknoloji | Neden | Alternatif | Sorumlu |
|---|---|---|---|---|---|
| İstemci | Web arayüzü | React 18 + Vite + TypeScript, TanStack Query | Electron ile aynı kod tabanı; tip güvenli API istemcisi OpenAPI'den otomatik üretilir. | Next.js | Anıl |
| İstemci | Masaüstü | Electron + electron-builder + electron-updater | Raporda belirtildiği gibi Windows ve macOS; web kodunu yeniden kullanır; otomatik güncelleme. | Tauri (daha hafif) | Anıl |
| İstemci | Mobil | React Native (Expo, EAS Build) | Electron/React ile aynı dil (TS) ve ortak API istemcisi; EAS sayesinde iOS için Mac gerekmez. Flutter yerine seçildi: ekip tek ekosistemde kalır. | Flutter | Burak |
| Ağ | Reverse proxy + TLS | Caddy 2 | Otomatik Let's Encrypt sertifikası (SSL maliyeti 0 TL), basit yapılandırma, HTTP/2-3. | Nginx + certbot | Ataberk |
| Backend | API | Python 3.12, FastAPI, Pydantic v2, Uvicorn/Gunicorn | Asenkron, otomatik OpenAPI, AI ekosistemi ile aynı dil. | Django REST | Anıl |
| Backend | Kimlik doğrulama | JWT (PyJWT) + argon2-cffi | Durumsuz access token + rotasyonlu refresh token; modern parola hash. | fastapi-users | Anıl |
| Backend | Kuyruk / zamanlayıcı | Celery 5 + Redis 7 (+ Celery beat) | LLM analizleri dakikalar sürebilir → senkron istek yerine iş kuyruğu. Raporun "Kuyruk Mimarisi" önlemi. | RQ, Dramatiq | Anıl |
| Backend | E-posta | İşlemsel e-posta servisi (ücretsiz katman) | E-posta doğrulama ve şifre sıfırlama. | SMTP (Gmail uygulama şifresi — sadece test) | Anıl |
| Veri | İlişkisel veri tabanı | PostgreSQL 16 | Raporda önerilen RDBMS; JSONB, tam metin arama, olgun ekosistem. | MySQL | Ataberk |
| Veri | Vektör arama | pgvector (HNSW, cosine) | Ayrı vektör veri tabanına gerek kalmaz; tek yedek, tek sistem. | Qdrant | Ataberk |
| Veri | ORM / migration | SQLAlchemy 2.0 + Alembic | Sürümlü şema değişiklikleri, geri alınabilir migration. | SQLModel | Ataberk |
| Veri toplama | İlan toplama | Playwright (Python) + httpx; resmi API'ler; Kaggle veri setleri | Dinamik sayfalar için headless tarayıcı; robots.txt ve kullanım koşullarına uyum; açık veri yedek planı. | Selenium | Ataberk |
| Veri toplama | Eğitim kaynakları | YouTube Data API v3 + elle küratörlük | Günlük ücretsiz kota yeterli; link doğruluğu garanti (LLM link üretmez). | Udemy/Coursera katalogları | Ataberk |
| AI | PDF ayrıştırma | pdfplumber + PyMuPDF | Metin tabanlı PDF'lerde yüksek doğruluk; düzen bilgisi. | pypdf | Burak |
| AI | OCR | Tesseract 5 (tur + eng) + pdf2image | Taranmış CV'ler için yedek; açık kaynak, yerel. | EasyOCR | Burak |
| AI | LLM sunucusu | Ollama | Yerel çalışma → CV'ler dışarı gitmez (KVKK); API maliyeti 0. | llama.cpp server, vLLM (GPU) | Burak |
| AI | LLM modeli | Llama 3.x 8B Instruct (q4_K_M) — benchmark ile kesinleşecek | 8B quantize model ~5-6 GB RAM; Türkçe yeterli; JSON çıktı desteği. | Gemma 9B, Qwen 7B | Burak |
| AI | Embedding | sentence-transformers: paraphrase-multilingual-MiniLM-L12-v2 (384 boyut) | Türkçe destekli, CPU'da hızlı, küçük. | multilingual-e5-small | Burak |
| AI | Ön filtre | TF-IDF (scikit-learn) + kosinüs benzerliği | Raporda belirtilen ön filtre; LLM'e giden veriyi küçültür. | — | Burak |
| Altyapı | Container | Docker + Docker Compose | Tek sunucu için yeterli; lokal = staging = production. | Kubernetes (gereksiz karmaşık) | Ataberk |
| Altyapı | CI/CD | GitHub Actions + GHCR | Ücretsiz (öğrenci), repo ile entegre. | GitLab CI | Ataberk |
| Altyapı | Sunucu | Linux VPS: 8 vCPU / 16 GB RAM / 160 GB SSD, Ubuntu 24.04 | Rapordaki bütçe. CPU'da analiz ~60-120 sn sürer → kuyruk + ilerleme ekranı ile yönetilir. | GPU sunucu (saatlik kiralama, demo günleri) | Ataberk |
| Operasyon | İzleme | Uptime Kuma, Sentry, Prometheus + Grafana | Ücretsiz/açık kaynak; kesinti ve hata uyarıları. | Better Stack | Ataberk |
| Operasyon | Yedekleme | pg_dump + restic → sunucu dışı depolama | Şifreli, artımlı, sürümlü yedek. | Sağlayıcı snapshot'ı (ek olarak) | Ataberk |
| Kalite | Test | pytest, httpx, testcontainers, Playwright, k6 | Birim → entegrasyon → E2E → yük test piramidi. | Locust | Ataberk |
| Kalite | Kod kalitesi | ruff, mypy, eslint, prettier, pre-commit | CI'da zorunlu; tutarlı kod stili. | — | Ataberk |

## Ortamlar

| Ortam | Amaç | Adres | Altyapı | Deploy tetikleyici | Veri | Erişim | Sorumlu |
|---|---|---|---|---|---|---|---|
| Lokal | Geliştirme | localhost | docker-compose (geliştirici bilgisayarı) | Elle (make up) | Seed + sahte veri; gerçek CV yok | Geliştirici | Ataberk |
| Staging | Test, demo, UAT, go-live provası | staging-api.<alanadi> | VPS üzerinde ayrı compose projesi | main'e merge → otomatik | Anonim test verisi, gerçek ilanlar | Ekip + beta kullanıcıları | Ataberk |
| Production | Canlı sistem | api.<alanadi>, app.<alanadi> | VPS, ayrı compose profili, kaynak limitli | vX.Y.Z etiketi + elle onay (environment protection) | Gerçek kullanıcı verisi (KVKK kapsamında) | Sadece Ataberk + 1 yedek (SSH anahtarı) | Ataberk |

## Production servisleri (docker compose)

| Servis | İmaj / Teknoloji | Port (iç ağ) | Dışa açık mı? | Bellek limiti | Replika | Sağlık kontrolü | Sorumlu |
|---|---|---|---|---|---|---|---|
| caddy | caddy:2 | 80, 443 | EVET (tek giriş noktası) | 256 MB | 1 | HTTP 200 | Ataberk |
| api | careerai/api (FastAPI + Gunicorn, 4 worker) | 8000 | Hayır (Caddy arkasında) | 1 GB | 1 | /health/ready | Anıl |
| worker-ai | careerai/worker (Celery, concurrency=1) | — | Hayır | 2 GB | 1 | celery inspect ping | Burak |
| worker-data | careerai/worker (Celery beat + toplama) | — | Hayır | 1,5 GB (Playwright) | 1 | celery inspect ping | Ataberk |
| ollama | ollama/ollama | 11434 | HAYIR (kesinlikle) | 8 GB | 1 | /api/tags | Burak |
| postgres | pgvector/pgvector:pg16 | 5432 | HAYIR | 2 GB | 1 | pg_isready | Ataberk |
| redis | redis:7 (AOF açık, şifreli) | 6379 | HAYIR | 256 MB | 1 | redis-cli ping | Ataberk |
| uptime-kuma / grafana | louislam/uptime-kuma, grafana | 3001, 3000 | Sadece status sayfası (şifreli panel) | 512 MB | 1 | — | Ataberk |

**Bellek bütçesi:** toplam ~15,5 GB / 16 GB RAM, sınırda. Bu yüzden AI worker eşzamanlılığı 1, 4 GB swap ve RAM %85'i aşınca uyarı var. Kullanıcı sayısı artarsa ilk adım Ollama'yı ayrı (tercihen GPU'lu) sunucuya taşımaktır.

## API

Endpoint listesi: [contracts/api.md](../contracts/api.md). Analiz sonucu formatı: [contracts/analysis_result.schema.json](../contracts/analysis_result.schema.json).

## Sorumluluk matrisi (RACI)

R = yapan · A = son onay · C = danışılan · I = bilgilendirilen

| İş paketi | Ataberk | Burak | Anıl | Danışman |
|---|---|---|---|---|
| Veri toplama ve ETL | A/R | C | I | I |
| Veri tabanı şeması ve migration'lar | A/R | C | C | I |
| Yetkinlik taksonomisi ve kaynak havuzu | A/R | C | I | I |
| PDF/OCR/PII ve yetkinlik çıkarımı | I | A/R | C | I |
| Eşleştirme ve öneri motoru (Ollama) | C | A/R | C | C |
| Model değerlendirme | C | A/R | C | C |
| FastAPI, auth, kuyruk | C | C | A/R | I |
| Web ve Electron arayüzü, UI/UX | I | I | A/R | I |
| Mobil uygulama | I | A/R | C | I |
| Play Store yayını | I | C | A/R | I |
| Altyapı, CI/CD, izleme, yedekleme | A/R | I | C | I |
| Güvenlik incelemesi | A/R | R | R | I |
| KVKK metinleri ve uyum | C | A/R | R | C |
| Kongre posteri ve sunumu | R | R | A/R | C |
| TÜBİTAK 2209-A başvurusu | A/R | R | R | A |
| Final raporu | R | A/R | R | C |
| Final sunumu | R | R | A/R | I |
| Sprint yönetimi ve takip | I | I | A/R | I |
| Go / No-Go kararı | R | R | A/R | I |
| Production deploy ve hypercare | A/R | R | R | I |
