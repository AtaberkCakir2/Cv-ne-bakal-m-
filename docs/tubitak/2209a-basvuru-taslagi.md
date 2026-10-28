# TÜBİTAK 2209-A Başvuru Taslağı (2026 çağrısı)

> **Durum: TASLAK v0.1 (29.10.2026)** · Görev: T-028 (Ataberk; destek Burak, Anıl) · Son başvuru: **11.11.2026 17:30** (danışman onayı dahil), kuruluş e-imzası 16–23.11.2026.
>
> Bu dosya TYBS'deki formun adımlarıyla aynı sırada yazıldı. Metinler buradan kopyalanıp TYBS'ye yapıştırılacak. Form ayrıca bir dosya yüklemeyi kabul etmiyor; öneri sistemde oluşturuluyor. Kaynak: TÜBİTAK "2209-A Başvuru İçeriği Bilgi Notu" (2026).
>
> **Önemli:**
> - Taslağın ilk hali üretken yapay zekâ desteğiyle hazırlandı. TÜBİTAK ÜYZ rehberine göre önemli ölçüde kullanım şeffaf biçimde beyan edilmeli. İçeriğin doğruluğundan ekip ve danışman sorumlu.
> - Gönderilmeden önce ekip ve danışman her cümleyi kontrol etmeli. `[DOLDUR: …]` ve `[KARAR: …]` işaretli yerler açık.

## 0. Form kuralları (2026 çağrısı, TÜBİTAK sayfası ve Bilgi Notu)

| Kural | Bizim için anlamı |
|---|---|
| Öneri **Türkçe**; şablondaki en az karakter sınırları (bölüm başına ≥ 350 karakter) | Her bölüm bu sınırın çok üstünde |
| Özet 25–450 kelime; bilimsel nitelik, yöntem, proje yönetimi ve yaygın etkiyi kapsamalı | Özet en sonda kesinleşir |
| **Kurum, firma, ticari ürün veya marka öne çıkarılmaz** (başlık dahil) | Metinde ilan siteleri, model ve yazılım adları yerine genel terimler kullanıldı ("yerel olarak çalıştırılan açık kaynak büyük dil modeli" gibi) |
| Çalışma takviminde literatür taraması, rapor yazımı, sonuç paylaşımı ve malzeme alımı **ayrı iş adımı olamaz**; başarı ölçütü ağırlıklarının toplamı 100 | Takvim buna göre kuruldu |
| Kaynakçadaki her kaynağa metin içinde atıf; **DOI varsa zorunlu** | Kaynakçadaki DOI'ler Crossref/DataCite'tan doğrulandı (29.10.2026) |
| Bütçe en fazla **12.000 TL**, süre en fazla **12 ay**. Kapsam: makine-teçhizat, sarf, seyahat, hizmet alımı. Kongre katılımı, yayın ve gündelik giderleri kapsam dışı | Bkz. Bölüm 7 |
| Yürütücü + en fazla **4** proje ortağı; herkesin ARBİS kaydı güncel; danışmanın YÖK kaydı güncel | Bkz. Bölüm 8 |
| İnsan katılımcılı çalışmalarda **Etik Kurul Onayı veya Muafiyet Belgesi** e-BİDEB'e yüklenmezse proje yürürlüğe girmez | Kullanıcı çalışması ve CV toplama nedeniyle gerekli; bkz. Bölüm 8 |

Değerlendirme ağırlıkları: **Bilimsel nitelik %35 · Yöntem %25 · Proje yönetimi %20 · Yaygın etki %20.**

---

## Proje başlığı

**Öneri:** Kişisel Veriyi Cihaz Dışına Çıkarmayan Yerel Dil Modeli ile Öğrenci Özgeçmişlerinde Yetkinlik Açığı Tespiti ve Talep Odaklı Eğitim Kaynağı Önerisi

*Alternatif (daha kısa):* İş İlanı Analizi ve Yerel Büyük Dil Modeli ile Öğrencilere Yönelik Yetkinlik Açığı Tespit ve Öğrenme Kaynağı Öneri Sistemi

`[KARAR: başlık]`

## Anahtar kelimeler

Yetkinlik çıkarımı; iş ilanı analizi; büyük dil modeli; geri getirme destekli üretim; kişisel verilerin korunması; kariyer rehberliği

---

## ÖZET (25–450 kelime; şu an ~250 kelime)

Yazılım sektöründe istenen teknolojiler, üniversite müfredatlarının güncellenme hızından daha hızlı değişmektedir. Öğrenciler hedefledikleri pozisyonun güncel olarak hangi yetkinlikleri gerektirdiğini ve kendilerinin hangi konularda eksik kaldığını nesnel olarak belirlemekte zorlanmaktadır. Mevcut çözümler çoğunlukla işverenin aday elemesine yöneliktir; öğrenciye "neyi, nereden öğrenmeli" sorusunun cevabını vermez. Bu projede öğrencinin özgeçmişini (PDF) okuyan, hedef pozisyon için güncel iş ilanlarından hesaplanan talep istatistikleriyle karşılaştıran, eksik yetkinlikleri talep oranına göre sıralayan ve her eksik için doğrulanmış eğitim kaynakları öneren bir sistem geliştirilecek ve değerlendirilecektir.

Yöntem; ilan verisinin kullanım koşullarına uygun kaynaklardan toplanıp normalize edilmesi, 374 yetkinlik ve 12 hedef pozisyondan oluşan iki dilli bir taksonomi ile etiketlenmesi, pozisyon × yetkinlik talep oranlarının hesaplanması, özgeçmişten yetkinliklerin sözlük tabanlı yöntem ile sunucuda yerel çalışan açık kaynak bir büyük dil modelinin birlikte kullanıldığı hibrit bir yaklaşımla çıkarılması ve önerilerin yalnızca doğrulanmış kaynak veritabanından seçilmesine (geri getirme destekli üretim) dayanır. Kişisel veriler modele gönderilmeden önce maskelenir; özgeçmiş dosyası ve ham metin hiçbir yerde saklanmaz.

Başarı; en az 50 elle etiketlenmiş özgeçmiş üzerinde yetkinlik çıkarımında F1 ≥ 0,80, üç değerlendiricinin öneri alakalılığı puanında ≥ 4,0/5, uydurma bağlantı oranında %0, merkezi işlem birimli bir sunucuda analiz süresinde p95 < 120 sn ve 20–30 öğrenciyle yapılacak kullanılabilirlik çalışmasında SUS ≥ 70 ile ölçülecektir. Proje altı iş paketiyle 12 ayda yürütülecektir. Ön çalışmada 2.048 güncel ilanlık havuz ve taksonomi tamamlanmıştır.

Beklenen çıktılar: web, masaüstü ve mobil istemcileri olan çalışan bir sistem, Türkçe/İngilizce yetkinlik taksonomisi, değerlendirme protokolü ve sonuçları, en az bir ulusal bildiri. Sistem öğrencilerin kariyer planlamasına ve üniversite kariyer merkezlerinin müfredat-sektör uyumu çalışmalarına veri sağlayacaktır.

`[DOLDUR: Bölümler kesinleşince özet en son güncellenecek.]`

---

## 1. ARAŞTIRMA ÖNERİSİNİN BİLİMSEL NİTELİĞİ

### 1.1. Konunun Önemi ve Araştırma Önerisinin Bilimsel Niteliği (≥ 350 karakter)

**Kapsam ve önem.** Yazılım ve bilişim alanında işverenlerin istediği teknolojiler (konteyner teknolojileri, bulut altyapıları, yeni çatı yazılımlar) birkaç yıl içinde sektör standardı hâline gelmektedir. Öğrenci binlerce saatlik ücretsiz eğitim içeriğine erişebilmekte, ancak kariyer hedefi için hangisine öncelik vermesi gerektiğini nesnel bir veriye dayanarak belirleyememektedir. Sorun artık bilgiye erişim değil, *hangi bilgiye* erişileceğinin seçimidir.

**Literatürdeki durum ve boşluk.** Çevrim içi iş ilanlarından yetkinlik tespiti, son yıllarda yoğun çalışılan bir alandır. Khaouja vd. (2021), ilanlardan yetkinlik tanımlama yöntemlerini sözlük tabanlı, makine öğrenmesi tabanlı ve hibrit olarak sınıflandırmış; standart taksonomilere eşleme ve dil çeşitliliğini açık sorunlar olarak belirtmiştir. Zhang vd. (2022), İngilizce ilanlarda yetkinlik çıkarımı için etiketli bir veri seti oluşturmuş ve görevin uzman etiketlemesine rağmen zor olduğunu göstermiştir. Bu çalışmaların büyük kısmı (1) **işveren/piyasa analizi** perspektifindedir, (2) İngilizce metinlere odaklanır ve (3) çıkarılan bilgiyi bireyin gelişimi için **eyleme dönüştürmez**. Büyük dil modelleri metinden yapılandırılmış bilgi çıkarmada güçlü olsa da gerçekte olmayan bilgi üretme (halüsinasyon) eğilimindedir (Ji vd., 2023). Öneri sistemlerinde bu durum uydurma kurs bağlantılarına dönüşebilir. Ayrıca özgeçmiş kişisel veri içerdiği için dış sunucularda çalışan ticari modellere gönderilmesi kişisel verilerin korunması mevzuatı açısından risklidir.

**Projenin getireceği çözüm.** Bu proje boşluğu üç noktada kapatmayı hedefler:
1. **Bireyin tarafında konumlanma:** Sistem bir eleme aracı değil, bir geliştirme aracıdır. Öğrenciye "eksiksin" demekle kalmaz; eksik yetkinliği, hedef pozisyonun güncel ilanlarındaki talep oranıyla birlikte ("incelenen ilanların %75'i bu yetkinliği istiyor") ve kapatmak için doğrulanmış kaynaklarla sunar.
2. **Halüsinasyona kapalı öneri:** Eğitim kaynakları yalnızca doğrulanmış bir veritabanından gelir. Dil modeli bağlantı üretmez; yalnızca bu listeden seçip gerekçe yazar. Bu, geri getirme destekli üretim yaklaşımının (Lewis vd., 2020) kapalı bir kaynak kümesiyle uygulanmasıdır.
3. **Kişisel veriyi dışarı çıkarmayan mimari:** Tüm dil modeli çağrıları, projenin kendi sunucusunda çalışan açık kaynak bir model üzerinden yapılır. Kişisel veriler modele gitmeden önce maskelenir; özgeçmiş dosyası ve ham metin saklanmaz, yalnızca özet (hash) ve çıkarılan yetkinlikler tutulur.

**Araştırma sorusu.** Öğrenci özgeçmişinden çıkarılan yetkinlikler, güncel iş ilanlarından hesaplanan pozisyon bazlı talep istatistikleriyle karşılaştırıldığında; kişisel veriyi kurum dışına göndermeyen yerel bir dil modeliyle, hangi doğrulukta yetkinlik açığı tespiti ve ne düzeyde alakalı kaynak önerisi üretilebilir?

**Hipotezler.**
- **H1:** Sözlük tabanlı eşleme ile yerel dil modelini birleştiren hibrit yetkinlik çıkarımı, yalnızca sözlük tabanlı yönteme göre anlamlı biçimde daha yüksek F1 değerine ulaşır ve etiketli test setinde F1 ≥ 0,80 sağlar.
- **H2:** Kaynak önerisinin doğrulanmış veritabanıyla sınırlandırılması, uydurma bağlantı oranını %0'da tutarken öneri alakalılığını 5'li ölçekte ≥ 4,0 düzeyinde sağlar.
- **H3:** Merkezi işlem birimli (GPU'suz) tek bir sunucuda, kuyruk tabanlı mimariyle analiz süresi p95 < 120 saniyedir.

**Kalkınma planı ve öncelikli alanlarla ilişki.** `[DOLDUR: 12. Kalkınma Planı ve 2030 Sanayi ve Teknoloji Stratejisi'ndeki yapay zekâ / dijital dönüşüm / beşeri sermaye ve nitelikli işgücü başlıklarıyla ilişki. Öncelikli Alanlar listesinden (Oncelikli_Alanlar_2025-2.pdf) ilgili madde bulunup buraya madde numarasıyla yazılacak. Uygun madde bulunursa taban puan avantajı olabilir.]`

### 1.2. Amaç ve Hedefler (≥ 350 karakter)

**Amaç:** Öğrencilerin özgeçmişlerini hedef pozisyonun güncel sektör talebiyle nesnel olarak karşılaştıran, eksik yetkinlikleri talep oranına göre önceliklendiren ve her eksik için doğrulanmış öğrenme kaynakları öneren, kişisel veriyi koruyan bir sistem geliştirmek ve bu sistemin doğruluğunu, öneri kalitesini ve kullanılabilirliğini ölçmek.

**Ölçülebilir hedefler:**

| # | Hedef | Ölçüt | Hedef değer |
|---|---|---|---|
| H-1 | Güncel ilan havuzu | Kullanım koşullarına uygun kaynaklardan aktif ilan sayısı; pozisyon başına ilan | ≥ 3.000 aktif ilan; 10 hedef pozisyonun en az 8'inde ≥ 50 ilan |
| H-2 | Yetkinlik taksonomisi | İki dilli (TR/EN) yetkinlik ve eş anlamlı sayısı | ≥ 300 yetkinlik (ön çalışmada 374'e ulaşıldı), ≥ 10 hedef pozisyon |
| H-3 | Yetkinlik çıkarım doğruluğu | Elle etiketlenmiş ≥ 50 özgeçmişte micro-F1 | ≥ 0,80 |
| H-4 | Öneri kalitesi | 3 değerlendiricinin 1–5 alakalılık puanı ortalaması; uydurma bağlantı oranı | ≥ 4,0; %0 |
| H-5 | Kaynak havuzu | Doğrulanmış eğitim kaynağı; yetkinlik başına kaynak | ≥ 900; her yetkinlik için ≥ 3 (Türkçe öncelikli) |
| H-6 | Performans ve güvenilirlik | Analiz süresi p95; analiz başarı oranı | < 120 sn; ≥ %95 |
| H-7 | Kullanılabilirlik | 20–30 öğrenciyle Sistem Kullanılabilirlik Ölçeği (SUS) | ≥ 70; kritik hata 0 |
| H-8 | Kişisel veri | Maskeleme testinde telefon, e-posta ve kimlik numarası yakalama oranı; saklanan özgeçmiş/ham metin | %100; 0 |

---

## 2. YÖNTEM (≥ 350 karakter)

**Araştırma tasarımı.** Proje, bir yazılım sisteminin geliştirilmesi ile bu sistem üzerinde yürütülecek nicel değerlendirme çalışmalarından oluşur: (a) etiketli test seti üzerinde karşılaştırmalı doğruluk deneyi, (b) uzman değerlendiricilerle öneri kalitesi değerlendirmesi, (c) yük testi, (d) öğrencilerle kullanılabilirlik çalışması.

**2.1. İlan verisinin toplanması ve normalizasyonu.** İlanlar yalnızca resmi programlama arayüzleri ve açık lisanslı veri setlerinden toplanır. Otomatik erişimi kullanım koşullarıyla yasaklayan sitelerden veri alınmaz; her kaynağın kullanım koşulları ve erişim kuralları önceden incelenmiştir. Ham ilanlar şu adımlardan geçer:
- HTML temizleme ve dil tespiti (TR/EN).
- İlan metnindeki e-posta, telefon ve kişisel profil bağlantılarının maskelenmesi.
- İlan başlığından pozisyon normalizasyonu. Kıdem ifadeleri ve teknoloji adları atılır, başlık hedef pozisyonların eş anlamlılarıyla eşlenir; Türkçe büyük/küçük harf dönüşümü ("İ/ı") ayrıca ele alınır. Pozisyon yalnızca başlıktan belirlenir; yetkinliklerden pozisyon tahmini yapılmaz. Aksi hâlde pozisyonu belirlemekte kullanılan yetkinlikler, o pozisyonun talep oranlarını yapay olarak yükseltirdi.
- Tekrar kayıtların temizlenmesi: birebir aynı metin için içerik özeti (hash), benzer metinler için 5 kelimelik parçaların Jaccard benzerliği (Broder, 1997; eşik 0,9).

**2.2. Yetkinlik taksonomisi ve ilan etiketleme.** Avrupa Komisyonu'nun açık lisanslı meslek ve beceri sınıflandırması ile elle derlenen teknoloji listesinden iki dilli bir taksonomi oluşturulmuştur: 374 yetkinlik, 8 kategori, Türkçe ve İngilizce eş anlamlılar. Yetkinliklerin 61'i uluslararası sınıflandırmadaki kavramlara bağlıdır. İlanlar bu taksonomiyle kelime sınırına duyarlı biçimde etiketlenir. Adı sıradan bir kelimeyle aynı olan yetkinlikler ayrıca ele alınır; örneğin bir programlama dili adının İngilizce bir fiille karışmaması için yalnızca o yazımla eşleşir. "Tercih sebebi" ifadesiyle geçen yetkinlikler "tercih edilen", diğerleri "zorunlu" olarak işaretlenir.

**2.3. Talep istatistikleri.** Her pozisyon × yetkinlik çifti için son 6 ayın aktif ilanlarından talep oranı hesaplanır: yetkinliği isteyen ilan sayısı / pozisyondaki toplam ilan. Bu değer kullanıcıya "ilanların %X'i" olarak gösterilir. 50 ilandan az veriyle hesaplanan pozisyonlar "düşük güven" uyarısıyla sunulur.

**2.4. Özgeçmişten yetkinlik çıkarımı (bağımsız değişken: yöntem).**
- PDF metin çıkarma; taranmış belgeler için optik karakter tanıma yedeği.
- Kişisel verilerin maskelenmesi: ad-soyad, telefon, e-posta, adres, kimlik numarası, doğum tarihi. Düzenli ifadeler ve isim varlığı tanıma ile yapılır.
- Üç yöntem karşılaştırılır:
  - **Y1:** Yalnızca sözlük tabanlı eşleme.
  - **Y2:** Yalnızca yerel dil modeli.
  - **Y3:** Hibrit. Sözlük sonucu, modele bağlam olarak verilir; model çıktısı taksonomiyle doğrulanır.
- Model, sunucuda yerel çalışan, 4-bit nicemlenmiş, yaklaşık 8 milyar parametreli açık kaynak modeller arasından ön karşılaştırmayla seçilir. Seçim ölçütleri: Türkçe doğruluk, yapılandırılmış (JSON) çıktı uyumu ve hız.
- Model çıktısı şema doğrulamasından geçer. Model çalışmazsa sözlük sonucu döner.
- Seviye ipuçları ("ileri düzey", "3 yıl") kural tabanlı olarak çıkarılır.

**2.5. Eşleştirme ve öneri.** Özgeçmiş yetkinlikleri ile pozisyon talebi karşılaştırılır. Eşleşmede çok dilli cümle gömme modelleri (Reimers ve Gurevych, 2019; 2020) ve vektör benzerlik araması (Malkov ve Yashunin, 2020) kullanılır. Ardından:
- 0–100 arası bir uyum skoru üretilir.
- Eksik yetkinlikler talep oranına göre sıralanır.
- Her eksik için doğrulanmış kaynak veritabanından (her yetkinlik için ≥ 3 kaynak; seviye, süre, ücretsiz/ücretli bilgisi) aday kaynaklar getirilir. Dil modeli yalnızca bu aday listeden seçim yapar ve Türkçe gerekçe yazar; bağlantı üretmez.

**2.6. Değişkenler ve ölçüm.**
- **Bağımsız değişkenler:** çıkarım yöntemi (Y1/Y2/Y3), dil modeli (aday modeller), özgeçmiş dili (TR/EN) ve biçimi (metin tabanlı/taranmış, tek/çok sütunlu).
- **Bağımlı değişkenler:** yetkinlik çıkarımında kesinlik, duyarlılık ve F1; öneri alakalılık puanı; uydurma bağlantı oranı; analiz süresi; SUS puanı.

**2.7. Etiketli test seti ve istatistiksel yöntemler.**
- **Test seti:** En az 50 özgeçmiş (TR + EN, farklı biçimler, en az 5'i taranmış). Özgeçmişler sahiplerinin yazılı izniyle toplanır ve anonimleştirilir. Her özgeçmiş iki kişi tarafından bağımsız etiketlenir, anlaşmazlıkları üçüncü kişi çözer. Etiketleyiciler arası F1 < 0,85 ise etiketleme kılavuzu güncellenir.
- **Doğruluk:** Özgeçmiş bazında ve toplamda micro-F1 raporlanır; %95 güven aralıkları bootstrap ile hesaplanır. Yöntemler (H1) aynı özgeçmişler üzerinde eşleştirilmiş olarak karşılaştırılır: özgeçmiş bazında F1 farkları için Wilcoxon işaretli sıralar testi ve eşleştirilmiş bootstrap, α = 0,05.
- **Öneri kalitesi (H2):** Üç değerlendiricinin puanlarının ortalaması alınır, değerlendiriciler arası uyum raporlanır.
- **Performans (H3):** 20 eşzamanlı kullanıcıyla 30 dakikalık yük testinde p50/p95 süreler ölçülür.
- **Kullanılabilirlik:** 20–30 öğrenciyle SUS (Brooke, 1996) uygulanır; yorumlama Bangor vd. (2008) ölçeğine göre yapılır.

**2.8. Ön çalışma (fizibilite).** Proje başlangıcında aşağıdakiler tamamlanmıştır:
- Veri kaynaklarının hukuki uygunluk incelemesi (robots.txt ve kullanım koşulları).
- Kullanım koşullarına uygun programlama arayüzlerinden **2.048 güncel ilan** (Mayıs–Ekim 2026). Yedek olarak açık lisanslı (CC0) bir ilan veri seti (Vidros vd., 2017) pasif tutulmaktadır.
- 374 yetkinlik ve 12 pozisyonluk taksonomi.
- Normalizasyon hattı. İlanların %88'inde en az bir yetkinlik bulundu, ilan başına ortalama 7,5. %39,6'sı başlıktan bir hedef pozisyona eşlendi; elle yapılan 30 ilanlık kontrolde atamalar doğru çıktı.
- Pozisyon × yetkinlik talep istatistikleri.
- Veritabanı şeması ve otomatik test/sürekli entegrasyon altyapısı.

Bu sonuçlar yöntemin uygulanabilirliğini göstermektedir. Ayrıca bir risk de ortaya koymuştur: mevcut havuz İngilizce ve uzaktan çalışma ilanı ağırlıklıdır ve 12 pozisyondan 7'sinde 50'den az ilan vardır. Bu risk İP1'de ele alınmaktadır.

**Yöntemlerin çalışma takvimiyle ilişkisi:** 2.1–2.3 → İP1; 2.7 test seti → İP2; 2.4 → İP3; 2.5 → İP4; performans → İP5; kullanılabilirlik → İP6.

---

## 3. PROJE YÖNETİMİ

### 3.1. Çalışma Takvimi

Kurallar: Toplam süre ≤ 12 ay. Literatür taraması, rapor, sonuç paylaşımı ve malzeme alımı ayrı iş adımı olarak yazılmadı. Başarı ölçütü ağırlıklarının toplamı **100**.

`[KARAR: Takvim — Ürünün canlıya çıkışı 18.01.2027, ama destek kararı büyük olasılıkla 2027 baharında açıklanacak. Proje süresinin bu tarihten sonra başlayacağı varsayılarak iş paketleri Ay 1–12 olarak yazıldı. Başlangıç tarihi ve canlıya çıkış öncesi yapılan işlerin "ön çalışma" mı sayılacağı danışmanla netleştirilmeli.]`

| No | İş paketi | Kim | Süre | Başarı ölçütü | Projenin başarısına katkı (%) |
|---|---|---|---|---|---|
| İP1 | İlan veri hattının genişletilmesi: yeni ve Türkçe kaynaklar, gece otomatik toplama, talep istatistiklerinin günlük yenilenmesi | `[DOLDUR]` | Ay 1–3 | ≥ 3.000 aktif ilan; 10 hedef pozisyonun ≥ 8'inde ≥ 50 ilan; toplama başarı oranı ≥ %95 | 15 |
| İP2 | Etiketli test setinin oluşturulması (izinli ve anonimleştirilmiş özgeçmişler, çift etiketleme) | `[DOLDUR]` | Ay 1–3 | ≥ 50 özgeçmiş; etiketleyiciler arası F1 ≥ 0,85 | 10 |
| İP3 | Yetkinlik çıkarımı (sözlük, yerel model, hibrit) ve model karşılaştırma deneyi | `[DOLDUR]` | Ay 3–6 | Hibrit yöntemde micro-F1 ≥ 0,80; şema uyumlu çıktı ≥ %98; kişisel veri maskelemesi %100 | 25 |
| İP4 | Eşleştirme, uyum skoru ve doğrulanmış kaynak havuzu ile öneri | `[DOLDUR]` | Ay 4–7 | ≥ 900 doğrulanmış kaynak; uydurma bağlantı %0; alakalılık ≥ 4,0/5 | 20 |
| İP5 | Sistem entegrasyonu, istemciler ve performans/güvenlik testleri | `[DOLDUR]` | Ay 6–9 | Analiz p95 < 120 sn; analiz başarı oranı ≥ %95; kritik güvenlik bulgusu 0 | 15 |
| İP6 | Öğrencilerle kullanılabilirlik çalışması (etik kurul onaylı) ve sistemin iyileştirilmesi | `[DOLDUR]` | Ay 9–12 | 20–30 katılımcı; SUS ≥ 70; kritik hata 0 | 15 |
| | | | | **Toplam** | **100** |

### 3.2. Risk Yönetimi

| No | Risk | Alınacak tedbir (B planı) |
|---|---|---|
| R1 | Dil modelinin GPU'suz sunucuda yavaş çalışması (H3'ün sağlanamaması) | Kuyruk tabanlı asenkron analiz ve ilerleme göstergesi zaten tasarımda var. Sapmada daha küçük (3–4 milyar parametreli) model yedeği ve demo günleri için saatlik GPU kiralama. Yöntem değişmez, yalnızca model boyutu değişir. |
| R2 | Türkçe ve belirli pozisyonlarda ilan verisinin yetersiz kalması | Birden fazla kaynak; Türkçe kaynaklardan yazılı izin istenmesi; İngilizce ilanların da kullanılması. Yetersiz pozisyonlarda kullanıcıya "düşük güven" uyarısı gösterilir veya pozisyonlar birleştirilir. Hedef pozisyon sayısı 10'un altına düşmez. |
| R3 | Dil modelinin taksonomide olmayan yetkinlik veya uydurma bağlantı üretmesi | Bağlantılar yalnızca veritabanından gelir, model bağlantı üretmez. Model çıktısı taksonomi ve şemayla doğrulanır. Sapmada sözlük tabanlı sonuca dönülür (Y1), H1 karşılaştırması raporlanır. |
| R4 | Farklı biçimdeki ve Türkçe özgeçmişlerde düşük çıkarım doğruluğu (F1 < 0,80) | Çok sütunlu PDF desteği, optik karakter tanıma yedeği, eş anlamlı sözlüğünün genişletilmesi. Sapmada kullanıcının yetkinlikleri elle düzeltebildiği ekran öne alınır. Hedeften sapma hata analiziyle raporlanır. |
| R5 | Kişisel veri sızıntısı | Özgeçmiş ve ham metin saklanmaz; modele gitmeden maskeleme; günlük kayıtlarında maskeleme; şifreli yedek; en az yetki ilkesi. İhlal şüphesinde olay prosedürü uygulanır (izole etme, etki analizi, mevzuattaki sürede bildirim). |
| R6 | Etiketli test seti için yeterli izinli özgeçmiş toplanamaması | İzin formu ve anonimleştirme süreci hazır. Sapmada test seti, gerçek özgeçmiş yapısı korunarak üretilmiş sentetik özgeçmişlerle tamamlanır ve bu durum ayrıca raporlanır. |
| R7 | Kullanılabilirlik çalışmasına yeterli katılımcı bulunamaması veya etik kurul onayının gecikmesi | Başvuru İP1 döneminde yapılır; katılımcılar bölüm öğrencilerinden ve kariyer merkezi duyurusuyla toplanır. Sapmada çalışma süresi İP6 içinde uzatılır. |
| R8 | Sınav dönemlerinde ekip kapasitesinin düşmesi | Sınav haftaları takvime işlenmiştir; her modül belgelenmiştir, ekip üyeleri birbirinin işini yürütebilir. |

### 3.3. Araştırma Olanakları

| Olanak | Açıklama | Projedeki kullanımı |
|---|---|---|
| Ekip bilgisayarları | `[DOLDUR: ör. 6 çekirdek / 32 GB RAM / 4 GB ekran kartı dizüstü (Ataberk); Burak ve Anıl'ın cihazları]` | Geliştirme, yerel model denemeleri, testler |
| Kiralık sanal sunucu | 8 vCPU / 16–32 GB RAM Linux sunucu (bütçeden, hizmet alımı) | Canlı sistem, dil modeli sunucusu, veritabanı |
| Açık kaynak yazılımlar | Açık kaynak dil modelleri, ilişkisel veritabanı ve vektör arama eklentisi, web çatıları | Ücretsiz; lisans maliyeti yok |
| Sürekli entegrasyon ve sürüm kontrolü | Öğrenci/ücretsiz katman | Otomatik testler, kod incelemesi |
| Üniversite olanakları | `[DOLDUR: bölüm laboratuvarı, kariyer merkezi iş birliği vb.]` | Kullanılabilirlik çalışması katılımcı erişimi |

---

## 4. ARAŞTIRMA ÖNERİSİNİN YAYGIN ETKİSİ

| Kategori | Çıktı | Ölçülebilir hedef |
|---|---|---|
| Bilimsel/akademik | Yöntem karşılaştırması ve değerlendirme sonuçlarını içeren bildiri | ≥ 1 ulusal bildiri `[DOLDUR: hedef kongre]`; sonuçların bitirme projesi raporunda yayımlanması |
| Bilimsel/akademik | Ulusal bilişim kongresinde poster sunumu | 1 poster (2026) |
| Veri/yöntem | İki dilli yetkinlik taksonomisi ve değerlendirme protokolü | ≥ 300 yetkinlik, açık lisansla paylaşım `[KARAR: paylaşılacak mı]`; etiketleme kılavuzu |
| Toplumsal | Öğrencilerin ücretsiz kullanabileceği web, masaüstü ve mobil uygulama | Beta döneminde 20–30 öğrenci; sonrasında `[DOLDUR: hedef kullanıcı sayısı]` |
| Eğitim/kurumsal | Üniversite kariyer merkezine pozisyon bazlı yetkinlik talep raporu | Dönemlik 1 rapor `[KARAR]` |
| Teknolojik | Kişisel veriyi dışarı göndermeyen yerel model mimarisinin uygulanabilirliğinin gösterilmesi | GPU'suz sunucuda p95 < 120 sn; dış yapay zekâ servisi maliyeti 0 TL |
| Ekonomik | Ticari kariyer danışmanlığına erişemeyen öğrenciler için ücretsiz alternatif | Kullanıcı başına maliyet `[DOLDUR: sunucu maliyeti / kullanıcı]` |

## 5. BELİRTMEK İSTEDİĞİNİZ DİĞER KONULAR

- Ön çalışma sonuçlarından bir tablo eklenebilir: pozisyon başına ilan sayısı ve en çok istenen ilk 3 yetkinlik. Örnek: Full-Stack 207 ilan, ilk yetkinlik %61; Backend 112 ilan, ilk yetkinlik %43.
- Sistem mimarisi diyagramı eklenebilir: `docs/diagrams/`. Diyagram ve tablolarda ürün/marka adı geçmemeli.
- Etik: Etik kurul başvurusu ve izin formu (`ai/eval/izin-formu.md`).

## 6. EKLER

- Kullanılabilirlik anketi (SUS, 10 madde, Türkçe) ve öneri alakalılığı değerlendirme formu `[DOLDUR]`
- Özgeçmiş sahibi izin formu (`ai/eval/izin-formu.md`)

## KAYNAKLAR

> TÜBİTAK kuralı: Her kaynağa metin içinde atıf yapılmalı, DOI varsa yazılmalı. Aşağıdaki DOI'ler Crossref/DataCite üzerinden doğrulandı (29.10.2026). Biçim, TÜBİTAK'ın "bibliyografik verilerin düzenlenmesi" duyurusuna göre son kez kontrol edilmeli.

1. Bangor, A., Kortum, P. T. ve Miller, J. T. (2008). An empirical evaluation of the System Usability Scale. *International Journal of Human–Computer Interaction*, 24(6), 574–594. https://doi.org/10.1080/10447310802205776
2. Broder, A. Z. (1997). On the resemblance and containment of documents. *Proceedings. Compression and Complexity of SEQUENCES 1997*, 21–29. https://doi.org/10.1109/SEQUEN.1997.666900
3. Brooke, J. (1996). SUS: A "quick and dirty" usability scale. P. W. Jordan vd. (Ed.), *Usability Evaluation in Industry* içinde (s. 189–194). Taylor & Francis. https://doi.org/10.1201/9781498710411-35
4. Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A. ve Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*, 55(12), 1–38. https://doi.org/10.1145/3571730
5. Khaouja, I., Kassou, I. ve Ghogho, M. (2021). A survey on skill identification from online job ads. *IEEE Access*, 9, 118134–118153. https://doi.org/10.1109/ACCESS.2021.3106120
6. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N. vd. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems 33*. https://doi.org/10.48550/arXiv.2005.11401
7. Malkov, Y. A. ve Yashunin, D. A. (2020). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824–836. https://doi.org/10.1109/TPAMI.2018.2889473
8. Reimers, N. ve Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *Proceedings of EMNLP-IJCNLP 2019*, 3982–3992. https://doi.org/10.18653/v1/D19-1410
9. Reimers, N. ve Gurevych, I. (2020). Making monolingual sentence embeddings multilingual using knowledge distillation. *Proceedings of EMNLP 2020*, 4512–4525. https://doi.org/10.18653/v1/2020.emnlp-main.365
10. Vidros, S., Kolias, C., Kambourakis, G. ve Akoglu, L. (2017). Automatic detection of online recruitment frauds: Characteristics, methods, and a public dataset. *Future Internet*, 9(1), 6. https://doi.org/10.3390/fi9010006
11. Zhang, M., Jensen, K. N., Sonniks, S. D. ve Plank, B. (2022). SkillSpan: Hard and soft skill extraction from English job postings. *Proceedings of NAACL 2022*, 4962–4984. https://doi.org/10.18653/v1/2022.naacl-main.366
12. European Commission. (2024). *ESCO: European Skills, Competences, Qualifications and Occupations* (v1.2.1). https://esco.ec.europa.eu `[Metinde "Avrupa Komisyonu'nun açık lisanslı meslek ve beceri sınıflandırması" olarak geçiyor; atıf zorunlu (lisans şartı). Marka kuralı açısından kaynakçada yer alması sorun değil, danışmana teyit ettirilmeli.]`

`[DOLDUR: Sayfa numaraları ve yazar listeleri yayıncı sayfasından son kez kontrol edilmeli. Türkiye'de mezun-sektör beceri uyumsuzluğuna dair 1–2 ulusal kaynak eklenirse "önem" bölümü güçlenir.]`

---

## 7. BÜTÇE TASLAĞI (≤ 12.000 TL)

Bütçe Bilgi Notu'ndaki içerik adımlarında yok; TYBS'de ayrı bir adımda giriliyor olabilir `[DOLDUR: TYBS'de kontrol]`. Yalnızca kapsamdaki kalemler kullanıldı (hizmet alımı).

| Kalem | Tür | Hesap | Tutar |
|---|---|---|---|
| Sanal sunucu kiralama (8 vCPU / 16 GB, 12 ay) | Hizmet alımı | 12 × 700 TL | 8.400 TL |
| Sunucu dışı şifreli yedek depolama (12 ay) | Hizmet alımı | 12 × 100 TL | 1.200 TL |
| Alan adı (1 yıl) | Hizmet alımı | 1 × 800 TL | 800 TL |
| Saatlik GPU sunucu (değerlendirme deneyleri ve demo günleri) | Hizmet alımı | `[DOLDUR: saat × fiyat]` | 1.500 TL |
| **Toplam** | | | **11.900 TL** |

Notlar:
- Fiyatlar `docs/riskler.md` ve fizibilite raporundaki varsayımlardan alındı. Gerçek tekliflerle güncellenmeli; harcamalar faturalı olmalı. 32 GB sunucu kararı (açık konu) bu satırı değiştirir.
- Mobil uygulama mağazası geliştirici ücreti "hizmet alımı" kapsamına girer mi, belirsiz: `[DOLDUR: bideb2209a@tubitak.gov.tr'ye sorulabilir]`. Kongre katılımı, yayın ve yeme-içme kapsam dışı.
- Öğrencilere ve danışmana ücret ödenmez. Destek, yürütücünün kendi IBAN'ına yatar.

---

## 8. BAŞVURU ÖNCESİ YAPILACAKLAR (kontrol listesi)

| # | İş | Kim | Son tarih | Durum |
|---|---|---|---|---|
| 1 | Danışmanla görüşme: konu, ekip, takvim varsayımı (Bölüm 3.1), etik kurul ihtiyacı. Danışmanın **YÖK kaydı güncel mi?** | Ataberk (+ Burak) | 01.11 | ☐ |
| 2 | **Yürütücü** ve proje ortakları kararı (yürütücü + en fazla 4 ortak); `docs/kararlar.md`'ye yaz | Ekip + danışman | 01.11 | ☐ |
| 3 | Tüm ekip üyelerinin **ARBİS** kaydı güncel; kimse aynı dönemde başka bir 2209 başvurusunda yok | Herkes | 03.11 | ☐ |
| 4 | Taslağın ekipçe okunması; `[DOLDUR]`/`[KARAR]` alanlarının kapatılması | Herkes | 05.11 | ☐ |
| 5 | Öncelikli Alanlar listesinden uygun maddenin bulunması (Bölüm 1.1) | Ataberk | 04.11 | ☐ |
| 6 | Etik kurul: kullanıcı çalışması ve özgeçmiş toplama için onay/muafiyet sürecinin öğrenilmesi (üniversite etik kurulu) | Burak | 05.11 | ☐ |
| 7 | Bütçe tekliflerinin netleşmesi (sunucu, yedek, GPU) | Ataberk | 05.11 | ☐ |
| 8 | ÜYZ kullanım beyanı metni (taslak yapay zekâ desteğiyle hazırlandı) | Ataberk | 06.11 | ☐ |
| 9 | TYBS'ye giriş, metinlerin yapıştırılması, **"Proje Önerisini Önizle"** ile kontrol (tablolar, karakterler) | Yürütücü | 07.11 | ☐ |
| 10 | **Danışman onayı** sistemde (son gün 11.11 17:30; son güne bırakmayın) | Danışman | 09.11 | ☐ |
| 11 | Kuruluş yetkilisi e-imzası (üniversite) | Üniversite | 16–23.11 | ☐ |

**İletişim:** bideb2209a@tubitak.gov.tr · 444 66 90 · Çağrı sayfası: https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi
