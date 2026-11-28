# Model kartı: Cv'ne Bakalım! analiz akışı (T-081)

> **Durum: taslak (28.11.2026).** Değerlendirme sayıları T-055'in ön sonucudur (`ai/eval/report.md`). Gold
> etiketlerinin ekip kontrolü (T-019, karar #43) ve production ölçümleri bitince bu kart güncellenir.

## Ne yapar, ne yapmaz

Öğrencinin yüklediği CV'den (PDF) yetkinlikleri çıkarır. Bunları seçilen pozisyonun güncel ilan istatistikleriyle
karşılaştırır, 0–100 arası bir uyum puanı ve eksik yetkinlik listesi verir, her eksik için eğitim kaynağı önerir.

- **Amaç:** kariyer planlamasına yardımcı, **tahmini** bir geri bildirim.
- **Amaç değil:** işe alım kararı, aday sıralama veya eleme, kişinin yetkinliğini sınama ya da belgeleme.
  Sistem işverenlere veya üçüncü kişilere sonuç vermez.
- **Hedef kullanıcı:** Türkçe veya İngilizce CV'si olan, bilişim alanındaki öğrenciler ve yeni mezunlar
  (12 pozisyon, taksonomide 374 yetkinlik).

## Akış ve modeller

| Adım | Yöntem / model | Kaynak | Not |
|---|---|---|---|
| PDF → metin | pdfplumber, yedek PyMuPDF; çok sütun düzeni | `ai/parsing` | Bellek içi; dosya diske yazılmaz (karar #9). Taranmış PDF'te OCR henüz yok (T-029) |
| Kişisel veri maskeleme | Kurallar + **BERTurk NER** `akdeniz27/bert-base-turkish-cased-ner` (MIT, revizyon sabit) | `ai/pii`, karar #24 | Ad-soyad, e-posta, telefon, T.C. kimlik no, IBAN, adres, doğum tarihi, kişisel bağlantılar. LLM maskelenmiş metni görür |
| Yetkinlik çıkarımı | v1 taksonomi sözlüğü + **Llama 3.1 8B Instruct** (q4_K_M, Ollama, yerel), prompt `skill_extraction` v2, JSON şeması zorunlu, temperature 0.1 | `ai/extraction`, karar #26 | Dış yapay zekâ API'si yok. LLM düşerse sadece v1 sonucu kullanılır |
| Eşleştirme | Talep oranı × IDF ağırlıklı puan; taksonomi dışı adlar **multilingual-e5-small** (384 boyut) ile kosinüs ≥ 0,90 | `ai/matching`, `ai/embedding` | Puan kuraldır, LLM üretmez |
| Kaynak önerisi | Veritabanındaki aday kaynaklardan Llama 3.1 8B seçer ve gerekçe yazar (prompt `recommendation` v1) | `ai/recommendation` | Link ve başlık her zaman veritabanı kaydından gelir (karar #10); ilan istatistiği cümlesini kod yazar |

Analizde kullanılan model ve prompt sürümleri her sonuçla birlikte kaydedilir (`model.name`,
`model.prompt_version`, karar #38).

## Veri

- **İlanlar:** gece toplanan uzaktan çalışma ilanları (Remotive, Himalayas, Remote OK, Hacker News, Arbeitnow,
  Jobicy), yetkinlik adları taksonomiye eşlenir. Bir pozisyonda 50'den az ilan varsa sonuç "az veri" olarak
  işaretlenir (karar #23).
- **Eğitim kaynakları:** veritabanındaki kaynak havuzu (YouTube, kurs siteleri, resmî dokümanlar; `resources`),
  sadece canlı linkler. Yetkinlik taksonomisi ESCO kavramlarına bağlanır.
- **Model eğitimi yok:** hiçbir model bu projenin verisiyle eğitilmedi veya ince ayarlanmadı. Kullanıcı CV'leri
  hiçbir modele eğitim verisi olarak gitmez ve saklanmaz (sadece SHA-256 hash ve çıkarılan yetkinlikler, karar #9).

## Değerlendirme (ön sonuç, T-055)

50 sentetik CV (karar #20: 25 Türkçe / 25 İngilizce, 21'i çok sütunlu, 6'sı taranmış), 822 gold yetkinlik.

| Ölçüt | Sonuç | Hedef |
|---|---|---|
| Yetkinlik çıkarımı F1, 50 CV (taranmışlar boş sayıldı) | 0,83 | ≥ 0,80 |
| Yetkinlik çıkarımı F1, metinli 44 PDF (kesinlik 0,87, duyarlılık 0,90) | 0,88 | ≥ 0,80 |
| Aynısı, sadece taksonomi içi yetkinlikler | 0,93 | — |
| Seviye doğruluğu (beginner/intermediate/advanced) | %35 | — |
| Gecikme, çıkarıma kadar, p50 / p95 (geliştirme GPU'su) | 5,5 / 8,8 sn | analiz < 180 sn |
| Öneri alakalılığı (3 değerlendirici, 1–5) | ölçülmedi | ≥ 4,0 |

Gruplara göre F1 (metinli PDF'ler): Türkçe 0,89 · İngilizce 0,88 · tek sütun 0,90 · çok sütun 0,86 ·
yeni mezun 0,92 · stajyer 0,89 · deneyimli 0,85. Ayrıntı ve hata analizi: `ai/eval/report.md`.

## Bilinen sınırlılıklar

1. **Taranmış (görüntü) PDF'ler okunmuyor.** OCR (T-029) gelene kadar kullanıcı "metin bulunamadı" hatası alır.
2. **Seviye tahmini zayıf (%35).** Seviye arayüzde gösterilir, ama uyum puanını etkilemez. Kullanıcıya
   "tahmini" olduğu söylenmeli.
3. **Dolaylı anlatılan yetkinlikler kaçabilir:** liderlik, kod incelemesi, performans iyileştirme gibi
   cümle içinde anlatılan beceriler, ayrıca liste halinde yazılmadıkça sıkça bulunamıyor.
4. **Taksonomi dışı adlar** (sertifikalar, Türkçe açıklamalar) "tahmini" olarak işaretlenir. Bunlar
   eşleştirmede sadece anlamsal benzerlikle ve kısmi puanla kullanılır.
5. **Değerlendirme seti sentetik.** CV metinleri ve gold etiketleri yapay zekâyla üretildi (karar #20 ve #43);
   sistemdeki model (Llama) farklı olsa da ölçüm gerçek CV'lere göre iyimser olabilir. Gerçek CV'lerle ölçüm yok.
6. **Puan ilan istatistiğine bağlı.** Uyum puanı "bu pozisyonun ilanlarında en sık istenen yetkinliklere ne kadar
   sahipsin" sorusunu yanıtlar. Kişinin işe uygunluğunu veya iş bulma olasılığını ölçmez.
7. **LLM hatası.** Model CV'de olmayan bir yetkinlik yazabilir (ölçülen kesinlik 0,87) veya olanı atlayabilir.
   Taksonomi doğrulaması ve JSON şeması bu riski azaltır, ama ortadan kaldırmaz.

## Yanlılık riskleri

- **İlan kaynağı yanlılığı:** ilanlar uzaktan çalışma sitelerinden ve çoğunlukla İngilizce. Türkiye'deki yerel
  iş piyasasının talebi eksik temsil ediliyor olabilir (risk R-11). Bir yetkinliğin "eksik" görünmesi, yerel
  piyasada da aranmadığı anlamına gelmeyebilir; tersi de olabilir.
- **Dil:** Türkçe ve İngilizce CV'lerde F1 yakın (0,89 / 0,88), ama İngilizce CV'lerde kesinlik daha düşük
  (0,83 / 0,90). Diğer diller desteklenmiyor.
- **CV biçimi:** çok sütunlu ve görsel ağırlıklı tasarımlar daha düşük sonuç veriyor (0,86 / 0,90). Taranmış PDF
  hiç okunmuyor. Bu, tasarım şablonu kullanan öğrencileri dezavantajlı bırakabilir.
- **Deneyim düzeyi:** deneyimli profillerde F1 daha düşük (0,85 / yeni mezun 0,92). Uzun CV'lerde yetkinlik daha
  çok cümle içinde anlatılıyor.
- **Ad tespiti:** NER modeli Türkçe adlarda ölçüldü (karar #24). Başka kökenden adlar daha zor yakalanabilir.
  Kurallar e-posta, telefon gibi alanları dilden bağımsız maskeler; kaçan bir ad sadece yerel LLM'e gider, saklanmaz.
- **Cinsiyet, yaş, köken:** akış bu bilgileri girdi olarak kullanmaz, doğum tarihi ve ad maskelenir. Ancak
  maskelemeden kaçan dolaylı ipuçlarının (okul, dernek, hobi) LLM çıktısını etkilemediği ayrıca ölçülmedi.

## Kullanıcıya gösterilecek sorumluluk reddi (öneri)

Sonuç ekranında (web `ResultDashboard`, mobil `ResultView`) puanın yanında veya altında:

> Bu sonuç yapay zekâ destekli, **tahmini** bir değerlendirmedir. Uyum puanı, seçtiğin pozisyonun güncel
> ilanlarında en sık istenen yetkinliklere göre hesaplanır; bir işe uygunluğunu veya işe alınma olasılığını
> göstermez. Yetkinlikler ve seviyeleri CV'nden otomatik çıkarıldı ve hatalı ya da eksik olabilir. Sonucu bir
> kariyer danışmanı veya öğretim üyesiyle birlikte değerlendirmeni öneririz. CV'n saklanmaz; sadece çıkarılan
> yetkinlikler kaydedilir.

İngilizce:

> This is an AI-assisted, **estimated** assessment. The match score reflects how many of the skills most often
> requested in current job postings for the selected role you have; it does not indicate your suitability for a
> job or your chances of being hired. Skills and levels were extracted automatically from your CV and may be
> wrong or incomplete. Your CV is not stored; only the extracted skills are saved.

Metin onaylanınca web'e Anıl, mobile Burak ekler; KVKK aydınlatma metniyle (#71) çelişmemeli.

## Bakım

- Model, prompt veya taksonomi değişince `ai/eval/scripts/evaluate.py` ile ölçüm tekrarlanır ve bu kart ile
  `ai/eval/report.md` güncellenir. Production'daki model etiketi v1.0.0'da digest'le sabitlenecek (go-live #33).
- Sorumlu: Burak (`ai/`).
