<!--
TASLAK (04.11.2026). Teslim: 12.11.2026 13:30, imza karşılığı, LEE tez formatında.
Biçim bu dosyada uygulanmadı; LEE şablonu gelince Word'e aktarılacak.
[DOLDUR] ile işaretli yerler bilinmiyor; tahminle doldurulmadı.
Sayılar repodaki belgelerden alındı; teslimden önce güncellenmeli (Bölüm 4, 5 ve 6).
-->

# YAPAY ZEKÂ DESTEKLİ KARİYER VE EĞİTİM YÖNLENDİRME SİSTEMİ: CAREERAI

**Bitirme Projesi Ara Sınav Raporu**

Hazırlayanlar: Ataberk Çakır ([DOLDUR: öğrenci no]), Burak Doğan ([DOLDUR: öğrenci no]), Anıl Akyıl ([DOLDUR: öğrenci no])

Danışman: [DOLDUR]

Üniversite / Fakülte / Bölüm: [DOLDUR]

İstanbul, Kasım 2026

---

## ÖN SÖZ

[DOLDUR: Şablon istiyorsa danışmana ve hocalara teşekkür metni.]

## İÇİNDEKİLER

[Word'de otomatik üretilecek. Şekil, tablo ve kısaltma listeleri de şablona göre eklenecek.]

## ÖZET

Yazılım sektöründe işverenlerin aradığı teknolojiler hızla değişmekte, öğrenciler ise kariyer hedefleri için hangi yetkinliğe öncelik vermeleri gerektiğini nesnel verilere dayanarak belirlemekte zorlanmaktadır. Bu projede geliştirilen CareerAI, öğrencinin özgeçmişini hedef pozisyona ait güncel iş ilanlarıyla karşılaştırmakta, eksik yetkinlikleri ilanlardaki talep oranlarıyla birlikte göstermekte ve bu eksikleri kapatacak eğitim kaynakları önermektedir. Kişisel verilerin kurum dışına çıkmaması için dil modeli yerel olarak çalıştırılmakta, kişisel veriler modele gönderilmeden önce maskelenmekte, özgeçmiş dosyası ve ham metni saklanmamaktadır. Öneri bağlantıları yalnızca doğrulanmış bir veri tabanından alındığından dil modelinin uydurma bağlantı üretmesi engellenmektedir.

Bu ara raporda 4 Kasım 2026 tarihine kadar yapılan çalışmalar sunulmaktadır. Bu tarih itibarıyla kullanım koşullarına uygun kaynaklardan 2.208 aktif ilan toplanmış, 374 yetkinlik ve 12 pozisyon içeren iki dilli bir taksonomi oluşturulmuş; ilan normalizasyonu, talep istatistikleri, PDF metin çıkarma, kişisel veri maskeleme, sözlük tabanlı yetkinlik çıkarımı, kimlik doğrulama ve web arayüzünün giriş ekranları tamamlanmıştır. Üç açık kaynak dil modelinin ön kıyası sonucunda Llama 3.1 8B seçilmiştir. Uçtan uca analiz akışı henüz bağlanmamıştır; planlanan 101 görevin 26'sı tamamlanmıştır ve canlıya çıkış Ocak 2027 için hedeflenmektedir.

**Anahtar Kelimeler:** Yetkinlik çıkarımı, iş ilanı analizi, yerel dil modeli, kişisel verilerin korunması, kariyer yönlendirme

## ABSTRACT

In the software industry, the technologies employers require change quickly, and students find it difficult to decide which skills to prioritize on objective grounds. CareerAI compares a student's résumé with current job postings for a target position, shows missing skills together with their demand rates, and recommends learning resources. To keep personal data on our own infrastructure, the language model runs locally, personal data is masked before reaching the model, and neither the résumé file nor its raw text is stored. Recommendation links come only from a verified database, which prevents the model from inventing links.

This interim report covers the work completed up to 4 November 2026. As of that date, 2,208 active postings have been collected from sources whose terms permit it, a bilingual taxonomy of 374 skills and 12 positions has been built, and the posting normalization, demand statistics, PDF text extraction, personal data masking, dictionary-based skill extraction, authentication and the web sign-in screens have been completed. Llama 3.1 8B was selected after a preliminary comparison of three open-source models. The end-to-end analysis flow is not yet connected; 26 of 101 planned tasks are complete, and release is targeted for January 2027.

**Keywords:** Skill extraction, job posting analysis, local language model, personal data protection, career guidance

---

## 1. GİRİŞ

### 1.1. Problem

Konteyner teknolojileri, bulut altyapıları ve yeni yazılım çatıları birkaç yıl içinde sektör standardı hâline gelebilmektedir. Üniversite müfredatlarının bu hıza anında uyum sağlaması güçtür. Öğrenci binlerce saatlik ücretsiz eğitim içeriğine erişebilmekte, ancak kariyer hedefi için hangisine öncelik vermesi gerektiğini belirlemekte zorlanmaktadır. Dolayısıyla sorun artık bilgiye erişim değil, hangi bilgiye erişileceğinin seçimidir.

### 1.2. Amaç

Projenin amacı, öğrencinin özgeçmişini hedef pozisyonun güncel iş ilanlarıyla karşılaştırarak eksik yetkinliklerini veriye dayalı biçimde göstermek ve bu eksikleri kapatacak doğrulanmış eğitim kaynaklarına yönlendirmektir. Hedeflenen çıktıya örnek olarak, öğrenciye "İncelenen backend ilanlarının belirli bir oranı bu teknolojiyi istiyor, özgeçmişinizde bu teknoloji bulunamadı, şu kaynakla başlayabilirsiniz" biçiminde bir sonuç sunulması verilebilir.

### 1.3. Kapsam

Proje yazılım ve veri alanındaki 10 hedef pozisyonla, Türkçe ve İngilizce özgeçmişlerle sınırlıdır. Sistem web, masaüstü (Electron) ve Android istemcilerinden kullanılacak, canlıya çıkış 18 Ocak 2027 tarihinde v1.0.0 sürümüyle hedeflenmektedir. Ekip üç kişiden oluşmaktadır.

### 1.4. Raporun Düzeni

Bölüm 2'de ilgili çalışmalar, Bölüm 3'te sistem tasarımı, Bölüm 4'te tamamlanan çalışmalar, Bölüm 5'te ön bulgular, Bölüm 6'da kalan çalışmalar ve riskler ele alınmıştır.

## 2. İLGİLİ ÇALIŞMALAR VE PROJENİN FARKI

### 2.1. Literatür

Çevrim içi iş ilanlarından yetkinlik tespiti son yıllarda yoğun biçimde çalışılan bir alandır. Khaouja vd. (2021), ilanlardan yetkinlik tanımlama yöntemlerini sözlük tabanlı, makine öğrenmesi tabanlı ve hibrit olarak sınıflandırmış; standart taksonomilere eşleme ve dil çeşitliliğini açık sorunlar olarak belirtmiştir. Zhang vd. (2022), İngilizce ilanlarda yetkinlik çıkarımı için etiketli bir veri seti oluşturmuş ve görevin uzman etiketlemesine rağmen zor olduğunu göstermiştir.

Büyük dil modelleri metinden yapılandırılmış bilgi çıkarmada güçlü olmakla birlikte gerçekte olmayan bilgi üretme eğilimindedir (Ji vd., 2023). Öneri sistemlerinde bu durum uydurma kurs bağlantılarına dönüşebilir. Geri getirme destekli üretim (Lewis vd., 2020) bu riski azaltan bir yaklaşımdır; bu projede kapalı bir kaynak kümesiyle uygulanacaktır.

### 2.2. Mevcut Uygulamalar

LinkedIn, Indeed ve Glassdoor gibi platformlar temel olarak anahtar kelime eşleştirmesi yapmaktadır. Türkiye'de kariyer siteleri ve üniversite kariyer merkezleri ağırlıklı olarak ilan listeleme ve danışmanlık hizmeti sunmakta, mevcut yazılımlar genellikle insan kaynaklarının aday elemesine yönelik kurgulanmaktadır. Ücretli kariyer danışmanlığı ise öğrenciler için her zaman erişilebilir değildir.

### 2.3. Projenin Farkı

- **Adayın tarafında konumlanma:** Sistem bir eleme aracı değil, bir geliştirme aracıdır.
- **Uydurma bağlantıya kapalı öneri:** Dil modeli bağlantı üretmez, yalnızca doğrulanmış veri tabanındaki kaynaklar arasından seçim yapar ve gerekçe yazar.
- **Kişisel veriyi dışarı göndermeyen mimari:** Dış yapay zekâ servisi kullanılmaz; bütün dil modeli çağrıları projenin kendi sunucusundaki açık kaynak modele yapılır.
- **Türkçe desteği:** Taksonomi ve özgeçmiş işleme Türkçe ve İngilizce için tasarlanmıştır.

## 3. SİSTEM TASARIMI

### 3.1. Genel Mimari

Sistem, istemciler, FastAPI tabanlı API, Redis kuyruğu, yapay zekâ işçisi, veri tabanı ve gece çalışan veri toplayıcıdan oluşmaktadır. Yapay zekâ analizi işlemcide dakikalar sürebildiği için istek içinde değil, kuyruk işi olarak çalıştırılır; istemci ilerlemeyi izler.

Analiz akışı şöyledir: özgeçmiş yüklenir, PDF metni çıkarılır, kişisel veriler maskelenir, yetkinlikler çıkarılır, vektör gösterimleri üretilir, ilan istatistikleriyle eşleştirme yapılır ve doğrulanmış kaynaklardan öneri oluşturulur.

**[Şekil 1: Bileşen diyagramı, `docs/diagrams/component-deployment.md`]**

**[Şekil 2: Özgeçmiş analizi sıralama diyagramı, `docs/diagrams/sequence-cv-analiz.md`]**

**[Şekil 3: Kullanım durumu diyagramı, `docs/diagrams/use-case.md`]**

### 3.2. Teknoloji Seçimleri

**Tablo 3.1.** Temel teknoloji seçimleri ve gerekçeleri

| Katman | Seçim | Gerekçe |
|---|---|---|
| API | Python 3.12, FastAPI, Pydantic v2 | Yapay zekâ ekosistemiyle aynı dil, otomatik API belgesi |
| Kuyruk | Celery, Redis 7 | Uzun süren analizlerin istekten ayrılması |
| Veri tabanı | PostgreSQL 16, pgvector | İlişkisel veri ve vektör araması tek sistemde; ayrı veri tabanı gerekmez |
| Dil modeli | Ollama, Llama 3.1 8B Instruct (q4_K_M) | Yerel çalışma, ön kıyas sonucu (Bölüm 5.3) |
| Vektör gösterimi | paraphrase-multilingual-MiniLM-L12-v2 (384 boyut) | Türkçe destekli, işlemcide hızlı (Reimers ve Gurevych, 2019, 2020) |
| PDF ve OCR | pdfplumber, PyMuPDF, Tesseract | Metin tabanlı ve taranmış belgeler |
| Web ve masaüstü | React, Vite, TypeScript, Electron | Ortak kod tabanı |
| Mobil | React Native (Expo) | Web ile aynı dil ve API istemcisi |
| Altyapı | Linux VPS (8 vCPU, 16 GB), Docker Compose, Caddy | Proje ölçeğine uygun, otomatik HTTPS |

### 3.3. Veri Modeli

Veri tabanı 17 tablodan oluşmaktadır. Kullanıcıya ait ve kimliği API'de görünen tablolarda tahmin edilemeyen UUID anahtarlar kullanılmaktadır. Özgeçmiş dosyası ve ham metni hiçbir tabloda tutulmaz; analiz kaydında yalnızca SHA-256 özeti, sayfa sayısı ve çıkarılan yetkinlikler yer alır. Vektör araması için HNSW indeksi kullanılmaktadır (Malkov ve Yashunin, 2020).

**[Şekil 4: Varlık-ilişki diyagramı, `backend/app/db/erd.svg`]**

### 3.4. Kişisel Verilerin Korunması

- Özgeçmiş dosyası ve ham metni veri tabanı, disk, log veya yedekte saklanmaz.
- Kişisel veriler dil modeline gitmeden önce maskelenir.
- Dış yapay zekâ API'si kullanılmaz.
- Rıza kayıtları sürümlü tutulur; kullanıcı verilerini indirebilir ve hesabını silebilir. Silinen hesap hemen anonimleştirilir, 30 gün sonra kalıcı olarak silinir.
- Kullanım koşulları otomatik erişimi yasaklayan sitelerden ilan toplanmaz.
- Değerlendirme setinde gerçek kişilere ait özgeçmiş kullanılmaz; set sentetiktir.

## 4. TAMAMLANAN ÇALIŞMALAR

Bu bölümdeki durumlar 4 Kasım 2026 tarihlidir. Ana dala birleşmiş işler "tamamlandı", kodu yazılmış ancak ekip incelemesi süren işler "inceleme aşamasında" olarak belirtilmiştir.

### 4.1. Proje Yönetimi ve Altyapı

- Fizibilite raporu hazırlanarak danışmana teslim edilmiştir; 20. Bilişim Kongresi posteri hazırlanıp gönderilmiştir.
- Kod tek bir depoda toplanmış, her iş ayrı dalda geliştirilip ekip incelemesinden sonra birleştirilmiştir. Bu tarihe kadar 43 değişiklik isteği birleştirilmiştir.
- Her değişiklik isteğinde çalışan sürekli entegrasyon kurulmuştur: kod stili, tip denetimi, testler, veri tabanı geçişleri ve Docker imajlarının derlenmesi denetlenmektedir. Ana dalda 230 test fonksiyonu bulunmaktadır.
- Yerel geliştirme ortamı Docker Compose ile kurulmuştur.
- Sunucu sertleştirme betikleri ve test ortamı yapılandırması inceleme aşamasındadır; gerçek sunucuda henüz denenmemiştir.

### 4.2. Veri Toplama ve İşleme

- **Hukuki uygunluk:** Veri kaynaklarının robots.txt dosyaları ve kullanım koşulları incelenmiş, Türk iş sitelerinin yazılı izin olmadan kullanılamayacağı görülmüştür. Bu nedenle ilanlar resmî API'lerden toplanmaktadır.
- **İlan havuzu:** Kullanım koşullarına uygun API'lerden 2.208 aktif ilan toplanmıştır (Mayıs–Ekim 2026). Açık lisanslı (CC0) bir veri seti (Vidros vd., 2017) yedek olarak pasif tutulmaktadır. İki yeni kaynak (Jobicy, Arbeitnow) inceleme aşamasındadır.
- **Taksonomi:** ESCO sınıflandırması (Avrupa Komisyonu) ve elle derlenen teknoloji listesinden 374 yetkinlik, 8 kategori ve 12 pozisyon içeren iki dilli bir taksonomi oluşturulmuştur.
- **Normalizasyon:** HTML temizleme, dil tespiti, kişisel verilerin maskelenmesi, başlıktan pozisyon atama ve yinelenen ilanların ayıklanması (Broder, 1997) tamamlanmıştır. Pozisyon yalnızca başlıktan belirlenmektedir; yetkinliklerden tahmin edilseydi talep oranları yapay olarak yükselirdi.
- **Talep istatistikleri:** Her pozisyon ve yetkinlik çifti için son 6 ayın aktif ilanlarından talep oranı hesaplanmaktadır. 50'den az ilanla hesaplanan pozisyonlar "düşük güven" olarak işaretlenmektedir.
- **Gece toplama:** Toplama, normalizasyon ve istatistik yenileme adımları Celery beat ile her gece 03.00'te çalışacak şekilde hazırlanmıştır.
- **Eğitim kaynakları:** Doğrulanmış kaynak havuzunun ilk bölümü (447 kaynak) oluşturulmuştur; çalışma sürmektedir.

### 4.3. Yapay Zekâ Modülleri

- **PDF metin çıkarma:** Tek sütunlu, çok sütunlu ve tablolu belgelerden metin çıkarılmakta; taranmış, şifreli ve bozuk dosyalar ayırt edilmektedir.
- **Kişisel veri maskeleme:** Ad, telefon, e-posta, kimlik numarası, adres ve doğum tarihi düzenli ifadeler ve yerel bir isim varlığı tanıma modeliyle (BERTurk) maskelenmektedir.
- **Yetkinlik çıkarımı v1:** Sözlük ve kural tabanlı çıkarım tamamlanmıştır. İlan ve özgeçmiş tarafları aynı eşleyiciyi kullanmaktadır.
- **Model ön kıyası:** Üç açık kaynak model karşılaştırılmıştır (Bölüm 5.3).
- **Değerlendirme seti:** Sentetik özgeçmiş üreticisi yazılmış ve 13 özgeçmiş oluşturulmuştur (10'u PDF); hedef 50'dir. Elle etiketleme sürmektedir.

### 4.4. Arka Uç

- **API iskeleti:** Katmanlı yapı, standart hata biçimi (RFC 7807), istek kimliği ve kişisel veri içermeyen log kurulmuştur.
- **Kimlik doğrulama:** Kayıt, giriş, e-posta doğrulama, şifre sıfırlama, argon2id ile parola saklama, kısa ömürlü erişim belirteci ve tek kullanımlık yenileme belirteci tamamlanmıştır.
- **Profil ve KVKK uçları:** Profil ve hedef pozisyon, sürümlü rıza kaydı, verilerimi indir ve hesabımı sil işlevleri tamamlanmıştır.
- **İstek sınırları:** Redis tabanlı sınırlar tamamlanmıştır (genel 100/dk, giriş ve kayıt 10/dk).
- **İnceleme aşamasında:** PDF özgeçmiş yükleme ucu ve açık rızanın geri alınması.

### 4.5. Web Arayüzü

- Tıklanabilir prototip (10 ekran) ve tasarım sistemi (açık/koyu tema, form bileşenleri, grafikler) hazırlanmıştır.
- Web altyapısı (React, TypeScript) ve API tiplerinin otomatik üretimi kurulmuştur.
- Giriş, kayıt, KVKK onayı, şifre sıfırlama ve e-posta doğrulama ekranları tamamlanmıştır.

**[Şekil 5: Giriş veya kayıt ekranı görüntüsü]**

**[Şekil 6: Sonuç panosu prototipi, `web/prototip/index.html`]**

### 4.6. Ekip İçi İş Bölümü

**Tablo 4.1.** Sorumluluk alanları ve ilerleme (4 Kasım 2026, ana dal)

| Üye | Sorumluluk | Biten görev | Biten iş (planlanan saat) |
|---|---|---|---|
| Ataberk Çakır | Veri toplama, veri tabanı, altyapı | 11 / 36 | 91 / 283 |
| Burak Doğan | Yapay zekâ modülleri, mobil | 5 / 28 | 48 / 260 |
| Anıl Akyıl | Arka uç, web arayüzü | 10 / 37 | 106 / 299 |
| **Toplam** | | **26 / 101** | **245 / 842 (%29)** |

## 5. ÖN BULGULAR

Bu bölümdeki sonuçlar ön çalışmadır. Yöntemin uygulanabilirliğini gösterir; nihai başarı ölçümleri değildir.

### 5.1. İlan Verisi

İlanların %88'inde en az bir yetkinlik bulunmuş, ilan başına ortalama 7,5 yetkinlik çıkarılmıştır. İlanların %39,6'sı başlıktan bir hedef pozisyona eşlenmiş, elle yapılan 30 ilanlık kontrolde atamalar doğru çıkmıştır.

**Tablo 5.1.** Örnek pozisyonlarda ilan sayısı ve en çok istenen yetkinliğin talep oranı (Ekim 2026)

| Pozisyon | İlan sayısı | En çok istenen yetkinliğin oranı |
|---|---|---|
| Tam yığın geliştirici | 219 | %62 |
| DevOps mühendisi | 130 | %52 |
| Arka uç geliştirici | 126 | %42 |
| Makine öğrenmesi mühendisi | 109 | %60 |

**Sınırlılık:** Havuz İngilizce ve uzaktan çalışma ilanı ağırlıklıdır; 12 pozisyonun 4'ünde 50'den az ilan bulunmaktadır.

### 5.2. Kişisel Veri Maskeleme

58 öğelik sentetik bir sette ad yakalama oranı yalnızca kurallarla %44 iken, kurallar, yerel model ve taksonomi filtresi birlikte kullanıldığında %100'e çıkmıştır. Set küçük ve sentetiktir. Ekip incelemelerinde gerçek ilan metinlerinde yanlış pozitifler bulunarak düzeltilmiş, bitişik yazılan bazı kimlik numarası biçimlerinin kaçırıldığı da saptanmıştır. Bu çalışma sürmektedir.

### 5.3. Dil Modeli Ön Kıyası

Üç açık kaynak model, 10 Türkçe sentetik özgeçmiş üzerinde yerel olarak karşılaştırılmıştır. JSON şeması zorunlu kılındığında bütün çıktılar geçerli olmuştur (30/30). Şema kullanılmadığında geçerli çıktı oranı model başına 6–8/10'dur.

**Tablo 5.2.** Modellerin özgeçmiş başına süresi ve bellek kullanımı

| Model | İşlemci (sn) | Grafik işlemci (sn) | Bellek, işlemci (GB) |
|---|---|---|---|
| **Llama 3.1 8B** | **53** | 8,6 | 5,8 |
| Gemma 2 9B | 71 | 21,2 | 6,1 |
| Qwen 2.5 7B | 73 | 10,4 | 5,1 |

Üretim sunucusunda grafik işlemci bulunmayacağı için işlemcide en hızlı model olan Llama 3.1 8B seçilmiş, Gemma 2 9B yedek olarak belirlenmiştir.

**Bu ölçümün sınırları:**
- Süre yalnızca yetkinlik çıkarımını kapsar ve geliştirici bilgisayarında ölçülmüştür; 8 vCPU'luk sunucuda ölçüm yapılmamıştır.
- Doğruluk sonucu bu raporda verilmemiştir, çünkü referans etiketler geçicidir ve insan etiketlemesi değildir. Doğruluk, elle etiketlenen setle ölçülecektir (hedef F1 ≥ 0,80).
- Set yalnızca Türkçe 10 özgeçmişten oluşmaktadır; taranmış 2 özgeçmişte OCR hazır olmadığı için metin doğrudan verilmiştir.

## 6. KALAN ÇALIŞMALAR VE RİSKLER

### 6.1. Plandan Sapmalar

- Kapsamın dondurulması (MVP) ve başlangıç toplantısı görevleri planlanan tarihte kapanmamıştır; kapsam taslağı ekip kararı beklemektedir. [DOLDUR: Toplantı yapıldıysa tarih ve sonuç.]
- Sunucu ve alan adı temini gecikmiştir; hazırlık betikleri yazılmış, sunucu henüz alınmamıştır. [DOLDUR: Ataberk teyit etsin.]
- Başlangıç planındaki izinli gerçek özgeçmişler yerine, etik ve KVKK riskini ortadan kaldırmak için sentetik değerlendirme setine geçilmiştir.
- Kararlaştırılan bütün değişiklikler `docs/kararlar.md` dosyasında gerekçeleriyle tutulmaktadır.

### 6.2. Takvim

**Tablo 6.1.** Kalan başlıca işler

| İş | Sorumlu | Hedef tarih |
|---|---|---|
| Özgeçmiş yükleme ucu | Anıl | 08.11.2026 |
| OCR yedek akışı | Burak | 08.11.2026 |
| TÜBİTAK 2209-A başvurusu | Ataberk | 11.11.2026 |
| Kongre sunumu ve demo | Anıl | 15.11.2026 |
| Analiz kuyruğu | Anıl | 15.11.2026 |
| Yetkinlik çıkarımı v2 (dil modeli), vektör servisi | Burak | 22.11.2026 |
| Sonuç uçları, yükleme ve bekleme ekranı | Anıl | 22.11.2026 |
| Eşleştirme ve kaynak önerisi | Burak | 29.11.2026 |
| Değerlendirme seti, sonuç panosu, eğitim kaynağı havuzu | Burak, Anıl, Ataberk | 29.11.2026 |
| Model değerlendirme raporu, yapay zekâ işçisinin bağlanması | Burak | 06.12.2026 |
| Mobil ve masaüstü uygulamaları | Burak, Anıl | 20.12.2026 |
| Güvenlik incelemesi, yedekleme, izleme | Ataberk | 13.12.2026 |
| Uçtan uca testler, yük testi, canlı ortam | Ataberk | 20.12.2026 |
| Google Play kapalı test başlangıcı | Anıl | En geç 21.12.2026 |
| Beta kullanım | Anıl | 10.01.2027 |
| Çıkış kararı | Ekip | 15.01.2027 |
| **v1.0.0 canlıya çıkış** | **Ekip** | **18.01.2027** |

### 6.3. Başlıca Riskler

**Tablo 6.2.** Başlıca riskler ve önlemler

| Risk | Önlem |
|---|---|
| Dil modelinin işlemcili sunucuda yavaş çalışması | Kuyruk ve ilerleme ekranı, sunucuda ölçüm, gerekirse daha küçük model |
| Türkçe ilan verisinin yetersiz kalması | Türk sitelerinden yazılı izin isteme, birden çok kaynak, düşük güven uyarısı |
| Türkçe ve farklı biçimli özgeçmişlerde düşük doğruluk | Dengeli değerlendirme seti, sözlük ve dil modelinin birlikte kullanımı |
| Kişisel veri sızıntısı | Saklamama kuralı, maskeleme testleri, log maskeleme, güvenlik incelemesi |
| Sentetik setin gerçek özgeçmişleri tam temsil etmemesi | Dağılım planı; sınırlılığın raporlanması |
| Modüllerin birbirine uymaması | Ortak veri sözleşmeleri, erken uçtan uca bağlama |
| Tek sunucunun tek hata noktası olması | Şifreli yedek, izleme, kurtarma tatbikatı |

## 7. SONUÇ

Projenin veri, yapay zekâ ön işleme ve kullanıcı yönetimi temelleri büyük ölçüde hazırlanmıştır. Ön bulgular yerel modelle yapılandırılmış yetkinlik çıkarımının uygulanabilir olduğunu göstermektedir. Temel açık iş, bu parçaların uçtan uca analiz akışında birleştirilmesi ve doğruluğun elle etiketlenmiş setle ölçülmesidir. Bir sonraki aşamada analiz kuyruğu, dil modeli tabanlı çıkarım, eşleştirme, kaynak önerisi ve sonuç panosu tamamlanacaktır.

## YAPAY ZEKÂ ARAÇLARININ KULLANIMI

[DOLDUR: Hocaya sorulup bu bölümün gerekip gerekmediği ve biçimi netleştirilecek.]

Bu raporun ilk taslağı ve projedeki kodun bir bölümü Anthropic'in Claude (Claude Opus 5.5) aracı desteğiyle hazırlanmıştır. Sentetik özgeçmiş metinlerinin üretiminde de aynı araç kullanılmıştır. İçerik ekip tarafından gözden geçirilmiştir. Ürünün kendisinde dış yapay zekâ servisi kullanılmamaktadır.

## KAYNAKLAR

[Biçim LEE şablonuna göre düzenlenecek.]

Avrupa Komisyonu. "ESCO: European Skills, Competences, Qualifications and Occupations (sınıflandırma sürümü v1.2.1)". ESCO Portalı. https://esco.ec.europa.eu, Son erişim tarihi: 26 Ekim 2026.

Broder, A. Z. 1997. "On the Resemblance and Containment of Documents", Proceedings. Compression and Complexity of SEQUENCES 1997, 21-29. Los Alamitos: IEEE Computer Society. https://doi.org/10.1109/SEQUEN.1997.666900

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., Fung, P. 2023. "Survey of Hallucination in Natural Language Generation", ACM Computing Surveys, 55 (12), 1-38. https://doi.org/10.1145/3571730

Khaouja, I., Kassou, I., Ghogho, M. 2021. "A Survey on Skill Identification From Online Job Ads", IEEE Access, 9, 118134-118153. https://doi.org/10.1109/ACCESS.2021.3106120

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., Kiela, D. 2020. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", Advances in Neural Information Processing Systems, 33, 9459-9474. https://doi.org/10.48550/arXiv.2005.11401

Malkov, Y. A., Yashunin, D. A. 2020. "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs", IEEE Transactions on Pattern Analysis and Machine Intelligence, 42 (4), 824-836. https://doi.org/10.1109/TPAMI.2018.2889473

Reimers, N., Gurevych, I. 2019. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks", Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP), 3980-3990. https://doi.org/10.18653/v1/D19-1410

Reimers, N., Gurevych, I. 2020. "Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation", Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP), 4512-4525. https://doi.org/10.18653/v1/2020.emnlp-main.365

Vidros, S., Kolias, C., Kambourakis, G., Akoglu, L. 2017. "Automatic Detection of Online Recruitment Frauds: Characteristics, Methods, and a Public Dataset", Future Internet, 9 (1), 6. https://doi.org/10.3390/fi9010006

Zhang, M., Jensen, K. N., Sonniks, S. D., Plank, B. 2022. "SkillSpan: Hard and Soft Skill Extraction from English Job Postings", Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, 4962-4984. https://doi.org/10.18653/v1/2022.naacl-main.366
