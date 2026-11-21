# Ataberk — Görevler

**Alan:** Veri, Veri Tabanı ve DevOps · **36 görev · 283 saat**

Bu dosya Ataberk'in görev listesidir ve görev durumlarının tek doğru kaynağıdır. Sadece Ataberk (veya onun Claude'u) günceller.

**Durum nasıl güncellenir:** İlgili görevin `- **Durum:**` satırını şu değerlerden biriyle değiştirin: `Yapılacak`, `Devam Ediyor`, `Engellendi`, `Tamamlandı`. Durum değişikliği, işin kendisiyle aynı PR'da gönderilir. `Engellendi` olursa sebebini **Not** satırına yazın ve gruba haber verin.

**Devam notu:** Yarım kalan görevin altına gün sonunda "bitiriyorum" rutiniyle `- **Devam notu (tarih):** Yapılan · Sıradaki adım · Açık sorular · Branch` satırı eklenir; görev bitince silinir. Not, görevin branch'inde durur ve "başlıyorum" rutini oradan okur.

Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (başlangıç planı, referans). Tarih veya kapsam değişirse Excel değil bu dosya güncellenir.

---

## Sprint 0

### T-006 · Monorepo ve Git akışı

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-001 (Anıl)
- **Destek:** —
- **Çıktı:** GitHub repo
- **Kabul kriteri:** Klasörler: /backend /ai /scraper /web /mobile /infra /docs (Electron `web/`'i kullanır). Tek ana dal `main` (karar #27); branch protection (1 onay + yeşil CI zorunlu), PR şablonu, conventional commits, CODEOWNERS.
- **Not:** 13.11.2026 kontrolü: klasör yapısı, PR şablonu ve `.github/CODEOWNERS` (CLAUDE.md'deki klasör sahipliğiyle aynı) repoda. `main` koruması açık: 1 onay zorunlu, yeni push'ta eski onay düşer, CI zorunlu (Backend, Scraper, Web, Docker) ve dal güncel olmalı, kurallar adminler için de geçerli.

### T-007 · Lokal geliştirme ortamı (docker-compose)

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-006
- **Destek:** —
- **Çıktı:** docker-compose.yml + Makefile
- **Kabul kriteri:** Servisler: postgres(+pgvector), redis, ollama, api, worker. Tek komutla ayağa kalkar (make up). .env.example dolu, gerçek sır yok. README'de 10 dakikada kurulum.
- **Not:** postgres/redis/ollama `make up` ile Windows'ta test edildi (healthy, pgvector çalışıyor, veri kalıcı). api ve worker compose'da `api`/`worker` profillerinde tanımlı; `backend/Dockerfile` (Anıl, T-023, port 8000) ve `ai/Dockerfile` (Burak, Celery worker) eklenince `make up` onları otomatik başlatır.

### T-009 · Production PC'si hazırlığı ve sertleştirme

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** —
- **Destek:** —
- **Çıktı:** `infra/pc/README.md` (PC kurulum ve kontrol listesi, sırlar hariç)
- **Kabul kriteri:** Karar #30: VPS yok, production Ataberk'in PC'sinde (i7-9750H, 32 GB RAM, GTX 1650, Windows 10 Pro). Docker Desktop (WSL2) elle açılır, `.wslconfig` ile en fazla 20 GB RAM; uyku/hazırda bekletme kapalı, kapak kapanınca "hiçbir şey yapma"; BitLocker canlıya çıkıştan önce açılır (go-live #1); etkin saatler ayarlanmaz (karar #31); Windows Güvenlik Duvarı açık, gelen port yok (modemde yönlendirme yok); saat dilimi Europe/Istanbul; C: diskinde en az 40 GB boş.
- **Not:** 06.11.2026: karar #30 ile VPS tedariki kaldırıldı, görev PC hazırlığına dönüştü. 10.11.2026: PC kontrol edildi (salt okunur): prizde uyku/hazırda bekletme hiçbir zaman, kapak kapanınca "hiçbir şey yapma" (Ataberk teyit etti), saat dilimi Türkiye, C: 53 GB boş, güvenlik duvarı üç profilde açık (ağ "Ortak"), otomatik oturum açma kapalı, `.wslconfig` `memory=20GB` yazıldı. Docker'ın oturumla başlaması, etkin saatler ve BitLocker karar #31 ile değişti; BitLocker go-live #1'de açılacak.

### T-010 · Alan adı, Cloudflare DNS ve Tunnel

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P1 · **Efor:** 2 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-009
- **Destek:** —
- **Çıktı:** DNS kayıtları + `cloudflared` servisi (compose)
- **Kabul kriteri:** Alan adı alındı, ad sunucuları Cloudflare'de (ücretsiz plan). Cloudflare Tunnel kuruldu; `cloudflared` production compose'da konteyner, tünel token'ı sadece PC'deki `.env`'de. app. ve api. tünele bağlı; tanıtım/yasal sayfalar için alan adının kökü Cloudflare Pages'e. Always Use HTTPS + HSTS + en düşük TLS 1.2 açık; SSL ücretsiz (Cloudflare).
- **Not:** 06.11.2026: karar #30 ile Caddy/Let's Encrypt yerine Cloudflare Tunnel; staging-api. ve status. alt alan adları kaldırıldı.

- **Not (13.11.2026):** Alan adı `cvnebakalim.com` Cloudflare'de (Registrar, 560 TL); `careerai-pc` tüneli production compose'da `cloudflared` konteyneri, token sadece PC'deki `infra/pc/.env.prod`'da. Uçtan uca denendi: `https://api.cvnebakalim.com/api/v1/health` ve `/health/ready` dışarıdan 200 (Cloudflare → tünel → `http://api:8000`; paneldeki servis türü HTTPS'ten HTTP'ye düzeltildi). `http://` → 301 `https://`, en düşük TLS 1.2 (TLS 1.1 reddediliyor), HSTS 6 ay + includeSubDomains (preload yok), `X-Content-Type-Options: nosniff` Cloudflare'den. Tanımsız alt alan adları açılmıyor. Kök alan adı → Cloudflare Pages T-070'e (tanıtım sayfası) devredildi; `app.` Pages'te mi tünelde mi Anıl'la karar verilecek. Cloudflare hesabında 2FA henüz yok (GitHub girişi 2FA'lı).
### T-011 · Veri tabanı şeması v1 (ERD)

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Veri Tabanı
- **Bağımlılık:** T-004 (Anıl)
- **Destek:** Burak
- **Çıktı:** ERD (dbdiagram.io) + şema dokümanı
- **Kabul kriteri:** "Veritabanı Şeması" sayfasındaki tablolar; 3NF, UUID PK, created_at/updated_at, soft delete (deleted_at). CV içeriği ASLA saklanmaz, sadece hash ve metadata.
- **Not:** ERD `backend/app/db/erd.dbml` + `erd.svg`, kararlar `docs/veritabani.md` (25.10). DBML → SQL geçici Postgres'te test edildi (17 tablo, 20 FK; silme/benzersizlik/CV-yok testleri geçti). UUID PK sadece kişisel tablolarda: contracts'taki job_posting.id ve resource_id integer. Onay bekleyen öneriler: `user_tokens` (Anıl, T-037), `analysis_unverified_skills` (Burak).

### T-014 · Veri kaynağı ve hukuki uygunluk analizi

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Veri Toplama
- **Bağımlılık:** —
- **Destek:** —
- **Çıktı:** Kaynak uygunluk tablosu
- **Kabul kriteri:** Her kaynak için robots.txt ve kullanım koşulları incelendi. Öncelik sırası: resmi API'ler > açık veri setleri (Kaggle) > izin veren siteler. Kullanım koşulları scraping'i yasaklayan sitelerden (ör. LinkedIn) veri ÇEKİLMEZ.
- **Not:** Tablo: `scraper/kaynak-uygunluk.md` (25.10). Kullanılabilir: Remotive, Himalayas, Remote OK, Hacker News API'leri + EMSCAD (CC0). Türk sitelerinin hiçbiri izinsiz kullanılamıyor; Secretcv/Techcareer/İŞKUR için izin e-postası şablonu hazır. Açık: LinkedIn kaynaklı Kaggle setleri için ekip/danışman kararı, Adzuna ve Arbeitnow yazılı teyidi.

### T-008 · CI pipeline (GitHub Actions)

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-006
- **Destek:** —
- **Çıktı:** .github/workflows/ci.yml
- **Kabul kriteri:** Her PR'da: ruff + mypy (Python), eslint + tsc (TS), pytest, docker build. Kırmızı CI ile merge yapılamaz.
- **Not:** `.github/workflows/ci.yml` + `infra/ci.md` (25.10). İşler: backend (Postgres servisiyle migration testleri dahil), ai, web, mobil (dosyaları gelince otomatik), docker (compose + imaj build + health smoke test). Adımlar yerelde CI ile aynı komutlarla denendi, actionlint temiz. GitHub'da #16 yeşil (25.10, Backend migration testleri dahil; #17 ile DB bağımlılıkları ve sabit ruff/mypy geldi). "Kırmızı CI ile merge yok" kuralının GitHub tarafından zorlanması branch protection'a bağlı: T-006 (Student Pack sonrası, adımlar `infra/ci.md`'de).

### T-012 · SQLAlchemy 2.0 modelleri + Alembic migration

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Veri Tabanı
- **Bağımlılık:** T-011
- **Destek:** Anıl
- **Çıktı:** Migration dosyaları
- **Kabul kriteri:** Tüm tablolar model olarak yazıldı; ilk migration; upgrade/downgrade test edildi; CI'da migration kontrolü.
- **Not:** 17 model + `0001_ilk_sema` migration `backend/app/db/` altında (25.10). upgrade → downgrade → upgrade ve `alembic check` yerelde geçti; `tests/db` (6 test, `TEST_DATABASE_URL` ile) hazır. Bağlı işler: (1) Anıl `backend/pyproject.toml`'a `sqlalchemy`, `alembic`, `pgvector` ekleyecek; (2) CI'da migration kontrolü T-008'de bağlanacak.

### T-015 · Açık veri setiyle başlangıç ilan havuzu

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-014, T-012
- **Destek:** —
- **Çıktı:** job_postings tablosunda ≥ 2.000 kayıt
- **Kabul kriteri:** Kaggle vb. setlerden en az 2.000 yazılım ilanı içe aktarıldı (scraping çalışmasa bile sistem çalışır = yedek plan).
- **Not:** `scraper/collector` (25.10): izinli kaynaklardan (T-014) **2.048 aktif** güncel yazılım ilanı (Hacker News 1.443, Himalayas 565, Remote OK 30, Remotive 10; Mayıs–Ekim 2026) + yedek plan olarak **EMSCAD 4.374** (CC0, 2012–14, pasif; `--active` ile açılır). Scraping yok, hepsi API/veri seti. E-posta, telefon ve profil linkleri maskeleniyor; iş arayan yorumları ve TR/EN dışı ilanlar alınmıyor. Açık: ilan metnindeki kişi adları (ör. işe alımcı) isim tanıma ister → Burak'ın T-030 maskeleyicisi T-033'te uygulanmalı. `role_id` ve yetkinlik etiketleri T-033'te.

---

## Sprint 1

### T-013 · pgvector eklentisi ve vektör indeksleri

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P1 · **Efor:** 3 saat · **Alan:** Veri Tabanı
- **Bağımlılık:** T-012
- **Destek:** Burak
- **Çıktı:** Migration + benchmark notu
- **Kabul kriteri:** skills.embedding ve job_postings.embedding için vector(384) + HNSW indeks (cosine). Örnek sorgu < 50 ms.
- **Not:** Migration `0003_vektor_indeksleri` (m=16, ef_construction=64, `vector_cosine_ops`), modellerde `hnsw_index()`; upgrade/downgrade, `alembic check` ve planlayıcının indeksi seçtiğini doğrulayan test geçti (29.10). Ölçüm `docs/veritabani.md` "Vektör indeksleri": sentetik vektörlerle 6.422 ilanda p95 12 ms, 50.000 ilanda p95 6 ms, recall@10 ≥ 0,99. Gerçek embedding yok (Burak'ın T-031/T-042'si); gelince ölçüm tekrarlanmalı. Burak için: sorgu `ORDER BY embedding <=> :v LIMIT k` biçiminde, `WHERE` süzmesinde `hnsw.iterative_scan`.

### T-016 · Playwright scraper PoC (1 kaynak)

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-014
- **Destek:** —
- **Çıktı:** scraper/ modülü
- **Kabul kriteri:** Uygun bulunan 1 kaynaktan ilan listesi + detay çekiliyor; 3-5 sn gecikme, User-Agent, hata durumunda tekrar deneme.

### T-017 · Yetkinlik taksonomisi ve pozisyon seed verisi

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** Veri Tabanı
- **Bağımlılık:** T-012
- **Destek:** Burak
- **Çıktı:** seed script + CSV
- **Kabul kriteri:** ESCO + elle derlenmiş en az 300 teknoloji; kategori ve eş anlamlılar ("JS", "Javascript" → JavaScript); en az 10 hedef pozisyon (Backend, Frontend, Full-Stack, Mobil, Veri Bilimci, DevOps, QA, ML Mühendisi, Siber Güvenlik, Oyun).
- **Not:** `scraper/taxonomy/` (25.10): 374 yetkinlik (8 kategori, TR+EN eş anlamlılar, 46'sı `case_sensitive`) + 12 pozisyon; `python -m collector seed-taxonomy`. Burak'ın 82 geçici yetkinliği ad/slug/kategoriyle korundu. 2.048 ilanla kapsam %85,9. ESCO v1.2.1 (26.10): 61 yetkinlik ESCO kavramına bağlı (sadece tercih edilen adla birebir, elle gözden geçirildi); lisans doğrulandı, uygulamada atıf cümlesi gerekiyor (`scraper/taxonomy/README.md`).

### T-033 · İlan normalizasyonu (ETL)

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 14 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-015, T-017
- **Destek:** Burak
- **Çıktı:** scraper/etl modülü
- **Kabul kriteri:** HTML temizleme, dil tespiti, pozisyon başlığı normalizasyonu ("Back-end Geliştirici" = Backend Developer), tekrar kayıt temizleme (hash + benzerlik), yetkinlik etiketleme (Burak'ın v1 modülü).
- **Not:** `scraper/etl/` + `python -m collector normalize` / `export-postings` (26.10). HTML temizleme ve dil tespiti T-015'ten (`collector/clean.py`). Pozisyon sadece başlıktan (ekip kararı 26.10: yetkinlikten tahmin yok, istatistik döngüsel olmasın); genel başlıklar ("Software Engineer") `role_id = NULL`. Benzer ilan: aynı şirket + pozisyonda Jaccard ≥ 0,9 → eski kopya pasif. 2.002 aktif ilanda pozisyonu belli **%39,6 (792)**, yetkinlik bulunan %88 (ilan başına 7,5), 46 benzer ilan pasife alındı; 30 ilanlık elle kontrolde pozisyon ataması doğru. Burak'ın T-031'i başlamadığı için ilan etiketleyicisi sözlük tabanlı olarak burada yazıldı (`etl/skills.py`, arayüz `tag(text, lang)`); 30.10'da T-031 ile ortaklaştırıldı: eşleme Burak'ın `extraction.taxonomy.Matcher`'ıyla, önem (required/preferred) burada (karar #28). Gerçek veride 248 hatalı bağ silindi (Objective-C → C 112, Ruby on Rails → Ruby 117, Azure DevOps → DevOps 19), başka bağ değişmedi. Kişisel veri maskeleme 30.10'da bağlandı: `pii.mask_posting` (Burak, T-030) `normalize`'ın varsayılanı, `mask_posting_once` sarmalayıcısı önceki etiketleri korur (6.632 ilandan 338'i maskelendi, 2 yetkinlik bağı kaybı, istatistik değişmedi). Açık: ince pozisyonlar (oyun 4, veri analisti 5 ilan) Türkçe kaynaklar gelince artar.

### T-035 · Prova (staging) ortamı

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-009, T-007
- **Destek:** —
- **Çıktı:** Prova ortamı (`careerai-staging` compose projesi, `infra/pc/compose.yml`)
- **Kabul kriteri:** PC'de `docker compose -p careerai-staging` ile production'dan ayrı volume'larla açılıp kapatılabilen prova ortamı (`bash infra/pc/deploy.sh <ref> staging` / `make staging-down`); sadece 127.0.0.1, gerektiğinde geçici tünel (staging.cvnebakalim.com); staging verisi production'dan ayrı.
- **Not:** 06.11.2026: karar #30 ile sürekli açık staging sunucusu kaldırıldı; prova ortamı ihtiyaç olunca açılır. Bu PC'de denendi: 41 sn'de bütün servisler healthy, host'a port açılmadı, `down -v` ortak Ollama modelini silmiyor. Geçici tünel gerekmedikçe kurulmadı. Analiz işçisi/CV Redis #58/#60 ve `ai/Dockerfile` sonrası eklenecek (PR #50).

### T-036 · CD: imaj üretimi ve PC'ye deploy betiği

- **Durum:** Tamamlandı
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-008, T-035
- **Destek:** —
- **Çıktı:** `.github/workflows/deploy.yml` + `infra/pc/deploy.sh` + `infra/pc/deploy.md`
- **Kabul kriteri:** `main` birleştirmesi image'ları commit adıyla GHCR'a push eder; `vX.Y.Z` etiketi o commit'i gösterir. PC'de tek komutla (Git Bash: `bash infra/pc/deploy.sh vX.Y.Z`): image çek, önce yedek, alembic upgrade, `docker compose -p careerai-prod up -d`, smoke test; başarısızsa önceki image etiketine dönüş. PC'ye dışarıdan SSH/deploy erişimi açılmaz.
- **Not:** 06.11.2026: karar #30 ile SSH'li otomatik staging deploy'u kaldırıldı.
- **Not:** 10.11.2026: main birleştirmesi imajları GHCR'a gönderiyor (b6703cc, api + worker-data); PC'de GHCR'dan çekilip `bash infra/pc/deploy.sh <ref> staging` ile prova ortamına alındı (5 servis healthy, `/health/ready` hazır). GHCR paketlerine repo Admin rolüyle bağlandı (Manage Actions access); bağlı olmayan pakete GITHUB_TOKEN yazamıyordu. Production dökümü gerçek `careerai-prod`'da T-075'te denenecek.

### T-028 · TÜBİTAK 2209-A başvuru dosyası

- **Durum:** Engellendi
- **Tarih:** 27.10.2026 – 11.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Kongre / TÜBİTAK
- **Bağımlılık:** T-000 (Anıl)
- **Destek:** Burak, Anıl
- **Çıktı:** Başvuru dosyası
- **Kabul kriteri:** Özgün değer, yöntem, iş-zaman planı, risk yönetimi, bütçe ve yaygın etki bölümleri; danışman onayı ve sisteme yükleme. Son tarihi güncel çağrı takviminden doğrulayın.
- **Not:** 2026 çağrısı (TÜBİTAK duyurusu, 27.10.2026'da doğrulandı): başvuru 07.10–**11.11.2026 17:30**, TÜBİTAK Yönetim Bilgi Sistemi üzerinden; danışman onayı başvuru aşamasında tamamlanmalı (danışmanın güncel YÖK kaydı gerekli); kuruluş yetkilisi e-imzası 16–23.11.2026. Planın 15.11 bitişi son tarihi kaçırıyordu, bitiş 11.11'e çekildi. 05.11.2026: **askıya alındı.** Başvuru dosyası hazır, danışman hocanın dönüşü bekleniyor (hocalarla görüşüldü). Ataberk danışmanla ilgili bilgiyi verince devam edilecek; o zamana kadar bu görevde iş yapılmaz. Son tarih (11.11 17:30) değişmedi.
- **Devir:** 27.10.2026'da Burak'tan devredildi (karar #18).

---

## Sprint 2

### T-034 · Zamanlanmış veri toplama (Celery beat)

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P1 · **Efor:** 10 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-016, T-033
- **Destek:** —
- **Çıktı:** Zamanlanmış görevler
- **Kabul kriteri:** Her gece 03:00; kaynak başına 3-5 sn rastgele gecikme, üstel geri çekilme ile tekrar deneme, dönüşümlü User-Agent. Her çalışma scrape_runs tablosuna yazılır.
- **Not:** `collector/nightly.py` (zincir: HN/Himalayas/Remote OK/Remotive → normalize → role_skill_stats) + `collector/tasks.py` (Celery beat 03:00 Europe/Istanbul, `data` kuyruğu, Redis kilidi, 3 sa sınır) + `python -m collector nightly`; `worker-data` compose servisi (`--profile data`, `scraper/Dockerfile`), CI'da imaj derleniyor (29.10). İstekler arası 3-5 sn rastgele bekleme, 429/5xx/ağ hatasında 5→40 sn üstel geri çekilme; bir kaynak düşerse diğerleri devam eder, 403/kalıcı 429 alan kaynak pasife alınır (kaynak-uygunluk kural 3). **Dönüşümlü User-Agent yapılmadı:** kaynak-uygunluk kural 3-4 UA sahteciliğini yasaklıyor, kimlik belirten tek UA kullanılıyor (karar önerisi). Gerçek deneme (Celery üzerinden, 29.10): 12,5 dk, +210 ilan (Himalayas 206), 4 kaynak `success`, istatistik 1.574 satır. T-016 (Playwright) bitmediği için şimdilik sadece API kaynakları; HTML kaynak gelince robots.txt kontrolü (kural 2) o adaptörde. Bilinen: HN'de alınmayan yorumlar (iş arayan, TR/EN dışı) her gece yeniden okunuyor (~150 istek, ~10 dk).

### T-045 · Pozisyon-yetkinlik istatistikleri

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-033
- **Destek:** —
- **Çıktı:** role_skill_stats tablosu
- **Kabul kriteri:** role_skill_stats: pozisyon × yetkinlik → ilan sayısı ve talep oranı; her gece toplama işinden sonra yenilenir.
- **Not:** `role_skill_stats` T-012'de materialized view olarak kuruldu (son 6 ayın aktif, pozisyonu belli ilanları); T-045'te yenileme ve okuma eklendi: `scraper/etl/stats.py`, `collector refresh-stats` / `role-stats` (29.10). `collector normalize` sonunda view'ı kendisi yeniler (CONCURRENTLY: API okumaya devam eder), yani sıra import → normalize → istatistik; gece zamanlaması T-034'te bu komut zincirine bağlanacak. Gerçek veride 1.464 satır, ~2 sn. 12 pozisyondan 7'si 50 ilanın altında (`low_data`): Frontend 45, Veri Mühendisi 42, Mobil 40, Güvenlik 29, Veri Bilimci 24, Veri Analisti 5, Oyun 4 (#4'teki açık soru 2). Sözlükte soft skill'ler de sayılıyor (ör. QA'da İletişim %57); eşleştirmede (Burak, T-042) kategoriye göre süzülebilir.

### T-046 · Eğitim kaynağı havuzu

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-017
- **Destek:** Burak
- **Çıktı:** resources tablosu (≥ 900 kayıt)
- **Kabul kriteri:** YouTube Data API v3 + elle küratörlük. Her yetkinlik için en az 3 kaynak (Türkçe öncelikli; seviye, süre, ücretsiz/ücretli). Haftalık link sağlık kontrolü (ölü link → pasif).
- **Not:** 12.11.2026 itibarıyla 1570 canlı kaynak (tr 470, en 1100; 1040 YouTube videosu + `resources.csv`'de elle derlenmiş linkler). 374/374 yetkinlikte ≥ 3 kaynak, 230 yetkinlikte en az 1 Türkçe kaynak. Seviye/süre/ücretsiz alanları dolu. Haftalık `collector.resources_check` ölü linkleri pasife alıyor.

### T-047 · 2. ve 3. veri kaynağı entegrasyonu

- **Durum:** Tamamlandı
- **Tarih:** 23.11.2026 – 29.11.2026 · **Öncelik:** P1 · **Efor:** 8 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-034
- **Destek:** —
- **Çıktı:** Ek adaptörler
- **Kabul kriteri:** Uygunluk analizinden geçen 2 kaynak daha eklendi; kaynak başına ayrı adaptör; tek kaynak düşerse sistem çalışmaya devam eder.

---

## Sprint 3

### T-063 · Yönetim paneli (admin)

- **Durum:** Tamamlandı
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Backend API
- **Bağımlılık:** T-037 (Anıl), T-046
- **Destek:** Anıl
- **Çıktı:** /admin paneli
- **Kabul kriteri:** SQLAdmin ile: kaynak ekle/düzenle, ilan kaynakları aç/kapa, scrape çalışmalarını izle, istatistikler. Sadece admin rolü.
- **Not:** `backend/app/admin/` (karar #33, kullanım `backend/app/admin/README.md`). Kaynak ekle/düzenle (sadece https, silme yok), ilan kaynağı aç/kapa ve istek aralığı (şartları incelenmemiş kaynak açılamaz), toplama çalışmaları (salt okunur), istatistikler; arayüz Türkçe. Sadece admin rolü, rol her istekte DB'den okunur; giriş denemesi sınırlı; girişler ve değişiklikler `audit_logs`'ta. Admin verme: `make prod-admin EMAIL=…`. 13 test (`backend/tests/auth/test_admin_panel.py`); geliştirme veritabanındaki gerçek veriyle (7.207 ilan, 1.571 kaynak) tarayıcıda denendi. Production'da yapılacak elle adım: Cloudflare Access uygulaması (README'deki adımlar), sonra gizli pencereden kontrol.

### T-066 · İzleme ve uyarı sistemi

- **Durum:** Tamamlandı
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-035
- **Destek:** —
- **Çıktı:** İzleme paneli (Grafana, PC'de)
- **Kabul kriteri:** PC dışından uptime izleme (UptimeRobot / Better Stack ücretsiz; api.cvnebakalim.com/health/ready her 1-5 dk), Sentry (backend + web + mobil, ücretsiz katman), Prometheus + Grafana PC'de (CPU/RAM/disk/kuyruk; sadece 127.0.0.1). Uyarılar Telegram/e-posta ile ekibe.
- **Not:** Kapsam karar #32 ile daraltıldı (15.11.2026): PC dışı uptime izleyici, status sayfası, Sentry ve bildirimler yapılmadı; ekip ihtiyaç duymuyor. Yapılan: `infra/monitoring/` (`monitoring` profili): Prometheus + Grafana (sadece 127.0.0.1:3000), node/redis/postgres/blackbox exporter'ları, 12 uyarı kuralı panonun en üstünde; alan adından erişim tünel üzerinden dış probla ölçülüyor (`DisErisimYok`). Salt okunur `careerai_monitor` rolünü `deploy.sh` oluşturur. 12.11.2026'da geçici bir compose projesinde denendi (tüm hedefler up, pano sorguları çalışıyor, rol kullanıcı tablosunu okuyamıyor). Production'da açmak: `.env.prod`'a `GRAFANA_ADMIN_PASSWORD`, `MONITOR_DB_PASSWORD` ve `COMPOSE_PROFILES`'a `monitoring`, sonra deploy (`infra/monitoring/README.md`).

### T-064 · Güvenlik incelemesi (OWASP Top 10)

- **Durum:** Tamamlandı
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Güvenlik & KVKK
- **Bağımlılık:** T-036
- **Destek:** Anıl
- **Çıktı:** Güvenlik bulguları raporu
- **Kabul kriteri:** pip-audit, npm audit, Dependabot; Trivy ile image taraması; gitleaks ile sır taraması; CORS sadece kendi alan adları; güvenlik başlıkları (HSTS, CSP, X-Content-Type-Options).
- **Not:** 15.11.2026. Rapor `docs/guvenlik-raporu.md` (G-1…G-8). CI `.github/workflows/security.yml` (gitleaks, pip-audit, npm audit, Trivy; PR, main ve haftalık) + `.github/dependabot.yml`; GitHub'da Dependabot uyarıları ve güvenlik güncellemeleri açık (secret scanning private repoda ücretli, gitleaks yeterli). Yedek imajı restic 0.19.1 (kritik açıklar kapandı); kalan restic açıkları `infra/backup/.trivyignore`, süre 15.01.2027'de doluyor, go-live öncesi tekrar bakılacak. Cloudflare başlık kuralları kuruldu, securityheaders.com A+. CORS canlıda doğrulandı. Açık kalan bulgular sahiplerinde: G-3 react-router ve G-6 `/docs` Anıl, G-8 mobil lock dosyası Burak; G-4 zlib sonraki deploy'da kapanır.

### T-067 · Merkezi log ve log maskeleme

- **Durum:** Tamamlandı
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-066
- **Destek:** —
- **Çıktı:** Log yapılandırması
- **Kabul kriteri:** JSON log + request_id; PII maskeleme filtresi (e-posta, telefon); 14 gün saklama; logrotate.
- **Not:** 15.11.2026. JSON log + `request_id` ve `mask_pii` API'de ve analiz işçisinde zaten vardı; veri işçisi de Celery'nin düz metin logu yerine aynı JSON biçimlendiriciye geçti (`scraper/collector/tasks.py`, test `scraper/tests/test_logging.py`). Merkezi log: izleme profiline Loki (14 gün saklama, compactor) + Alloy (Docker loglarını okur, e-posta/telefon/TCKN'yi ikinci kez maskeler); Grafana'da **Loglar** veri kaynağı, SLO sorguları `infra/monitoring/README.md` "Loglar". Postgres hata satırına değer yazmıyor (`log_error_verbosity=terse`, `log_min_error_statement=panic`). Rotasyon: Docker json-file 3 × 10 MB. Production'da sahte veriyle denendi. Production'da sürekli açık olması izleme profilinin açılmasına bağlı (`.env.prod` → `COMPOSE_PROFILES=…,monitoring`, Grafana şifreleri). #88'in (T-066) üstüne kurulu.

### T-068 · Yedekleme

- **Durum:** Tamamlandı
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-035
- **Destek:** —
- **Çıktı:** Yedekleme scriptleri + zamanlayıcı
- **Kabul kriteri:** pg_dump her gün 02:00 (PC o saatte kapalıysa açılışta); 7 günlük + 4 haftalık saklama; restic ile şifreli olarak PC dışına (Backblaze B2 ücretsiz katman vb.). Zamanlayıcı Windows'ta çalışır (compose içinde yedek konteyneri veya Görev Zamanlayıcı; PR #57'deki systemd birimleri PC'de kullanılmaz). Geri yükleme testi yapıldı.
- **Not:** 15.11.2026'da gerçek B2 ile denendi. B2'nin kendi indirme sunucusu (`f003.backblazeb2.com`) bu ağda TLS'te kesildiği için restic B2'nin S3 uyumlu adresine bağlanıyor (`s3:https://s3.eu-central-003.backblazeb2.com/cvnebakalim-yedek/careerai`, aynı uygulama anahtarı; `infra/pc/compose.yml`, `.env.example`, `infra/backup/README.md`). Depo oluşturuldu, ilk production yedeği alındı (zamanlayıcı "Yedek tamam: production", `restic check` hatasız). Dev verisiyle B2 üzerinden gidiş-dönüş: 6,57 MiB yedek 17 sn, geri yükleme 7 sn, tablo sayıları birebir (job_postings 7207, resources 1571, skills 374, roles 12, job_sources 8, scrape_runs 13); test snapshot'ı sonra silindi. `restore-test.sh production` yedeği 10 sn'de yükledi ama production veritabanı henüz boş olduğu için tablo kontrolünde başarısız sayıldı; production'a veri gelince (T-075) bir kez daha çalıştırılmalı. RESTIC_PASSWORD ve B2 anahtarı parola yöneticisinde.

### T-070 · Tanıtım (landing) sayfası

- **Durum:** Yapılacak
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P2 · **Efor:** 6 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-022 (Anıl)
- **Destek:** Anıl
- **Çıktı:** Landing sayfası
- **Kabul kriteri:** Ürün tanıtımı, ekran görüntüleri, indirme linkleri (Windows/macOS/Android), gizlilik politikası ve KVKK linkleri, iletişim.
- **Not:** 13.11.2026: T-010'dan devralındı: sayfa Cloudflare Pages'te yayınlanır ve kök alan adı `cvnebakalim.com` Pages projesine bağlanır (Anıl'ın yasal sayfaları #71 ile aynı Pages projesi olabilir).

---

## Sprint 4

### T-071 · E2E testleri (Playwright)

- **Durum:** Tamamlandı
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Test & QA
- **Bağımlılık:** T-053 (Anıl)
- **Destek:** Anıl
- **Çıktı:** tests/e2e
- **Kabul kriteri:** Kritik akışlar: kayıt → CV yükle → sonuç → kaynak aç → hesap sil. CI'da docker compose ile ayağa kaldırılan geçici ortama karşı gece çalışır (karar #30: ayrı staging sunucusu yok).
- **Not:** 15.11.2026. `tests/e2e/` (Playwright 1.64.1): `kritik-akis.spec.ts` kayıt → giriş → CV yükle (çalışma anında üretilen sahte PDF) → sonuç → kaynak aç (yeni sekme, dış istek yok) → hesap sil → silinen hesapla giriş reddi. Ortam `tests/e2e/ortam.sh` (docker compose, `careerai-e2e`, boş kurulup silinir; migration + seed-taxonomy + resources-seed); CI `.github/workflows/e2e.yml` her gece 03:30, PR'da sadece E2E dosyaları değişince. Yerelde 3 kez üst üste geçti (~12 sn). **Geçici:** `ExampleAnalyzer` eksik yetkinlik/kaynak yazmadığı için test o adımda sözleşme örneği biçiminde bir öneri ekler; T-057 veya ExampleAnalyzer'ın `missing_skills` yazması (Anıl) gelince kaldırılacak.

### T-072 · Yük testi (k6 / Locust)

- **Durum:** Devam Ediyor
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Test & QA
- **Bağımlılık:** T-057 (Burak), T-035
- **Destek:** Burak
- **Çıktı:** Yük testi raporu
- **Kabul kriteri:** 20 eşzamanlı kullanıcı, 30 dk. Hedef: API p95 < 300 ms (analiz hariç), hata oranı < %1, RAM < %85. Kuyruk birikme süresi ölçüldü; worker sayısı buna göre ayarlandı.
- **Not:** 18.11.2026: k6 betiği ve çalıştırıcı hazır (`tests/yuk/`). API kısmı ölçüldü (E2E ortamı, örnek analiz): 20 kullanıcı 30 dk, p95 49,5 ms, hata %0, RAM en yüksek %14,7 (`tests/yuk/README.md`). Kalan: T-057 (Burak) gelince gerçek analizle kuyruk bekleme süresini ölçüp worker/kuyruk sınırlarını ayarlamak.

### T-075 · Production ortamı kurulumu

- **Durum:** Tamamlandı
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-036, T-064
- **Destek:** —
- **Çıktı:** Production ortamı
- **Kabul kriteri:** PC'de ayrı compose projesi (`careerai-prod`, kendi volume'ları); en az yetkili DB kullanıcıları; sırlar `.env` (sadece bu PC'de, Windows kullanıcı izinleriyle korunur, repoda yok); hiçbir servis host'a port açmaz, dış erişim sadece `cloudflared`; kaynak limitleri (mem_limit), `restart: unless-stopped`. PC kapalıyken kaçan gece toplaması açılışta telafi edilir (R-18).
- **Not:** 15.11.2026. Ayrı `careerai-prod` projesi, kendi volume'ları, `mem_limit` + `restart: unless-stopped` (15 servisin hepsi), host'a port yok (tek istisna Grafana 127.0.0.1) zaten vardı; denetlendi. Yeni: en az yetkili `careerai_app` rolü (`infra/pc/app-role.sql`, deploy.sh `setup_app_role`; migration sahip rolle `migrate`), view yenileme migration 0004 `refresh_role_skill_stats()` (SECURITY DEFINER), `audit_logs` sadece ekleme; test `backend/tests/db/test_app_role.py`. Kaçan gece toplaması açılışta telafi (`scraper/collector/tasks.py` `missed_nightly`, test `test_catch_up.py`). `.env.prod` izinleri sadece Ataberk/SYSTEM/Administrators (icacls, `infra/pc/deploy.md` §2). Production'da denendi: api ve worker-data `careerai_app` ile bağlı, DDL ve doğrudan REFRESH reddediliyor, kaçan toplama açılışta başladı. #89 ve #94'ün (o da #88'in) üstüne kurulu.

### T-079 · Mimari doküman ve ADR'ler

- **Durum:** Tamamlandı
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-075
- **Destek:** Burak
- **Çıktı:** docs/architecture
- **Kabul kriteri:** Mimari kararlar (neden Ollama, neden pgvector, neden Celery) ADR olarak; deployment diyagramı.
- **Not:** 18.11.2026: `docs/architecture/`: dört ADR (Ollama, pgvector, Celery + Redis, PC + Cloudflare Tunnel) ve production deployment diyagramı (`deployment.md`: servisler, ağ sınırları, deploy ve yedek akışı, bellek bütçesi). `docs/diagrams/component-deployment.md`'deki eski VPS diyagramı oraya yönlendirildi.

---

## Sprint 5

### T-085 · Beta hata düzeltmeleri — Veri ve altyapı

- **Durum:** Yapılacak
- **Tarih:** 28.12.2026 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-082 (Anıl)
- **Destek:** —
- **Çıktı:** Kapanmış issue'lar
- **Kabul kriteri:** Veri kalitesi sorunları, eksik kaynaklar, altyapı ayarları.

### T-087 · Felaket kurtarma tatbikatı

- **Durum:** Tamamlandı
- **Tarih:** 28.12.2026 – 03.01.2027 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-068, T-075
- **Destek:** —
- **Çıktı:** DR tatbikat raporu
- **Kabul kriteri:** Başka bir bilgisayara (ör. Burak'ın veya Anıl'ın) yedekten sıfırdan kurulum ve tünelin oraya taşınması. Hedef: RTO < 4 saat, RPO < 24 saat. Süre ölçülüp runbook'a yazıldı.
- **Not:** 20.11.2026: Başka bilgisayarda tatbikat **iptal edildi (karar #37)**; görev prosedür ve production PC'sindeki geri yükleme testiyle kapatıldı. Kabul kriterindeki RTO ölçülmedi. 18.11.2026: Prosedür ve tatbikat kaydı hazır (`docs/runbook/felaket-kurtarma.md`); production PC'sinde gerçek veriyle geri yükleme testi geçti (1,97 MB, 12 sn, 11 tablo eşleşti). Kalan: Burak'ın veya Anıl'ın bilgisayarında tatbikat (geçici `dr-test` tüneliyle), süreleri tabloya yazmak; önce parola yöneticisindeki `.env.prod` kaydının eksiksiz olduğu kontrol edilmeli (prosedür 0. adım).

### T-088 · Operasyon runbook'u

- **Durum:** Tamamlandı
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-087
- **Destek:** Burak, Anıl
- **Çıktı:** docs/runbook
- **Kabul kriteri:** Deploy, rollback, Ollama yeniden başlatma, disk dolu, kuyruk birikmesi, veri ihlali şüphesi senaryoları için adım adım prosedür ("Operasyon & SLO" sayfası).
- **Not:** 18.11.2026: `docs/runbook/operasyon.md`: altı senaryo, her biri uyarı adı, sorumlu, hedef süre ve production PC'sinde Git Bash'te çalışan komutlarla. Rollback'teki migration geri alma `make backup-migration-test` ile gerçek veride denendi. Veri ihlali bölümü sır yenileme tablosu ve 72 saat KVK Kurulu bildirimini içerir (go-live #39). Ollama (Burak) ve analiz kuyruğu (Anıl) bölümleri PR incelemesinde sahiplerince kontrol edilmeli; ekibin okuması go-live #44. T-087 tatbikatı bitince felaket-kurtarma.md'deki süreler buraya da yansıtılır.

### T-091 · Go-live provası

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** Go-Live
- **Bağımlılık:** T-075, T-088
- **Destek:** Burak, Anıl
- **Çıktı:** Prova notu
- **Kabul kriteri:** PC'de prova projesinde (`careerai-staging`) production'ın birebir kopyasıyla deploy + rollback provası; checklist üzerinden kuru çalıştırma; sunum B planı (127.0.0.1'de yerel demo, telefondan internet paylaşımı) denendi.
- **Not:** 21.11.2026: deploy + rollback provasının ilk turu yapıldı (go-live #49): production dökümüyle 146 sn, geri yükleme prosedüründeki yetki hatası düzeltildi (`docs/runbook/operasyon.md` 2. bölüm). `infra/pc/.env.staging` bu PC'de oluşturuldu. Ocak'ta v1.0.0 adayıyla tekrarlanacak; kalan: checklist kuru çalıştırma.
- **Not (21.11.2026, B planı):** `make prod-local` + yeni `make prod-local-web` / `prod-local-down` ile yerel demo ~1 dk'da hazır, production verisiyle tarayıcıda denendi (`infra/pc/deploy.md` §6). Düzeltilen: B planında CORS kapalıydı, yerel web derleme komutu yoktu. Kalan: telefondan internet paylaşımıyla tünel denemesi (Ataberk, elle), analiz akışı T-057'den sonra.

---

## Sprint 6

### T-094 · Production deploy (v1.0.0)

- **Durum:** Yapılacak
- **Tarih:** 18.01.2027 – 18.01.2027 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** Go-Live
- **Bağımlılık:** T-093 (Anıl)
- **Destek:** Burak, Anıl
- **Çıktı:** Canlı sistem
- **Kabul kriteri:** v1.0.0 etiketi; PC'de `make deploy TAG=v1.0.0`; migration; smoke test alan adı üzerinden; DNS/tünel/SSL kontrolü; başarısızlıkta 15 dk içinde rollback.

### T-097 · Hypercare (2 hafta yakın izleme)

- **Durum:** Yapılacak
- **Tarih:** 18.01.2027 – 31.01.2027 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-094
- **Destek:** Burak, Anıl
- **Çıktı:** Hypercare raporu
- **Kabul kriteri:** Günlük: hata oranı, analiz süresi, kuyruk, disk, yedek kontrolü; PC açık saatleri (09:00–23:00) duyuruldu; nöbet çizelgesi (her gün 1 kişi); kritik hatalara 4 saat içinde müdahale.
