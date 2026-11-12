# Ataberk — Görevler

**Alan:** Veri, Veri Tabanı ve DevOps · **36 görev · 283 saat**

Bu dosya Ataberk'in görev listesidir ve görev durumlarının tek doğru kaynağıdır. Sadece Ataberk (veya onun Claude'u) günceller.

**Durum nasıl güncellenir:** İlgili görevin `- **Durum:**` satırını şu değerlerden biriyle değiştirin: `Yapılacak`, `Devam Ediyor`, `Engellendi`, `Tamamlandı`. Durum değişikliği, işin kendisiyle aynı PR'da gönderilir. `Engellendi` olursa sebebini **Not** satırına yazın ve gruba haber verin.

**Devam notu:** Yarım kalan görevin altına gün sonunda "bitiriyorum" rutiniyle `- **Devam notu (tarih):** Yapılan · Sıradaki adım · Açık sorular · Branch` satırı eklenir; görev bitince silinir. Not, görevin branch'inde durur ve "başlıyorum" rutini oradan okur.

Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (başlangıç planı, referans). Tarih veya kapsam değişirse Excel değil bu dosya güncellenir.

---

## Sprint 0

### T-006 · Monorepo ve Git akışı

- **Durum:** Devam Ediyor
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-001 (Anıl)
- **Destek:** —
- **Çıktı:** GitHub repo
- **Kabul kriteri:** Klasörler: /backend /ai /scraper /web /mobile /infra /docs (Electron `web/`'i kullanır). Tek ana dal `main` (karar #27); branch protection (1 onay + yeşil CI zorunlu), PR şablonu, conventional commits, CODEOWNERS.
- **Not:** Repo, klasör yapısı ve PR şablonu hazır. Kalan: ana dal koruması ve CODEOWNERS; özel repoda GitHub Pro gerektiriyor (Student Pack başvurusu 30.10'da yapıldı, onay bekleniyor).

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

- **Durum:** Devam Ediyor
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P1 · **Efor:** 2 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-009
- **Destek:** —
- **Çıktı:** DNS kayıtları + `cloudflared` servisi (compose)
- **Kabul kriteri:** Alan adı alındı, ad sunucuları Cloudflare'de (ücretsiz plan). Cloudflare Tunnel kuruldu; `cloudflared` production compose'da konteyner, tünel token'ı sadece PC'deki `.env`'de. app. ve api. tünele bağlı; tanıtım/yasal sayfalar için alan adının kökü Cloudflare Pages'e. Always Use HTTPS + HSTS + en düşük TLS 1.2 açık; SSL ücretsiz (Cloudflare).
- **Not:** 06.11.2026: karar #30 ile Caddy/Let's Encrypt yerine Cloudflare Tunnel; staging-api. ve status. alt alan adları kaldırıldı.
- **Devam notu (06.11.2026):** Yapılan: `cvnebakalim.com` Cloudflare Registrar'dan 560 TL'ye alındı (ad sunucuları Cloudflare'de); dokümanlardaki yer tutucular gerçek adla değiştirildi. Cloudflare'e GitHub ile giriliyor (GitHub'da authenticator 2FA açık; Cloudflare'in kendi 2FA'sı şifre doğrulama sorunu yüzünden sonraya kaldı). Zero Trust'ta `careerai-pc` tüneli oluşturuldu, token parola yöneticisinde (repoda yok); tünel bir kez bağlanıp kapatıldı; `api.cvnebakalim.com` → `http://api:8000` public hostname'i eklendi; SSL/TLS Full, Always Use HTTPS, en düşük TLS 1.2 (HSTS sistem çalışınca açılacak). Sıradaki adım: production (T-075) açılınca token'ı `infra/pc/.env.prod`'a yaz, `https://api.cvnebakalim.com/api/v1/health` ile uçtan uca dene, sonra HSTS; Cloudflare 2FA'yı yeniden dene. Açık sorular / engeller: web arayüzü (`app.`) Pages'te mi tünelde mi (Anıl); kök alan adı Cloudflare Pages'e (tanıtım/yasal sayfalar, T-070). Branch: ataberk/karar-sunucusuz

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

- **Durum:** Yapılacak
- **Tarih:** 16.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Veri Toplama
- **Bağımlılık:** T-017
- **Destek:** Burak
- **Çıktı:** resources tablosu (≥ 900 kayıt)
- **Kabul kriteri:** YouTube Data API v3 + elle küratörlük. Her yetkinlik için en az 3 kaynak (Türkçe öncelikli; seviye, süre, ücretsiz/ücretli). Haftalık link sağlık kontrolü (ölü link → pasif).

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

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Backend API
- **Bağımlılık:** T-037 (Anıl), T-046
- **Destek:** Anıl
- **Çıktı:** /admin paneli
- **Kabul kriteri:** SQLAdmin ile: kaynak ekle/düzenle, ilan kaynakları aç/kapa, scrape çalışmalarını izle, istatistikler. Sadece admin rolü.

### T-066 · İzleme ve uyarı sistemi

- **Durum:** Devam Ediyor
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-035
- **Destek:** —
- **Çıktı:** İzleme paneli + status sayfası
- **Kabul kriteri:** PC dışından uptime izleme (UptimeRobot / Better Stack ücretsiz; api.cvnebakalim.com/health/ready her 1-5 dk), Sentry (backend + web + mobil, ücretsiz katman), Prometheus + Grafana PC'de (CPU/RAM/disk/kuyruk; sadece 127.0.0.1). Uyarılar Telegram/e-posta ile ekibe.
- **Not:** 06.11.2026: karar #30 ile Uptime Kuma yerine dış izleyici (PC kapanınca içindeki izleyici de kapanır). 12.11.2026: PC tarafı hazır (`infra/monitoring/`, `monitoring` profili): Prometheus + Grafana (127.0.0.1:3000), 12 uyarı kuralı (bildirim yok, panoda görünür; karar #32); geçici bir compose projesinde denendi (tüm hedefler up, 16 pano sorgusu çalışıyor, salt okunur `careerai_monitor` rolü kullanıcı tablosunu okuyamıyor). Kalan: UptimeRobot hesabı + status sayfası, Sentry hesabı (adımlar `infra/monitoring/README.md` 2-3); production `.env.prod`'a şifreler. Sentry entegrasyon kodu Anıl (backend, web) ve Burak (mobil).
- **Devam notu (12.11.2026):** Yapılan: `infra/monitoring/` (Prometheus, Grafana panosu `grafana/dashboards/careerai.json` — üretici betik repoda yok, JSON elle düzenlenebilir —, 12 kural `prometheus/alerts.yml`, exporter'lar) + `infra/pc/compose.yml` `monitoring` profili + `deploy.sh` `setup_monitor_role`; geçici `careerai-izlemetest` projesinde denendi, pano tarayıcıda kontrol edildi. Karar #32 (bildirim yok) yazıldı. · Sıradaki adım: Ataberk UptimeRobot hesabı + `CareerAI API` monitörü + status sayfası (`infra/monitoring/README.md` 2. adım), Sentry hesabı + 3 proje (3. adım); status sayfası linki `docs/go-live.md` iletişim planına; sonra T-066 Tamamlandı ve PR (inceleyici Anıl, Burak). · Açık sorular / engeller: Karar #32 için Burak ve Anıl onayı; Sentry entegrasyon kodu Anıl/Burak'ta. · Branch: ataberk/izleme

### T-064 · Güvenlik incelemesi (OWASP Top 10)

- **Durum:** Yapılacak
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Güvenlik & KVKK
- **Bağımlılık:** T-036
- **Destek:** Anıl
- **Çıktı:** Güvenlik bulguları raporu
- **Kabul kriteri:** pip-audit, npm audit, Dependabot; Trivy ile image taraması; gitleaks ile sır taraması; CORS sadece kendi alan adları; güvenlik başlıkları (HSTS, CSP, X-Content-Type-Options).

### T-067 · Merkezi log ve log maskeleme

- **Durum:** Yapılacak
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-066
- **Destek:** —
- **Çıktı:** Log yapılandırması
- **Kabul kriteri:** JSON log + request_id; PII maskeleme filtresi (e-posta, telefon); 14 gün saklama; logrotate.

### T-068 · Yedekleme

- **Durum:** Devam Ediyor
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-035
- **Destek:** —
- **Çıktı:** Yedekleme scriptleri + zamanlayıcı
- **Kabul kriteri:** pg_dump her gün 02:00 (PC o saatte kapalıysa açılışta); 7 günlük + 4 haftalık saklama; restic ile şifreli olarak PC dışına (Backblaze B2 ücretsiz katman vb.). Zamanlayıcı Windows'ta çalışır (compose içinde yedek konteyneri veya Görev Zamanlayıcı; PR #57'deki systemd birimleri PC'de kullanılmaz). Geri yükleme testi yapıldı.
- **Devam notu (06.11.2026):** Yapılan: karar #30 ile PC'ye uyarlandı. systemd birimleri kaldırıldı; yedek `infra/pc/compose.yml`'de `backup` konteyneri (restic 0.18 + pg16 istemcisi, `infra/backup/Dockerfile`), zamanlayıcı içinde (`scheduler.sh`: 02:00, PC kapalıysa açılışta, başarısızsa 30 dk sonra tekrar). Prova ortamında dev verisiyle denendi: 6,5 MB yedek ~3 sn, kaçan yedek yeniden başlatınca alındı, güncel yedek varken tekrar alınmadı, yanlış parolada hata verdi; `restore-test.sh staging` 11 sn, 11 tablo eşleşti; shellcheck temiz. Backblaze B2 hesabı açıldı (EU Central, sınırlar $0, bucket `cvnebakalim-yedek`, anahtar `careerai-pc`; anahtarlar parola yöneticisinde). Sıradaki adım: production açılınca (T-075) anahtarları ve RESTIC_PASSWORD'ü `.env.prod`'a yaz, `make backup-init`, ilk gerçek yedek ve `restore-test.sh production`. Açık sorular / engeller: gerçek B2 deposu henüz denenmedi (sadece yerel restic deposu). PR #57, #50'nin üstüne kurulu (`infra/pc`). Branch: ataberk/t068-yedekleme

### T-070 · Tanıtım (landing) sayfası

- **Durum:** Yapılacak
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P2 · **Efor:** 6 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-022 (Anıl)
- **Destek:** Anıl
- **Çıktı:** Landing sayfası
- **Kabul kriteri:** Ürün tanıtımı, ekran görüntüleri, indirme linkleri (Windows/macOS/Android), gizlilik politikası ve KVKK linkleri, iletişim.

---

## Sprint 4

### T-071 · E2E testleri (Playwright)

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Test & QA
- **Bağımlılık:** T-053 (Anıl)
- **Destek:** Anıl
- **Çıktı:** tests/e2e
- **Kabul kriteri:** Kritik akışlar: kayıt → CV yükle → sonuç → kaynak aç → hesap sil. CI'da docker compose ile ayağa kaldırılan geçici ortama karşı gece çalışır (karar #30: ayrı staging sunucusu yok).

### T-072 · Yük testi (k6 / Locust)

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Test & QA
- **Bağımlılık:** T-057 (Burak), T-035
- **Destek:** Burak
- **Çıktı:** Yük testi raporu
- **Kabul kriteri:** 20 eşzamanlı kullanıcı, 30 dk. Hedef: API p95 < 300 ms (analiz hariç), hata oranı < %1, RAM < %85. Kuyruk birikme süresi ölçüldü; worker sayısı buna göre ayarlandı.

### T-075 · Production ortamı kurulumu

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** DevOps / Altyapı
- **Bağımlılık:** T-036, T-064
- **Destek:** —
- **Çıktı:** Production ortamı
- **Kabul kriteri:** PC'de ayrı compose projesi (`careerai-prod`, kendi volume'ları); en az yetkili DB kullanıcıları; sırlar `.env` (sadece bu PC'de, Windows kullanıcı izinleriyle korunur, repoda yok); hiçbir servis host'a port açmaz, dış erişim sadece `cloudflared`; kaynak limitleri (mem_limit), `restart: unless-stopped`. PC kapalıyken kaçan gece toplaması açılışta telafi edilir (R-18).

### T-079 · Mimari doküman ve ADR'ler

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-075
- **Destek:** Burak
- **Çıktı:** docs/architecture
- **Kabul kriteri:** Mimari kararlar (neden Ollama, neden pgvector, neden Celery) ADR olarak; deployment diyagramı.

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

- **Durum:** Yapılacak
- **Tarih:** 28.12.2026 – 03.01.2027 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-068, T-075
- **Destek:** —
- **Çıktı:** DR tatbikat raporu
- **Kabul kriteri:** Başka bir bilgisayara (ör. Burak'ın veya Anıl'ın) yedekten sıfırdan kurulum ve tünelin oraya taşınması. Hedef: RTO < 4 saat, RPO < 24 saat. Süre ölçülüp runbook'a yazıldı.

### T-088 · Operasyon runbook'u

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Operasyon / İzleme
- **Bağımlılık:** T-087
- **Destek:** Burak, Anıl
- **Çıktı:** docs/runbook
- **Kabul kriteri:** Deploy, rollback, Ollama yeniden başlatma, disk dolu, kuyruk birikmesi, veri ihlali şüphesi senaryoları için adım adım prosedür ("Operasyon & SLO" sayfası).

### T-091 · Go-live provası

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** Go-Live
- **Bağımlılık:** T-075, T-088
- **Destek:** Burak, Anıl
- **Çıktı:** Prova notu
- **Kabul kriteri:** PC'de prova projesinde (`careerai-staging`) production'ın birebir kopyasıyla deploy + rollback provası; checklist üzerinden kuru çalıştırma; sunum B planı (127.0.0.1'de yerel demo, telefondan internet paylaşımı) denendi.

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
