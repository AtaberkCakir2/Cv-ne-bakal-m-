# Riskler ve Bütçe

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

Skor = Olasılık × Etki (1–5). Seviye: ≥ 15 Yüksek, 8–14 Orta, < 8 Düşük. Yüksek riskler her sprint planlamasında gözden geçirilir.

## Risk kaydı

### R-01 · LLM'in CPU'da yavaş çalışması (analiz 1-3 dk)

- **Olasılık / Etki / Skor:** 5 / 4 / **20 (Yüksek)** · **Sorumlu:** Burak
- **Önlem:** Asenkron kuyruk + ilerleme ekranı; q4 quantize 8B model; keep_alive; num_ctx sınırı; aynı CV için önbellek; prompt kısaltma.
- **Gerçekleşirse (B planı):** PC'deki GTX 1650 (4 GB) ile Ollama'da kısmi GPU hızlandırması; daha küçük model (3-4B) yedeği; son çare demo günü için saatlik GPU kiralama.
- **Erken uyarı:** Analiz p95 > 120 sn

### R-02 · İlan sitelerinin scraping'i engellemesi veya kullanım koşullarının yasaklaması

- **Olasılık / Etki / Skor:** 4 / 4 / **16 (Yüksek)** · **Sorumlu:** Ataberk
- **Önlem:** Önce resmi API'ler ve açık veri setleri; robots.txt uyumu; 3-5 sn gecikme; yasaklayan siteler kapsam dışı.
- **Gerçekleşirse (B planı):** Kaggle/açık veri seti ile çalışmaya devam (sistem veri kaynağından bağımsız tasarlandı).
- **Erken uyarı:** scrape_runs'ta art arda failed

### R-03 · LLM halüsinasyonu: olmayan yetkinlik veya uydurma kurs linki

- **Olasılık / Etki / Skor:** 3 / 5 / **15 (Yüksek)** · **Sorumlu:** Burak
- **Önlem:** Linkler sadece DB'den (RAG); taksonomi doğrulaması; JSON şema doğrulaması; golden testler.
- **Gerçekleşirse (B planı):** Sözlük tabanlı v1 sonuca düş; ilgili prompt sürümünü geri al.
- **Erken uyarı:** Kullanıcı puanı < 3 oranı artışı

### R-04 · Türkçe ve farklı formatlı CV'lerde düşük çıkarım doğruluğu

- **Olasılık / Etki / Skor:** 3 / 4 / **12 (Orta)** · **Sorumlu:** Burak
- **Önlem:** Çok sütunlu PDF desteği, OCR yedeği, eş anlamlı sözlüğü, 50 CV'lik etiketli değerlendirme seti.
- **Gerçekleşirse (B planı):** Kullanıcının yetkinlikleri elle düzeltebildiği ekran (v1.1).
- **Erken uyarı:** F1 < 0,80

### R-05 · KVKK ihlali / kişisel veri sızıntısı

- **Olasılık / Etki / Skor:** 2 / 5 / **10 (Orta)** · **Sorumlu:** Burak
- **Önlem:** CV saklanmaz; LLM öncesi PII maskeleme; log maskeleme; şifreli yedek; en az yetki; güvenlik testleri.
- **Gerçekleşirse (B planı):** Runbook'taki ihlal prosedürü: izole et, etkiyi belirle, 72 saat içinde KVK Kurulu'na bildir, kullanıcıları bilgilendir.
- **Erken uyarı:** Loglarda PII görülmesi

### R-06 · Kapsam kayması (her şeyi yapmaya çalışmak)

- **Olasılık / Etki / Skor:** 4 / 4 / **16 (Yüksek)** · **Sorumlu:** Anıl
- **Önlem:** MoSCoW ile dondurulmuş MVP; iOS v1.1'e ertelendi; yeni istekler v1.1 listesine.
- **Gerçekleşirse (B planı):** P2 görevleri kes; mobil sadece Android.
- **Erken uyarı:** Sprint sonunda tamamlanmayan P0 görev

### R-07 · Ders yükü / vize-final haftalarında ekip kapasitesinin düşmesi

- **Olasılık / Etki / Skor:** 4 / 3 / **12 (Orta)** · **Sorumlu:** Anıl
- **Önlem:** Sınav haftaları takvime işlendi; o sprintlerde düşük yük; her modülün README'si sayesinde yedeklenebilirlik.
- **Gerçekleşirse (B planı):** P2 görevlerini ertele; hypercare nöbetini paylaştır.
- **Erken uyarı:** Haftalık efor < 10 saat/kişi

### R-08 · Google Play kapalı test şartı (12 testçi × 14 gün) nedeniyle gecikme

- **Olasılık / Etki / Skor:** 4 / 3 / **12 (Orta)** · **Sorumlu:** Anıl
- **Önlem:** Kapalı test en geç 21.12.2026'da başlar; 20+ testçi listesi önceden hazırlanır.
- **Gerçekleşirse (B planı):** Web + Electron ile 18.01'de canlıya çık, Android yayınını birkaç gün kaydır.
- **Erken uyarı:** 21.12'de kapalı test başlamamış olması

### R-09 · PC RAM'inin tükenmesi (Ollama + Playwright + DB + Windows ve geliştirme ortamı)

- **Olasılık / Etki / Skor:** 2 / 4 / **8 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** PC'de 32 GB RAM (VPS planının iki katı); Docker Desktop'a (WSL2) en fazla 20 GB; container bellek limitleri; worker-ai eşzamanlılık 1; production açıkken geliştirme ortamının Ollama'sı kapalı; toplama işi gece; RAM uyarısı %85.
- **Gerçekleşirse (B planı):** Ollama'yı GPU'ya al; scraping'i başka bir ekip bilgisayarında çalıştır.
- **Erken uyarı:** RAM > %85 uyarısı

### R-10 · PC = tek hata noktası (elektrik, internet, donanım, Windows güncellemesi, uyku)

- **Olasılık / Etki / Skor:** 4 / 3 / **12 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Karar #30: uyku ve hazırda bekletme kapalı, Docker Desktop otomatik başlar, konteynerler `unless-stopped`; güncellemeler etkin saatler dışında, sunum haftası ertelenir; Grafana'da dış erişim probu (PC açıkken; PC dışı izleyici yok, karar #32); günlük şifreli PC dışı yedek; DR tatbikatı; sunum için B planı (aynı sürüm 127.0.0.1'de yerel demo, telefondan internet paylaşımı). PC'de pil algılanmıyor: elektrik kesilince kapanır.
- **Gerçekleşirse (B planı):** Yedekten başka bir ekip bilgisayarına kurulum ve tünel bağlantısını oraya taşıma (RTO < 4 saat).
- **Erken uyarı:** Grafana'da `DisErisimYok`; Cloudflare 1033/530 hata sayfası (PC tamamen kapanırsa otomatik uyarı yok, Ataberk günlük kontrolde fark eder, karar #41)

### R-11 · Türkçe ilan verisinin yetersiz kalması

- **Olasılık / Etki / Skor:** 3 / 3 / **9 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Birden fazla kaynak; İngilizce ilanların da kullanılması; son 6 ay filtresi.
- **Gerçekleşirse (B planı):** Pozisyon başına ilan sayısı < 50 ise kullanıcıya "düşük güven" uyarısı.
- **Erken uyarı:** role_skill_stats total_postings < 50

### R-12 · Bağımlılıklardaki güvenlik açıkları

- **Olasılık / Etki / Skor:** 3 / 3 / **9 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Dependabot, pip-audit, npm audit, Trivy; CI'da kontrol.
- **Gerçekleşirse (B planı):** Acil yama sürümü (hotfix branch).
- **Erken uyarı:** Dependabot kritik uyarısı

### R-13 · CV'ye gömülü prompt injection

- **Olasılık / Etki / Skor:** 2 / 4 / **8 (Orta)** · **Sorumlu:** Burak
- **Önlem:** CV metni veri olarak sınırlandırılır; çıktı şema doğrulaması; LLM'in araç/ağ erişimi yok.
- **Gerçekleşirse (B planı):** Şüpheli CV'yi sözlük tabanlı akışla işle.
- **Erken uyarı:** Şema doğrulama hatası artışı

### R-14 · Eğitim kaynağı linklerinin zamanla ölmesi

- **Olasılık / Etki / Skor:** 3 / 2 / **6 (Düşük)** · **Sorumlu:** Ataberk
- **Önlem:** Haftalık link sağlık kontrolü; her yetkinlik için ≥ 3 kaynak.
- **Gerçekleşirse (B planı):** Ölü linki pasifleştir, alternatif göster.
- **Erken uyarı:** Ölü link oranı > %2

### R-15 · Ekip içi entegrasyon sorunları (modüllerin birbirine uymaması)

- **Olasılık / Etki / Skor:** 3 / 4 / **12 (Orta)** · **Sorumlu:** Anıl
- **Önlem:** İlk hafta yazılan sözleşmeler (JSON şeması, OpenAPI); her sprint sonunda entegrasyon demosu; ortak CI.
- **Gerçekleşirse (B planı):** Entegrasyon için ayrılmış tampon gün (sprint sonu).
- **Erken uyarı:** Sprint demosunda çalışmayan akış

### R-16 · Apple hesabı / iOS süreçleri

- **Olasılık / Etki / Skor:** 3 / 2 / **6 (Düşük)** · **Sorumlu:** Burak
- **Önlem:** iOS v1.1'e ertelendi; EAS Build ile Mac gerekmez.
- **Gerçekleşirse (B planı):** Sadece Android + masaüstü + web ile devam.
- **Erken uyarı:** —

### R-17 · Production'ın geliştirme bilgisayarında ve ev ağında çalışması

- **Olasılık / Etki / Skor:** 3 / 3 / **9 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Production ayrı compose projesi (`careerai-prod`) ve ayrı volume'larla çalışır, host'a port açmaz; dışarıya sadece Cloudflare Tunnel üzerinden app. ve api. açılır (admin paneli ve izleme panelleri açılmaz); modemde port yönlendirme yok; disk şifreli (BitLocker); production `.env` sadece bu PC'de; geliştirme sırasında production'a dokunan komutlar proje adıyla (`-p careerai-prod`) çalıştırılır.
- **Gerçekleşirse (B planı):** Yanlışlıkla silinen/bozulan veride son yedekten geri yükleme; şüpheli erişimde tüneli kapat, sırları yenile (olay prosedürü).
- **Erken uyarı:** Production konteynerlerinin beklenmedik yeniden başlaması; `docker compose -p careerai-prod ps` dışında çalışan production volume'u

### R-18 · PC kapalıyken gece toplamasının ve yedeğin kaçması

- **Olasılık / Etki / Skor:** 3 / 2 / **6 (Düşük)** · **Sorumlu:** Ataberk
- **Önlem:** Açılışta telafi: son başarılı toplamadan veya yedekten 24 saat geçtiyse ilk açılışta çalışır; veri tazeliği SLO'su (≤ 7 gün) birkaç günlük boşluğu tolere eder.
- **Gerçekleşirse (B planı):** Elle toplama ve yedek (`make` hedefleri).
- **Erken uyarı:** scrape_runs'ta 48 saatten eski son başarılı çalışma

## Bütçe

| Kalem | Açıklama | Adet / süre | Birim fiyat | Tutar | Tür | Kaynak / varsayım |
|---|---|---|---|---|---|---|
| AI sunucusu (VPS) | **Kiralanmıyor** (karar #30): sistem Ataberk'in PC'sinde çalışır | 0 | - | 0 TL | — | Fizibilite raporunda 6 ay için 4.200 TL'ydi |
| Cloudflare | DNS, Tunnel, Pages (statik sayfalar) | 1 | - | - | Zorunlu | Ücretsiz plan |
| Mobil mağaza lisansları | Google Play (tek seferlik) + Apple Developer (yıllık) | 1 | 4.500 TL | 4.500 TL | Zorunlu | Fizibilite raporu. Apple v1.1'e ertelenirse sadece Google Play ödenir (ön ödeme azalır). |
| Alan adı | `cvnebakalim.com`, 1 yıl, otomatik yenileme (alındı: 06.11.2026) | 1 | 560 TL | 560 TL | Zorunlu | Gerçek tutar (Cloudflare Registrar, 06.11.2026). Fizibilite raporunda 800 TL ayrılmıştı. Ad sunucuları Cloudflare'de, SSL ücretsiz. Yenileme ücreti dolar bazlı, kura göre değişir. |
| Yapay zeka API'leri | Ollama ile yerel modeller | 1 | - | - | Zorunlu | Fizibilite raporu: dış API maliyeti 0 |
| PC dışı yedek depolama | Şifreli yedekler için nesne depolama (ör. Backblaze B2 ücretsiz 10 GB) | 6 | - | 0 TL | Önerilen | Yedekler ücretsiz katmana sığar varsayımı; aşılırsa ayda ~100 TL (6 ay 600 TL) |
| PC elektriği ve internet | Production PC'sinin sürekli açık kalması | — | - | - | — | Ekip karşılar; bütçeye yazılmadı |
| GPU sunucu (demo günleri) | Kongre/final demosunda saatlik GPU kiralama | 0 | - | - | Opsiyonel | Varsayım — gerekirse fiyat teklifi alınıp adet/fiyat girilmeli |
| İzleme, CI/CD, e-posta | Prometheus + Grafana (PC'de), GitHub Actions, e-posta servisi (ücretsiz) | 1 | - | - | Zorunlu | Ücretsiz/öğrenci katmanları |
| Poster baskısı | Kongre posteri | 1 | - | - | Zorunlu | Üniversite aracılığıyla basılıyor (rapora göre) |

**Zorunlu:** 5.060 TL · **Önerilen:** 0 TL (yedek ücretsiz katmanı aşarsa 600 TL) · **Genel toplam:** 5.060 TL. Fizibilite raporundaki prototip maliyeti 9.500 TL'dir; VPS kiralanmadığı için (karar #30) 4.200 TL, alan adı beklenenden ucuza alındığı için 240 TL düşer. Harcanan: alan adı 560 TL (06.11.2026). TÜBİTAK başvuru taslağındaki bütçe bu tablodan ayrıdır ve bu kararla değiştirilmedi (T-028 askıda). Döviz bazlı kalemler (mağaza ücretleri) kura göre güncellenmelidir.
