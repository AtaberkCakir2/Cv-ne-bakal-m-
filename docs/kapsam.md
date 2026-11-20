# MVP Kapsamı (v1.0)

> **Durum: TASLAK** — Kick-off toplantısında üç kişinin onayıyla dondurulacak (görev T-003). Onaydan sonra kapsam değişikliği sadece ekip kararıyla yapılır ve `docs/kararlar.md`'ye yazılır.

**v1.0 canlıya çıkış:** 18.01.2027 · **Platformlar:** Web, Windows/macOS (Electron), Android · **iOS:** v1.1

## Tek cümlede v1.0

Öğrenci hesap açar, hedef pozisyonunu seçer, CV'sini (PDF) yükler; sistem 1-2 dakika içinde CV'deki yetkinlikleri, o pozisyonun güncel ilanlarında istenen ama CV'de olmayan yetkinlikleri (talep oranıyla, ör. "ilanların %75'i") ve her eksik için doğrulanmış eğitim kaynaklarını gösterir.

## Must — v1.0'da olmazsa olmaz

Bunlardan biri eksikse canlıya çıkılmaz.

| # | Özellik | Sorumlu | İlgili görevler |
|---|---|---|---|
| M1 | Hesap: kayıt, giriş, e-posta doğrulama, şifre sıfırlama | Anıl | T-037, T-051 |
| M2 | KVKK: aydınlatma metni ve açık rıza onayı, hesabımı sil, verilerimi indir | Anıl, Burak | T-049, T-065 |
| M3 | Hedef pozisyon seçimi (en az 10 pozisyon) | Ataberk, Anıl | T-017, T-048 |
| M4 | CV yükleme: sadece PDF, ≤ 5 MB, ≤ 5 sayfa; Türkçe ve İngilizce CV | Anıl | T-038, T-052 |
| M5 | Metin çıkarma + taranmış CV için OCR yedeği | Burak | T-020, T-029 |
| M6 | Kişisel veri maskeleme (LLM'e gitmeden önce); CV ve ham metin saklanmaz | Burak | T-030 |
| M7 | Yetkinlik çıkarımı: sözlük + yerel LLM (Ollama); LLM çökerse sözlük sonucu döner | Burak | T-031, T-032 |
| M8 | İlan havuzu: en az 2.000 ilan (açık veri + en az 1 uygun kaynak), her gece güncelleme | Ataberk | T-015, T-033, T-034 |
| M9 | Talep istatistikleri: pozisyon × yetkinlik → ilan oranı | Ataberk | T-045 |
| M10 | Eşleştirme: 0-100 uyum skoru, eksik yetkinlikler talep oranına göre sıralı | Burak | T-042 |
| M11 | Kaynak önerisi: her eksik yetkinlik için veritabanından en az 3 kaynak (Türkçe öncelikli); LLM link üretmez | Burak, Ataberk | T-043, T-046 |
| M12 | Sonuç ekranı: uyum skoru, mevcut/eksik yetkinlikler, kaynak kartları; geçmiş analizler | Anıl | T-053 |
| M13 | Asenkron analiz (kuyruk) + ilerleme göstergesi | Anıl, Burak | T-039, T-057 |
| M14 | İstemciler: web, Windows/macOS kurulum dosyası, Android uygulaması (Play Store) | Anıl, Burak | T-059, T-061, T-062, T-095 |
| M15 | Basit yönetim paneli: kaynak ekle/düzenle, toplama çalışmalarını izle | Ataberk | T-063 |
| M16 | Operasyon: HTTPS, rate limit, günlük yedek, izleme ve uyarılar | Ataberk, Anıl | T-050, T-066, T-068 |

## Should — v1.0'da olmalı, sıkışırsak ilk ertelenecekler

| # | Özellik | Sorumlu |
|---|---|---|
| S1 | Sonuç puanlama (1-5 yıldız + yorum) — model kalitesini ölçmek için | Anıl |
| S2 | Canlı ilerleme (SSE); olmazsa birkaç saniyede bir yenileme (polling) | Anıl |
| S3 | 2. ve 3. ilan kaynağı | Ataberk |
| S4 | Yetkinlik seviyesi tahmini (başlangıç / orta / ileri) | Burak |
| S5 | Electron otomatik güncelleme | Anıl |
| S6 | Tanıtım (landing) sayfası ve indirme linkleri | Ataberk |

## Could — vakit kalırsa

| # | Özellik |
|---|---|
| C1 | iOS TestFlight (dahili test; mağaza yayını v1.1) |
| C2 | Koyu tema |
| C3 | Sonucu PDF olarak indirme |
| C4 | İngilizce arayüz |
| C5 | Kullanıcının çıkarılan yetkinlikleri elle düzeltebilmesi |

## Won't — v1.0'da kesinlikle yok

| # | Kapsam dışı | Neden / ne zaman |
|---|---|---|
| W1 | iOS App Store yayını | v1.1 (karar #3) |
| W2 | Dış yapay zeka API'leri (OpenAI, Claude API vb.) | Hiçbir sürümde (karar #1, KVKK) |
| W3 | LinkedIn veya scraping'i yasaklayan sitelerden veri | Hiçbir sürümde (karar #8) |
| W4 | İş ilanı listeleme, ilana başvuru — iş bulma sitesi değiliz | Ürün konumu: geliştirme aracı, eleme/başvuru aracı değil |
| W5 | İşveren / İK paneli | Ürün konumu: öğrencinin tarafındayız |
| W6 | Ödeme, abonelik, premium | Bitirme projesi kapsamı dışında |
| W7 | Akademik transkript analizi | v1.1 adayı — açık soru 1'e bakın |
| W8 | Mülakat soruları, öğrenme ilerleme takibi, LinkedIn PDF içe aktarma | v1.1 yol haritası |

## v1.0 başarı kriterleri

Canlıya çıkış kararı (Go/No-Go, 15.01.2027) bu ölçütlere göre verilir; ayrıntılar `docs/go-live.md`.

| Ölçüt | Hedef |
|---|---|
| Yetkinlik çıkarımı doğruluğu (50 etiketli CV) | F1 ≥ 0,80 |
| Öneri alakalılığı (3 değerlendirici, 1-5) | ≥ 4,0 |
| Analiz süresi | p95 < 120 sn |
| Analiz başarı oranı | ≥ %95 |
| Beta kullanılabilirliği (20-30 öğrenci) | SUS ≥ 70, kritik hata 0 |
| Erişilebilirlik (aylık) | ≥ %99 |

## Açık sorular (kick-off'ta karara bağlanacak)

| # | Soru | Öneri |
|---|---|---|
| 1 | Fizibilite raporu "CV **veya akademik transkript**" diyor. Transkript v1.0'da olacak mı? | **Hayır**, v1.1. Transkript formatları üniversiteye göre çok farklı; v1.0'ı riske atar. Jüriye "v1.1 yol haritasında" denir. Danışmana teyit ettirilmeli. |
| 2 | Hangi 10 hedef pozisyon? | Backend, Frontend, Full-Stack, Mobil, Veri Bilimci, ML Mühendisi, DevOps, QA/Test, Siber Güvenlik, Oyun Geliştirici. Ataberk ilan verisi yeterli olanları teyit eder (pozisyon başına ≥ 50 ilan). |
| 3 | Arayüz dili sadece Türkçe mi? | **Evet**, v1.0 Türkçe; CV'ler Türkçe ve İngilizce okunur. İngilizce arayüz Could (C4). |
| 4 | Hesap açmadan (misafir) analiz yapılabilsin mi? | **Hayır**, hesap zorunlu: KVKK rızası, rate limit ve geçmiş analizler için. |
| 5 | Apple geliştirici hesabı (yıllık ücret) şimdi mi alınsın? | **Hayır**, v1.1'e kadar ertelensin; bütçede tasarruf. |
| 6 | Kapsamın danışman onayı | Toplantı sonrası bu belge danışmana iletilsin. |

## Kapsam değişikliği nasıl yapılır?

1. Değişiklik önerisi WhatsApp'ta değil, bu dosyayı değiştiren bir PR ile yapılır.
2. PR açıklamasında neyin neden değiştiği ve hangi görevlerin etkilendiği yazılır.
3. Üç kişinin onayıyla birleşir; karar `docs/kararlar.md`'ye eklenir.
4. Must listesine eklenen her şey için Must'tan veya Should'dan eşit büyüklükte bir şey çıkarılır — takvim sabit.
