# web/prototip — Wireframe (T-021)

Uygulamanın 10 ekranının tıklanabilir, düşük çözünürlüklü taslağı. Görsel tasarım değil; ekranların **içeriğini, akışını, API bağlantılarını ve hata durumlarını** gösterir. Renk ve tipografi T-022'de (tasarım sistemi) belirlenecek.

## Nasıl açılır

`index.html` dosyasına çift tıklayın — tarayıcıda açılır, kurulum gerekmez. Tek dosyadır, internet bağlantısı istemez.

## Ekranlar

| # | Ekran | Adres |
|---|---|---|
| 1 | Giriş / Kayıt | `#giris` |
| 2 | KVKK onayı | `#kvkk` |
| 3 | Hedef pozisyon seçimi | `#pozisyon` |
| 4 | CV yükleme | `#yukle` |
| 5 | Analiz bekleme | `#bekleme` |
| 6 | Sonuç panosu | `#sonuc` |
| 7 | Kaynak detayı (pop-up) | `#sonuc?kaynak=101` |
| 8 | Geçmiş analizler | `#gecmis` |
| 9 | Profil / ayarlar | `#profil` |
| 10 | Hesap silme | `#hesap-sil` |

Sağdaki sarı notlar her ekranın kullandığı endpoint'i (`contracts/api.md`) ve kurallarını gösterir. **"Durumu dene"** düğmeleriyle hata ve boş durumlar (ör. PDF olmayan dosya, saatlik analiz sınırı, kuyrukta bekleme, zaman aşımı, düşük ilan verisi) görülebilir.

## Notlar

- Veriler uydurmadır; formatı `contracts/examples/analysis_result.example.json` ile aynıdır.
- Aynı akış web, Electron ve mobilde kullanılacak; tarayıcıyı daraltarak mobil görünüm denenebilir.
- Bu dosya gerçek arayüzün kodu değildir; React arayüzü T-040'ta `web/` altında ayrıca kurulacak. Prototip referans olarak kalır.
- Figma'ya aktarmak isteğe bağlıdır.
