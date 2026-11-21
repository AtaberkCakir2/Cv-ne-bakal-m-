# Veri kaynağı ve hukuki uygunluk analizi (T-014)

**İnceleme tarihi:** 25.10.2026 · **İnceleyen:** Ataberk · **Bağlı kararlar:** #8 (kaynak önceliği), #9 (kişisel veri)

> Bu tablo bir mühendislik ön incelemesidir, hukuki görüş değildir. "İzin gerekli" ve "teyit" satırları danışmanla konuşulmadan ve yazılı izin alınmadan kullanılmaz. Kullanım koşulları değişebilir: bir kaynak devreye alınmadan önce bu dosyadaki satır yeniden kontrol edilir ve tarih güncellenir.

## Yöntem

Her kaynak için:
1. `robots.txt` indirildi ve `User-agent: *` kuralları okundu.
2. Kullanım koşulları / üyelik sözleşmesi / API şartları okundu; otomatik erişim, kopyalama, çoğaltma, yeniden yayın ve atıf maddeleri arandı.
3. Siteye otomatik istek atıldığında aktif bot koruması (403, "Access denied") olup olmadığı not edildi. **Karar #8 gereği bot korumasını aşmaya çalışılmadı**; koruma, sitenin otomatik erişim istemediğinin işareti sayıldı.

Durum değerleri: ✅ **Kullanılır** (şartlara uyarak) · 🟡 **Teyit / izin gerekli** · ⛔ **Kullanılmaz**

## Özet

- **Resmi ve serbest kaynaklar sadece İngilizce/uluslararası (çoğu uzaktan çalışma) ilanları kapsıyor.** Remotive, Himalayas, Remote OK, Arbeitnow, Jobicy ve Hacker News API'leri şartlarına uyulursa hemen kullanılabilir.
- **Türk iş sitelerinin hiçbiri izinsiz kullanılamıyor.** Kariyer.net, Yenibiriş ve Glassdoor otomatik erişimi teknik olarak engelliyor; Eleman.net ve Youthall kopyalamayı yazılı olarak yasaklıyor. Secretcv ve Techcareer'de açık bot yasağı yok ama içerik kullanımı rızaya bağlı, bu yüzden **yazılı izin istenmeli** (şablon aşağıda).
- **Kaggle'daki büyük, güncel ilan setlerinin çoğu LinkedIn / Glassdoor / Indeed'den kazınmış.** Kaggle'daki lisansı veri setini yükleyen kişi seçiyor; asıl kaynağın şartları kazımayı yasaklıyor. Bunlar için ekip kararı gerekiyor (aşağıda "Karar önerisi").
- **T-015 için (≥ 2.000 ilan) temiz yol:** resmi API'lerden ilk toplu çekim + EMSCAD (CC0, gerçek ilanlar). Bu ikisi scraping olmadan sistemin çalışmasını sağlar.
- **Türkçe ilan açığı (R-11) gerçek.** İzin gelene kadar İngilizce ilanlarla çalışılır; pozisyon başına ilan sayısı < 50 ise kullanıcıya "düşük güven" uyarısı gösterilir.

## 1. Resmi API'ler

| Kaynak | Kapsam | robots.txt | Şartlar (özet) | Durum | Uyulacak koşullar |
|---|---|---|---|---|---|
| [Remotive API](https://github.com/remotive-com/remote-jobs-api) `remotive.com/api/remote-jobs` | Uzaktan, teknoloji ağırlıklı, EN | `/api/*` tarayıcılara kapalı (API dokümantasyonu programatik kullanıma ayrıca izin veriyor) | Günde en fazla 4 çağrı önerilir, dakikada 2'den fazlası engellenir; ilanlar 24 saat gecikmeli; Remotive kaynak olarak anılır ve ilan URL'sine link verilir; ilanlar başka iş sitelerine (Jooble, Google Jobs, LinkedIn vb.) gönderilmez; ilanlarla e-posta/üye toplanmaz | ✅ | Gecede 1 çağrı. İlan gösterilen her yerde "Kaynak: Remotive" + ilan linki. JobPosting yapılandırılmış verisi / feed yayınlanmaz |
| [Himalayas API](https://himalayas.app/api) | Uzaktan, teknoloji ağırlıklı, EN | `/apply` ve sayfalama URL'leri kapalı; API serbest | Ücretsiz; anahtarlı hesapta 60 istek/dk, 10.000/gün; "Apply" için `applicationLink` değiştirilmeden kullanılır; Himalayas'a görünür kaynak linki; ilanlar başka iş sitelerine / Google Jobs / LinkedIn'e aktarılmaz; süresi dolan ilan kaldırılır | ✅ | Ücretsiz anahtar alınır. Gece çekiminde süresi dolanlar `is_active=false` yapılır. Kaynak linki gösterilir |
| [Remote OK API](https://remoteok.com/api) | Uzaktan, teknoloji ağırlıklı, EN | `Crawl-delay: 1`, `/` açık | Remote OK'nin ilan URL'sine **follow** link (nofollow değil) ve kaynak adı zorunlu; logo yazılı izinsiz kullanılmaz | ✅ | Kaynak adı + follow link. Logo kullanılmaz. İstekler arası ≥ 1 sn |
| [Arbeitnow API](https://www.arbeitnow.com/blog/job-board-api) `arbeitnow.com/api/job-board-api` | Avrupa (ağırlıkla Almanya), EN/DE | Tamamen açık | Anahtarsız, ücretsiz. Atıf, oran sınırı ve ticari kullanım hakkında yazılı şart yok | ✅ | 01.11.2026: `arbeitnow.com/terms` madde 11 API kullanımında site linkini şart koşuyor, izin geri alınabilir. Arayüzde Arbeitnow.com linki verilir |
| [Hacker News API](https://github.com/HackerNews/API) (`/v0/jobstories`, `whoishiring` kullanıcısının aylık "Who is hiring?" başlıkları) | Teknoloji, ABD ağırlıklı, EN | — (Firebase API) | Resmi, herkese açık, salt okunur; README'ye göre oran sınırı yok; repo MIT lisanslı. İçerik ilanı yazan kişiye ait | ✅ | Kaynak "Hacker News" + öğe linki. Yorumlardaki e-posta/telefon ETL'de silinir (bkz. kişisel veri kuralları) |
| [Adzuna API](https://developer.adzuna.com/docs/terms_of_service) | 12–19 ülke (TR listede görünmüyor, teyit edilecek), EN | `www.adzuna.com/robots.txt` 403 döndü | Kişisel iş arama, ilan yayınlama ve **kişisel/akademik araştırma** için lisanslı; ticari analiz, veri satışı ve lead generation yazılı anlaşma ister; ilan gösterilirse ≥ 116×23 px "Adzuna" atfı; araştırmada "The Adzuna API" kaynak olarak anılır; sözleşme bitince veri silinir | 🟡 | Ücretsiz katmanın bitirme projesi + canlı uygulama için yeterli olduğu e-postayla yazılı teyit edilir. Atıf kurallarına uyulur |
| [YouTube Data API v3](https://developers.google.com/youtube/terms/developer-policies) (eğitim kaynağı, ilan değil; T-046) | Yetkinlik başına TR/EN eğitim videosu | — (resmi API) | Ücretsiz; günde 100 arama + 10.000 birim (30.10.2026'da doğrulandı). Saklanan veri en geç 30 günde bir yenilenmeli; YouTube kaynağı belirtilmeli ve YouTube Hizmet Şartları'na link verilmeli; API verisinden skor türetilmez | ✅ | Haftalık `resources-check` veriyi yeniler; izlenme sayısı saklanmaz; anahtar sadece `.env`'de. **Anıl:** arayüzde YouTube kaynaklı öneride kaynak adı ve Şartlar linki gösterilecek |
| [Jobicy API](https://jobicy.com/jobs-rss-feed) `jobicy.com/api/jobs` | Uzaktan, ABD ağırlıklı, EN | Açık (arama parametreleri kapalı) | Anahtarsız, ticari kullanım dahil serbest; saklama, işleme ve yeniden dağıtım izinli; sadece son 7 gün | ✅ | 01.11.2026'da incelendi. İlan gösterilen yerde kaynak Jobicy olarak belirtilir; 429'da beklenir |
| [The Muse API](https://www.themuse.com/developers/api/v2) | ABD ağırlıklı, EN | — | Lisans uygulamada gösterim için; kayıt zorunlu; türev çalışma ve scraping yasak | ⛔ | 01.11.2026: toplu istatistik kullanımını kapsamadığı için alınmadı |
| Careerjet, Jooble API'leri | TR dahil çok ülke | Kendi API'leri dışında çoğu yol kapalı | Yayıncı/ortaklık (affiliate) API'leri: sitende arama sonucu göstermek içindir, son kullanıcının IP'si ve tarayıcı bilgisi istenir, linkler takip yönlendirmesinden geçer. Veri toplama amacına uygun değil | ⛔ | Kapsam dışı (amaç uyuşmuyor; yasaklı olduğu için değil) |

## 2. Açık veri setleri

| Veri seti | Lisans | İçerik | Asıl kaynak | Durum | Not |
|---|---|---|---|---|---|
| [EMSCAD — Real or Fake Job Postings](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) | CC0 | ~17.880 gerçek ilan (~800 sahte etiketli), EN, 2012–2014 | University of the Aegean, Workable ilanları | ✅ | **T-015 yedek planı.** `fraudulent=1` olanlar çıkarılır, sadece yazılım pozisyonları alınır. Eski olduğu için "son 6 ay" talep istatistiğine girmez; ETL ve taksonomi testleri için kullanılır |
| [NYC Jobs](https://www.kaggle.com/datasets/new-york-city/new-york-city-current-job-postings) | CC0 (NYC Open Data) | Kamu ilanları, EN | New York Belediyesi | 🟡 | Temiz ama yazılım ilanı az; düşük öncelik |
| [Data Analyst Job Postings (Google Search)](https://www.kaggle.com/datasets/lukebarousse/data-analyst-job-postings-google-search) | Apache 2.0 | Günlük güncellenen veri analisti ilanları, ABD | Google arama sonuçları (başka sitelerin ilanlarının toplamı) | 🟡 | Asıl ilan sahibi siteler belirsiz; danışmana sorulmadan kullanılmaz |
| [LinkedIn Job Postings 2023–2024 (arshkon)](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) | CC BY-SA 4.0 (yükleyen seçti) | 124.000+ ilan | **LinkedIn kazıma** (açıklamada scraper kodu linkli) | ⛔* | *Ekip kararına kadar kullanılmaz. LinkedIn şartları otomatik erişimi yasaklıyor |
| asaniczka setleri ([Software Engineering](https://www.kaggle.com/datasets/asaniczka/software-engineer-job-postings-linkedin), [1.3M Jobs & Skills](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024) vb.) | ODC-By (yükleyen seçti) | Yazılım/veri ilanları + yetkinlik alanı | **LinkedIn kazıma** | ⛔* | Aynı sebep |
| Glassdoor / Indeed / Monster kaynaklı setler (thedevastator, andrewmvd, PromptCloud vb.) | CC0 / CC BY-SA / "Other" | Çeşitli | Glassdoor / Indeed / Monster kazıma | ⛔* | Aynı sebep |
| [Job Description Dataset (ravindrasinghrana)](https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset) ve benzeri "synthetic" setler | CC0 | 1,6M ilan | **Sentetik** (açıklamada yazıyor) | ⛔ | Gerçek piyasa verisi değil; talep istatistiği için kullanılamaz. İstenirse sadece birim testlerinde kullanılır |
| [ESCO](https://esco.ec.europa.eu/en/use-esco/download) | 2011/833/EU: her amaçla ücretsiz, kaynak gösterilerek ([SSS](https://esco.ec.europa.eu/en/about-esco/faq), 26.10.2026'da doğrulandı) | Meslek ve yetkinlik taksonomisi (ilan değil) | Avrupa Komisyonu | ✅ | T-017: 61 yetkinlik ESCO'ya bağlı. Uygulamada atıf: "This service uses the ESCO classification of the European Commission." |

## 3. Türk iş siteleri

| Site | robots.txt (`User-agent: *`) | Kullanım koşulları | Bot koruması | Durum |
|---|---|---|---|---|
| Kariyer.net | İlan sayfaları kapalı değil; profil, özgeçmiş, başvuru ve filtre yolları kapalı | Aday Hizmet Sözleşmesi'nde açık bot maddesi bulunamadı; "Genel Koşullar" sayfası okunamadı | **Var** — Genel Koşullar sayfası tarayıcıda da "Access to this page has been denied" verdi | ⛔ |
| Yenibiriş | `robots.txt` 403 | Üyelik sözleşmelerinde site verilerinin izinsiz kopyalanması/dağıtılması yasak (arama sonucu özetlerinden; tam metin 403 nedeniyle okunamadı) | **Var** (tüm otomatik istekler 403) | ⛔ |
| Eleman.net | Arama ve ilan detay parametreleri (`?ilan_id=`, `is_ilanlari.php`) kapalı | "Sitede mevcut bulunan bilgiler, Eleman.net'in önceden yazılı olarak izni alınmadan kısmen veya tamamen kopya edilemez." | Yok | ⛔ (yazılı izinle 🟡) |
| Youthall | Genel tarayıcılara açık; yapay zeka botlarına (GPTBot, ClaudeBot vb.) `Disallow: /` | Madde 8.2: içerik ve yazılım kopyalanamaz, çoğaltılamaz; 8.1: veritabanı hakları STJ'ye ait | Yok | ⛔ (yazılı izinle 🟡) |
| Secretcv | `Allow: /`; arama ve takip parametreleri kapalı | Açık bot maddesi yok; Madde 16: "Portal'da Secretcv.com tarafından yayınlanan hiçbir veri Secretcv.com'un rızası olmaksızın kullanılamaz." | Yok | 🟡 **Yazılı izin iste** |
| Techcareer.net (Kariyer.net grubu) | Neredeyse tamamen açık | Hizmet sözleşmesinde açık bot/kopyalama yasağı bulunamadı | Yok | 🟡 **Yazılı izin iste** (Kariyer.net grubu olduğu için izinsiz kullanılmaz) |
| Coderspace | Panel, rapor ve `/api/v1.0/` kapalı | Okunamadı (bağlantı kesildi) | Belirsiz | 🟡 Okunup izin istenmeden kullanılmaz |
| İŞKUR e-Şube | `Allow: /` | Sitede kullanım koşulu bulunamadı | Yok | 🟡 Kamu verisi: açık veri / resmi izin talebi |

## 4. Global siteler

| Site | robots.txt | Kullanım koşulları | Durum |
|---|---|---|---|
| [Python.org Jobs](https://www.python.org/jobs/) | `/jobs/` kapalı değil | [Legal](https://www.python.org/about/legal/): üçüncü taraf içeriği sağlayanlar site kullanıcılarına çoğaltma ve yayın lisansı verir; otomatik erişim yasağı yok | ✅ (01.11.2026) İletişim bölümü alınmaz, kaynak linki verilir |
| LinkedIn | `User-agent: *` → `Disallow: /`; "otomatik erişim açık izin olmadan kesinlikle yasaktır" notu | User Agreement otomatik erişimi yasaklıyor | ⛔ |
| Indeed | Sayfalar kısmen açık | Site Rules (21): bot, scraper, spider veya yapay zeka ile erişim ve veri madenciliği; tarama, kazıma, kopyalama yasak | ⛔ |
| Glassdoor | Kısmen açık | Şartlar sayfası 403 (bot korumalı); Indeed ile aynı şirket grubu | ⛔ |

## Kişisel veri ve teknik kurallar (scraper ve ETL için)

Bu kurallar T-016, T-033, T-034 ve T-047'nin kabul kriterine eklenir:

1. **Önce izin:** Sadece bu tabloda ✅ olan kaynaklar `job_sources.is_active = true` olur. `tos_checked = true` ancak bu dosyadaki satır güncel ise işaretlenir.
2. **robots.txt her çalışmada kontrol edilir** (`urllib.robotparser`); kural değişip yol kapanırsa o kaynağın çalışması `failed` olarak kaydedilir ve atlanır.
3. **Bot koruması aşılmaz:** 403/429/CAPTCHA görülürse geri çekilinir, kaynak pasife alınır ve ekibe uyarı gider. Proxy, UA sahteciliği ya da CAPTCHA çözme kullanılmaz.
4. **Kimlik belirten User-Agent:** `CvneBakalim-Bot/1.0 (+https://cvnebakalim.com/bot; iletisim@cvnebakalim.com)`.
5. **Hız:** API'lerde kendi limitlerinin altında kalınır (Remotive günde 1); HTML kaynaklarda 3–5 sn rastgele gecikme (T-034).
6. **İlandaki kişisel veriler saklanmaz (KVKK, karar #9 ruhu):** İK sorumlusunun adı, e-posta, telefon ve kişisel profil linkleri `description_clean`'e yazılmadan önce silinir veya maskelenir. Şirket adı tutulabilir.
7. **Atıf:** Her ilan `source` ve `url` ile saklanır. Arayüzde ilan veya ilan sayısı gösterilen yerde kaynak listesi ("Veriler: Remotive, Himalayas, Remote OK, Hacker News, Jobicy, Arbeitnow…") ve gerekli linkler bulunur (Anıl'a iletilecek, T-053).
8. **Yeniden yayın yok:** İlanlar dışarıya feed, API veya JobPosting yapılandırılmış verisi olarak verilmez; sadece kendi uygulamamızda istatistik ve öneri için kullanılır.
9. **Sona erme:** Süresi dolan ilan pasife alınır; bir kaynağın izni biterse o kaynağın ilanları silinir (Adzuna şartı, diğerleri için de uygulanır).

## Karar önerisi (ekip + danışman)

`docs/kararlar.md`'ye eklenmek üzere önerilir:

> **Kazınmış açık veri setleri:** LinkedIn, Glassdoor, Indeed gibi otomatik erişimi yasaklayan sitelerden kazınarak Kaggle'a yüklenmiş veri setleri (lisansı ne olursa olsun) ürünün talep istatistiklerinde kullanılmaz. Başlangıç havuzu resmi API'ler + EMSCAD (CC0) ile kurulur. Türkçe ilan için Secretcv, Techcareer ve İŞKUR'dan yazılı izin istenir; izin gelene kadar İngilizce ilanlarla çalışılır. *Gerekçe:* Karar #8'in ruhu (yasaklayan siteden veri çekilmez) dolaylı yoldan delinmesin; jüri ve KVKK açısından savunulabilir veri kökeni.

Alternatif (danışman uygun görürse): LinkedIn kaynaklı setler **sadece** çevrimdışı model değerlendirmesinde (T-055) kullanılır, ürüne ve veritabanına girmez.

## İzin talep e-postası şablonu

Secretcv, Techcareer, Eleman.net, Youthall, Coderspace ve İŞKUR'a gönderilebilir. **Gönderim ekip/danışman onayıyla, kişisel değil ekip e-postasından yapılır.**

> **Konu:** Bitirme projesi için iş ilanı verisi kullanım izni
>
> Merhaba,
>
> [Üniversite Adı] Bilgisayar Mühendisliği bölümünde, danışmanımız [Danışman Adı] yönetiminde "Cv'ne Bakalım!" adlı bir bitirme projesi geliştiriyoruz. Proje, öğrencilerin yetkinliklerini güncel iş ilanlarındaki taleplerle karşılaştırıp eksik yetkinlikler için eğitim kaynağı öneriyor.
>
> Sitenizdeki yazılım alanındaki ilanları, yalnızca **toplu istatistik** üretmek (ör. "Backend ilanlarının %75'i PostgreSQL istiyor") amacıyla kullanmak istiyoruz. İlanları yeniden yayınlamayacak, kişisel veri (İK sorumlusu adı, iletişim bilgisi) saklamayacak, sunucunuza günde en fazla [N] istek atacak ve kaynak olarak sitenizi belirteceğiz. Tercih ettiğiniz bir API veya veri aktarım yöntemi varsa onu kullanmaktan memnuniyet duyarız.
>
> Bu kullanım için yazılı izninizi rica ederiz. Uygun görmezseniz sitenizden hiçbir veri çekmeyeceğiz.
>
> Saygılarımızla,
> [Ad Soyad], [Ad Soyad], [Ad Soyad]
> Cv'ne Bakalım! ekibi — [ekip e-postası]

## Açık sorular (danışmana)

1. Kaggle'daki LinkedIn kaynaklı setler: tamamen hariç mi, yoksa sadece çevrimdışı değerlendirmede mi?
2. Remotive'in `robots.txt`'si `/api/*` yolunu tarayıcılara kapatıyor, ama API dokümantasyonu programatik kullanımı açıkça tarif ediyor. API şartlarına uyarak kullanmak yeterli mi?
3. Adzuna'nın "akademik araştırma" lisansı, canlıya çıkan (ücretsiz) bir bitirme projesi uygulamasını kapsıyor mu? (Adzuna'ya da yazılı sorulacak.)
4. İzin e-postaları kimin adına ve hangi adresten gitmeli?

## Kaynaklar (erişim: 25.10.2026)

- robots.txt: kariyer.net, secretcv.com, eleman.net, techcareer.net, coderspace.io, youthall.com, esube.iskur.gov.tr, careerjet.com.tr, tr.jooble.org, linkedin.com, tr.indeed.com, glassdoor.com, remotive.com, remoteok.com, arbeitnow.com, himalayas.app, huggingface.co (yenibiris.com ve adzuna.com: 403)
- Secretcv Kullanım Şartları: https://www.secretcv.com/kullanim-sartlari
- Eleman.net Site Kullanım Şartları: https://www.eleman.net/site_kullanim_sartlari.php
- Youthall Kullanıcı Sözleşmesi: https://www.youthall.com/en/page/user-agreement/
- Techcareer Hizmet Sözleşmesi: https://www.techcareer.net/hizmet-sozlesmesi
- Kariyer.net Hizmet Sözleşmesi: https://www.kariyer.net/veri-politikamiz/hizmet-sozlesmesi
- Yenibiriş üyelik sözleşmeleri: https://www.yenibiris.com/bireysel-kullanim-sartlari, https://www.yenibiris.com/kurumsal-uyelik-sozlesmesi (403; içerik arama özetlerinden)
- Indeed Terms (Site Rules): https://www.indeed.com/legal
- LinkedIn robots.txt notu ve User Agreement: https://www.linkedin.com/legal/user-agreement
- Remotive API: https://github.com/remotive-com/remote-jobs-api
- Himalayas API: https://himalayas.app/api
- Remote OK API: https://remoteok.com/api
- Arbeitnow API: https://www.arbeitnow.com/blog/job-board-api
- Hacker News API: https://github.com/HackerNews/API
- Adzuna API Terms: https://developer.adzuna.com/docs/terms_of_service
- Kaggle veri seti lisansları: Kaggle API (`/api/v1/datasets/list`, `/datasets/view`)
