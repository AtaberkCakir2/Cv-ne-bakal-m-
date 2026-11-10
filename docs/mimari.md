# Sistem Mimarisi

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

## Akış

```
İstemci (Web / Electron / React Native)
   │ HTTPS (alan adı, TLS Cloudflare'de)
   ▼
Cloudflare Tunnel ──► cloudflared (PC'de konteyner, gelen port açmaz)
   ▼
FastAPI (backend/)  ──►  PostgreSQL 16 + pgvector
   │ iş kuyruğa atılır          ▲
   ▼                            │
Redis kuyruğu ──► AI worker (ai/)
                   PDF → kişisel veri maskeleme → yetkinlik çıkarımı
                   → embedding → eşleştirme → kaynak önerisi (Ollama)

Toplayıcı (scraper/, Celery beat, her gece 03:00)
   ilanları toplar → temizler → yetkinlik etiketler → istatistikleri yeniler

Hepsi tek bir bilgisayarda (Ataberk'in PC'si) Docker Compose ile çalışır (karar #30).
Tanıtım ve yasal sayfalar PC'den bağımsız olarak Cloudflare Pages'te durur.
```

### Bir analizin yaşam döngüsü

1. Kullanıcı hedef pozisyonu seçer ve CV'sini (PDF, ≤ 5 MB, ≤ 5 sayfa) yükler.
2. API dosyayı diske yazmadan kuyruğa atar ve hemen `202 {analysis_id}` döner. İstemci ilerlemeyi SSE veya polling ile izler.
3. AI worker metni çıkarır (gerekirse OCR), kişisel verileri maskeler, yetkinlikleri çıkarır (sözlük + LLM), pozisyonun talep istatistikleriyle karşılaştırır.
4. Eksik yetkinlikler için kaynaklar **veri tabanından** seçilir; LLM sadece bu listeden seçip Türkçe gerekçe yazar.
5. Sonuç `contracts/analysis_result.schema.json` formatında kaydedilir; CV dosyası ve ham metin hiçbir yerde saklanmaz.

Production PC'sinde (i7-9750H, CPU) bir analiz yaklaşık 1–2 dakika sürer; bu yüzden işlem senkron istek değil kuyruk işidir.

## Teknoloji kararları

| Katman | Bileşen | Teknoloji | Neden | Alternatif | Sorumlu |
|---|---|---|---|---|---|
| İstemci | Web arayüzü | React 18 + Vite + TypeScript, TanStack Query | Electron ile aynı kod tabanı; tip güvenli API istemcisi OpenAPI'den otomatik üretilir. | Next.js | Anıl |
| İstemci | Masaüstü | Electron + electron-builder + electron-updater | Raporda belirtildiği gibi Windows ve macOS; web kodunu yeniden kullanır; otomatik güncelleme. | Tauri (daha hafif) | Anıl |
| İstemci | Mobil | React Native (Expo, EAS Build) | Electron/React ile aynı dil (TS) ve ortak API istemcisi; EAS sayesinde iOS için Mac gerekmez. Flutter yerine seçildi: ekip tek ekosistemde kalır. | Flutter | Burak |
| Ağ | Dış erişim + TLS | Cloudflare Tunnel (`cloudflared`) + Cloudflare DNS (ücretsiz plan) | PC'de modem portu açmadan ve ev IP'sini göstermeden alan adıyla erişim; sertifika Cloudflare'de (SSL maliyeti 0 TL); ağ değişse de çalışır (karar #30). | Caddy + port yönlendirme (sabit IP gerekir), Tailscale Funnel | Ataberk |
| Ağ | Statik sayfalar | Cloudflare Pages (ücretsiz) | Tanıtım, aydınlatma metni, gizlilik politikası PC kapalıyken de açık kalır (Play Store gizlilik URL'si). | GitHub Pages | Anıl |
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
| Altyapı | Container | Docker Desktop (WSL2) + Docker Compose | Tek makine için yeterli; lokal ve production aynı compose dosyası, ayrı proje adı ve volume'lar. | Kubernetes (gereksiz karmaşık) | Ataberk |
| Altyapı | CI/CD | GitHub Actions + GHCR | Ücretsiz (öğrenci), repo ile entegre. CI imajı üretir; PC'deki production etiketle elle güncellenir (PC'ye dışarıdan deploy erişimi açılmaz). | GitLab CI | Ataberk |
| Altyapı | Sunucu | Ataberk'in PC'si: Casper Excalibur G770, i7-9750H (6C/12T), 32 GB RAM, GTX 1650 4 GB, 476 GB SSD (~71 GB boş, 06.11.2026), Windows 10 Pro | Kira 0 TL (karar #30). CPU'da analiz ~60-120 sn sürer → kuyruk + ilerleme ekranı; GTX 1650 ile Ollama'da kısmi GPU hızlandırması ölçülecek. | VPS (fizibilite planı), GPU sunucu (saatlik kiralama) | Ataberk |
| Operasyon | İzleme | Dış uptime izleyici (UptimeRobot / Better Stack ücretsiz), Sentry, Prometheus + Grafana | PC kapanınca içindeki izleyici de kapanacağı için erişilebilirlik dışarıdan izlenir; hata ve kaynak izleme PC'de. | Uptime Kuma (PC içinde) | Ataberk |
| Operasyon | Yedekleme | pg_dump + restic → PC dışı depolama (Backblaze B2 ücretsiz katman vb.) | Şifreli, artımlı, sürümlü yedek; PC bozulursa başka bir ekip bilgisayarına geri yüklenir. | Harici disk (ek olarak) | Ataberk |
| Kalite | Test | pytest, httpx, testcontainers, Playwright, k6 | Birim → entegrasyon → E2E → yük test piramidi. | Locust | Ataberk |
| Kalite | Kod kalitesi | ruff, mypy, eslint, prettier, pre-commit | CI'da zorunlu; tutarlı kod stili. | — | Ataberk |

## Ortamlar

| Ortam | Amaç | Adres | Altyapı | Deploy tetikleyici | Veri | Erişim | Sorumlu |
|---|---|---|---|---|---|---|---|
| Lokal | Geliştirme | 127.0.0.1 | docker-compose (her geliştiricinin bilgisayarı; proje adı `careerai`) | Elle (make up) | Seed + sahte veri; gerçek CV yok | Geliştirici | Ataberk |
| Prova (staging) | Go-live provası, UAT, rollback denemesi | Sadece 127.0.0.1 (gerekirse geçici tünel: staging.cvnebakalim.com) | Production PC'sinde geçici compose projesi (`careerai-staging`), iş bitince kapatılır | Elle, ihtiyaç olunca | Anonim test verisi, gerçek ilanlar | Ekip | Ataberk |
| Production | Canlı sistem, hocalara sunum | app.cvnebakalim.com, api.cvnebakalim.com | Ataberk'in PC'si, compose projesi `careerai-prod`, kaynak limitli, host'a port açmaz; dış erişim sadece Cloudflare Tunnel | vX.Y.Z etiketi + PC'de elle güncelleme (`git checkout vX.Y.Z`, `docker compose pull`, `up -d`) | Gerçek kullanıcı verisi (KVKK kapsamında) | PC başında Ataberk; Cloudflare ve yedek erişimi Ataberk + 1 yedek kişi | Ataberk |

## Production servisleri (docker compose)

| Servis | İmaj / Teknoloji | Port (iç ağ) | Dışa açık mı? | Bellek limiti | Replika | Sağlık kontrolü | Sorumlu |
|---|---|---|---|---|---|---|---|
| cloudflared | cloudflare/cloudflared | — (sadece dışarıya giden bağlantı) | Tek giriş noktası; gelen port yok | 128 MB | 1 | metrics /ready | Ataberk |
| api | careerai/api (FastAPI + Gunicorn, 4 worker) | 8000 | Hayır (tünel arkasında) | 1 GB | 1 | /health/ready | Anıl |
| worker-ai | careerai/worker (Celery, concurrency=1) | — | Hayır | 2 GB | 1 | celery inspect ping | Burak |
| worker-data | careerai/worker (Celery beat + toplama) | — | Hayır | 1,5 GB (Playwright) | 1 | celery inspect ping | Ataberk |
| ollama | ollama/ollama | 11434 | HAYIR (kesinlikle) | 8 GB | 1 | /api/tags | Burak |
| postgres | pgvector/pgvector:pg16 | 5432 | HAYIR | 2 GB | 1 | pg_isready | Ataberk |
| redis | redis:7 (AOF açık, şifreli) | 6379 | HAYIR | 256 MB | 1 | redis-cli ping | Ataberk |
| grafana (+ prometheus) | grafana, prometheus | 3000 | Hayır (sadece 127.0.0.1) | 512 MB | 1 | — | Ataberk |

**Bellek bütçesi:** production konteynerleri toplam ~15,5 GB. PC'de 32 GB RAM var ama Windows ve geliştirme ortamı da aynı makinede: Docker Desktop'a (WSL2, `.wslconfig`) en fazla 20 GB verilir, production açıkken geliştirme ortamının Ollama'sı kapatılır. AI worker eşzamanlılığı 1; RAM %85'i aşınca uyarı. Kullanıcı sayısı artarsa ilk adım Ollama'yı GPU'ya (GTX 1650 kısmi veya ayrı makine) almaktır.

**PC'nin sunucu gibi çalışması için:** uyku ve hazırda bekletme kapalı, kapak kapanınca "hiçbir şey yapma", Windows Update etkin saatleri ayarlı ve sunum öncesi hafta güncellemeler ertelenir, Docker Desktop oturum açılınca başlar, konteynerler `restart: unless-stopped`. Kontrol listesi: `infra/pc/README.md` (T-009).

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
