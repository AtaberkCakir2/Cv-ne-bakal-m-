# Riskler ve Bütçe

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

Skor = Olasılık × Etki (1–5). Seviye: ≥ 15 Yüksek, 8–14 Orta, < 8 Düşük. Yüksek riskler her sprint planlamasında gözden geçirilir.

## Risk kaydı

### R-01 · LLM'in CPU sunucuda yavaş çalışması (analiz 1-3 dk)

- **Olasılık / Etki / Skor:** 5 / 4 / **20 (Yüksek)** · **Sorumlu:** Burak
- **Önlem:** Asenkron kuyruk + ilerleme ekranı; q4 quantize 8B model; keep_alive; num_ctx sınırı; aynı CV için önbellek; prompt kısaltma.
- **Gerçekleşirse (B planı):** Demo/kongre günleri için saatlik GPU sunucu kiralama; daha küçük model (3-4B) yedeği.
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
- **Erken uyarı:** Sentry/loglarda PII görülmesi

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

### R-09 · Sunucu RAM'inin tükenmesi (Ollama + Playwright + DB)

- **Olasılık / Etki / Skor:** 3 / 4 / **12 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Container bellek limitleri; worker-ai eşzamanlılık 1; toplama işi gece; swap; RAM uyarısı %85.
- **Gerçekleşirse (B planı):** Ollama'yı ayrı sunucuya taşı; scraping'i başka makinede çalıştır.
- **Erken uyarı:** RAM > %85 uyarısı

### R-10 · Tek sunucu = tek hata noktası

- **Olasılık / Etki / Skor:** 3 / 3 / **9 (Orta)** · **Sorumlu:** Ataberk
- **Önlem:** Günlük şifreli yedek, DR tatbikatı, runbook, uptime izleme.
- **Gerçekleşirse (B planı):** Yedekten yeni sunucuya kurulum (RTO < 4 saat).
- **Erken uyarı:** Uptime izleme kesinti uyarısı

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

## Bütçe

| Kalem | Açıklama | Adet / süre | Birim fiyat | Tutar | Tür | Kaynak / varsayım |
|---|---|---|---|---|---|---|
| AI sunucusu (VPS) | 8 vCPU / 16 GB RAM Linux sunucu, 6 ay | 6 | 700 TL | 4.200 TL | Zorunlu | Fizibilite raporu: 6 ay için 4.200 TL |
| Mobil mağaza lisansları | Google Play (tek seferlik) + Apple Developer (yıllık) | 1 | 4.500 TL | 4.500 TL | Zorunlu | Fizibilite raporu. Apple v1.1'e ertelenirse sadece Google Play ödenir (ön ödeme azalır). |
| Alan adı | 1 yıllık alan adı | 1 | 800 TL | 800 TL | Zorunlu | Fizibilite raporu (domain + SSL). SSL Let's Encrypt ile ücretsiz olduğundan tutar alan adı için kullanılabilir. |
| Yapay zeka API'leri | Ollama ile yerel modeller | 1 | - | - | Zorunlu | Fizibilite raporu: dış API maliyeti 0 |
| Sunucu dışı yedek depolama | Şifreli yedekler için nesne depolama, 6 ay | 6 | 100 TL | 600 TL | Önerilen | Varsayım — ekip tarafından teklif alınarak güncellenmeli |
| GPU sunucu (demo günleri) | Kongre/final demosunda saatlik GPU kiralama | 0 | - | - | Opsiyonel | Varsayım — gerekirse fiyat teklifi alınıp adet/fiyat girilmeli |
| İzleme, CI/CD, e-posta | Uptime Kuma, Sentry, GitHub Actions, e-posta servisi (ücretsiz katmanlar) | 1 | - | - | Zorunlu | Ücretsiz/öğrenci katmanları |
| Poster baskısı | Kongre posteri | 1 | - | - | Zorunlu | Üniversite aracılığıyla basılıyor (rapora göre) |

**Zorunlu:** 9.500 TL · **Önerilen:** 600 TL · **Genel toplam:** 10.100 TL. Fizibilite raporundaki prototip maliyeti 9.500 TL'dir; yalnızca sunucu dışı yedek depolama eklenmiştir. Döviz bazlı kalemler (mağaza ücretleri) kura göre güncellenmelidir.
