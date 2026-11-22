# Burak — Görevler

**Alan:** AI / NLP + Mobil · **28 görev · 260 saat**

Bu dosya Burak'ın görev listesidir ve görev durumlarının tek doğru kaynağıdır. Sadece Burak (veya onun Claude'u) günceller.

**Durum nasıl güncellenir:** İlgili görevin `- **Durum:**` satırını şu değerlerden biriyle değiştirin: `Yapılacak`, `Devam Ediyor`, `Engellendi`, `Tamamlandı`. Durum değişikliği, işin kendisiyle aynı PR'da gönderilir. `Engellendi` olursa sebebini **Not** satırına yazın ve gruba haber verin.

**Devam notu:** Yarım kalan görevin altına gün sonunda "bitiriyorum" rutiniyle `- **Devam notu (tarih):** Yapılan · Sıradaki adım · Açık sorular · Branch` satırı eklenir; görev bitince silinir. Not, görevin branch'inde durur ve "başlıyorum" rutini oradan okur.

Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (başlangıç planı, referans). Tarih veya kapsam değişirse Excel değil bu dosya güncellenir.

---

## Sprint 0

### T-018 · Ollama kurulumu ve model benchmark'ı

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-007 (Ataberk)
- **Destek:** —
- **Çıktı:** Benchmark raporu (poster için de kullanılacak)
- **Kabul kriteri:** Aday modeller: Llama 3.x 8B Instruct (q4_K_M), Gemma 9B, Qwen 7B. 10 Türkçe CV ile: JSON uyumu, yetkinlik doğruluğu, token/sn, RAM. CPU ve (varsa) GPU ölçümü. Kazanan model + yedek model seçildi.
- **Not:** Rapor `ai/eval/benchmark/README.md`, karar #26: Llama 3.1 8B (yedek Gemma 2 9B), JSON şeması zorunlu. Referans etiketler geçici (Claude); T-019 gold gelince ve VPS'te (T-056) tekrar ölçülmeli. Docker gerekmedi: Ollama Windows'a doğrudan kuruldu (0.40.13).

### T-019 · Etiketli değerlendirme veri seti (altın standart)

- **Durum:** Devam Ediyor
- **Tarih:** 19.10.2026 – 28.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat (Burak; ekipçe toplam ~26–36 kişi-saat) · **Alan:** AI / NLP
- **Bağımlılık:** —
- **Destek:** Ataberk (şablon girdisi, etiketleme), Anıl (etiketleme)
- **Çıktı:** ai/eval/dataset (sentetik)
- **Kabul kriteri:** 50 sentetik CV (karar #20: gerçek kişilere ait CV toplanmaz): 25 TR + 25 EN; 10 pozisyon × 5; tek ve çok sütunlu; en az 5 taranmış; yeni mezun / stajyer / deneyimli dengeli. Tamamı en az 1 kişi, 20'si 2 kişi tarafından bağımsız elle etiketlendi; anlaşmazlıklar 3. kişiyle çözüldü; çift etiketlenen alt kümede etiketleyiciler arası F1 ≥ 0,85. Çift etiketlenen 20 CV dengeli seçilir: en az 8 TR + 8 EN, en az 6 çok sütunlu, en az 2 taranmış, üç deneyim düzeyinden de. Etiketler sıfırdan verilir; şablonun yetkinlik listesi veya bir eşleyicinin çıktısı cevap anahtarı olarak kullanılmaz.
- **Not:** Plan #30'da Ataberk'le kararlaştırıldı (29.10.2026). İlk 10 Türkçe CV T-018 benchmark'ı için öncelikli (hedef 03.11). Şablon betiği `ai/eval/`'de; girdi listesi (pozisyon × yetkinlik × eş anlamlı, `role_skill_stats` oranlarıyla) Ataberk'ten JSON olarak gelir. CV üretiminde ÜYZ kullanılırsa araç adı ve sürümü TÜBİTAK beyanına eklenir.
- **Devam notu (30.10.2026):** Yapılan: plan ve `agreement.py --write-gold` düzeltmesi main'de (#34); Ataberk'in şablon girdisi main'de (#38, `scraper/exports/template_input.json`); `ai/eval/scripts/generate_cvs.py` (JSON → tek/çok sütunlu PDF, taranmış benzetimi, manifest) ve **ilk 10 TR CV** (`syn-004`…`syn-013`; metinleri Claude Opus 5.5 ile yazıldı, ÜYZ beyanında) bu branch'te (PR #35). · Sıradaki adım: (1) 10 TR CV'yi etiketle → T-018 referansını (`ai/eval/benchmark/reference_draft.json`) gerçek etiketle değiştir; (2) kalan 37 CV (25 EN dahil) `template_input.json`'dan; low_data pozisyonlarda (game-developer 4, data-analyst 5 ilan) yetkinlik listesi yakın pozisyonla tamamlanır; (3) çift etiketlenecek 20 CV'yi dengeli seç (`double: true`; bu 10 CV'nin hepsi şu an false, en az 8 TR gerekli); ilerleme: `.venv\Scripts\python ai/eval/scripts/check_labels.py`. · Açık sorular / engeller: Ataberk'in önerisi, kalan taranmış CV'lerde ±1–2° eğim ve hafif gürültü (T-029 için). · Branch: `burak/sentetik-cv-uretimi` (PR #35)

### T-024 · UML diyagramları

- **Durum:** Tamamlandı
- **Tarih:** 19.10.2026 – 25.10.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-011 (Ataberk)
- **Destek:** Ataberk, Anıl
- **Çıktı:** docs/diagrams
- **Kabul kriteri:** Use Case, Sequence (CV yükleme → sonuç), Component/Deployment ve ERD diyagramları. Poster ve final raporda kullanılacak.
- **Not:** ERD `docs/veritabani.md`'den çizildi; T-011 (Ataberk) kesinleşince karşılaştırılıp güncellenecek.

### T-020 · PDF metin çıkarma modülü

- **Durum:** Tamamlandı
- **Tarih:** 26.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-007 (Ataberk)
- **Destek:** —
- **Çıktı:** ai/parsing modülü + testler
- **Kabul kriteri:** pdfplumber + PyMuPDF yedeği; çok sütunlu CV düzeni; tamamen bellek içi (BytesIO), diske yazma yok. Bozuk/şifreli PDF için anlamlı hata kodu.
- **Not:** Testler bellekte üretilen sentetik PDF'lerle (tek sütun, iki sütun, tablo, taranmış, şifreli, bozuk). Gerçek CV düzenleri (Word/Canva çıktıları) T-019 veri setiyle ayrıca denenmeli. T-007 (Docker) gerekmedi; modül saf Python.

---

## Sprint 1

### T-029 · OCR yedek akışı (Tesseract)

- **Durum:** Yapılacak
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P1 · **Efor:** 8 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-020
- **Destek:** —
- **Çıktı:** ai/ocr modülü
- **Kabul kriteri:** Çıkarılan metin 200 karakterden kısaysa OCR devreye girer: pdf2image 300 DPI + Tesseract (tur+eng). 5 taranmış CV'de karakter doğruluğu ≥ %95.

### T-030 · Kişisel veri anonimleştirme (PII maskeleme)

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 08.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** Güvenlik & KVKK
- **Bağımlılık:** T-020
- **Destek:** —
- **Çıktı:** ai/pii modülü + testler
- **Kabul kriteri:** LLM'e gitmeden ÖNCE ad-soyad, telefon, e-posta, adres, TC kimlik no, doğum tarihi maskelenir (regex + NER). Test: telefon/e-posta/TCKN için %100 maskeleme.
- **Not:** Ad tespiti kurallar + yerel BERTurk NER (karar #24). #37 incelemesi (Ataberk) düzeltildi: unvan satırındaki yetkinlikler ad sayılmıyor, adres ipucu tek başına adres değil, NER kütüphaneleri sabit sürümde. Ataberk'e devredilenler: worker-ai imajına `ai[ner]` (CPU torch) kurulup model derleme sırasında indirilmeli (`HF_HUB_OFFLINE=1`) (CI'daki mypy komutu ve ilan maskelemesi `pii.mask_posting` Ataberk'te yapıldı). #43 incelemesinde (Ataberk, gerçek ilanlar) bulunanlar düzeltildi: maskeleme idempotent (etiketler tekrar maskelenmez), İngilizce metinde "Bay" hitap değil, unvanla başlayan marka adları küçük bir istisna listesinde ("Dr. Squatch"), bağlantı içindeki ön eksiz sayı telefon/TCKN değil, hash içindeki 11 hane TCKN değil. #44 incelemesindeki üç sızıntı da kapatıldı: harfe bitişik TCKN ("TC12345678901") ve unvandan sonra tek soyadı ("Mr. Johnson") maskeleniyor, bağlantıdaki telefon biçimli numara (05…, +90…, `?phone=`) telefon sayılıyor.

### T-031 · Yetkinlik çıkarımı v1 (sözlük + kural)

- **Durum:** Tamamlandı
- **Tarih:** 02.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-017 (Ataberk), T-020
- **Destek:** Ataberk
- **Çıktı:** ai/extraction v1
- **Kabul kriteri:** Taksonomi + eş anlamlılarla hızlı eşleme (FlashText/regex); deneyim yılı ve seviye ipuçları ("ileri düzey", "3 yıl"). LLM çalışmasa bile sonuç üretir (yedek yol).
- **Not:** `ai/extraction` (sözlük + kural, LLM'siz). 10 TR sentetik CV'de geçici referansa göre P 0,98 / R 0,97 (referans da sözlükle üretildiği için iyimser; T-019 gold ile tekrar ölç). Referans düzeltme önerileri: syn-012 Kriptografi CTF cümlesinde de geçiyor (geri eklenmeli); "GitHub Actions" içindeki GitHub ayrı sayılmamalı; MLOps/DevOps başlıkları tutarlı olmalı. Ataberk'le ortaklaştırma: `extraction/taxonomy.py` ve `scraper/etl/skills.py` aynı kurallar; CI mypy komutuna `extraction` eklenmeli.

### T-044 · Prompt versiyonlama

- **Durum:** Devam Ediyor
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P1 · **Efor:** 4 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-031
- **Destek:** —
- **Çıktı:** Prompt kütüphanesi
- **Kabul kriteri:** Prompt'lar /ai/prompts altında versiyonlu; her analizde model_name ve prompt_version kaydedilir (tekrarlanabilirlik).
- **Devam notu (10.11.2026):** Yapılan: `ai/prompts/` (`get_prompt`, `model_info`, `skill_extraction/v1.txt`, #68); T-032 (#78) LLM çağrısında `get_prompt("skill_extraction")` kullanıyor ve `ExtractionResult.model` alanında `{"name", "prompt_version"}` döndürüyor. · Sıradaki adım: T-057'de işçi `result.model` değerini analiz sonucuna ve `analyses` tablosuna yazınca kriterin "her analizde kaydedilir" kısmı kapanır, görev o zaman Tamamlandı yapılır. · Açık sorular / engeller: T-043 ikinci prompt'u getirince sözleşmedeki tek `prompt_version` alanının nasıl kullanılacağı karar ister. · Branch: yok (kod main'de; kalan iş T-057'nin dalında)

---

## Sprint 2

### T-032 · Yetkinlik çıkarımı v2 (LLM)

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 14 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-031, T-018, T-030
- **Destek:** —
- **Çıktı:** ai/extraction v2
- **Kabul kriteri:** Ollama structured output (JSON şeması), temperature 0.1. v1 sonucu ile birleştirilir; taksonomide olmayan yetkinlik "doğrulanmamış" işaretlenir (halüsinasyon filtresi).
- **Not:** v1 ile v2'nin F1 karşılaştırması ve LLM'in tamamladığı seviyelerin doğruluğu T-019 altın standardı gelince ölçülecek (doğru değilse seviye tamamlama kapatılır). Ataberk'e taksonomi önerisi: "Express" (Express.js) tek başına eşleşmiyor.

### T-041 · Embedding servisi

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-013 (Ataberk), T-033 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** ai/embedding modülü
- **Kabul kriteri:** Çok dilli model (paraphrase-multilingual-MiniLM-L12-v2 veya multilingual-e5-small, 384 boyut). Yetkinlik ve ilan vektörleri toplu üretilip pgvector'e yazılır.
- **Not:** Model MiniLM yerine multilingual-e5-small (leave-one-out doğruluk %53 → %65; ölçüm `ai/README.md`), `docs/kararlar.md`'ye ekip kararı olarak yazılmalı. T-042 eşiği bu modelde ~0,90 (0,80 her şeyi eşler). Ataberk için: gece toplamasına `python -m embedding` adımı, işçi imajına modelin önceden indirilmesi, `catalog.py`'deki model yorumu ve T-013 ölçümünün gerçek vektörlerle tekrarı.

### T-042 · Eşleştirme algoritması

- **Durum:** Tamamlandı
- **Tarih:** 16.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-041, T-032, T-045 (Ataberk)
- **Destek:** —
- **Çıktı:** ai/matching modülü
- **Kabul kriteri:** Pozisyon için talep ağırlığı = ilan frekansı × TF-IDF; kosinüs benzerliği ile anlamsal eşleşme (eşik 0,80, ayarlanabilir); 0-100 uyum skoru; eksik yetkinlikler talep oranına göre sıralanır.
- **Not:** `ai/matching` (`match`, `load_role_demand`). Anlamsal eşik varsayılanı 0,90: kriterdeki 0,80 MiniLM içindi, T-041'de seçilen e5-small'da her şeyi eşliyor; eşik parametre olarak ayarlanabilir. Anlamsal eşleşme sadece taksonomide olmayan adlara uygulanır (farklı taksonomi yetkinlikleri vektörle eşlenmez). Sözleşmede `low_data` alanı yok; karar #23'teki uyarı için API'ye ayrı alan gerekirse sözleşme önerisi yapılmalı (Anıl). 10 sentetik CV'de hedef pozisyon 9'unda 1. sırada (README). #79 (T-041) birleşince PR açılır.

### T-043 · Kaynak öneri üretimi (RAG)

- **Durum:** Tamamlandı
- **Tarih:** 23.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-042, T-046 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** ai/recommendation modülü
- **Kabul kriteri:** Eksik yetkinlik için aday kaynaklar DB'den çekilir; LLM SADECE bu listeden seçer ve Türkçe gerekçe yazar → uydurma link imkânsız. Örn: "İncelenen 150 ilanın %75'i Docker istiyor".
- **Not:** 17.11.2026. `ai/recommendation` (`load_candidates`, `recommend`): adaylar `resources`'tan (sadece `is_alive`); LLM sadece aday numarası seçer, numara o yetkinliğin adaylarında yoksa atılır, link/başlık her zaman DB kaydından gelir. İlan istatistiği cümlesi koddan üretilir (LLM sayı yazmaz); bozuk gerekçe veya LLM hatasında kurallı seçim ve gerekçe. Prompt `prompts/recommendation/v1.txt`. Deneme: `resources.csv` adayları + Llama 3.1 8B, 9/9 geçerli seçim, 9/9 LLM gerekçesi, 7,8 sn (ilk çağrı 85 sn). SQL geçici tablolarla test edildi; gerçek `resources` tablosuyla deneme T-057'de. Açık soru: analizde artık iki prompt var (`skill_extraction` v1, `recommendation` v1), sözleşmede tek `prompt_version` alanı; T-057'de nasıl yazılacağı kararlaştırılmalı (bkz. T-044).

---

## Sprint 3

### T-054 · AI modülü birim testleri

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P1 · **Efor:** 8 saat · **Alan:** Test & QA
- **Bağımlılık:** T-042
- **Destek:** —
- **Çıktı:** tests/ai
- **Kabul kriteri:** pytest; parsing, PII, çıkarım, eşleştirme için birim testler; kapsama ≥ %70; CI'da zorunlu.

### T-055 · Model değerlendirme raporu

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-043, T-019
- **Destek:** Ataberk, Anıl
- **Çıktı:** eval/report.md
- **Kabul kriteri:** 50 etiketli CV üzerinde precision/recall/F1 (hedef F1 ≥ 0,80); öneri alakalılığı (3 değerlendirici, 1-5, hedef ≥ 4,0); gecikme p50/p95. Final rapor ve TÜBİTAK için.

### T-057 · AI worker'ının kuyruğa entegrasyonu

- **Durum:** Devam Ediyor
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-039 (Anıl), T-043
- **Destek:** Anıl
- **Çıktı:** worker servisi
- **Kabul kriteri:** Celery worker eşzamanlılık = 1 (RAM koruması), görev zaman aşımı, başarısız işler için hata kaydı ve kullanıcıya anlamlı mesaj; LLM düşerse v1 sözlük sonucuyla devam.
- **Devam notu (21.11.2026):** Yapılan: AI tarafı `ai/pipeline` (`analyze_cv(pdf, role_id=, conn=)`): PDF → maskeleme → çıkarım v2 → eşleştirme → öneri; sözleşme hata kodları (`AnalysisError`), 165 sn bütçe, LLM düşerse v1 + kurallı öneri; karar önerisi #38 (`prompt_version` biçimi). Eşzamanlılık 1, 180 sn sınır ve hata kaydı Anıl'ın işçisinde (T-039, #123) hazır. · Sıradaki adım: Anıl `backend/app/services/analyzer.py`'de `AiAnalyzer` ile `analyze_cv` sonucunu `output_from_result`'a bağlar (`AnalysisError.code` → `AnalysisFailed`); analiz işçisinin imajına `ai` paketi ve modeller (Ataberk/Anıl); sonra gerçek veritabanı ve Ollama ile uçtan uca deneme, görev Tamamlandı. · Açık sorular / engeller: karar #38 onayı; production kaynak havuzu küçük (yetkinlik başına 2, Ataberk büyütüyor). · Branch: burak/ai-pipeline

### T-060 · React Native (Expo) proje kurulumu

- **Durum:** Tamamlandı
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Mobil
- **Bağımlılık:** T-040 (Anıl)
- **Destek:** Anıl
- **Çıktı:** mobile/ iskeleti
- **Kabul kriteri:** Expo + TypeScript; web ile ortak API istemcisi ve tipler; expo-secure-store ile token saklama; EAS Build yapılandırması.
- **Not:** 21.11.2026. `mobile/`: Expo SDK 58 + TypeScript (5.9, web ile aynı ana sürüm; openapi-typescript TS 6'yı desteklemiyor). Tipler web'in `openapi.json`'ından `npm run gen:api` ile üretilir, istemci web'deki gibi `openapi-fetch` + aynı yenileme kuralları (`src/auth/session.ts`). Refresh token `expo-secure-store`'da (bu cihaza özel), access token bellekte. `eas.json`: `preview` (APK) ve `production` (AAB), API `https://api.cvnebakalim.com`; ilk EAS derlemesi için Expo hesabı ve `eas init` gerekir. `npm run typecheck` temiz, `expo export --platform android` paketliyor. `package-lock.json` eklendi (güvenlik raporu G-8); `npm audit`: 3 orta seviye, Expo'nun derleme aracındaki minimatch (uygulamaya girmiyor, düzeltme Expo güncellemesiyle). Ekran şimdilik backend sağlığı; giriş ve CV yükleme T-061.

### T-061 · Mobil ekranlar — giriş, KVKK onayı, CV yükleme

- **Durum:** Yapılacak
- **Tarih:** 07.12.2026 – 13.12.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** Mobil
- **Bağımlılık:** T-060, T-039 (Anıl)
- **Destek:** Anıl
- **Çıktı:** Mobil akış (1/2)
- **Kabul kriteri:** Giriş/kayıt, KVKK onayı, CV seçme (expo-document-picker), analiz bekleme ekranı. Android cihazda test.

---

## Sprint 4

### T-056 · Çıkarım performans optimizasyonu

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-055
- **Destek:** Ataberk
- **Çıktı:** Performans notu
- **Kabul kriteri:** Modeli bellekte tutma (keep_alive), num_ctx sınırlama, prompt kısaltma, aynı CV hash + pozisyon için sonuç önbelleği. Hedef analiz süresi p95 < 120 sn (CPU) / < 30 sn (GPU).

### T-062 · Mobil ekranlar — sonuç panosu, kaynaklar, profil

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** Mobil
- **Bağımlılık:** T-061, T-048 (Anıl)
- **Destek:** Anıl
- **Çıktı:** Android AAB
- **Kabul kriteri:** Sonuç panosu, kaynak detayı, geçmiş analizler, profil ve hesap silme; Android AAB üretimi (EAS Build).

### T-074 · Prompt injection koruması ve çıktı doğrulama

- **Durum:** Yapılacak
- **Tarih:** 14.12.2026 – 20.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-032
- **Destek:** —
- **Çıktı:** ai/guard modülü
- **Kabul kriteri:** CV metni veri olarak işaretlenir (talimatlar yok sayılır); çıktı Pydantic ile doğrulanır; 2 başarısız denemede sözlük tabanlı sonuca düşülür.

### T-058 · Uçtan uca pipeline testleri (golden test)

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P1 · **Efor:** 6 saat · **Alan:** Test & QA
- **Bağımlılık:** T-057
- **Destek:** —
- **Çıktı:** tests/e2e_pipeline
- **Kabul kriteri:** 10 örnek CV: PDF → sonuç JSON; beklenen yetkinlikler sabit; şema doğrulaması. Prompt/model değişikliğinde regresyon yakalar.

### T-073 · Temel sızma testi

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** Güvenlik & KVKK
- **Bağımlılık:** T-064 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** Sızma testi raporu
- **Kabul kriteri:** OWASP ZAP baseline; manuel: başkasının analizine erişim (IDOR), kötü amaçlı PDF yükleme, aşırı büyük dosya, JWT manipülasyonu, CV içine gömülü prompt injection.

### T-081 · Model kartı ve sınırlılıklar

- **Durum:** Yapılacak
- **Tarih:** 21.12.2026 – 27.12.2026 · **Öncelik:** P1 · **Efor:** 3 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-055
- **Destek:** —
- **Çıktı:** docs/model-card
- **Kabul kriteri:** Kullanılan modeller, değerlendirme sonuçları, bilinen sınırlılıklar ve yanlılık riskleri; kullanıcıya gösterilen sorumluluk reddi metni.

---

## Sprint 5

### T-083 · Beta hata düzeltmeleri — AI

- **Durum:** Yapılacak
- **Tarih:** 28.12.2026 – 10.01.2027 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-082 (Anıl)
- **Destek:** —
- **Çıktı:** Kapanmış issue'lar
- **Kabul kriteri:** Beta'da bulunan çıkarım/eşleştirme hataları; golden testlere yeni vakalar eklenir.

### T-077 · iOS TestFlight (v1.1 hazırlığı)

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P2 · **Efor:** 6 saat · **Alan:** Mobil
- **Bağımlılık:** T-062
- **Destek:** Anıl
- **Çıktı:** TestFlight build
- **Kabul kriteri:** Apple Developer Program (yıllık ücret); EAS Build ile bulutta derleme (Mac gerekmez); TestFlight dahili test. Mağaza yayını v1.1'de.

### T-086 · Geri bildirime göre prompt ve eşik ayarı

- **Durum:** Yapılacak
- **Tarih:** 04.01.2027 – 10.01.2027 · **Öncelik:** P1 · **Efor:** 8 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-082 (Anıl)
- **Destek:** —
- **Çıktı:** prompt v-next + eval sonucu
- **Kabul kriteri:** Kullanıcı puanları düşük analizler incelendi; eşik ve prompt güncellendi; değerlendirme yeniden koşturuldu (F1 düşmedi).

---

## Sprint 6

### T-098 · Bitirme projesi final raporu

- **Durum:** Yapılacak
- **Tarih:** 11.01.2027 – 31.01.2027 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** Dokümantasyon
- **Bağımlılık:** T-055
- **Destek:** Ataberk, Anıl
- **Çıktı:** Final raporu
- **Kabul kriteri:** Giriş, literatür, yöntem, mimari, uygulama, değerlendirme sonuçları, sonuç ve gelecek çalışmalar. Üniversite şablonuna uygun.

### T-096 · Canlı smoke test

- **Durum:** Yapılacak
- **Tarih:** 18.01.2027 – 18.01.2027 · **Öncelik:** P0 · **Efor:** 3 saat · **Alan:** Go-Live
- **Bağımlılık:** T-094 (Ataberk)
- **Destek:** Ataberk, Anıl
- **Çıktı:** Smoke test kaydı
- **Kabul kriteri:** Gerçek hesapla: kayıt → CV yükle → sonuç → kaynak → hesap sil. Web, Windows, macOS, Android ayrı ayrı.
