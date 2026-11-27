# Canlıya Çıkış ve Operasyon

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

- **Go / No-Go toplantısı:** 15.01.2027
- **Canlıya çıkış (v1.0.0):** 18.01.2027
- **Hypercare (yakın izleme):** 18–31.01.2027, her gün bir kişi nöbetçi
- **Barındırma:** production Ataberk'in PC'sinde Docker Compose ile çalışır, alan adına Cloudflare Tunnel ile bağlanır (karar #30). Sistem PC açıkken erişilebilir; hocalara sunum bu PC üzerinden alan adıyla yapılır.

**Kural:** Kritik (★) maddelerin tamamı tamamlanmadan canlıya çıkılmaz. Tamamlanan maddeyi `[x]` olarak işaretleyin (PR ile).

## Kontrol listesi

### Altyapı

- [ ] **1.** ★ Production PC'si hazırlandı (Windows güncel, disk şifreli (BitLocker; karar #31 ile canlıya çıkıştan hemen önce açılır, kurtarma anahtarı PC dışında), güçlü yerel hesap şifresi, uyku/hazırda bekletme kapalı, Windows Güvenlik Duvarı açık; Docker Desktop elle açılır, karar #31) — _Doğrulama:_ `infra/pc/README.md` kontrol listesi — _Sorumlu:_ Ataberk
- [ ] **2.** ★ Postgres, Redis ve Ollama portları ağdan erişilemez; PC'de gelen port açılmadı (modemde port yönlendirme yok) — _Doğrulama:_ production compose'da `ports:` yok (`docker compose config`); aynı ağdaki başka cihazdan nmap: hepsi kapalı — _Sorumlu:_ Ataberk
- [ ] **3.** ★ HTTPS aktif (Cloudflare: Always Use HTTPS, HSTS, en düşük TLS 1.2) — _Doğrulama:_ SSL Labs testi A veya üstü — _Sorumlu:_ Ataberk
- [ ] **4.** DNS Cloudflare'de; app. ve api. alt alan adları tünele bağlı — _Doğrulama:_ dig api.cvnebakalim.com; `cloudflared tunnel info` — _Sorumlu:_ Ataberk
- [ ] **5.** Container bellek limitleri ve yeniden başlatma politikası (unless-stopped) tanımlı — _Doğrulama:_ docker compose config — _Sorumlu:_ Ataberk
- [ ] **6.** C: diskinde en az 40 GB boş (06.11.2026: ~71 GB), Docker log rotasyonu (json-file max-size) aktif — _Doğrulama:_ `docker system df`; `Get-PSDrive C` — _Sorumlu:_ Ataberk
- [ ] **51.** ★ Sunum düzeni hazır: PC prize takılı, mümkünse kablolu internet, sunum haftası Windows güncellemeleri ertelendi; B planı (aynı sürüm 127.0.0.1'de yerel demo + telefondan internet paylaşımı) denendi — _Doğrulama:_ Prova kaydı — _Sorumlu:_ Ataberk
- [ ] **52.** Tanıtım ve yasal sayfalar Cloudflare Pages'te; PC kapalıyken de açılıyor — _Doğrulama:_ PC kapalıyken URL'ler — _Sorumlu:_ Anıl

### Güvenlik

- [ ] **7.** ★ Repoda sır yok (gitleaks temiz), production sırları güçlü ve yeni üretilmiş — _Doğrulama:_ gitleaks raporu — _Sorumlu:_ Ataberk
- [ ] **8.** ★ Kritik/yüksek seviye bağımlılık açığı yok — _Doğrulama:_ pip-audit, npm audit, Trivy raporları — _Sorumlu:_ Ataberk
- [ ] **9.** ★ IDOR testi: kullanıcı başkasının analizine erişemiyor (404/403) — _Doğrulama:_ Otomatik test + manuel deneme — _Sorumlu:_ Anıl
- [ ] **10.** ★ Dosya yükleme sınırları: sadece PDF, ≤ 5 MB, ≤ 5 sayfa, magic byte kontrolü — _Doğrulama:_ Kötü dosya test seti — _Sorumlu:_ Anıl
- [ ] **11.** Rate limit aktif (giriş, kayıt, analiz) — _Doğrulama:_ Script ile 429 alındığı doğrulandı — _Sorumlu:_ Anıl
- [ ] **12.** CORS sadece kendi alan adlarına açık; güvenlik başlıkları mevcut — _Doğrulama:_ securityheaders.com — _Sorumlu:_ Anıl
- [ ] **13.** Prompt injection test CV'leri sistemi yönlendiremiyor — _Doğrulama:_ 5 saldırı CV'si ile test — _Sorumlu:_ Burak
- [ ] **14.** Admin paneli sadece admin rolüne açık, varsayılan şifre yok — _Doğrulama:_ Normal kullanıcı ile 403 testi — _Sorumlu:_ Ataberk

### Veri tabanı

- [ ] **15.** ★ Tüm migration'lar production'a uygulandı, downgrade test edildi — _Doğrulama:_ alembic current = head — _Sorumlu:_ Ataberk
- [ ] **16.** ★ Seed verisi: ≥ 300 yetkinlik, ≥ 10 pozisyon, ≥ 900 eğitim kaynağı, ≥ 2.000 ilan — _Doğrulama:_ Sayım sorguları — _Sorumlu:_ Ataberk
- [ ] **17.** En az yetkili DB kullanıcısı (uygulama kullanıcısı tablo silemez) — _Doğrulama:_ \du ve yetki kontrolü — _Sorumlu:_ Ataberk
- [ ] **18.** Yavaş sorgu yok (p95 < 50 ms), indeksler mevcut — _Doğrulama:_ pg_stat_statements — _Sorumlu:_ Ataberk

### Yedekleme

- [ ] **19.** ★ Günlük otomatik yedek çalışıyor ve PC dışında şifreli duruyor — _Doğrulama:_ restic snapshots listesi — _Sorumlu:_ Ataberk
- [ ] ~~**20.** ★ Yedekten başka bir bilgisayara geri yükleme test edildi (RTO < 4 saat) — _Doğrulama:_ DR tatbikat raporu — _Sorumlu:_ Ataberk~~ — **İptal (karar #37):** başka bilgisayarda tatbikat yapılmayacak; prosedür (`docs/runbook/felaket-kurtarma.md`) ve production PC'sindeki geri yükleme testi yeterli sayıldı

### İzleme

- [ ] **21.** ★ Production PC'sinde Grafana panosu açık, 12 uyarı kuralı yüklü; dış prob (`api.cvnebakalim.com`) çalışıyor. PC dışı izleyici ve bildirim yok (karar #32) — _Doğrulama:_ Tünel durdurulunca 5 dk içinde panoda `DisErisimYok` görüldü — _Sorumlu:_ Ataberk
- ~~**22.** Sentry backend, web ve mobilde aktif~~ — Karar #32 ile kaldırıldı; hatalar API logları (T-067) ve Grafana'daki analiz hata oranıyla izlenir.
- [ ] **23.** Grafana panosu: CPU, RAM, disk, kuyruk derinliği, analiz süresi — _Doğrulama:_ Pano linki — _Sorumlu:_ Ataberk
- [ ] **24.** Loglarda kişisel veri (e-posta, telefon, CV metni) yok — _Doğrulama:_ Log örneklemesi — _Sorumlu:_ Ataberk

### Uygulama

- [ ] **25.** ★ Uçtan uca akış production'da çalışıyor (kayıt → CV → sonuç → kaynak → hesap silme) — _Doğrulama:_ Smoke test kaydı — _Sorumlu:_ Burak
- [ ] **26.** ★ E-posta doğrulama ve şifre sıfırlama e-postaları ulaşıyor (spam değil) — _Doğrulama:_ Gmail/Outlook testi — _Sorumlu:_ Anıl
- [ ] **27.** Hata ekranları anlaşılır (zaman aşımı, bozuk PDF, kuyruk dolu) — _Doğrulama:_ Manuel test — _Sorumlu:_ Anıl
- [ ] **28.** Electron kurulum dosyaları Windows 10/11 ve macOS'ta test edildi — _Doğrulama:_ Temiz makinede kurulum — _Sorumlu:_ Anıl
- [ ] **29.** Otomatik güncelleme (electron-updater) çalışıyor — _Doğrulama:_ v1.0.0 → v1.0.1 test — _Sorumlu:_ Anıl

### AI

- [ ] **30.** ★ Değerlendirme hedefleri tutuyor: F1 ≥ 0,80, öneri puanı ≥ 4,0 — _Doğrulama:_ eval/report.md — _Sorumlu:_ Burak
- [ ] **31.** ★ Önerilen tüm linkler DB'den geliyor (uydurma link yok) — _Doğrulama:_ Golden testler + 100 analiz örneklemi — _Sorumlu:_ Burak
- [ ] **32.** Analiz süresi p95 < 120 sn; LLM düşerse sözlük tabanlı sonuç dönüyor — _Doğrulama:_ Yük testi + Ollama durdurma testi — _Sorumlu:_ Burak
- [ ] **33.** Model ve prompt sürümü sabitlendi (v1.0.0 ile etiketli) — _Doğrulama:_ Config kontrolü — _Sorumlu:_ Burak

### Veri

- [ ] **34.** Gece toplama işi PC'nin açık olduğu son 7 takvim gününde hatasız çalıştı; PC'nin kapalı kaldığı gecelerin toplaması açılışta telafi edildi (karar #39) — _Doğrulama:_ scrape_runs tablosu — _Sorumlu:_ Ataberk
- [ ] **35.** Ölü kaynak linki oranı < %2 — _Doğrulama:_ Link kontrol raporu — _Sorumlu:_ Ataberk

### KVKK / Hukuki

- [ ] **36.** ★ Aydınlatma metni, açık rıza, gizlilik politikası ve kullanım koşulları yayında — _Doğrulama:_ Web URL'leri açılıyor — _Sorumlu:_ Burak
- [ ] **37.** ★ CV dosyası ve ham metni hiçbir yerde saklanmıyor (DB, disk, log, yedek) — _Doğrulama:_ Kod incelemesi + disk taraması — _Sorumlu:_ Burak
- [ ] **38.** ★ Hesap silme ve veri dışa aktarma çalışıyor — _Doğrulama:_ Test hesabı ile — _Sorumlu:_ Anıl
- [ ] **39.** Veri ihlali müdahale prosedürü (72 saat içinde KVK Kurulu'na bildirim) runbook'ta — _Doğrulama:_ Runbook kontrolü — _Sorumlu:_ Burak
- [ ] **40.** Toplanan ilan kaynaklarının kullanım koşulları kontrol edildi — _Doğrulama:_ Kaynak uygunluk tablosu — _Sorumlu:_ Ataberk

### Mağaza

- [ ] **41.** ★ Play Store kapalı testi 12+ testçi ile 14 gün tamamlandı ve üretim erişimi alındı — _Doğrulama:_ Play Console — _Sorumlu:_ Anıl
- [ ] **42.** Veri güvenliği formu, içerik derecelendirmesi, gizlilik URL'si dolduruldu — _Doğrulama:_ Play Console — _Sorumlu:_ Anıl
- [ ] **43.** Ekran görüntüleri, ikon, açıklamalar (TR/EN) hazır — _Doğrulama:_ Mağaza önizlemesi — _Sorumlu:_ Anıl

### Dokümantasyon

- [ ] **44.** Runbook (deploy, rollback, olaylar) güncel ve herkes okudu — _Doğrulama:_ Ekip onayı — _Sorumlu:_ Ataberk
- [ ] **45.** README, API dokümanı, mimari doküman ve model kartı güncel — _Doğrulama:_ Repo — _Sorumlu:_ Anıl
- [ ] **46.** Kullanıcı rehberi / SSS (imzasız kurulum uyarıları dahil) — _Doğrulama:_ Landing sayfası — _Sorumlu:_ Anıl

### Destek

- [ ] **47.** Destek e-postası ve hata bildirme formu aktif — _Doğrulama:_ Test mesajı — _Sorumlu:_ Anıl
- [ ] **48.** Hypercare nöbet çizelgesi (18-31 Ocak) hazır — _Doğrulama:_ Takvim — _Sorumlu:_ Ataberk

### Rollback

- [ ] **49.** ★ Rollback planı test edildi: önceki imaj etiketi + DB yedeği ile 15 dk içinde dönüş — _Doğrulama:_ PC'de prova projesiyle (`careerai-staging`) — _Sorumlu:_ Ataberk
- [ ] **50.** Go/No-Go toplantısı yapıldı, karar ve katılımcılar kayıtlı — _Doğrulama:_ Toplantı notu — _Sorumlu:_ Anıl

### Ön kontrol (18.11.2026, Ataberk)

Canlıya çıkıştan iki ay önce, sorumlusu Ataberk olan ve production'da bugün ölçülebilen maddeler. Kutular **işaretlenmedi**: işaretleme Go/No-Go öncesi son kontrolde yapılır. Amaç eksikleri erken görmek.

| Madde | Bugünkü durum | Kanıt / eksik |
|---|---|---|
| 2 ★ Port açık değil | Uygun | `docker compose config`: hiçbir serviste `ports:` yok; tek istisna Grafana `127.0.0.1:3000`. Ağdan nmap henüz yapılmadı |
| 5 Bellek limiti, restart | Uygun | 15 servisin hepsinde `mem_limit` ve `restart: unless-stopped` |
| 6 Disk ≥ 40 GB boş | **Uygun** | 20.11.2026: C: **67,5 GB** boş (önce 49,6 GB). Kullanılmayan imajlar (eski Ollama 0.40.10 dahil), build önbelleği, trivy önbelleği ve sahipsiz birimler silindi; Docker'ın sanal diski `fstrim` + `Optimize-VHD` ile 43,6 GB'tan 22,8 GB'a küçültüldü (yönetici PowerShell, Docker kapalıyken; production ~10 dk kapalı kaldı). Docker içinde silinen yer C:'ye kendiliğinden dönmez, sanal disk ayrıca küçültülmelidir |
| 15 ★ Migration'lar | Uygun | `alembic_version` = 0004 (head). Downgrade gerçek veriyle denendi (18.11.2026, `make backup-migration-test`): production yedeğinin kopyasında 0004 → 0003 → 0004 satır sayıları aynı; base'e kadar tek tek geri alma ve head'e dönüş 26 sn. Not: uygulama rolü `alembic_version`'ı okuyamaz (en az yetki), kontrol sahip rolle yapılır |
| 16 ★ Seed verisi | **Uygun** | 20.11.2026: yetkinlik 374 (≥ 300 ✓), pozisyon 12 (≥ 10 ✓), canlı kaynak **1.565** (≥ 900 ✓; 469 Türkçe, 1.096 İngilizce; T-046'nın 1.039 YouTube videosu `resources-import` ile yüklendi, `.env.prod`'a `YOUTUBE_API_KEY` eklendi), aktif ilan **2.213** (≥ 2.000 ✓). 3'ten az kaynağı kalan 4 yetkinlik: gradle, ibm-cloud, turkish, wandb (günlük YouTube araması 06:00'da sürüyor). Vektörler: 374 yetkinlik ve 2.213 aktif ilanın hepsinde `embedding` dolu (20.11.2026, `infra/pc/deploy.md` "7. Vektörler"; AI işçisi gelene kadar yeni ilanlar için elle tekrarlanır) |
| 17 En az yetkili DB kullanıcısı | Uygun | `careerai_app`: süper kullanıcı değil, hiçbir tablonun sahibi değil, `TRUNCATE` yok; `careerai_monitor` salt okunur (T-075) |
| 18 Yavaş sorgu yok | Ölçüm hazır | HNSW indeksleri var. `pg_stat_statements` açıldı (18.11.2026: `compose.yml` + `deploy.sh setup_stats`); bir sonraki deploy'dan sonra birkaç gün kullanımın ardından `make prod-slow-queries` ile ölçülecek (≈p95 = ortalama + 1,645σ; kesin p95 Loki'deki istek süresinden) |
| 19 ★ Günlük yedek, PC dışında şifreli | Uygun | restic → B2, son yedek 18.11.2026 00:33; haftalık depo kontrolü 15.11.2026 |
| 20 ★ Başka bilgisayara geri yükleme | **İptal (karar #37)** | Prosedür: `docs/runbook/felaket-kurtarma.md`. Production PC'sinde geri yükleme testi geçti (12 sn, 11 tablo eşleşti); başka bilgisayarda tatbikat yapılmadı (T-087) |
| 21 ★ Grafana, 12 kural, dış prob | Uygun | 12 uyarı kuralı yüklü, dış prob `api.cvnebakalim.com` `up`. Tünel durdurma testi yapılmadı |
| 24 Loglarda kişisel veri yok | Uygun (örneklem) | Son 1 saatin api ve worker-data loglarında e-posta adresi biçiminde metin yok |
| 34 Gece toplaması 7 gün hatasız | **Değil** | 12 çalışmanın 12'si başarılı, ama sadece 15.11 ve 18.11 günleri: PC kapalı kaldığı için 7 günlük kesintisiz seri yok |
| 35 Ölü link < %2 | **Uygun** | 20.11.2026, deploy sonrası işçi açılışında telafi edilen ilk kontrol: 526 link, **4 ölü = %0,8**, geri gelen 0 (`python -m collector resources-report`, worker-data içinde). YouTube videoları yüklendikten sonra 4/1.565 = %0,3 (yeni videolar yüklenirken API'den doğrulanır). Haftalık kontrol pazar 07:00; PC kapalıysa açılışta telafi edilir |
| 49 ★ Rollback 15 dk içinde | **Uygun** | 21.11.2026, prova ortamında production dökümüyle: yeni sürüm deploy + veri bozulması → önceki imaj + deploy öncesi dökümden yükleme + yetkiler = **146 sn**; satır sayıları ve API uçları doğru (`docs/runbook/operasyon.md` 2. bölüm "Prova"). Provada geri yükleme prosedüründeki yetki hatası bulunup düzeltildi |

### Ön kontrol (18.11.2026, Anıl)

Sorumlusu Anıl olan maddeler, Ataberk'in tablosuyla aynı amaçla. Kutular işaretlenmedi.

| Madde | Bugünkü durum | Kanıt / eksik |
|---|---|---|
| 9 ★ IDOR | Uygun (otomatik test) | `test_result_of_another_user_is_404`: başkasının analizine GET ve DELETE 404, listede görünmüyor, kayıt silinmiyor. `test_status_is_visible_only_to_the_owner`: durum yoklaması sadece sahibine açık. Production'da iki hesapla elle deneme yapılmadı |
| 10 ★ Dosya yükleme sınırları | Uygun (otomatik test) | `backend/app/core/uploads.py`: 5 MB, 5 sayfa. Testlerde: 5 MB'tan büyük dosya ve sınırı aşan istek gövdesi okunmadan reddediliyor; 6 sayfa reddediliyor; PDF diye gönderilen PNG/ZIP (magic byte) ve şifreli PDF 415 alıyor (`backend/tests/test_analyses_upload.py`). Kötü dosya setiyle production'da deneme yapılmadı |
| 26 ★ Doğrulama ve sıfırlama e-postaları | Ölçülmedi | Production'dan Gmail ve Outlook'a deneme gönderimi yapılmadı |
| 27 Hata ekranları | Uygun (yerel, elle) | 18.11'de e2e yığınında (`tests/e2e/ortam.sh`) web'den denendi. Her durumda Türkçe ve ne yapılacağını söyleyen mesaj çıktı: 6 MB dosya, 6 sayfa, şifreli PDF, bozuk PDF, PDF diye gönderilen PNG, kuyruk Redis'i kapalıyken 503 ("Sistem şu an yoğun… 60 saniye sonra tekrar dene", yanıt ~9 sn), saatlik sınır 429 ("… 60 dakika sonra tekrar dene"). Bulgular: reddedilen yüklemeler saatlik 5 hakkı harcıyordu (düzeltme #127); 6 sayfalık dosyada mesaj, sınırlardan hangisinin aşıldığını söylemiyor (P2). Analiz zaman aşımı: 19.11'de işçi durdurulup `ANALYSIS_STALE_AFTER_S=40` ile denendi; süre dolunca analiz `failed` (INTERNAL) oldu ve web'de "Analiz tamamlanamadı. Lütfen tekrar deneyin." ile "Tekrar dene" düğmesi çıktı. Production'da bu süre 65 dk; bekleme ekranı 7. dakikadan sonra "beklenenden uzun sürüyor" uyarısı gösteriyor |
| 28 Electron kurulumu | Kısmen | Windows: kurulum dosyası (0.1.0, 121 MB) 19.11'de geliştirme bilgisayarında sessiz kurulumla (kullanıcı kapsamı) kurulup kaldırıldı: kurulum 12 sn, kısayollar ve kayıt girdisi oluştu, kurulu uygulama `--smoke` ile açıldı, kaldırma 11 sn ve iz bırakmadı. Kaldırınca oturum klasörünün kalması bulgusu #125'te düzeltildi. Eksik: temiz Windows 10/11 makinesi ve sihirbazın elle tıklanarak denenmesi; macOS (Mac erişimi yok, CI ile derleme önerisi #141) |
| 29 Otomatik güncelleme | **Engelli** | Repo özel olduğu için Releases dosyaları token'sız indirilemiyor; yayın yeri önerisi karar #36. Karar çıkmadan v1.0.0 → v1.0.1 testi yapılamaz |
| 41 ★ Play kapalı testi | Başlamadı | 21.12.2026'da en az 12 testçiyle başlamalı (T-076); testçiler beta listesinden (`docs/uat/beta-uat-plani.md`) |
| 47 Destek e-postası, hata bildirme | Kısmen | Web ve masaüstünde "Hata bildir" bağlantısı `iletisim@cvnebakalim.com` adresine e-posta açıyor (#124). Adresin posta alıp almadığı ve gelen kutusunu kimin okuyacağı belirlenmedi |

### Kuru çalıştırma (24.11.2026, Ataberk, T-091)

Listenin tamamı production'a karşı bir kez yürütüldü. Sorumlusu Ataberk olan maddeler ölçüldü; diğerlerinde repodaki ve production'daki kanıt kontrol edildi, sahibinin ön kontrolü varsa ona atıf yapıldı. Kutular **işaretlenmedi**. ★ = kritik.

**Özet:** 50 madde (#20 ve #22 iptal, listede yok). **Uygun 18 · Kısmen 18 · Değil 8 · Ölçülemedi / henüz zamanı değil 6** (27.11: #3 ve #21 Kısmen → Uygun). Kritik maddelerden 4'ü **Değil**: #25, #30, #36 ve #41. #25 ve #30 analiz işçisinin production'da olmamasından kaynaklanıyor (T-057). #36 yasal sayfaların yayında olmamasından (#71). #41 için Play kapalı testi 21.12'de başlayacak.

| Madde | Sorumlu | Durum | Kanıt / eksik (24.11.2026) |
|---|---|---|---|
| 1 ★ PC hazırlığı | Ataberk | Kısmen | Uyku ve hazırda bekletme (prizde) kapalı, Güvenlik Duvarı üç profilde açık, son Windows güncellemesi 21.11, NVIDIA sürücüsü 621.24. BitLocker karar #31 gereği canlıdan hemen önce açılacak (durumu yönetici yetkisiyle okunur, bugün okunmadı) |
| 2 ★ Port açık değil | Ataberk | Kısmen | `docker compose config`: 15 serviste `ports:` yok, tek istisna Grafana `127.0.0.1:3000`. Aynı ağdaki başka cihazdan nmap hâlâ yapılmadı |
| 3 ★ HTTPS | Ataberk | Uygun | SSL Labs (27.11.2026, `api.cvnebakalim.com`, sonuç gizli): Cloudflare'in 4 adresinin (2 IPv4, 2 IPv6) hepsi **A+**. Protokoller: TLS 1.3 ve 1.2 açık; TLS 1.1, 1.0, SSL 3, SSL 2 kapalı. HSTS uzun süreli (`max-age=15552000; includeSubDomains`), HTTP → HTTPS 301 |
| 4 DNS, app./api. | Ataberk | Kısmen | `api.cvnebakalim.com` çözülüyor. `app.`, `www.` ve kök alan adının kaydı yok: web adresi kararı (Anıl) ve #71 bekleniyor |
| 5 Bellek limiti, restart | Ataberk | Uygun | 15 serviste `mem_limit`, `restart: unless-stopped` ve json-file log rotasyonu var |
| 6 Disk ≥ 40 GB | Ataberk | Uygun | C: 56,2 GB boş (20.11: 67,5 GB; aradaki fark deploy imajları ve vektör imajı) |
| 51 ★ Sunum düzeni, B planı | Ataberk | Kısmen | B planı 21.11'de denendi (yerel demo ~1 dk). Telefondan internet paylaşımıyla tünel denenmedi; sunum haftası Windows güncellemesi ertelemesi o hafta yapılacak |
| 52 Tanıtım/yasal sayfalar Pages'te | Anıl | Değil | Kök ve `www` için DNS kaydı yok; Pages projesi #71 birleşince açılacak (`infra/landing/README.md`) |
| 7 ★ Repoda sır yok | Ataberk | Uygun | gitleaks tüm geçmiş temiz (23.11 haftalık tarama ve 24.11 `main` push'u); GitHub secret scanning açık uyarı 0 |
| 8 ★ Kritik/yüksek açık yok | Ataberk | Uygun | 23.11 haftalık taramada pip-audit (backend, ai, scraper), npm audit (web, mobile) ve Trivy (api, worker-data, backup) yeşil. Dependabot'ta 2 orta seviye uyarı (`minimatch`: `mobile/`, `web/desktop/`), kritik/yüksek yok |
| 9 ★ IDOR | Anıl | Kısmen | Otomatik testler var (Anıl'ın ön kontrolü); production'da iki hesapla elle deneme yok |
| 10 ★ Dosya yükleme sınırları | Anıl | Kısmen | Otomatik testler var; production'da kötü dosya setiyle deneme yok |
| 11 Rate limit | Anıl | Kısmen | Kodda var, reddedilen yükleme hakkı yemiyor (#127); production'da betikle 429 doğrulaması yapılmadı |
| 12 CORS, güvenlik başlıkları | Anıl | Kısmen | API yanıtında CSP `default-src 'none'`, `X-Frame-Options: DENY`, HSTS var. Production `CORS_ORIGINS` sadece `app://careerai` (masaüstü); web adresi belli olunca eklenecek. securityheaders.com testi yapılmadı |
| 13 Prompt injection | Burak | Kısmen | Koruma ve çıktı doğrulama birleşti (#158); production'da analiz olmadığı için 5 saldırı CV'siyle deneme yapılamadı |
| 14 Admin paneli | Ataberk | Uygun | `/admin` → Cloudflare Access girişine 302 (uygulama ayrıca Access JWT'sini doğruluyor), `/docs` 404 |
| 15 ★ Migration'lar | Ataberk | Uygun | `alembic_version` = 0004 = head |
| 16 ★ Seed verisi | Ataberk | Uygun | Yetkinlik 374, pozisyon 12, canlı kaynak 1.695, aktif ilan 3.105; boş vektör 0 (24.11 `make prod-embed`) |
| 17 En az yetkili kullanıcı | Ataberk | Uygun | `careerai_app` ve `careerai_monitor`: süper kullanıcı değil, rol/DB oluşturamaz; `audit_logs`'ta silme/`TRUNCATE` yetkisi yok |
| 18 Yavaş sorgu yok | Ataberk | Ölçülemedi | `pg_stat_statements` sayaçları bugün WSL yeniden başlatılınca sıfırlandı (24.11 16:05); kayıtta sadece sağlık sorgusu var. Ölçüm için PC'nin birkaç gün yeniden başlatılmadan açık kalması ve gerçek kullanım gerekiyor |
| 19 ★ Günlük şifreli yedek | Ataberk | Uygun | restic → B2, 7 snapshot, son 24.11 15:10. PC 02:00'de kapalıysa yedek açılışta alınıyor |
| 21 ★ Grafana, 12 kural, dış prob | Ataberk | Uygun | 12 kural yüklü; iç ve dış prob `probe_success=1`. Tünel testi (27.11.2026): `cloudflared` 22:49:38'de durduruldu → alan adı 530, dış prob ~1 dk içinde 0, `DisErisimYok` 22:50:19'da beklemede, 5 dk sonra tetiklendi; iç prob 1 kaldı (yanlışlıkla `ApiHazirDegil` çıkmadı). Tünel 22:59:57'de açıldı → 7 sn'de 200, alarm 55 sn'de kapandı. Kesinti toplam ~10 dk (bilerek) |
| 23 Grafana panosu | Ataberk | Kısmen | `careerai.json` panosu yüklü (CPU, RAM, disk, kuyruk). Analiz süresi paneli analiz işçisi gelene kadar boş |
| 24 Loglarda kişisel veri yok | Ataberk | Uygun (örneklem) | Son 72 saatin api ve worker-data loglarında e-posta biçiminde metin 0 satır |
| 25 ★ Uçtan uca akış production'da | Burak | **Değil** | Production'da analiz işçisi yok: `ai/Dockerfile` (Burak) ve backend'in `analyze_cv`'ye bağlanması (`AiAnalyzer`, Anıl) bekleniyor; sonra `infra/pc/compose.yml`'e `worker-ai` eklenecek (Ataberk) |
| 26 ★ Doğrulama/sıfırlama e-postaları | Anıl | Ölçülmedi | Anıl'ın ön kontrolündeki durum değişmedi |
| 27 Hata ekranları | Anıl | Uygun (yerel) | Anıl'ın ön kontrolü; production'da analiz hatası ekranları T-057 sonrası |
| 28 Electron kurulumu | Anıl | Kısmen | Anıl'ın ön kontrolü: temiz Windows ve macOS eksik |
| 29 Otomatik güncelleme | Anıl | Kısmen | Yayın deposu açıldı (`cvnebakalim-surumler`, public); v1.0.0 → v1.0.1 testi yapılmadı |
| 30 ★ F1 ≥ 0,80, öneri puanı ≥ 4,0 | Burak | **Değil** | `ai/eval/report.md` yok; ölçüm raporu bekleniyor |
| 31 ★ Uydurma link yok | Burak | Kısmen | Golden testler birleşti (#160); production'da 100 analiz örneklemi analiz olmadığı için yapılamaz |
| 32 Analiz p95 < 120 sn | Burak | Ölçülemedi | Ollama GPU ile (#168): prompt 82, üretim 4,8 token/sn (CPU'da 14,8 ve 3,1). Gerçek analiz süresi T-057 sonrası yük testiyle (T-072) |
| 33 Model ve prompt sürümü sabit | Burak | Değil | Model karar #26 ile seçildi (`llama3.1:8b`, `ai/extraction/llm.py` `DEFAULT_MODEL`); sürüm sabitlenmedi: production'daki etiket digest'le bağlı değil (şu an `46e0c10c039e`), v1.0.0 ile birlikte sabitlenecek |
| 34 Gece toplaması hatasız (karar #39) | Ataberk | Uygun | 18–24.11 arası PC'nin açık olduğu 6 günde 42 çalışma, **0 hata**; 19.11'de PC kapalıydı. 22.11 ve 23.11'de kaçan geceler açılışta telafi edildi, ikinci kez toplanmadı (#162) |
| 35 Ölü link < %2 | Ataberk | Uygun | 4 / 1.699 = **%0,24**, son kontrol 24.11 15:09 |
| 36 ★ Yasal metinler yayında | Burak | **Değil** | Metinler #71'de (taslak); yayın yeri (Pages, kök alan adı) henüz açılmadı. Mobil ve web bu adreslere bağlantı veriyor |
| 37 ★ CV saklanmıyor | Burak | Kısmen | Mobil önbellek kopyası silme #161'de eklendi; disk/yedek taraması production'da analiz başlayınca yapılmalı |
| 38 ★ Hesap silme, dışa aktarma | Anıl | Kısmen | E2E testinde hesap silme var (#166 ile React Router 7 sonrası düzeltildi); production'da test hesabıyla deneme yok |
| 39 Veri ihlali prosedürü | Burak | Uygun | `docs/runbook/operasyon.md` §6: ilk adımlar ≤ 1 saat, KVK Kurulu'na ≤ 72 saat |
| 40 İlan kaynaklarının koşulları | Ataberk | Uygun | Production'daki 6 kaynak (Hacker News, Himalayas, Remote OK, Remotive, Jobicy, Arbeitnow) `scraper/kaynak-uygunluk.md`'de ✅. Arbeitnow ve Jobicy kaynak atfı istiyor: web'de `SourceAttribution.tsx` var; mobilde de olmalı (Burak) |
| 41 ★ Play kapalı testi | Anıl | **Değil** (zamanı gelmedi) | 21.12.2026'da başlayacak (T-076) |
| 42 Play formları | Anıl | Henüz zamanı değil | Gizlilik URL'si #36'ya bağlı |
| 43 Mağaza görselleri | Anıl | Henüz zamanı değil | — |
| 44 Runbook güncel, herkes okudu | Ataberk | Kısmen | `docs/runbook/operasyon.md` ve `felaket-kurtarma.md` güncel; "herkes okudu" onayı alınmadı |
| 45 README, API, mimari, model kartı | Anıl | Kısmen | README, `docs/mimari.md` ve ADR'ler (T-079) var; model kartı yok (Burak) |
| 46 Kullanıcı rehberi / SSS | Anıl | Değil | Tanıtım sayfası yayında değil |
| 47 Destek e-postası | Anıl | Kısmen | Anıl'ın ön kontrolü: adresin posta alıp almadığı belirsiz |
| 48 Hypercare nöbet çizelgesi | Ataberk | Değil | Hazırlanmadı (Ocak başında, T-097 öncesi) |
| 49 ★ Rollback 15 dk | Ataberk | Uygun | 21.11 provası 146 sn; v1.0.0 adayıyla Ocak'ta tekrarlanacak |
| 50 Go/No-Go toplantısı | Anıl | Henüz zamanı değil | 15.01.2027 |

**Ataberk'in kendi açıkları (canlıdan önce):** #2 nmap (başka cihazdan), #3 SSL Labs, #21 tünel durdurma testi, #18 birkaç günlük kesintisiz ölçüm, #51 telefon paylaşımı denemesi, #44 ekip onayı, #48 nöbet çizelgesi, #1 BitLocker (canlıdan hemen önce), #25 için `worker-ai` servisi (T-057'den sonra).

## Hizmet seviyesi hedefleri (SLO)

| Metrik | Hedef | Ölçüm | Hedef tutmazsa | Sorumlu |
|---|---|---|---|---|
| Erişilebilirlik | Duyurulan açık saatlerde (sunum/demo günleri ve hypercare boyunca 09:00–23:00) ≥ %95; PC'de barındırıldığı için 7/24 hedefi yok (karar #30) | Grafana, dış prob (`probe="dis"`, PC açıkken) | Kök neden analizi + runbook güncellemesi | Ataberk |
| API yanıt süresi (analiz hariç) | p95 < 300 ms | API logları (`duration_ms`, T-067) | Yavaş sorgu analizi, indeks | Anıl |
| Analiz tamamlanma süresi | p95 < 120 sn (PC, CPU; GTX 1650 kısmi GPU ölçülecek) | analyses.duration_ms | Model/prompt optimizasyonu, GPU değerlendirmesi | Burak |
| Analiz başarı oranı | ≥ %95 | analyses.status | Hata kodlarına göre düzeltme | Burak |
| Hata oranı (5xx) | < %1 | API logları (T-067) | Hotfix | Anıl |
| Veri tazeliği | İlanlar ≤ 7 gün eski | scrape_runs | Kaynak adaptörünü onar / yedek veri | Ataberk |
| RPO (kabul edilebilir veri kaybı) | ≤ 24 saat | Yedek zamanlaması | Yedek sıklığını artır | Ataberk |
| RTO (sistemi geri getirme süresi) | ≤ 4 saat (gerekirse başka bir ekip bilgisayarında) | DR tatbikatı | Otomasyonu artır | Ataberk |

## Rutin operasyonlar

| İşlem | Ayrıntı | Sıklık | Kontrol / çıktı | Sorumlu |
|---|---|---|---|---|
| İlan toplama + istatistik yenileme | Celery beat, 03:00; PC o saatte kapalıysa açılışta telafi | Günlük | scrape_runs başarılı; role_skill_stats güncel | Ataberk |
| Veri tabanı yedeği | pg_dump + restic, 02:00; PC kapalıysa açılışta | Günlük | restic snapshots; haftalık bütünlük kontrolü | Ataberk |
| Yedekten geri yükleme testi | Prova projesine (`careerai-staging`) son yedeği yükle | Aylık | Test raporu | Ataberk |
| Eğitim kaynağı link kontrolü | HTTP HEAD ile tüm linkler | Haftalık | Ölü link oranı < %2 | Ataberk |
| Bağımlılık ve imaj güvenlik taraması | Dependabot, Trivy | Haftalık | Kritik açık = 0 | Ataberk |
| Silinmiş hesapların kalıcı silinmesi | deleted_at > 30 gün olan kayıtlar | Günlük | audit_logs kaydı | Anıl |
| Model kalite izleme | Düşük puanlı analizlerin incelenmesi, golden test | Haftalık | Ortalama puan ≥ 4,0 | Burak |
| İşletim sistemi güvenlik güncellemeleri | Windows Update (etkin saatler dışında) + Docker Desktop güncellemesi, aylık planlı yeniden başlatma; sunum haftası ertelenir | Aylık | Kesinti penceresi duyurusu | Ataberk |
| SSL sertifika ve tünel | Cloudflare edge sertifikası otomatik; tünel bağlantısı dış izleyiciyle | Otomatik | Cloudflare uyarı e-postası | Ataberk |

## Olay prosedürleri (runbook özeti)

Adım adım komutlar: `docs/runbook/operasyon.md` (deploy, geri dönüş, Ollama, disk, kuyruk, veri ihlali) ve `docs/runbook/felaket-kurtarma.md`.

| Olay | Belirti | Önem | Müdahale adımları | Sorumlu |
|---|---|---|---|---|
| Hatalı deploy | Smoke test başarısız / 5xx artışı | Kritik | 1) Önceki imaj etiketine dön (docker compose up -d ile TAG=<önceki>) 2) Migration geri alınacaksa alembic downgrade (önce yedek) 3) Ekibe bildir 4) Kök neden analizi | Ataberk |
| Ollama yanıt vermiyor | /health/ready → ollama: false; analizler zaman aşımında | Yüksek | 1) docker compose restart ollama 2) RAM kontrolü (docker stats; Görev Yöneticisi) 3) Model yüklü mü (ollama list) 4) Bu sürede sözlük tabanlı yedek akış devrede | Burak |
| Kuyruk birikmesi | Kuyruk derinliği > 50 iş veya bekleme > 10 dk | Yüksek | 1) Worker loglarını incele 2) Takılı görevleri iptal et 3) Kullanıcıya "yoğunluk" mesajı 4) Gerekirse analiz rate limit'ini geçici düşür | Anıl |
| Disk dolmak üzere | Disk > %80 uyarısı | Orta | 1) docker system prune (dikkatli) 2) Eski logları temizle 3) Eski imajları sil 4) Kullanılmayan Ollama modellerini ve büyük dosyaları sil | Ataberk |
| Veri tabanı bozulması / kaybı | Bağlantı hataları, tutarsız veri | Kritik | 1) Uygulamayı bakım moduna al 2) Son yedekten geri yükle (DR prosedürü) 3) Veri kaybı aralığını belirle 4) Kullanıcıları bilgilendir | Ataberk |
| Kişisel veri ihlali şüphesi | Yetkisiz erişim, logda PII, sızıntı bildirimi | Kritik | 1) Erişimi kes / sırları yenile 2) Etki analizi (hangi veri, kaç kişi) 3) Danışman ve üniversiteyi bilgilendir 4) 72 saat içinde KVK Kurulu'na bildirim 5) Etkilenen kullanıcılara bildirim | Burak |
| Scraping kaynağı engelledi | scrape_runs art arda failed / 403 | Düşük | 1) Kaynağı pasif yap (is_active=false) 2) Gecikmeyi artır 3) Diğer kaynaklar ve açık veri ile devam; engeli aşmaya çalışma | Ataberk |
| Sertifika / DNS / tünel sorunu | Tarayıcıda SSL hatası veya Cloudflare 1033/530 sayfası | Yüksek | 1) docker compose logs cloudflared 2) Cloudflare panelinde tünel ve DNS durumu 3) cloudflared'i yeniden başlat | Ataberk |
| PC kapandı / elektrik veya internet kesildi | Dış izleyici uyarısı; Cloudflare hata sayfası | Yüksek | 1) PC'yi aç, oturum aç (Docker Desktop konteynerleri başlatır) 2) docker compose ps: hepsi healthy mi 3) tünel bağlandı mı 4) kaçan yedek ve gece toplaması çalıştı mı (scrape_runs) 5) uzun sürecekse tanıtım sayfasına duyuru | Ataberk |
| Sunum sırasında dış erişim yok | Alan adı açılmıyor | Kritik | 1) Aynı PC'de 127.0.0.1 üzerinden sunuma devam (yerel demo, aynı veri) 2) Telefondan internet paylaşımı ile tüneli tekrar bağla 3) Sunumdan sonra kök neden | Ataberk |
