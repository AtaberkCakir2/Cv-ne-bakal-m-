# Burak — Görevler

**Alan:** AI / NLP + Mobil · **28 görev · 260 saat**

Bu dosya Burak'ın görev listesidir ve görev durumlarının tek doğru kaynağıdır. Sadece Burak (veya onun Claude'u) günceller.

**Durum nasıl güncellenir:** İlgili görevin `- **Durum:**` satırını şu değerlerden biriyle değiştirin: `Yapılacak`, `Devam Ediyor`, `Engellendi`, `Tamamlandı`. Durum değişikliği, işin kendisiyle aynı PR'da gönderilir. `Engellendi` olursa sebebini **Not** satırına yazın ve gruba haber verin.

**Devam notu:** Yarım kalan görevin altına gün sonunda "bitiriyorum" rutiniyle `- **Devam notu (tarih):** Yapılan · Sıradaki adım · Açık sorular · Branch` satırı eklenir; görev bitince silinir. Not, görevin branch'inde durur ve "başlıyorum" rutini oradan okur.

Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (başlangıç planı, referans). Tarih veya kapsam değişirse Excel değil bu dosya güncellenir.

---

## Sprint 0

### T-018 · Ollama kurulumu ve model benchmark'ı

- **Durum:** Yapılacak
- **Tarih:** 19.10.2026 – 01.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-007 (Ataberk)
- **Destek:** —
- **Çıktı:** Benchmark raporu (poster için de kullanılacak)
- **Kabul kriteri:** Aday modeller: Llama 3.x 8B Instruct (q4_K_M), Gemma 9B, Qwen 7B. 10 Türkçe CV ile: JSON uyumu, yetkinlik doğruluğu, token/sn, RAM. CPU ve (varsa) GPU ölçümü. Kazanan model + yedek model seçildi.
- **Devam notu (29.10.2026):** Yapılan: henüz başlanmadı. Docker Desktop kurulu ama motor çalışmıyor: WSL kurulu değil. Repo kökünde `.env` oluşturuldu (rastgele şifreler, git dışı). #10 birleşti; Ollama `0.40.10`'a sabitlendi. Bu bilgisayar: i7-13700H, 32 GB RAM, RTX 4060 Laptop 8 GB → GPU ölçümü yapılabilir. · Sıradaki adım: yönetici PowerShell'de `wsl --install` + yeniden başlatma → Docker'da "Engine running" → `docker compose up -d --wait` → 3 aday modeli indir (`docker compose exec ollama ollama pull <model>`) → benchmark scripti (`ai/benchmark/`): JSON uyumu, token/sn, RAM/VRAM (CPU ve GPU), doğruluk T-019'un ilk 10 TR CV'si etiketlenince. · Açık sorular / engeller: WSL kurulumu Burak'ta (yönetici izni); 10 TR CV T-019'dan (hedef 03.11). · Branch: yok (başlarken `burak/ollama-benchmark` açılacak)

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
- **Not:** Ad tespiti kurallar + yerel BERTurk NER (karar #24). #37 incelemesi (Ataberk) düzeltildi: unvan satırındaki yetkinlikler ad sayılmıyor, adres ipucu tek başına adres değil, NER kütüphaneleri sabit sürümde. Ataberk'e devredilenler: worker-ai imajına `ai[ner]` (CPU torch) kurulup model derleme sırasında indirilmeli (`HF_HUB_OFFLINE=1`); CI'daki mypy komutuna `pii` eklenmeli; `scraper/etl/pipeline.py`'deki ad maskeleme `pii.mask_text` ile değiştirilebilir.

### T-031 · Yetkinlik çıkarımı v1 (sözlük + kural)

- **Durum:** Yapılacak
- **Tarih:** 02.11.2026 – 15.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-017 (Ataberk), T-020
- **Destek:** Ataberk
- **Çıktı:** ai/extraction v1
- **Kabul kriteri:** Taksonomi + eş anlamlılarla hızlı eşleme (FlashText/regex); deneyim yılı ve seviye ipuçları ("ileri düzey", "3 yıl"). LLM çalışmasa bile sonuç üretir (yedek yol).

### T-044 · Prompt versiyonlama

- **Durum:** Yapılacak
- **Tarih:** 09.11.2026 – 15.11.2026 · **Öncelik:** P1 · **Efor:** 4 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-031
- **Destek:** —
- **Çıktı:** Prompt kütüphanesi
- **Kabul kriteri:** Prompt'lar /ai/prompts altında versiyonlu; her analizde model_name ve prompt_version kaydedilir (tekrarlanabilirlik).

---

## Sprint 2

### T-032 · Yetkinlik çıkarımı v2 (LLM)

- **Durum:** Yapılacak
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 14 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-031, T-018, T-030
- **Destek:** —
- **Çıktı:** ai/extraction v2
- **Kabul kriteri:** Ollama structured output (JSON şeması), temperature 0.1. v1 sonucu ile birleştirilir; taksonomide olmayan yetkinlik "doğrulanmamış" işaretlenir (halüsinasyon filtresi).

### T-041 · Embedding servisi

- **Durum:** Yapılacak
- **Tarih:** 16.11.2026 – 22.11.2026 · **Öncelik:** P0 · **Efor:** 10 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-013 (Ataberk), T-033 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** ai/embedding modülü
- **Kabul kriteri:** Çok dilli model (paraphrase-multilingual-MiniLM-L12-v2 veya multilingual-e5-small, 384 boyut). Yetkinlik ve ilan vektörleri toplu üretilip pgvector'e yazılır.

### T-042 · Eşleştirme algoritması

- **Durum:** Yapılacak
- **Tarih:** 16.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 16 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-041, T-032, T-045 (Ataberk)
- **Destek:** —
- **Çıktı:** ai/matching modülü
- **Kabul kriteri:** Pozisyon için talep ağırlığı = ilan frekansı × TF-IDF; kosinüs benzerliği ile anlamsal eşleşme (eşik 0,80, ayarlanabilir); 0-100 uyum skoru; eksik yetkinlikler talep oranına göre sıralanır.

### T-043 · Kaynak öneri üretimi (RAG)

- **Durum:** Yapılacak
- **Tarih:** 23.11.2026 – 29.11.2026 · **Öncelik:** P0 · **Efor:** 12 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-042, T-046 (Ataberk)
- **Destek:** Ataberk
- **Çıktı:** ai/recommendation modülü
- **Kabul kriteri:** Eksik yetkinlik için aday kaynaklar DB'den çekilir; LLM SADECE bu listeden seçer ve Türkçe gerekçe yazar → uydurma link imkânsız. Örn: "İncelenen 150 ilanın %75'i Docker istiyor".

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

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 8 saat · **Alan:** AI / NLP
- **Bağımlılık:** T-039 (Anıl), T-043
- **Destek:** Anıl
- **Çıktı:** worker servisi
- **Kabul kriteri:** Celery worker eşzamanlılık = 1 (RAM koruması), görev zaman aşımı, başarısız işler için hata kaydı ve kullanıcıya anlamlı mesaj; LLM düşerse v1 sözlük sonucuyla devam.

### T-060 · React Native (Expo) proje kurulumu

- **Durum:** Yapılacak
- **Tarih:** 30.11.2026 – 06.12.2026 · **Öncelik:** P0 · **Efor:** 6 saat · **Alan:** Mobil
- **Bağımlılık:** T-040 (Anıl)
- **Destek:** Anıl
- **Çıktı:** mobile/ iskeleti
- **Kabul kriteri:** Expo + TypeScript; web ile ortak API istemcisi ve tipler; expo-secure-store ile token saklama; EAS Build yapılandırması.

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
