# Anıl — Görevler

**Alan:** Backend API, Web/Masaüstü ve Proje Yönetimi · **37 görev · 299 saat**

Bu dosya Anıl'ın görev listesidir ve görev durumlarının tek doğru kaynağıdır. Sadece Anıl (veya onun Claude'u) günceller.

**Durum nasıl güncellenir:** İlgili görevin `- **Durum:**` satırını şu değerlerden biriyle değiştirin: `Yapılacak`, `Devam Ediyor`, `Engellendi`, `Tamamlandı`. Durum değişikliği, işin kendisiyle aynı PR'da gönderilir. `Engellendi` olursa sebebini **Not** satırına yazın ve gruba haber verin.

**Devam notu:** Yarım kalan görevin altına gün sonunda "bitiriyorum" rutiniyle `- **Devam notu (tarih):** Yapılan · Sıradaki adım · Açık sorular · Branch` satırı eklenir; görev bitince silinir. Not, görevin branch'inde durur ve "başlıyorum" rutini oradan okur.

Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (başlangıç planı, referans). Tarih veya kapsam değişirse Excel değil bu dosya güncellenir.

---

## Ön Hazırlık

### T-000 · Fizibilite raporu (revize 2)

- **Durum:** Tamamlandı
- **Tarih:** 14.09.2026 – 18.10.2026 · **Öncelik:** P0 · **Efor:** 20 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** —
- **Destek:** Ataberk, Burak
- **Çıktı:** Fizibilite raporu PDF
- **Kabul kriteri:** Problem, pazar, mimari, maliyet, risk ve takvim bölümleri yazıldı; danışmana teslim edildi.
- **Not:** Rapor danışmana teslim edildi.

---

## Sprint 0

### T-001 · Kick-off toplantısı ve rol dağılımı

- **Durum:** Yapılacak
- **Tarih:** 19.10.2026 – 19.10.2026 · **Öncelik:** P0 · **Efor:** 3 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** —
- **Destek:** Ataberk, Burak
- **Çıktı:** Toplantı notu + RACI
- **Kabul kriteri:** RACI onaylandı; iletişim kanalı (Discord/WhatsApp) açıldı; haftalık toplantı günü ve danışman görüşme periyodu (2 haftada bir) belirlendi.

### T-002 · Kanban panosu kurulumu (GitHub Projects)

- **Durum:** Yapılacak
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P1 · **Efor:** 3 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** T-001
- **Destek:** —
- **Çıktı:** GitHub Projects panosu
- **Kabul kriteri:** Bu Excel'deki görevler issue olarak açıldı; etiketler (alan, öncelik, sprint), milestone'lar ve sprint görünümü hazır.

### T-003 · MVP kapsamının dondurulması (MoSCoW)

- **Durum:** Yapılacak
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** T-001
- **Destek:** Ataberk, Burak
- **Çıktı:** Kapsam dokümanı
- **Kabul kriteri:** Must/Should/Could/Won't listesi yazıldı. Karar: v1.0 = Web + Windows/macOS (Electron) + Android. iOS = v1.1. Kapsam değişikliği sadece ekip kararıyla.

### T-004 · Arayüz sözleşmelerinin yazılması (JSON şemaları)

- **Durum:** Devam Ediyor
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** T-003
- **Destek:** Ataberk, Burak
- **Çıktı:** /contracts klasörü + OpenAPI v0
- **Kabul kriteri:** Üç sözleşme: (1) ilan/yetkinlik veri formatı (Ataberk→Burak), (2) analiz sonucu JSON şeması (Burak→Anıl), (3) OpenAPI taslağı. Hepsi repoda /contracts altında; değişiklik PR ile.
- **Not:** Taslaklar contracts/ altında. Üç kişinin birlikte okuyup onaylaması gerekiyor.

### T-021 · Wireframe ve kullanıcı akışları (Figma)

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** UI / UX
- **Bağımlılık:** T-003
- **Destek:** —
- **Çıktı:** Figma linki
- **Kabul kriteri:** Ekranlar: giriş/kayıt, KVKK onayı, hedef pozisyon seçimi, CV yükleme, analiz bekleme, sonuç panosu, kaynak detayı (pop-up), geçmiş analizler, profil/ayarlar, hesap silme.
- **Not:** Figma yerine tıklanabilir HTML wireframe: `web/prototip/index.html` (10 ekran, API notları ve hata durumlarıyla). Figma'ya aktarmak isteğe bağlı.

### T-025 · Bilişim Kongresi posteri

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 04.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** Kongre / TÜBİTAK
- **Bağımlılık:** T-021, T-024 (Burak), T-018 (Burak)
- **Destek:** Ataberk, Burak
- **Çıktı:** Poster PDF (baskı formatında)
- **Kabul kriteri:** Problem, mimari diyagram, akış, arayüz prototipi ve ilk benchmark sonuçları. Danışman onayı alındı, baskıya hazır PDF teslim edildi. SON TARİH: 04.11.2026.
- **Not:** Poster hazırlandı ve gönderildi.

### T-022 · Tasarım sistemi

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** UI / UX
- **Bağımlılık:** T-021
- **Destek:** —
- **Çıktı:** Figma bileşen kütüphanesi
- **Kabul kriteri:** Renk paleti, tipografi, buton/kart/grafik bileşenleri, açık/koyu tema, erişilebilirlik (kontrast AA).
- **Not:** Figma yerine doğrudan kodda yapıldı (tek kaynak kod; Figma kütüphanesi istenirse buradan çıkarılabilir): `web/src/ui/` — renk/tipografi/boşluk değerleri (`tokens.css`), açık/koyu tema (sistem tercihi + elle seçim), buton, kart, form alanı, onay kutusu, uyarı, etiket, ilerleme çubuğu, skor halkası ve talep çubuk grafiği. AA kontrastı `npm run check:contrast` ile iki temada ölçülüyor. Canlı örnekler: `/tasarim` sayfası.

### T-023 · FastAPI proje iskeleti

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Backend API
- **Bağımlılık:** T-007 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** backend/ iskeleti
- **Kabul kriteri:** Katmanlı yapı (routers / services / repositories / schemas), pydantic-settings, yapılandırılmış JSON log, /health ve /health/ready, otomatik OpenAPI, global hata formatı.
- **Not:** 24.10.2026: Ataberk'in compose ortamıyla (PR #10) gerçek Postgres/Redis/Ollama üzerinde doğrulandı: konteynerde ve Windows'ta /health/ready 200; Redis durdurulunca 503, geri gelince 200. Windows'ta servis adresleri `localhost` değil `127.0.0.1` olmalı (IPv6 sorunu, PR #12).

---

## Sprint 1

### T-037 · Kimlik doğrulama ve yetkilendirme

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Backend API
- **Bağımlılık:** T-023, T-012 (Ataberk)
- **Destek:** —
- **Çıktı:** /auth endpoint'leri + testler
- **Kabul kriteri:** Kayıt/giriş, argon2 parola hash, JWT access (15 dk) + refresh (7 gün, rotasyonlu, DB'de hash), e-posta doğrulama, şifre sıfırlama, user/admin rolleri.
- **Not:** 28.10.2026: 17 kimlik doğrulama testi (gerçek Postgres) + 5 güvenlik testi, toplam 50 geçti. code-reviewer incelemesindeki 7 bulgunun 5'i düzeltildi, 2'si (eşzamanlı yenileme, şifremi unuttum yanıt süresi) belgelendi. Ekip: `.env`'e `ENVIRONMENT=local` gerekli.

### T-038 · CV yükleme endpoint'i

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Backend API
- **Bağımlılık:** T-023
- **Destek:** Burak
- **Çıktı:** POST /analyses
- **Kabul kriteri:** Multipart, en fazla 5 MB ve 5 sayfa, MIME + magic byte kontrolü (sadece PDF). Dosya diske yazılmaz; bellekten kuyruğa aktarılır; SHA-256 hash kaydedilir.
- **Not:** 24.10.2026: doğrulamalar, SHA-256 ve diske yazmama (testle kanıtlı) tamam. Kuyruk şimdilik örnek sonuç döndüren geçici sınıf; gerçek kuyruk T-039. Kimlik doğrulama T-037.

### T-026 · Poster baskı kontrolü ve teslim alma

- **Durum:** Yapılacak
- **Tarih:** 05.11.2026 – 05.11.2026 · **Öncelik:** P0 · **Efor:** 2 saat · **Alan:** Kongre / TÜBİTAK
- **Bağımlılık:** T-025
- **Destek:** —
- **Çıktı:** Basılı poster
- **Kabul kriteri:** Baskı provası renk/çözünürlük kontrolü; üniversiteden teslim alındı.

### T-027 · Kongre sunumu ve canlı demo

- **Durum:** Yapılacak
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Kongre / TÜBİTAK
- **Bağımlılık:** T-026
- **Destek:** Ataberk, Burak
- **Çıktı:** Demo videosu + sunum
- **Kabul kriteri:** Posterin yerleştirilmesi; 3 dakikalık anlatım provası (herkes sunabilmeli); yedek olarak 2 dk demo videosu.

### T-039 · Asenkron analiz işi (Celery + Redis)

- **Durum:** Tamamlandı
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 14 saat · **Alan:** Backend API
- **Bağımlılık:** T-038
- **Destek:** Burak
- **Çıktı:** Kuyruk altyapısı
- **Kabul kriteri:** POST /analyses → 202 + analysis_id; durum: queued/processing/done/failed; ilerleme SSE veya polling ile; görev zaman aşımı 180 sn; otomatik 1 tekrar deneme.
- **Not:** 05.11.2026: Celery `analysis` kuyruğu (`app/worker/`), CV baytları kalıcılığı kapalı ayrı Redis'te (`CV_REDIS_URL`, 1 saat), mesajda sadece kimlik. Soft 180 sn, geçici hatada 1 tekrar. `POST /analyses` artık giriş ve saatlik sınır istiyor, kayıt PostgreSQL'de; ilerleme `GET /analyses/{id}` ile yoklama (SSE yok). Askıda kalan analiz 65 dk sonra ilk yoklamada `failed` olur. Gerçek akış T-057'de `app/services/analyzer.py`'ye bağlanır; local/test dışında o zamana kadar analiz `failed` olur. Yetkinlik listeleri T-048'de. Docker'da gerçek API, Linux işçisi, PostgreSQL ve iki Redis ile denendi. Ataberk: compose ve staging'e CV Redis'i (`--save "" --appendonly no`, `maxmemory`, `noeviction`), `.env.example`'a `CV_REDIS_URL`, analiz işçisi servisi.

### T-040 · Web arayüzü altyapısı (Electron ile ortak)

- **Durum:** Tamamlandı
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-023, T-022
- **Destek:** —
- **Çıktı:** web/ iskeleti
- **Kabul kriteri:** React + Vite + TypeScript, TanStack Query, React Router; OpenAPI'den otomatik TS istemci (openapi-typescript); ortam değişkenleri.
- **Not:** Vite 6 + React 18 + TS (strict), React Router 6, TanStack Query 5, openapi-fetch + openapi-typescript (`npm run gen:api`), `VITE_API_URL`. Sayfalar yer tutucu; `/durum` backend sağlığını tipli istemciyle gösterir. CORS için #12 gerekli (127.0.0.1:5173).

---

## Sprint 2

### T-048 · Analiz sonuç ve katalog endpoint'leri

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Backend API
- **Bağımlılık:** T-039
- **Destek:** —
- **Çıktı:** Endpoint'ler + testler
- **Kabul kriteri:** GET /analyses, /analyses/{id}, DELETE /analyses/{id}; GET /roles, /roles/{slug}/skills, /skills/{slug}/resources. Kullanıcı sadece kendi analizini görebilir (IDOR testi).
- **Not:** 06.11.2026: `GET /analyses` (`limit`/`offset`, `{items, total}`, askıdakiler `failed` olur), `GET /analyses/{id}` artık yetkinlikleri ve önerilen kaynakları da döner (ölü linkler gösterilmez, `priority` sıra numarası), `DELETE /analyses/{id}` (soft delete, 30 günde kalıcı silinir). Katalog uçları giriş istemez, 5 dk önbelleklenebilir. Başkasının analizi GET/DELETE'te 404 (testli). Sözleşmedeki `/skills?q=` kabul kriterinde yok, yapılmadı. İşçi henüz `analysis_skills`/`analysis_recommendations` yazmıyor: gerçek akışta listeler T-057'ye (Burak) kadar boş.

### T-051 · Giriş, kayıt, şifre sıfırlama ve KVKK onay ekranları

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-040, T-037
- **Destek:** —
- **Çıktı:** Auth ekranları
- **Kabul kriteri:** Form doğrulama, hata mesajları, token yenileme (otomatik), KVKK/açık rıza onay kutuları zorunlu.
- **Not:** Ekranlar: giriş, kayıt (3 zorunlu onay), şifremi unuttum, şifre sıfırlama, e-posta doğrulama; korumalı sayfalar girişe yönlendirir (`?sonra=`). Token otomatik yenilenir (`web/src/auth/session.ts`: süresi bitmeden ve 401 gelince, tek seferde). Gerçek backend (#24) ile uçtan uca denendi. Onay metni sürümü şimdilik `2026-10-taslak`; metinler T-065 ile kesinleşince değişecek.

### T-052 · CV yükleme ve analiz bekleme ekranı

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-040, T-039
- **Destek:** —
- **Çıktı:** Yükleme ekranı
- **Kabul kriteri:** Sürükle-bırak, dosya kontrolü, hedef pozisyon seçimi, ilerleme durumu (kuyrukta / analiz ediliyor), zaman aşımında anlamlı mesaj.
- **Not:** 06.11.2026: `/yukle` (pozisyon seçimi, profildeki hedef varsayılan; az ilan uyarısı; sürükle-bırak veya dosya seç; istemcide boyut + `%PDF-` kontrolü; 413/415/422/429/503 için Türkçe mesaj, `Retry-After` ile kalan süre; 60 sn yükleme zaman aşımı) ve `/analiz/:id` (3 sn'de bir yoklama; Sırada → Analiz ediliyor → Tamamlandı; 7 dk'yı geçince "uzun sürüyor" uyarısı; hata koduna göre ipucu ve "Tekrar dene"; bitince skor özeti, sonuç panosu T-053). Gerçek API + Celery işçisi + ayrı CV Redis ile uçtan uca denendi. SSE (`/analyses/{id}/events`) yok, yoklama kullanılıyor.

### T-049 · Profil ve KVKK endpoint'leri

- **Durum:** Tamamlandı
- **Tarih:** 23.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Backend API
- **Bağımlılık:** T-037
- **Destek:** —
- **Çıktı:** /users/me endpoint'leri
- **Kabul kriteri:** Profil güncelleme, hedef pozisyon; rıza kaydı (sürümlü); verilerimi indir (JSON); hesabımı sil (anında anonimleştirme, 30 gün içinde kalıcı silme).
- **Not:** 29.10.2026: `GET/PATCH /users/me` (hedef pozisyon dahil), `GET/POST /users/me/consents` (sürümlü, eski sürüm silinmez), `GET /users/me/export` (profil, onaylar, oturumlar, analizler, işlem kayıtları), `DELETE /users/me` (şifre tekrar istenir; e-posta/ad/şifre hemen anonimleşir, oturumlar kapanır) ve `scripts/purge_deleted_users.py` (30 günü geçen hesap ve analizleri kalıcı siler; Celery beat T-039'a bağlanana kadar cron). 04.11.2026: `DELETE /users/me/consents/acik_riza` eklendi (#33'teki `withdrawn_at` ile; kayıt silinmez, denetim kaydına yazılır, aynı sürüm yeniden onaylanabilir). **T-048'e bağlı:** geçerli açık rıza yoksa yeni analiz başlatılmamalı (açık rıza metni taslağı, branch `anil/kvkk-metinleri`; danışman kararına göre).

### T-053 · Sonuç panosu

- **Durum:** Tamamlandı
- **Tarih:** 23.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-052, T-048
- **Destek:** —
- **Çıktı:** Sonuç ekranı
- **Kabul kriteri:** Uyum skoru göstergesi; mevcut / eksik yetkinlik grafiği; "150 ilanın %75'i" ifadeleri; kaynak kartları; pop-up detay; geri bildirim (1-5 yıldız); geçmiş analizler.
- **Not:** 06.11.2026: `/analiz/:id` bitince pano: skor halkası, mevcut yetkinlik etiketleri (taksonomide olmayanlar "tahmini"), eksiklerin talep çubukları, "150 ilanın %75'i" (Türkçe ek sayıya göre), öncelik sırasıyla kaynak kartları ve `<dialog>` detay, 1-5 yıldız + yorum (`POST /analyses/{id}/feedback`, tekrar gönderilirse güncellenir; `GET` yanıtında `feedback` API eki), ilan kaynağı + ESCO atfı (`scraper/kaynak-uygunluk.md` kural 7). `/gecmis`: 20'şer liste, aç / tekrar dene / onaylı silme. DB'den gelen kaynak linkleri sadece http(s). Gerçek akışta yetkinlik listeleri T-057'ye (Burak) kadar boş.

---

## Sprint 3

### T-050 · Rate limit ve hata yönetimi

- **Durum:** Tamamlandı
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Backend API
- **Bağımlılık:** T-037
- **Destek:** —
- **Çıktı:** Middleware
- **Kabul kriteri:** Redis tabanlı sınır: analiz 5/saat/kullanıcı, giriş 10/dk/IP, genel 100/dk. RFC 7807 hata formatı; 429 için Retry-After başlığı.
- **Not:** 29.10.2026: `app/core/rate_limit.py` (Redis sabit pencere, fail-open, IP özetli anahtar) ve `app/api/rate_limits.py`. Genel 100/dk/IP ve giriş-kayıt-sıfırlama 10/dk/IP uçlara bağlı; analiz 5/saat/kullanıcı (`AnalysesRateLimit`) hazır, analiz oluşturma ucu kimlik doğrulamaya bağlanınca (#9, T-048) eklenecek. Production'da `FORWARDED_ALLOW_IPS` (Caddy) şart (T-075, Ataberk).

### T-059 · Electron masaüstü uygulaması

- **Durum:** Devam Ediyor
- **Tarih:** 30.11.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 14 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-053
- **Destek:** —
- **Çıktı:** Kurulum dosyaları
- **Kabul kriteri:** Web arayüzünü sarmalar; contextIsolation açık, nodeIntegration kapalı; electron-builder ile Windows (NSIS) ve macOS (dmg); electron-updater + GitHub Releases ile otomatik güncelleme.
- **Devam notu (13.11.2026):** Yapılan: `web/desktop/` (Electron 44, app://careerai protokolü, güvenli webPreferences, CSP, dış bağlantılar sistem tarayıcısında, izinler kapalı, electron-updater); Windows NSIS kurulum dosyası üretildi ve paketli uygulama `--smoke` ile denendi. Simge (`web/desktop/resources/icon.png`) ve backend varsayılan `CORS_ORIGINS`'e `app://careerai` eklendi (testli). · Sıradaki adım: macOS dmg'yi bir Mac'te üretmek; güncellemenin çalışması için repo/yayın yeri kararı (özel repo token'sız indirilemez); production `.env.prod`'da `CORS_ORIGINS`'e `app://careerai` (Ataberk). · Açık sorular / engeller: Mac erişimi; kod imzalama yok (uyarılar README'de). · Branch: anil/electron-cors-simge

### T-065 · KVKK aydınlatma metni, açık rıza, gizlilik politikası, kullanım koşulları

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Güvenlik & KVKK
- **Bağımlılık:** T-030 (Burak)
- **Destek:** Burak
- **Çıktı:** Yasal metinler (web sayfası)
- **Kabul kriteri:** Danışman/hukuk birimi kontrolü; uygulama içi onay; consents tablosuna sürüm kaydı; gizlilik politikası URL'si (mağazalar için zorunlu); VERBİS yükümlülüğü değerlendirildi.

### T-069 · API entegrasyon testleri

- **Durum:** Tamamlandı
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Test & QA
- **Bağımlılık:** T-048, T-049
- **Destek:** —
- **Çıktı:** tests/api
- **Kabul kriteri:** pytest + httpx + testcontainers (gerçek Postgres/Redis); auth, yükleme, analiz, silme, yetki (IDOR) akışları. Kapsama ≥ %70.
- **Not:** 10.11.2026: testler `backend/tests/` altında (ayrı `tests/api` açılmadı). `TEST_DATABASE_URL` / `TEST_REDIS_URL` yoksa testcontainers geçici PostgreSQL ve Redis başlatır; uçtan uca senaryo ve gerçek Redis testleri eklendi; kapsam eşiği %70 `pyproject.toml`'da (ölçülen %97,5). IDOR: her analiz ucu için başkasının analizi 404.

---

## Sprint 4

### T-076 · Google Play kapalı test (14 gün, 12+ testçi)

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 04.01.2027 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Mobil
- **Bağımlılık:** T-062 (Burak), T-065
- **Destek:** Burak
- **Çıktı:** Kapalı test kanalı
- **Kabul kriteri:** Play Console hesabı; veri güvenliği formu, gizlilik politikası URL'si, içerik derecelendirmesi; AAB yükleme. Yeni kişisel geliştirici hesaplarında üretime çıkmak için en az 12 testçiyle 14 gün kesintisiz kapalı test ZORUNLU → en geç 21.12.2026'da başlamalı.

### T-078 · Beta / UAT planı ve beta kullanıcı toplama

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Test & QA
- **Bağımlılık:** T-053
- **Destek:** Ataberk, Burak
- **Çıktı:** UAT planı
- **Kabul kriteri:** 20-30 öğrenci beta kullanıcısı; test senaryoları; geri bildirim formu + SUS anketi; hata bildirme kanalı.

### T-080 · API dokümantasyonu ve README'ler

- **Durum:** Tamamlandı
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P1 · **Efor:** 4 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-048
- **Destek:** —
- **Çıktı:** docs/api + README
- **Kabul kriteri:** OpenAPI açıklamaları ve örnekler; her modül için README (kurulum, çalıştırma, test).
- **Not:** 11.11.2026: `docs/api/README.md` (kimlik doğrulama, örnek akış, CV kuralları, hata biçimi, sınırlar) ve `docs/api/openapi.json` (`backend/scripts/export_openapi.py` üretir, web kopyasıyla birlikte; eskiyse `tests/test_openapi.py` kırılır). Her uçta özet + açıklama, her JSON gövdesinde örnek, tüm 4xx/5xx yanıtlarında RFC 7807 `Problem` şeması, health dışı her uçta 429 belgelendi. README'ler: backend (endpoint tablosu güncellendi) ve web; `scraper/`, `ai/`, `infra/`, `mobile/` README'leri sahiplerinde.

---

## Sprint 5

### T-082 · Beta / UAT yürütme

- **Durum:** Yapılacak
- **Tarih:** 28.12.2026 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Test & QA
- **Bağımlılık:** T-078, T-075 (Ataberk)
- **Destek:** Ataberk, Burak
- **Çıktı:** Beta raporu
- **Kabul kriteri:** 2 hafta; günlük hata triyajı. Çıkış kriteri: kritik (P0) hata = 0, SUS ≥ 70, analiz başarı oranı ≥ %95.

### T-084 · Beta hata düzeltmeleri — Backend ve istemciler

- **Durum:** Yapılacak
- **Tarih:** 28.12.2026 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** Backend API
- **Bağımlılık:** T-082
- **Destek:** —
- **Çıktı:** Kapanmış issue'lar
- **Kabul kriteri:** API, web, Electron ve mobil hataları; regresyon testi.

### T-089 · Masaüstü dağıtım

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P1 · **Efor:** 4 saat · **Alan:** Web / Masaüstü
- **Bağımlılık:** T-059
- **Destek:** —
- **Çıktı:** Release v1.0.0-rc
- **Kabul kriteri:** Windows kurulum dosyası ve macOS dmg; imzasız kurulum uyarıları (SmartScreen/Gatekeeper) için kullanıcı rehberi; indirme sayfası.

### T-090 · Mağaza kayıtları

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P1 · **Efor:** 5 saat · **Alan:** Mobil
- **Bağımlılık:** T-076
- **Destek:** Burak
- **Çıktı:** Play Store kaydı
- **Kabul kriteri:** Uygulama ikonu, ekran görüntüleri, kısa/uzun açıklama (TR+EN), kategori, iletişim e-postası, içerik derecelendirmesi.

---

## Sprint 6

### T-092 · Kod dondurma ve v1.0.0 sürüm adayı

- **Durum:** Yapılacak
- **Tarih:** 13.01.2027 – 15.01.2027 · **Öncelik:** P0 · **Efor:** 2 saat · **Alan:** Go-Live
- **Bağımlılık:** T-082
- **Destek:** Ataberk, Burak
- **Çıktı:** v1.0.0 etiketi
- **Kabul kriteri:** Sadece kritik hata düzeltmesi; CHANGELOG; sürüm etiketi v1.0.0; release notları.

### T-093 · Go-Live kontrol listesinin tamamlanması

- **Durum:** Yapılacak
- **Tarih:** 13.01.2027 – 15.01.2027 · **Öncelik:** P0 · **Efor:** 4 saat · **Alan:** Go-Live
- **Bağımlılık:** T-092
- **Destek:** Ataberk, Burak
- **Çıktı:** İmzalı checklist + Go/No-Go kararı
- **Kabul kriteri:** "Go-Live Kontrol Listesi" sayfasındaki tüm maddeler Tamamlandı; eksik madde varsa Go/No-Go toplantısında karar.

### T-095 · Play Store üretim yayını

- **Durum:** Yapılacak
- **Tarih:** 18.01.2027 – 18.01.2027 · **Öncelik:** P0 · **Efor:** 2 saat · **Alan:** Go-Live
- **Bağımlılık:** T-076, T-094 (Ataberk)
- **Destek:** Burak
- **Çıktı:** Play Store'da yayında
- **Kabul kriteri:** Kapalı testten üretime yükseltme (aşamalı yayın %20 → %100); inceleme süresi için tampon bırakıldı.

### T-099 · Final sunumu ve canlı demo

- **Durum:** Yapılacak
- **Tarih:** 25.01.2027 – 31.01.2027 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-098 (Burak)
- **Destek:** Ataberk, Burak
- **Çıktı:** Sunum dosyası
- **Kabul kriteri:** Jüri sunumu; canlı demo + yedek video; herkesin kendi modülünü anlattığı bölümler.
- **Not:** Tarih bölüm takvimine göre güncellenmeli.

### T-100 · Proje retrospektifi ve v1.1 yol haritası

- **Durum:** Yapılacak
- **Tarih:** 25.01.2027 – 31.01.2027 · **Öncelik:** P2 · **Efor:** 2 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** T-097 (Ataberk)
- **Destek:** Ataberk, Burak
- **Çıktı:** Yol haritası
- **Kabul kriteri:** Ne iyi gitti / ne kötü gitti; v1.1 planı (iOS, LinkedIn PDF içe aktarma, mülakat soruları, öğrenme ilerleme takibi).

---

## Sürekli

### T-005 · Sprint törenleri (tüm dönem)

- **Durum:** Yapılacak
- **Tarih:** 19.10.2026 – 31.01.2027 · **Öncelik:** P1 · **Efor:** 14 saat · **Alan:** Proje Yönetimi
- **Bağımlılık:** T-001
- **Destek:** Ataberk, Burak
- **Çıktı:** Sprint notları
- **Kabul kriteri:** Her sprint başında planlama (1 sa), sonunda demo + retro (1 sa); haftalık 15 dk durum toplantısı. Notlar wiki'de.
