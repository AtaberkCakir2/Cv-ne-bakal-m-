# Canlıya Çıkış ve Operasyon

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

- **Go / No-Go toplantısı:** 15.01.2027
- **Canlıya çıkış (v1.0.0):** 18.01.2027
- **Hypercare (yakın izleme):** 18–31.01.2027, her gün bir kişi nöbetçi
- **Barındırma:** production Ataberk'in PC'sinde Docker Compose ile çalışır, alan adına Cloudflare Tunnel ile bağlanır (karar #30). Sistem PC açıkken erişilebilir; hocalara sunum bu PC üzerinden alan adıyla yapılır.

**Kural:** Kritik (★) maddelerin tamamı tamamlanmadan canlıya çıkılmaz. Tamamlanan maddeyi `[x]` olarak işaretleyin (PR ile).

## Kontrol listesi

### Altyapı

- [ ] **1.** ★ Production PC'si hazırlandı (Windows güncel, disk şifreli (BitLocker), güçlü yerel hesap şifresi, uyku/hazırda bekletme kapalı, Docker Desktop oturumla başlıyor, Windows Güvenlik Duvarı açık) — _Doğrulama:_ `infra/pc/README.md` kontrol listesi — _Sorumlu:_ Ataberk
- [ ] **2.** ★ Postgres, Redis ve Ollama portları ağdan erişilemez; PC'de gelen port açılmadı (modemde port yönlendirme yok) — _Doğrulama:_ production compose'da `ports:` yok (`docker compose config`); aynı ağdaki başka cihazdan nmap: hepsi kapalı — _Sorumlu:_ Ataberk
- [ ] **3.** ★ HTTPS aktif (Cloudflare: Always Use HTTPS, HSTS, en düşük TLS 1.2) — _Doğrulama:_ SSL Labs testi A veya üstü — _Sorumlu:_ Ataberk
- [ ] **4.** DNS Cloudflare'de; app. ve api. alt alan adları tünele bağlı — _Doğrulama:_ dig api.<alanadi>; `cloudflared tunnel info` — _Sorumlu:_ Ataberk
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
- [ ] **20.** ★ Yedekten başka bir bilgisayara geri yükleme test edildi (RTO < 4 saat) — _Doğrulama:_ DR tatbikat raporu — _Sorumlu:_ Ataberk

### İzleme

- [ ] **21.** ★ PC dışından uptime izleme ve uyarılar ekip kanalına düşüyor — _Doğrulama:_ Test uyarısı gönderildi — _Sorumlu:_ Ataberk
- [ ] **22.** Sentry backend, web ve mobilde aktif; kaynak haritaları yüklü — _Doğrulama:_ Test hatası görüldü — _Sorumlu:_ Anıl
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

- [ ] **34.** Gece toplama işi son 7 günde hatasız çalıştı — _Doğrulama:_ scrape_runs tablosu — _Sorumlu:_ Ataberk
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

## Hizmet seviyesi hedefleri (SLO)

| Metrik | Hedef | Ölçüm | Hedef tutmazsa | Sorumlu |
|---|---|---|---|---|
| Erişilebilirlik | Duyurulan açık saatlerde (sunum/demo günleri ve hypercare boyunca 09:00–23:00) ≥ %95; PC'de barındırıldığı için 7/24 hedefi yok (karar #30) | Dış uptime izleyici | Kök neden analizi + runbook güncellemesi | Ataberk |
| API yanıt süresi (analiz hariç) | p95 < 300 ms | Grafana / Sentry Performance | Yavaş sorgu analizi, indeks | Anıl |
| Analiz tamamlanma süresi | p95 < 120 sn (PC, CPU; GTX 1650 kısmi GPU ölçülecek) | analyses.duration_ms | Model/prompt optimizasyonu, GPU değerlendirmesi | Burak |
| Analiz başarı oranı | ≥ %95 | analyses.status | Hata kodlarına göre düzeltme | Burak |
| Hata oranı (5xx) | < %1 | Sentry | Hotfix | Anıl |
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
