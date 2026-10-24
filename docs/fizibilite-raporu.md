# Fizibilite Raporu — CareerAI

**Yapay Zeka Destekli Kariyer ve Eğitim Yönlendirme Sistemi** · Güz 2026 · Bitirme Projesi Raporu (revize 2)

> Bu dosya danışmana teslim edilen fizibilite raporunun metnidir; jüriye ve TÜBİTAK başvurusuna verilen taahhütlerin kaynağıdır. Raporda "veya" ile bırakılan seçenekler sonradan kararlaştırıldı (ör. mobil için React Native, veri tabanı için PostgreSQL): güncel kararlar için [kararlar.md](kararlar.md), güncel mimari için [mimari.md](mimari.md).

## 1. Ön Söz

Yazılım ve teknoloji sektörleri çok hızlı değişiyor; yeni diller, framework'ler ve bulut teknolojileri kısa sürede endüstri standardı oluyor. Üniversite müfredatları bu hıza anlık uyum sağlayamıyor; öğrenciler mezuniyet veya staj arayışında sektörün hangi teknolojileri talep ettiğini (ör. Docker, Kubernetes, Next.js, bulut mimarileri) ve kendilerinin hangi alanlarda eksik kaldığını tespit etmekte zorlanıyor.

Bu rapor, öğrencilerin CV veya transkript verilerini Doğal Dil İşleme (NLP) ve Üretken Yapay Zeka (ÜZ) ile güncel iş ilanlarıyla karşılaştıran bir bitirme projesinin teknik, operasyonel ve ekonomik yapılabilirliğini inceler. Proje, 2026-2027 Güz Dönemi yönergelerinde **"YZ/ÜZ ve Eğitim"** ile **"YZ/ÜZ ve Yazılım"** başlıkları altında konumlanır.

**Vizyon:** Öğrencinin eksik yetkinliğini veri güdümlü algoritmalarla anında tespit etmek, sektörel standartları baz alarak kişiselleştirilmiş analiz sunmak ve öğrenciyi gelişimine doğrudan katkı sağlayacak kaynaklara (video, kurs, makale) yönlendirmek.

## 2. Projenin Tanıtımı ve Problem Analizi

### 2.1 Çıkış noktası ve amaç

Bilgiye erişim sorunu çözüldü, ancak "hangi bilgiye erişilmeli" sorunu ortaya çıktı: öğrenci binlerce saatlik ücretsiz eğitim bulabiliyor ama kariyer hedefi için hangisine öncelik vereceğini bilemiyor. Proje, öğrencilerin iş arama ve kendini geliştirme süreçlerini dijital bir mentorluk sistemiyle optimize etmeyi amaçlar. Sistem CV'yi NLP ile ayrıştırır, güncel ilan gereksinimleriyle çapraz eşleştirir; kullanıcı neyi bilmediğini ve nereden öğreneceğini net görür.

### 2.2 Temel işleyiş adımları

1. **Veri girişi ve işleme:** Kullanıcı mobil veya masaüstü uygulamadan CV'sini PDF olarak yükler; sistem metin ayrıştırma ve gerekirse OCR ile ham metni çıkarır.
2. **Yetkinlik çıkarımı (NER):** Yerel yapay zeka motoru mevcut yetkinlikleri, deneyim sürelerini ve eğitim geçmişini kategorize eder (ör. "İleri düzey Python, temel düzey SQL, Docker bilinmiyor").
3. **Sektör ve ilan taraması:** Hedef unvana (ör. Backend Developer) yönelik güncel ilan havuzundan piyasa standartları belirlenir; en çok tekrar eden gereksinimler veri madenciliğiyle ağırlıklandırılır.
4. **Çapraz eşleştirme ve tavsiye:** Yetkinlikler talep ile karşılaştırılır. Örnek çıktı: *"İncelediğimiz 150 Backend Developer ilanının %75'i PostgreSQL ve Docker tecrübesi arıyor. Özgeçmişinde bu teknolojiler bulunamadı. Bu açığı kapatmak için şu eğitim serisini tamamlamalısın."*

## 3. Kapsam ve Pazar Analizi

### 3.1 Küresel benzerler ve eksikleri

LinkedIn, Indeed, Glassdoor temel anahtar kelime eşleştirmesi yapar. LinkedIn Premium adayın diğer başvuranlar arasındaki konumunu gösterir ama proaktif bir eğitim rotası çizmez: "eksiksin" der, "şuradan öğren" demez. Ücretli kariyer koçluğu ve danışmanlık öğrenciler için erişilebilir değildir.

### 3.2 Türkiye'deki durum ve projenin farkı

Kariyer.net ve üniversite kariyer merkezleri geleneksel listeleme ve danışmanlıkla çalışır; mevcut yazılımlar genelde İK'nın aday elemesi için kurgulanmıştır. **Projenin inovasyonu, sistemi adayın tarafına konumlandırmasıdır:** bir eleme aracı değil, bir geliştirme aracı. Kurumsal çözümlerin büyük veri analiz yeteneğini öğrenci bütçesine uygun hale getirir.

## 4. Sistem Mimarisi ve UML

### 4.1 İstemci-sunucu mimarisi

İki katman: kullanıcı etkileşimini yöneten istemci ve veri işleme yükünü üstlenen backend. İstemcide farklı ekran boyutlarına uyumlu HTML/CSS yerleşimleri ve analiz sonuçları için pop-up pencereler kullanılır. Backend'de FastAPI (Python) ara katmanı ve yerel ağda çalışan Ollama sunucusu bulunur; geliştirme ve hata ayıklamada sunucu ve API bağlantıları terminal komutlarıyla yönetilir.

### 4.2 Veri akışı (sequence)

1. Kullanıcı arayüzden CV'sini (PDF) yükler.
2. Arayüz dosyayı REST API üzerinden FastAPI'ye iletir.
3. Backend dosyayı ayrıştırma modülüne gönderip metni elde eder.
4. Çıkarılan yetkinlikler, ilan veritabanıyla eşleştirilmek üzere yerel Ollama modeline (Llama 3 / Gemma) aktarılır.
5. Eksik yetkinlik listesi ve e-öğrenme tavsiyeleri JSON olarak istemciye döner ve görselleştirilir.

## 5. NLP ve Veri Toplama Metodolojisi

### 5.1 Metin ayrıştırma ve OCR

PDF'ler pdfplumber veya PyPDF ile metne çevrilir. Görsel olarak taranmış CV'ler için Tesseract OCR yedek mekanizması devreye girer.

### 5.2 Web scraping ve hız sınırlama

Güncel ilan gereksinimleri belirli periyotlarla çalışan veri toplama botlarıyla toplanır; dinamik sayfalar için Selenium veya Playwright gibi headless tarayıcılar kullanılır. Anti-bot mekanizmalarına takılmamak ve süreci etik tutmak için dinamik gecikmeler ve hız sınırlama uygulanır.

### 5.3 Eşleştirme ve ön filtreleme

Yetkinlikler, maliyet ve süre optimizasyonu için önce TF-IDF veya HuggingFace embedding modelleriyle kosinüs benzerliği üzerinden ilan anahtar kelimeleriyle karşılaştırılır. Bu filtreden geçen rafine veri Ollama'ya verilir; böylece daha isabetli ve halüsinasyonsuz tavsiyeler üretilir.

## 6. Yazılım Teknolojileri

### 6.1 Yerel yapay zeka (Ollama ve açık kaynak modeller)

Dışa bağımlı, maliyetli ve veri mahremiyeti riski taşıyan üçüncü parti API'ler (ChatGPT, Claude vb.) **kullanılmayacaktır**. KVKK uyumu için yerel model sunucusu Ollama üzerinde Llama 3 (8B) veya Gemma gibi açık kaynak modeller çalıştırılır; CV'ler dış sunuculara gitmez.

### 6.2 Backend (Python ve FastAPI)

İş mantığı, veritabanı bağlantıları ve model iletişimi Python ile; yüksek performanslı ve asenkron FastAPI framework'ü ile yazılır.

### 6.3 İstemciler (cross-platform)

Mobil uygulama tek kod tabanıyla iOS ve Android'de çalışan React Native veya Flutter ile; masaüstü uygulaması Windows ve macOS için Electron.js ile geliştirilir.

### 6.4 Veritabanı

Kullanıcı profilleri, belge logları, iş ilanları ve önerilen kurs linklerinin bütünlüğü için PostgreSQL veya MySQL gibi ilişkisel veritabanı kullanılır.

## 7. Maliyet ve Risk Yönetimi

### 7.1 Maliyet

Donanım ihtiyacı yoktur; açık kaynak modeller sayesinde dış API maliyeti sıfırdır.

| Gider kalemi | Açıklama | Tahmini bütçe |
|---|---|---|
| AI sunucusu (VPS) | Ollama, modeller ve FastAPI için en az 8-16 GB RAM'li, 6 aylık Linux sunucu | 4.200 TL |
| Yapay zeka API'leri | Yerel modeller; token/sorgu ücreti yok | 0 TL |
| Mobil market lisansları | Apple App Store (yıllık) + Google Play Console (ömür boyu) | 4.500 TL |
| Domain ve güvenlik | Alan adı ve SSL (1 yıllık) | 800 TL |
| **Toplam prototip maliyeti** | | **9.500 TL** |

### 7.2 Riskler ve önlemler

- **KVKK ihlali:** CV'deki adres, telefon gibi hassas veriler diske yazılmaz; yalnızca analiz anında bellekte işlenir ve anonimleştirilerek sonuç üretilir.
- **Scraping engellemeleri:** Bekleme süreleri, dinamik User-Agent; gerektiğinde Kaggle gibi açık veri setleriyle (mock data) kesintisiz çalışma.
- **Model performans darboğazı:** Eşzamanlı istekler kuyruk mimarisiyle (RabbitMQ veya Redis + Celery) sıraya alınır ve asenkron işlenir.

## 8. Zaman Planlaması

Proje, TBD İstanbul Şube Başkanlığı ile düzenlenen **20. Bilişim Kongresi**'ne yetiştirilmek üzere planlandı.

Rapordaki aşamalar (sırasıyla):

1. Proje analizi, benzer uygulamaların incelenmesi, veri temini, veritabanı şemalarının tasarımı, Ollama testleri ve altyapının tamamlanması
2. Kongre için kapsam, sistem mimarisi ve arayüz prototiplerini içeren posterin baskıya hazır hale getirilmesi
3. Posterin üniversite aracılığıyla baskı kontrolü ve teslim alınması
4. Posterlerin kongre öncesinde sergi ve sunum alanına yerleştirilmesi
5. 20. Bilişim Kongresi'nde projenin akademisyenlere, öğrencilere ve sektör temsilcilerine sunulması
6. TÜBİTAK 2209-A başvurusunun yapılması
7. Kongre sonrası istemci uygulamaların (mobil/PC) kodlanması, model optimizasyonu ve entegrasyon

Raporun takvim tablosunda geçen tarihler: 14 Eylül, 5 Ekim, 19 Ekim, 4 Kasım, 5 Kasım 2026, Kasım ortası ve güz dönemi boyunca. (PDF'teki tablo düzeni nedeniyle tarih–aşama eşleşmesi burada birebir verilmedi; kesin eşleşme için orijinal PDF'e bakın.)

Güncel ve ayrıntılı takvim: `docs/gorevler/` ve `docs/plan/`.

## 9. Sonuç

Sistem, günümüz teknolojileriyle teknik ve operasyonel açıdan hayata geçirilebilir niteliktedir. Yerel yapay zeka modellerinin kullanımı hem KVKK uyumunu sağlar hem de mühendislik derinliğini artırır. Proje, öğrencilere rehberlik eden ölçeklenebilir ve somut bir dijital ürün ortaya koyma potansiyeli taşır; Bilişim Kongresi ve TÜBİTAK 2209-A hedefleriyle desteklenir.
