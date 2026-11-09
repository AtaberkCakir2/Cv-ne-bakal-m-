<!--
TASLAK. Teslim: 12 Kasım 2026 saat 13.30. Biçim kuralları ve açık sorular: docs/ara-rapor/README.md
Yapı ve metin LEE Tez ve Proje Yazım Kılavuzu'na (Eylül 2022) göre düzenlendi; sayfa biçimi Word'e aktarılırken uygulanacak.
[DOLDUR] ile işaretli yerler bilinmiyor; tahminle doldurulmadı.
-->

<!-- DIŞ KAPAK: öğrenci adları ve basım ayı dışındaki yazılar büyük harf -->

T.C.
İSTANBUL NİŞANTAŞI ÜNİVERSİTESİ
MÜHENDİSLİK MİMARLIK FAKÜLTESİ
BİLGİSAYAR MÜHENDİSLİĞİ BÖLÜMÜ

YAPAY ZEKÂ DESTEKLİ KARİYER VE EĞİTİM YÖNLENDİRME SİSTEMİ

Ataberk ÇAKIR
Burak DOĞAN
Anıl AKYIL

BİTİRME PROJESİ ARA SINAV RAPORU

İSTANBUL
Kasım 2026

---

<!-- İÇ KAPAK -->

YAPAY ZEKÂ DESTEKLİ KARİYER VE EĞİTİM YÖNLENDİRME SİSTEMİ

Ataberk ÇAKIR ([DOLDUR: öğrenci no])
Burak DOĞAN ([DOLDUR: öğrenci no])
Anıl AKYIL ([DOLDUR: öğrenci no])

İstanbul Nişantaşı Üniversitesi
Mühendislik Mimarlık Fakültesi
Bilgisayar Mühendisliği Bölümü

Bitirme Projesi Ara Sınav Raporu

Danışman: Prof. Dr. Yaşar HOŞCAN

İstanbul
Kasım 2026

---

# ÖZET

Ataberk ÇAKIR, Burak DOĞAN, Anıl AKYIL

Yapay Zekâ Destekli Kariyer ve Eğitim Yönlendirme Sistemi

Bitirme Projesi Ara Sınav Raporu, İstanbul, 2026

Yazılım sektöründe işverenlerin aradığı teknolojiler hızla değişmekte, öğrenciler ise hangi yetkinliğe öncelik vermeleri gerektiğini nesnel verilere dayanarak belirlemekte zorlanmaktadır. Bu projede geliştirilen CareerAI, öğrencinin özgeçmişini hedef pozisyona ait güncel iş ilanlarıyla karşılaştırmakta, eksik yetkinlikleri talep oranlarıyla birlikte göstermekte ve doğrulanmış eğitim kaynakları önermektedir. Dil modeli yerel olarak çalıştırılmakta, kişisel veriler modele gönderilmeden önce maskelenmekte, özgeçmiş dosyası ve ham metni saklanmamaktadır. Öneri bağlantıları yalnızca doğrulanmış bir veri tabanından alındığı için dil modelinin uydurma bağlantı üretmesi engellenmektedir. Bu raporda 07 Kasım 2026 tarihine kadar yapılan çalışmalar sunulmaktadır. Kullanım koşullarına uygun kaynaklardan ilan toplanmış, iki dilli bir yetkinlik taksonomisi oluşturulmuş; ilan normalizasyonu, talep istatistikleri, PDF metin çıkarma, kişisel veri maskeleme, sözlük tabanlı yetkinlik çıkarımı, kimlik doğrulama, özgeçmiş yükleme ucu ve web arayüzünün giriş ekranları tamamlanmıştır. Üç açık kaynak dil modelinin ön kıyası sonucunda Llama 3.1 8B seçilmiştir. Uçtan uca analiz akışı henüz bağlanmamış, doğruluk ölçümü elle etiketlenen değerlendirme seti tamamlanmadığı için yapılmamıştır. Planlanan görevlerin 30'u tamamlanmış olup canlıya çıkış Ocak 2027 için hedeflenmektedir.

Anahtar Kelimeler: Yetkinlik çıkarımı, iş ilanı analizi, yerel dil modeli, kişisel verilerin korunması, kariyer yönlendirme

# ABSTRACT

Ataberk ÇAKIR, Burak DOĞAN, Anıl AKYIL

AI-Assisted Career and Education Guidance System

Graduation Project Interim Report, Istanbul, 2026

In the software industry, the technologies employers require change quickly, and students find it difficult to decide on objective grounds which skills to prioritize. CareerAI, developed in this project, compares a student's résumé with current job postings for a target position, shows missing skills together with their demand rates, and recommends verified learning resources. The language model runs locally, personal data is masked before reaching the model, and neither the résumé file nor its raw text is stored. This report presents the work completed up to 7 November 2026. Postings have been collected from sources whose terms permit it and a bilingual skill taxonomy has been built. Posting normalization, demand statistics, PDF text extraction, personal data masking, dictionary-based skill extraction, authentication, the résumé upload endpoint and the web sign-in screens have been completed. Llama 3.1 8B was selected after a preliminary comparison of three open-source language models. The end-to-end analysis flow is not yet connected, and accuracy has not been measured because the manually labeled evaluation set is incomplete. Thirty of the planned tasks are complete, and release is targeted for January 2027.

Keywords: Skill extraction, job posting analysis, local language model, personal data protection, career guidance

# İÇİNDEKİLER

[Word'de otomatik üretilecek: birinci derece büyük harf, ikinci derece 0,5 cm, üçüncü derece 1 cm girintili.]

# TABLOLAR DİZİNİ

[Word'de otomatik üretilecek.]

# ŞEKİLLER DİZİNİ

[Word'de otomatik üretilecek.]

# KISALTMALAR DİZİNİ

API: Uygulama programlama arayüzü (*application programming interface*)

ESCO: Avrupa beceri, yeterlilik ve meslek sınıflandırması (*European Skills, Competences, Qualifications and Occupations*)

HNSW: Hiyerarşik gezinilebilir küçük dünya (*hierarchical navigable small world*)

HTTPS: Güvenli hiper metin aktarım protokolü (*hypertext transfer protocol secure*)

JSON: JavaScript nesne gösterimi (*JavaScript object notation*)

KVKK: Kişisel Verilerin Korunması Kanunu

OCR: Optik karakter tanıma (*optical character recognition*)

PDF: Taşınabilir belge biçimi (*portable document format*)

RFC: Yorum talebi (*request for comments*)

SHA-256: 256 bitlik güvenli özet algoritması (*secure hash algorithm*)

UUID: Evrensel benzersiz tanımlayıcı (*universally unique identifier*)

---

# 1. GİRİŞ

Konteyner teknolojileri, bulut altyapıları ve yeni yazılım çatıları birkaç yıl içinde sektör standardı hâline gelebilmekte, üniversite müfredatlarının bu hıza anında uyum sağlaması ise güçleşmektedir. Öğrenci binlerce saatlik ücretsiz eğitim içeriğine erişebilmekte, ancak kariyer hedefi için hangisine öncelik vermesi gerektiğini belirlemekte zorlanmaktadır. Dolayısıyla sorun artık bilgiye erişim değil, hangi bilgiye erişileceğinin seçimidir.

Projenin konusu, öğrencinin özgeçmişini hedef pozisyonun güncel iş ilanlarıyla karşılaştırarak eksik yetkinlikleri veriye dayalı biçimde gösteren ve bu eksikleri kapatacak doğrulanmış eğitim kaynaklarına yönlendiren CareerAI adlı sistemin geliştirilmesidir. Çalışmanın önemi, öğrenciye genel tavsiye yerine güncel ilanlardan hesaplanmış talep oranlarına dayanan somut bir gelişim önceliği sunmasından kaynaklanmaktadır.

Sistemin özgün yönleri üç başlıkta toplanmaktadır: (1) bir eleme aracı olarak değil, adayın tarafında bir geliştirme aracı olarak konumlanması, (2) dil modelinin bağlantı üretmemesi ve yalnızca doğrulanmış veri tabanındaki kaynaklardan seçim yapması, (3) özgeçmişlerin dış yapay zekâ servislerine gönderilmemesi. Kapsam, yazılım ve veri alanındaki 10 hedef pozisyon ile Türkçe ve İngilizce özgeçmişlerle sınırlıdır. Sistemin web, masaüstü ve Android istemcileriyle 18 Ocak 2027 tarihinde v1.0.0 sürümü olarak yayımlanması hedeflenmektedir.

Yöntem olarak ilanlar kullanım koşullarına uygun kaynaklardan toplanmakta, normalize edilerek pozisyon bazlı talep istatistiklerine dönüştürülmekte, özgeçmişten çıkarılan yetkinlikler bu istatistiklerle karşılaştırılmaktadır. Çalışma üç kişilik ekiple, her değişikliğin ekip incelemesinden geçirildiği bir süreçle yürütülmektedir. Bölüm 2'de ilgili çalışmalar, Bölüm 3'te sistem tasarımı ve yöntem, Bölüm 4'te tamamlanan çalışmalar, Bölüm 5'te ön bulgular, Bölüm 6'da kalan çalışmalar ve riskler ele alınmış, Bölüm 7'de sonuçlar değerlendirilmiştir.

# 2. LİTERATÜR TARAMASI

## 2.1. İlgili Çalışmalar

Çevrim içi iş ilanlarından yetkinlik tespiti son yıllarda yoğun biçimde çalışılan bir alandır. Khaouja vd. (2021), ilanlardan yetkinlik tanımlama yöntemlerini sözlük tabanlı, makine öğrenmesi tabanlı ve hibrit olarak sınıflandırmış; standart taksonomilere eşleme ve dil çeşitliliğini açık sorunlar olarak belirtmiştir. Zhang vd. (2022), İngilizce ilanlarda yetkinlik çıkarımı için etiketli bir veri seti oluşturmuş ve görevin uzman etiketlemesine rağmen zor olduğunu göstermiştir.

Büyük dil modelleri metinden yapılandırılmış bilgi çıkarmada güçlü olmakla birlikte gerçekte olmayan bilgi üretme eğilimindedir (Ji vd., 2023). Öneri sistemlerinde bu durum uydurma kurs bağlantılarına dönüşebilir. Geri getirme destekli üretim (Lewis vd., 2020) bu riski azaltan bir yaklaşımdır; bu projede kapalı bir kaynak kümesiyle uygulanacaktır.

## 2.2. Mevcut Uygulamalar ve Projenin Farkı

Fizibilite çalışmasında yapılan incelemeye göre genel iş platformları ağırlıklı olarak anahtar kelime eşleştirmesine ve ilan listelemeye dayanmakta, adaya kapatması gereken eksikler için bir öğrenme yolu sunmamaktadır. Türkiye'deki kariyer siteleri ve üniversite kariyer merkezleri ise daha çok ilan listeleme ve danışmanlık hizmeti vermektedir. Ücretli kariyer danışmanlığı öğrenciler için her zaman erişilebilir değildir.

CareerAI bu uygulamalardan, yetkinlik açığını ilan verisindeki talep oranıyla göstermesi ve doğrudan eğitim kaynağına yönlendirmesiyle ayrılmaktadır. Taksonomi ve özgeçmiş işleme Türkçe ve İngilizce için tasarlanmıştır.

# 3. SİSTEM TASARIMI VE YÖNTEM

## 3.1. Genel Mimari

Sistem, istemciler, FastAPI tabanlı API, Redis kuyruğu, yapay zekâ işçisi, veri tabanı ve gece çalışan veri toplayıcıdan oluşmaktadır. Yapay zekâ analizi işlemcide dakikalar sürebildiği için istek içinde değil, kuyruk işi olarak çalıştırılmakta, istemci ilerlemeyi izlemektedir. Bileşenler Şekil 1'de, analiz akışı Şekil 2'de, kullanım durumları Şekil 3'te gösterilmiştir. Bu şekiller planlanan tasarımı göstermekte olup uçtan uca akış henüz bağlanmamıştır.

Analiz akışında özgeçmiş yüklenmekte, PDF metni çıkarılmakta, kişisel veriler maskelenmekte, yetkinlikler çıkarılmakta, vektör gösterimleri üretilmekte, ilan istatistikleriyle eşleştirme yapılmakta ve doğrulanmış kaynaklardan öneri oluşturulmaktadır.

[Görsel: `docs/diagrams/component-deployment.md`]

**Şekil 1. Planlanan sistem bileşenleri**

[Görsel: `docs/diagrams/sequence-cv-analiz.md`]

**Şekil 2. Planlanan özgeçmiş analizi akışının ana adımları**

[Görsel: `docs/diagrams/use-case.md`]

**Şekil 3. Kullanım durumu diyagramı**

## 3.2. Teknoloji Seçimleri

Temel teknoloji seçimleri ve gerekçeleri Tablo 1'de özetlenmiştir.

**Tablo 1. Temel teknoloji seçimleri ve gerekçeleri**

| Katman | Seçim | Gerekçe |
|---|---|---|
| API | Python 3.12, FastAPI, Pydantic v2 | Yapay zekâ ekosistemiyle aynı dil, otomatik API belgesi |
| Kuyruk | Celery, Redis 7 | Uzun süren analizlerin istekten ayrılması |
| Veri tabanı | PostgreSQL 16, pgvector | İlişkisel veri ve vektör aramasının tek sistemde olması |
| Dil modeli | Ollama, Llama 3.1 8B Instruct | Yerel çalışma, ön kıyas sonucu |
| Vektör gösterimi | paraphrase-multilingual-MiniLM-L12-v2 | Türkçe desteği, işlemcide hız |
| PDF ve OCR | pdfplumber, PyMuPDF, Tesseract | Metin tabanlı ve taranmış belgeler |
| Web ve masaüstü | React, Vite, TypeScript, Electron | Ortak kod tabanı |
| Mobil | React Native (Expo) | Web ile aynı dil ve API istemcisi |
| Altyapı | Docker Compose, Cloudflare Tunnel | Kiralık sunucu yerine ekip bilgisayarında çalışma, port açmadan HTTPS |

Vektör gösterimi için çok dilli cümle gömme modelleri (Reimers ve Gurevych, 2019, 2020), vektör araması için HNSW indeksi (Malkov ve Yashunin, 2020) kullanılmaktadır.

## 3.3. Veri Modeli

Veri tabanı 17 tablodan oluşmaktadır ve yapısı Şekil 4'te gösterilmiştir. Kullanıcıya ait ve kimliği API'de görünen tablolarda tahmin edilemeyen UUID anahtarlar kullanılmaktadır. Özgeçmiş dosyası ve ham metni hiçbir tabloda tutulmamakta, analiz kaydında yalnızca SHA-256 özeti, sayfa sayısı ve çıkarılan yetkinlikler yer almaktadır.

[Görsel: `backend/app/db/erd.svg`]

**Şekil 4. Veri tabanı tabloları ve ilişkileri**

## 3.4. Kişisel Verilerin Korunması

Proje genelinde aşağıdaki kurallar uygulanmaktadır:

• Özgeçmiş dosyası ve ham metni veri tabanı, disk, log veya yedekte saklanmaz.

• Kişisel veriler dil modeline gitmeden önce maskelenir ve dış yapay zekâ API'si kullanılmaz.

• Rıza kayıtları sürümlü tutulur; kullanıcı verilerini indirebilir ve hesabını silebilir. Silinen hesap hemen anonimleştirilir, 30 gün sonra kalıcı olarak silinir.

• Kullanım koşulları otomatik erişimi yasaklayan sitelerden ilan toplanmaz.

• Değerlendirme setinde gerçek kişilere ait özgeçmiş kullanılmaz; set sentetiktir.

## 3.5. Değerlendirme Yöntemi

Sistemin başarısı, elle etiketlenmiş en az 50 sentetik özgeçmişle ölçülecektir. Her özgeçmiş en az bir kişi, dengeli seçilen 20 özgeçmiş iki kişi tarafından bağımsız olarak etiketlenecek, anlaşmazlıkları üçüncü kişi çözecektir. Hedef değerler yetkinlik çıkarımında F1 ≥ 0,80, etiketleyiciler arası uyumda F1 ≥ 0,85, öneri alakalılığında üç değerlendiricinin ortalamasıyla 5 üzerinden ≥ 4,0, uydurma bağlantı oranında %0 ve üretim bilgisayarında işlemci üzerinde analiz süresinde p95 < 120 saniyedir. Bu hedeflerin ölçümü henüz yapılmamıştır.

## 3.6. Yapay Zekâ Araçlarının Kullanımı

Bu raporun hazırlanmasında ve projedeki kodun bir bölümünün yazılmasında Anthropic'in Claude (Claude Opus 5.5) yapay zekâ aracından yararlanılmıştır. Araç; rapor metninin taslağının hazırlanması, kod yazımı, kod incelemesi ve değerlendirme setindeki sentetik özgeçmiş metinlerinin üretimi için kullanılmıştır. Üretilen içeriğin tamamı ekip tarafından okunmuş, denetlenmiş ve gerektiğinde düzeltilmiştir. Rapordaki sayısal sonuçlar ekibin çalıştırdığı ölçüm ve testlerden alınmıştır. Geliştirilen sistemin kendisinde dış yapay zekâ servisi kullanılmamakta, özgeçmiş analizi yerel olarak çalışan açık kaynak bir dil modeliyle yapılmaktadır.

# 4. TAMAMLANAN ÇALIŞMALAR

Bu bölümdeki durumlar ve kaynak sayıları 07 Kasım 2026, ilan sayıları 05 Kasım 2026 tarihlidir. Ana dala birleşmiş işler tamamlandı, kodu yazılmış ancak ekip incelemesi süren işler inceleme aşamasında olarak belirtilmiştir.

## 4.1. Proje Yönetimi ve Altyapı

Fizibilite raporu hazırlanarak danışmana teslim edilmiş, 20. Bilişim Kongresi posteri hazırlanıp gönderilmiştir. Kod tek bir depoda toplanmış, her iş ayrı dalda geliştirilip ekip incelemesinden sonra birleştirilmiştir; bu tarihe kadar 53 değişiklik isteği birleştirilmiştir. Ana dal koruması açılmıştır: her değişiklik en az bir onay ve başarılı otomatik denetimler olmadan birleştirilememektedir. Her değişiklik isteğinde kod stili, tip denetimi, testler, veri tabanı geçişleri ve Docker imajlarının derlenmesi otomatik olarak denetlenmektedir. Ana dalda 271 test fonksiyonu bulunmaktadır. Yerel geliştirme ortamı Docker Compose ile kurulmuştur. Canlı ortamın ekip bilgisayarında çalıştırılmasına karar verilmiş (bkz. 6.1), alan adı alınmıştır. Bu ortamın yapılandırması, dağıtım betiği ve günlük şifreli yedekleme inceleme aşamasındadır.

## 4.2. Veri Toplama ve İşleme

Veri kaynaklarının robots.txt dosyaları ve kullanım koşulları incelenmiş, Türk iş sitelerinin yazılı izin olmadan kullanılamayacağı görülmüştür. Bu nedenle ilanlar resmî API'lerden toplanmaktadır. Yapılan çalışmalar aşağıda özetlenmiştir:

• Kullanım koşullarına uygun yedi kaynaktan 2.733 aktif ilan toplanmıştır (Mayıs–Ekim 2026; 05 Kasım 2026 itibarıyla). Açık lisanslı bir veri seti (Vidros vd., 2017) yedek olarak pasif tutulmaktadır. Jobicy ve Arbeitnow API'leri eklenmiş; dinamik sayfalar için tarayıcı tabanlı bir toplayıcı (Playwright) eklenmiş ve Python.org iş ilanlarıyla ilk örneği tamamlanmıştır.

• ESCO sınıflandırması (Avrupa Komisyonu, t.y.) ve elle derlenen teknoloji listesinden 374 yetkinlik, sekiz kategori ve 12 pozisyon içeren iki dilli bir taksonomi oluşturulmuştur. Pozisyonların 10'u kullanıcının seçebileceği hedef pozisyonlardır; veri mühendisi ve veri analisti ilanların sınıflandırılması için ayrıca eklenmiştir.

• HTML temizleme, dil tespiti, kişisel verilerin maskelenmesi, başlıktan pozisyon atama ve yinelenen ilanların ayıklanması (Broder, 1997) tamamlanmıştır. Pozisyon yalnızca başlıktan belirlenmektedir; yetkinliklerden tahmin edilseydi talep oranları yapay olarak yükselirdi.

• Her pozisyon ve yetkinlik çifti için son 6 ayın aktif ilanlarından talep oranı hesaplanmakta, 50'den az ilanla hesaplanan pozisyonlar düşük güven olarak işaretlenmektedir.

• Toplama, normalizasyon ve istatistik yenileme adımları her gece saat 03.00'te çalışacak şekilde hazırlanmıştır.

• Doğrulanmış eğitim kaynağı havuzunda 1.172 kaynak (342'si Türkçe) bulunmaktadır; 374 yetkinliğin 360'ında en az bir kaynak vardır (07 Kasım 2026). Çalışma sürmektedir.

## 4.3. Yapay Zekâ Modülleri

Özgeçmiş işleme hattının ilk parçaları aşağıdaki gibi tamamlanmıştır:

• Tek sütunlu, çok sütunlu ve tablolu belgelerden metin çıkarılmakta; taranmış, şifreli ve bozuk dosyalar ayırt edilmektedir.

• Ad, telefon, e-posta, kimlik numarası, adres ve doğum tarihi düzenli ifadeler ve yerel bir isim varlığı tanıma modeliyle maskelenmektedir.

• Sözlük ve kural tabanlı yetkinlik çıkarımı tamamlanmıştır. İlan ve özgeçmiş tarafları aynı eşleyiciyi kullanmaktadır.

• Üç açık kaynak dil modeli karşılaştırılmıştır.

• Sentetik özgeçmiş üreticisi yazılmış ve 13 özgeçmiş oluşturulmuştur (10'u PDF); hedef 50'dir. Elle etiketleme sürmektedir.

## 4.4. Arka Uç

Katmanlı API iskeleti, standart hata biçimi (RFC 7807), istek kimliği ve kişisel veri içermeyen log yapısı kurulmuştur. Kayıt, giriş, e-posta doğrulama, şifre sıfırlama, argon2id ile parola saklama, kısa ömürlü erişim belirteci ve tek kullanımlık yenileme belirteci tamamlanmıştır. Profil ve hedef pozisyon, sürümlü rıza kaydı, verilerimi indir ve hesabımı sil işlevleri eklenmiştir. Redis tabanlı istek sınırları dakikada genel 100, giriş ve kayıt için 10 istek olarak uygulanmaktadır. PDF özgeçmiş yükleme ucu ve açık rızanın geri alınması tamamlanmıştır. Analiz kuyruğu, özgeçmişin yalnızca bellekte tutulduğu geçici depo, analiz sonucu, geçmiş, silme, geri bildirim ve katalog uçları inceleme aşamasındadır. Açık rızasını geri alan kullanıcının yeni özgeçmişi işlenmemekte, kuyrukta bekleyen işi de çalıştırılmamaktadır; bu kural da inceleme aşamasındadır.

## 4.5. Web Arayüzü

On ekranlık tıklanabilir prototip ve açık ile koyu temalı tasarım sistemi hazırlanmıştır. Web altyapısı ve API tiplerinin otomatik üretimi kurulmuş; giriş, kayıt, KVKK onayı, şifre sıfırlama ve e-posta doğrulama ekranları tamamlanmıştır. Özgeçmiş yükleme, analiz bekleme, sonuç panosu, geçmiş analizler ve profil (verileri indirme, onayları yönetme, hesap silme) ekranları inceleme aşamasındadır. Aynı arayüzü Windows ve macOS'ta açan Electron masaüstü uygulamasının ilk sürümü hazırlanmış, Windows kurulum dosyası üretilerek denenmiştir. Aydınlatma metni, gizlilik politikası, kullanım koşulları ve hesap silme sayfası taslak olarak yazılmış, uygulamanın çalıştığı bilgisayardan bağımsız yayımlanacak statik sayfalara dönüştürülmüştür; metinler danışman ve hukuk birimi kontrolünü beklemektedir. Giriş ekranı Şekil 5'te, sonuç panosu prototipi Şekil 6'da gösterilmiştir.

[Görsel: ekran görüntüsü alınacak]

**Şekil 5. Giriş ekranı**

[Görsel: `web/prototip/index.html`]

**Şekil 6. Sonuç panosu prototipi (örnek veri)**

## 4.6. Ekip İçi İş Bölümü

Ekip üyelerinin sorumluluk alanları ve ilerlemeleri Tablo 2'de verilmiştir. Planlanan 101 görevin 30'u, planlanan iş saatinin %32'si tamamlanmıştır.

**Tablo 2. Sorumluluk alanları ve ilerleme (07 Kasım 2026)**

| Üye | Sorumluluk | Biten görev | Biten iş (saat) |
|---|---|---|---|
| Ataberk Çakır | Veri toplama, veri tabanı, altyapı | 14 / 36 | 109 / 283 |
| Burak Doğan | Yapay zekâ modülleri, mobil | 5 / 28 | 48 / 260 |
| Anıl Akyıl | Arka uç, web arayüzü | 11 / 37 | 114 / 299 |
| Toplam | | 30 / 101 | 271 / 842 |

# 5. ÖN BULGULAR

Bu bölümdeki sonuçlar ön çalışmadır. Yöntemin uygulanabilirliğini gösterir, nihai başarı ölçümleri değildir.

## 5.1. İlan Verisi

05 Kasım 2026 tarihindeki 2.733 aktif ilanın %90,8'inde en az bir yetkinlik bulunmuş, ilan başına ortalama 8,9 yetkinlik çıkarılmıştır. İlanların %40,2'si başlıktan bir hedef pozisyona eşlenmiş, elle yapılan 30 ilanlık kontrolde atamalar doğru çıkmıştır. Örnek pozisyonlardaki ilan sayıları ve en çok istenen yetkinliğin talep oranı Tablo 3'te verilmiştir.

**Tablo 3. Örnek pozisyonlarda ilan sayısı ve en çok istenen yetkinliğin talep oranı (05 Kasım 2026)**

| Pozisyon | İlan sayısı | Talep oranı |
|---|---|---|
| Tam yığın geliştirici | 218 | %64 (React) |
| Arka uç geliştirici | 157 | %43 (PostgreSQL) |
| DevOps mühendisi | 154 | %57 (Kubernetes) |
| Makine öğrenmesi mühendisi | 123 | %63 (Python) |

Havuzdaki ilanların tamamı İngilizcedir ve uzaktan çalışma ilanı ağırlıklıdır; 12 pozisyonun üçünde 50'den az ilan bulunmaktadır (veri bilimci 41, veri analisti 18, oyun geliştirici 5). Bu durum Türkçe ilanlar için sonuçların genellenmesini sınırlamaktadır.

## 5.2. Kişisel Veri Maskeleme

Elli sekiz öğelik sentetik bir sette ad yakalama oranı yalnızca kurallarla %44 iken, kurallar, yerel model ve taksonomi filtresi birlikte kullanıldığında %100'e çıkmıştır. Set küçük ve sentetiktir. Ekip incelemelerinde gerçek ilan metinlerinde yanlış pozitifler bulunarak düzeltilmiş, bitişik yazılan bazı kimlik numarası biçimlerinin kaçırıldığı da saptanmıştır. Bu çalışma sürmektedir.

## 5.3. Dil Modeli Ön Kıyası

Üç açık kaynak model, 10 Türkçe sentetik özgeçmiş üzerinde yerel olarak karşılaştırılmıştır. JSON şeması zorunlu kılındığında bütün çıktılar geçerli olmuş (30/30), şema kullanılmadığında geçerli çıktı oranı model başına 6–8/10 düzeyinde kalmıştır. Süre ve bellek sonuçları Tablo 4'te verilmiştir.

**Tablo 4. Modellerin özgeçmiş başına süresi ve bellek kullanımı**

| Model | İşlemci (sn) | Grafik işlemci (sn) | Bellek, işlemci (GB) |
|---|---|---|---|
| Llama 3.1 8B | 53 | 8,6 | 5,8 |
| Gemma 2 9B | 71 | 21,2 | 6,1 |
| Qwen 2.5 7B | 73 | 10,4 | 5,1 |

Analizler üretim ortamında ağırlıklı olarak işlemcide çalışacağı için işlemcide en hızlı model olan Llama 3.1 8B seçilmiş, Gemma 2 9B yedek olarak belirlenmiştir. Süre yalnızca yetkinlik çıkarımını kapsamakta ve geliştirici bilgisayarında ölçülmüş olup üretim bilgisayarında ölçüm henüz yapılmamıştır. Doğruluk sonucu verilmemiştir, çünkü referans etiketler geçicidir ve insan etiketlemesi değildir. Set yalnızca Türkçe 10 özgeçmişten oluşmakta, taranmış iki özgeçmişte OCR hazır olmadığı için metin doğrudan verilmiştir.

# 6. KALAN ÇALIŞMALAR VE RİSKLER

## 6.1. Plandan Sapmalar

Ekip kararıyla (06 Kasım 2026) sunucu kiralanmamasına, sistemin bir ekip üyesinin bilgisayarında Docker Compose ile çalıştırılmasına ve alan adına Cloudflare Tunnel ile bağlanmasına karar verilmiştir. Gerekçe, projenin amacının jüriye ve hocalara çalışan sistemi göstermek olması ve altı aylık sunucu kirasının (4.200 TL) bu kullanım için gereksiz bulunmasıdır. Kullanılan bilgisayarda planlanan sunucunun iki katı bellek (32 GB) ve bir grafik işlemci bulunmakta, tünel sayesinde modemde port açılmadan HTTPS erişimi sağlanmaktadır. Bunun bedeli, sistemin yalnızca bu bilgisayar açıkken erişilebilir olmasıdır; erişilebilirlik hedefi buna göre güncellenmiştir. Alan adı alınmıştır. Başlangıç planındaki izinli gerçek özgeçmişler yerine, etik ve KVKK riskini ortadan kaldırmak için sentetik değerlendirme setine geçilmiştir. Alınan kararlar gerekçeleriyle proje deposunda tutulmaktadır.

## 6.2. Takvim

Kalan başlıca işler ve hedef tarihleri Tablo 5'te listelenmiştir.

**Tablo 5. Kalan başlıca işler**

| İş | Sorumlu | Hedef tarih |
|---|---|---|
| OCR yedek akışı | Burak Doğan | 08 Kasım 2026 |
| TÜBİTAK 2209-A başvurusu | Ataberk Çakır | 11 Kasım 2026 |
| Kongre sunumu ve demo | Anıl Akyıl | 15 Kasım 2026 |
| Analiz kuyruğu | Anıl Akyıl | 15 Kasım 2026 |
| Dil modeli tabanlı çıkarım, vektör servisi | Burak Doğan | 22 Kasım 2026 |
| Sonuç uçları, yükleme ve bekleme ekranı | Anıl Akyıl | 22 Kasım 2026 |
| Değerlendirme seti | Burak Doğan | 28 Kasım 2026 |
| Eşleştirme ve kaynak önerisi | Burak Doğan | 29 Kasım 2026 |
| Sonuç panosu | Anıl Akyıl | 29 Kasım 2026 |
| Eğitim kaynağı havuzu | Ataberk Çakır | 29 Kasım 2026 |
| Model değerlendirme raporu, yapay zekâ işçisi | Burak Doğan | 06 Aralık 2026 |
| Güvenlik incelemesi, yedekleme | Ataberk Çakır | 13 Aralık 2026 |
| Masaüstü uygulaması (macOS sürümü, simge) | Anıl Akyıl | 13 Aralık 2026 |
| Mobil uygulama | Burak Doğan | 20 Aralık 2026 |
| Uçtan uca testler, yük testi, canlı ortam | Ataberk Çakır | 20 Aralık 2026 |
| Google Play kapalı test başlangıcı | Anıl Akyıl | 21 Aralık 2026 |
| Beta kullanım | Anıl Akyıl | 10 Ocak 2027 |
| Çıkış kararı | Ekip | 15 Ocak 2027 |
| v1.0.0 canlıya çıkış | Ekip | 18 Ocak 2027 |

## 6.3. Başlıca Riskler

Başlıca riskler ve alınan önlemler Tablo 6'da özetlenmiştir.

**Tablo 6. Başlıca riskler ve önlemler**

| Risk | Önlem |
|---|---|
| Dil modelinin işlemcide yavaş çalışması | Kuyruk ve ilerleme ekranı, üretim bilgisayarında ölçüm, kısmi grafik işlemci hızlandırması, gerekirse daha küçük model |
| Türkçe ilan verisinin yetersiz kalması | Türk sitelerinden yazılı izin isteme, birden çok kaynak, düşük güven uyarısı |
| Farklı biçimli özgeçmişlerde düşük doğruluk | Dengeli değerlendirme seti, sözlük ve dil modelinin birlikte kullanımı |
| Kişisel veri sızıntısı | Saklamama kuralı, maskeleme testleri, log maskeleme, güvenlik incelemesi |
| Sentetik setin gerçek özgeçmişleri tam temsil etmemesi | Dağılım planı, sınırlılığın raporlanması |
| Modüllerin birbirine uymaması | Ortak veri sözleşmeleri, erken uçtan uca bağlama |
| Sistemin tek bir bilgisayarda çalışması (elektrik, internet, güncelleme) | Bilgisayar dışında şifreli yedek, dışarıdan erişim izleme, kurtarma tatbikatı, sunum için yerel yedek demo |

# 7. SONUÇ

Bu çalışmanın amacı, öğrencinin özgeçmişini güncel iş ilanlarıyla karşılaştırarak eksik yetkinlikleri gösteren ve doğrulanmış kaynaklara yönlendiren bir sistem geliştirmektir. Bu amaçla ilanlar kullanım koşullarına uygun kaynaklardan toplanmış, iki dilli bir taksonomiyle etiketlenmiş ve pozisyon bazlı talep istatistiklerine dönüştürülmüş; özgeçmiş tarafında metin çıkarma, kişisel veri maskeleme ve sözlük tabanlı yetkinlik çıkarımı tamamlanmıştır.

Ön bulgular, JSON şemasıyla yerel modelden yapılandırılmış çıktı alınabildiğini ve işlemci üzerinde yetkinlik çıkarımının özgeçmiş başına yaklaşık bir dakikada tamamlanabildiğini göstermektedir. Bu sonuçlar doğruluk hakkında bir kanıt sunmamaktadır. Khaouja vd. (2021) ve Zhang vd. (2022) çalışmalarının büyük ölçüde ilan tarafına ve İngilizce metinlere odaklanmasına karşın, bu proje bulguları öğrencinin gelişimine yönelik bir çıktıya dönüştürmeyi ve Türkçe özgeçmişleri kapsamayı hedeflemektedir. Ancak bu katkı, elle etiketlenmiş setle yapılacak ölçüm tamamlanmadan karşılaştırmalı olarak ileri sürülemez.

Çalışmanın başlıca sınırlılıkları ilan havuzunun İngilizce ağırlıklı olması, değerlendirme setinin sentetik olması ve uçtan uca akışın henüz bağlanmamış olmasıdır. Bir sonraki aşamada öncelikle analiz kuyruğu, dil modeli tabanlı çıkarım, eşleştirme, kaynak önerisi ve sonuç panosu tamamlanacak, ardından doğruluk ve performans hedefleri ölçülecektir. Türkçe ilan kaynakları için yazılı izin çalışmalarının sürdürülmesi önerilmektedir.

# KAYNAKLAR

Avrupa Komisyonu. (t.y.). *ESCO: European skills, competences, qualifications and occupations* (v1.2.1). Erişim adresi: https://esco.ec.europa.eu. Erişim tarihi: 26 Ekim 2026.

Broder, A. Z. (1997). On the resemblance and containment of documents. *Proceedings. Compression and Complexity of SEQUENCES 1997* içinde (ss. 21-29). Los Alamitos, CA: IEEE Computer Society. Erişim adresi: https://doi.org/10.1109/SEQUEN.1997.666900.

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A. & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*, 55(12), 1-38. Erişim adresi: https://doi.org/10.1145/3571730.

Khaouja, I., Kassou, I. & Ghogho, M. (2021). A survey on skill identification from online job ads. *IEEE Access*, 9, 118134-118153. Erişim adresi: https://doi.org/10.1109/ACCESS.2021.3106120.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S. & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459-9474. Erişim adresi: https://doi.org/10.48550/arXiv.2005.11401.

Malkov, Y. A. & Yashunin, D. A. (2020). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824-836. Erişim adresi: https://doi.org/10.1109/TPAMI.2018.2889473.

Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)* içinde (ss. 3980-3990). Erişim adresi: https://doi.org/10.18653/v1/D19-1410.

Reimers, N. & Gurevych, I. (2020). Making monolingual sentence embeddings multilingual using knowledge distillation. *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)* içinde (ss. 4512-4525). Erişim adresi: https://doi.org/10.18653/v1/2020.emnlp-main.365.

Vidros, S., Kolias, C., Kambourakis, G. & Akoglu, L. (2017). Automatic detection of online recruitment frauds: Characteristics, methods, and a public dataset. *Future Internet*, 9(1), 6. Erişim adresi: https://doi.org/10.3390/fi9010006.

Zhang, M., Jensen, K. N., Sonniks, S. D. & Plank, B. (2022). SkillSpan: Hard and soft skill extraction from English job postings. *Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies* içinde (ss. 4962-4984). Erişim adresi: https://doi.org/10.18653/v1/2022.naacl-main.366.
