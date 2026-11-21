# ai/ — Sahibi: Burak

PDF ayrıştırma ve OCR, kişisel veri maskeleme, yetkinlik çıkarımı, embedding, eşleştirme, kaynak önerisi (Ollama).

Girdi: `contracts/job_posting.schema.json` · Çıktı: `contracts/analysis_result.schema.json`

## Kurulum ve test

Python 3.12 gerekir. `ai/` klasöründe:

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
mypy parsing pii extraction prompts embedding matching tests eval/scripts
```

Testler gerçek CV kullanmaz; PDF'ler test sırasında bellekte üretilir.

## Modüller

| Modül | Görev | Durum |
|---|---|---|
| `parsing/` | PDF → metin (T-020) | ✅ |
| `ocr/` | Taranmış CV için OCR (T-029) | — |
| `pii/` | Kişisel veri maskeleme (T-030) | ✅ |
| `extraction/` | Yetkinlik çıkarımı (T-031 v1 sözlük + kural; T-032 LLM) | v1 ✅, v2 devam ediyor |
| `prompts/` | Versiyonlu LLM prompt'ları (T-044) | Devam ediyor |
| `embedding/` | Yetkinlik ve ilan vektörleri, pgvector (T-041) | ✅ |
| `matching/` | Uyum skoru ve eksik yetkinlikler (T-042) | ✅ |
| `eval/` | Etiketli değerlendirme seti ve araçları (T-019) | Devam ediyor |
| `eval/benchmark/` | Yerel LLM benchmark'ı (T-018): Llama 3.1 8B seçildi, karar #26 | ✅ |

### `pipeline` — analiz zinciri (T-057)

```python
from pipeline import AnalysisError, analyze_cv

try:
    out = analyze_cv(pdf_bytes, role_id=3, conn=psycopg_conn)  # embed=default_encoder().encode isteğe bağlı
except AnalysisError as e:
    e.code  # PDF_UNREADABLE | PDF_TOO_LARGE | NO_TEXT_FOUND | INTERNAL (sözleşmedeki error.code)
out.result  # target_role, postings_analyzed, match_score, present_skills, missing_skills, model
out.stats  # loglanabilir: sayfa, dil, maskelenen alan sayıları, adım süreleri, LLM hata kodları
```

- **Sıra:** PDF → metin (`parsing`) → dil tahmini → maskeleme (`pii`, NER kuruluysa BERTurk) → çıkarım v2 (`extraction.llm`) → eşleştirme (`matching`, `role_skill_stats`) → öneri (`recommendation`, `resources`). Backend'in `output_from_result` fonksiyonu `out.result`'ı doğrudan okur.
- **Gizlilik:** PDF ve ham metin sadece fonksiyonun içinde bellekte; yazılmaz, loglanmaz, sonuçta yok. LLM'e maskelenmiş metin, öneri adımına sadece yetkinlik adları gider. Hata mesajları sadece kod taşır.
- **Süre:** analiz işçisinin sınırı 180 sn; zincir 165 sn bütçeyle çalışır. Çıkarım en fazla 90 sn bekler (yavaş makinede öneriye de süre kalsın; #155 incelemesinde production PC'de çıkarım 145 sn sürüp zaman aşımına düşüyordu), LLM çağrılarının zaman aşımı kalan süreye göre kısalır; 20 sn'den az kaldıysa LLM atlanır. LLM düşerse çıkarım v1 sözlük sonucuyla, öneri kurallı sıralamayla devam eder; analiz yine tamamlanır (`stats` hata kodunu taşır).
- **Taranmış PDF:** metin 200 karakterden azsa `NO_TEXT_FOUND`; OCR yedek akışı (T-029) gelince değişecek.
- **`model.prompt_version`:** iki prompt tek alanda, `"skill_extraction:v1,recommendation:v1"` (karar önerisi #38).
- **Deneme (21.11.2026):** 3 TR sentetik CV (`eval/dataset/cv_specs`, syn-005…007), gerçek Ollama (Llama 3.1 8B, bu bilgisayar), sahte veritabanı: CV başına 10–28 sn (çıkarım 7–16 sn, öneri 0–2,4 sn), LLM hatası yok; ad, e-posta, telefon maskelendi.

### `parsing` — PDF metin çıkarma

```python
from parsing import PdfError, extract_text

try:
    result = extract_text(pdf_bytes)  # bytes; dosya diske yazılmaz
except PdfError as err:
    err.code  # sözleşmedeki kod: PDF_UNREADABLE / PDF_TOO_LARGE
    err.message  # kullanıcıya gösterilecek Türkçe mesaj
else:
    result.text  # okuma sırasına dizilmiş metin
    result.needs_ocr  # < 200 karakter → OCR'a (T-029) gönder
    result.backend  # "pdfplumber" veya yedek "pymupdf"
    result.multi_column_pages  # sütunlu düzen algılanan sayfa sayısı
```

- **Kütüphaneler:** önce pdfplumber; hata verirse veya az metin çıkarsa PyMuPDF denenir, uzun sonuç alınır. İki kütüphane de kelimeleri koordinatlarıyla verir, okuma sırası tek yerde (`parsing/layout.py`) hesaplanır.
- **Çok sütunlu CV:** sayfanın ortasında dikey boşluk aranır; varsa önce üst başlık (ad, iletişim), sonra sol, sonra sağ sütun okunur. Satırları aynı hizada olan iki sütun tablo sayılır ve satır satır okunur ("Python Orta").
- **Hatalar:** PDF değil / bozuk / şifreli → `PDF_UNREADABLE`; > 5 MB veya > 5 sayfa → `PDF_TOO_LARGE`. Ayrıntılı sebep `err.reason`'da (loglar için).
- **KVKK:** girdi bellekte işlenir; CV metni hiçbir yerde loglanmaz (sadece hata türü loglanır). Testlerden biri dosya yazma ve geçici dosya açma çağrılarını engelleyerek bunu doğrular.
- **Lisans notu:** PyMuPDF AGPL lisanslıdır; akademik/açık kaynak kullanımda sorun yok, ticari kullanımda gözden geçirilmeli.

### `pii` — kişisel veri maskeleme (T-030)

```python
from pii import mask, mask_text

from pii.ner import default_detector

result = mask(cv_text, "tr", detector=default_detector())  # LLM'e sadece result.text gider
result.counts  # {Kind.EMAIL: 1, Kind.PHONE: 1, Kind.NAME: 3, ...} — loglanabilir, kişisel veri içermez
mask_text(text, "en")  # sadece metin, sadece kurallar; scraper/etl/pipeline.py NameMasker imzasıyla aynı
```

| Tür | Etiket | Nasıl |
|---|---|---|
| E-posta | `[E-POSTA]` | düzenli ifade |
| Telefon | `[TELEFON]` | +90/0090/0 önekli 10 hane (cep ve sabit), parantez/nokta/tire; yurt dışı `+` numaralar |
| TCKN | `[TCKN]` | 11 haneli her sayı (sağlama kontrolü yapılmaz: kaçırmaktansa fazla maskele) |
| IBAN | `[IBAN]` | TR IBAN |
| Bağlantı | `[BAĞLANTI]` | http/www ve küçük harfli alan adları; "Node.js", "ASP.NET", "socket.io" dokunulmaz |
| Doğum tarihi | `[DOĞUM TARİHİ]` | "Doğum Tarihi:", "D.T.", "Date of birth" sonrası; ayrıca yılı 1950–2012 olan her tam tarih |
| Adres | `[ADRES]` | "Adres:" etiketi; Mah./Sok./Cad./Bulvarı/Street… ipucu ancak yanında kapı numarası, il veya posta kodu varsa ("Acme Street Labs" adres değil); posta kodu + il |
| Ad soyad | `[AD SOYAD]` | kurallar (etiketli alan, belgenin ilk satırları, unvanlı adlar, bilinen ilk adla başlayan grup) + yerel BERTurk NER; bulunan adın kelimeleri metnin her yerinde (ör. "Mert'in"). Taksonomi ve unvan kelimeleri (Python, Backend, Developer, Kıdemli…) ad sayılmaz ve yayılmaz |

- **Kabul kriteri:** telefon, e-posta, TCKN %100. Testler 12 telefon biçimi × 6 bağlam, 4 e-posta × 6 bağlam ve 500 rastgele TCKN × 4 bağlamla bunu doğrular; ayrıca yetkinlik metninin bozulmadığını (`KEEP` örnekleri) ve sentetik CV'lerde ad/iletişim kalmadığını (PDF → metin → maske) test eder.
- **Ad tespiti: kurallar + NER (karar #24).** `pii/ner.py` yerel `akdeniz27/bert-base-turkish-cased-ner` modelini (MIT, sürüm sabit) kullanır. Modelin parçaladığı kelimeler ("Post" + "##man") tam kelimeye genişletilir; yetkinlik taksonomisindeki kelimeler (`scraper/taxonomy/skills.csv`, başka yol için `CAREERAI_TAXONOMY`) ad sayılmaz. Uzun metin satır sınırlarından 1000 karakterlik parçalara bölünür.
  - Ölçüm (58 öğelik sentetik set, 63 ad kelimesi): kurallar %44 → kurallar + NER + filtre %100, gerçek yanlış pozitif 3. ~420 MB disk, ~760 MB bellek, CV başına ~170 ms (CPU).
  - Kurulum isteğe bağlı: `pip install -e ".[ner]"` (sunucuda torch'un CPU sürümü). Kurulu değilse `default_detector()` None döner ve sadece kurallar çalışır; CI bu şekilde çalışır, gerçek model testi atlanır.
  - Model ilk kullanımda Hugging Face'ten bir kez indirilir; sunucuda imaj derlenirken indirilip `HF_HUB_OFFLINE=1` ile çalıştırılmalı. Metin hiçbir zaman dışarı gönderilmez.

### `extraction` v2 — yerel LLM ile birleşik çıkarım (T-032)

```python
from extraction.llm import extract_skills_v2

result = extract_skills_v2(masked_text, "tr")  # OLLAMA_URL, OLLAMA_MODEL ortam değişkenleri; yoksa yerel llama3.1:8b
result.present_skills()  # sözleşmedeki present_skills (verified dahil)
result.model  # {"name": "llama3.1:8b", "prompt_version": "v1"}
result.llm_error  # None, "LLM_TIMEOUT" veya "INTERNAL"; hata olursa sonuç v1'dir
```

- İstek: JSON şeması (`format`), `temperature` 0,1, prompt `prompts/skill_extraction` (T-044). Zaman aşımı 150 sn.
- **v1 temeldir.** LLM'in taksonomiye eşlenen yetkinliği sadece v1'de de varsa kullanılır ve v1'in bilinmeyen seviye/yılını tamamlar. v1'de olmayan taksonomi yetkinliği alınmaz: ya v1 kuralı onu bilerek eledi (istek cümlesi, ders satırı) ya da metinde yok.
- **Halüsinasyon filtresi:** taksonomide olmayan yetkinlik `verified: false` ile eklenir, ama sadece adı CV metninde geçiyorsa. Metinde olmayan ad atılır.
- Model yanıtı ve CV metni loglanmaz; hata ayrıntısı da istisnaya taşınmaz.
- **Deneme (10.11.2026, 10 TR sentetik CV, llama3.1:8b, geliştirici bilgisayarında GPU):** hata 0; CV başına ~6–9 sn (ilk çağrı model yüklemesiyle 46 sn); v1'in seviyesi bilinmeyen 44 yetkinliğine LLM seviye verdi; 12 doğrulanmamış ad eklendi (ör. Room, DVC, Plastic SCM, "Manuel test"). LLM'in verdiği seviyelerin doğruluğu ölçülmedi: T-019 altın standardı bekleniyor.

### `prompts` — versiyonlu LLM prompt'ları (T-044)

```python
from prompts import get_prompt, model_info

prompt = get_prompt("skill_extraction")  # CURRENT'taki sürüm; ("skill_extraction", "v1") ile sabitlenebilir
model = model_info("llama3.1:8b", prompt)  # {"name": "llama3.1:8b", "prompt_version": "v1"}
```

- Her prompt `prompts/<ad>/<sürüm>.txt` dosyasıdır. Yayımlanmış dosya değiştirilmez: yeni sürüm aç, `CURRENT`'ı güncelle, özetini `tests/prompts/test_library.py` içine ekle.
- `model_info` çıktısı `contracts/analysis_result.schema.json` içindeki `model` nesnesi ve `analyses.model_name` / `analyses.prompt_version` değerleridir.
- Örneklerde gerçek yetkinlik adı yazılmaz (karar #26).

### `matching` — uyum skoru ve eksik yetkinlikler (T-042)

```python
from matching import CvSkill, load_role_demand, match
from embedding import default_encoder

role = load_role_demand(conn, "backend-developer")  # role_skill_stats + skills.embedding (psycopg)
cv = [CvSkill(s["skill"], s.get("verified", True)) for s in result.present_skills()]  # extraction v2
m = match(cv, role.demands, corpus_postings=role.corpus_postings, embed=default_encoder())
(
    m.match_score,
    m.postings_analyzed,
    m.low_data,
    m.missing_skills(),
)  # contracts: match_score, postings_analyzed, missing_skills
```

- **Talep ağırlığı** = pozisyondaki talep oranı × IDF; IDF = ln((1+N)/(1+df)) + 1, N tüm pozisyonların ilanı, df yetkinliği isteyen ilan (`role_skill_stats`'tan). Her yerde istenen yetkinlik (Git, İngilizce) skoru az etkiler. Talep oranı %5'in altındaki uzun kuyruk hesaba katılmaz (`MIN_DEMAND_RATIO`).
- **Uyum skoru** (0–100) = eşleşen yetkinliklerin ağırlığı / pozisyonun toplam ağırlığı.
- **Eşleşme:** taksonomideki yetkinlik adıyla eşleşir (büyük/küçük harf duyarsız). Taksonomide olmayan ad (`verified=False`) kosinüs benzerliğiyle pozisyondaki en yakın yetkinliğe bağlanır, katkısı ağırlık × benzerlik. İki farklı taksonomi yetkinliği vektörle eşlenmez (Redux–Redis, Vite–Vitest çok yakın çıkıyor, T-041 ölçümü).
- **Eşik** ayarlanabilir (`threshold`); varsayılan **0,90**, çünkü e5-small'da 0,80 neredeyse her şeyi eşler (T-041 ölçümü). Kabul kriterindeki 0,80 MiniLM içindi.
- **Eksik yetkinlikler** talep oranına göre (eşitse pozisyona özgü olan önce); `resources` boş liste, T-043 doldurur. **`low_data`**: pozisyonda 50'den az ilan (karar #23, `scraper/etl/stats.py` ile aynı değer, test denetliyor); sözleşmede alanı yok, API/arayüz uyarısı için.
- **Deneme (17.11.2026):** 10 TR sentetik CV (v1 çıkarım) × 12 pozisyonun gerçek istatistiği (`scraper/exports/template_input.json`, pozisyon başına ilk 30 yetkinlik). Hedef pozisyon 9 CV'de 1., birinde 2. sırada; hedef skoru diğer pozisyonların ortalamasından medyan 39 puan yüksek. Skorlar 31–65. Not: en çok istenenler arasında kişisel beceriler (İletişim, Takım Çalışması) var ve CV'de açıkça yazılmadıkça eksik çıkıyor; T-043'te öneri listesinde nasıl sunulacağı düşünülmeli.

### `recommendation` — eğitim kaynağı önerisi (T-043, RAG)

```python
from recommendation import load_candidates, recommend

candidates = load_candidates(conn, [x.skill for x in m.missing])  # resources (sadece canlı link) + skills
rec = recommend(
    m.missing, candidates, role_name=role.name, postings_analyzed=m.postings_analyzed, present=[s.skill for s in cv]
)
rec.missing_skills()  # contracts: missing_skills, resources dolu
rec.model  # {"name": ..., "prompt_version": ...} (prompts/recommendation)
```

- **Aday:** eksik yetkinliğin `resources` kayıtları (`is_alive`). Kurallı sıra: Türkçe, başlangıç, ücretsiz, kısa süre önce; LLM'e yetkinlik başına en çok 8 aday gösterilir.
- **LLM sadece numara seçer** (Ollama, JSON şeması): seçilen `resource_id` o yetkinliğe gösterilen adaylardan değilse atılır. Başlık, link, sağlayıcı, seviye her zaman veritabanındaki kayıttan gelir; LLM'in yazdığı hiçbir şey link olamaz (karar #10). LLM'e link gösterilmez, CV metni gitmez (sadece pozisyon adı, eksik ve mevcut yetkinlik adları, kaynak bilgisi).
- **Gerekçe** = koddan üretilen ilan istatistiği ("İncelenen 150 Backend Developer ilanının %62'si PostgreSQL istiyor.", ek ses uyumuna göre) + LLM'in tek cümlesi. LLM gerekçesi boşsa, link/adres veya yüzde içeriyorsa ya da 240 karakteri aşıyorsa kurallı gerekçe yazılır.
- **LLM çalışmazsa** veya az seçerse boşluklar kurallı sırayla dolar (`llm_error` hata kodunu taşır); öneri her durumda çıkar. Yetkinlik başına 3 kaynak (`PER_SKILL`); LLM sadece ilk 5 eksik yetkinliğin gerekçesini yazar (`LLM_SKILLS`, CPU süresi için), kalanlar kurallı.
- **Deneme (17.11.2026):** `scraper/taxonomy/resources.csv` adayları, 5 eksik yetkinlik (Docker, PostgreSQL, Kubernetes, Redis, Linux), Llama 3.1 8B (bu bilgisayar, CPU): 9/9 seçim geçerli, 9 gerekçenin 9'u LLM'den, uydurma/atılan seçim 0. Süre 7,8 sn (model bellekteyken; ilk çağrıda modelin yüklenmesiyle 85 sn).

### `embedding` — yetkinlik ve ilan vektörleri (T-041)

```bash
pip install -e ".[embedding]"     # torch CPU: --index-url https://download.pytorch.org/whl/cpu
python -m embedding               # DATABASE_URL; vektörü olmayan yetkinlik ve aktif ilanlar
python -m embedding --hepsi       # model veya metin biçimi değişince hepsi yeniden
```

```python
from embedding import default_encoder, cosine

(cv_vec,) = default_encoder()(["Express"])  # sorgu tarafı (T-042): taksonomide olmayan ad, çıplak
```

- **Model:** `intfloat/multilingual-e5-small` (384 boyut, normalize; her metne `query: ` öneki). İlk çalışmada Hugging Face'ten indirilir (~470 MB), sonra önbellekten; çağrılar tamamen yereldir. Sunucuda/işçi imajında model önceden indirilmeli.
- **Metinler:** yetkinlik = "ad, eş anlamlılar" (`skills.csv`); ilan = başlık + maskelenmiş açıklamanın ilk 1.000 karakteri; pasif ilanlar atlanır. Yazım parti parti (256) commit'lenir; yarıda kesilen çalışma kaldığı yerden sürer. Metin loglanmaz.
- **Neden e5-small, MiniLM değil** (10.11.2026 ölçümü, 374 yetkinlik / 414 eş anlamlı): her eş anlamlı kendi yetkinliğinin metninden çıkarılıp "taksonomide olmayan ad" gibi sorgulandı (leave-one-out). En yakın yetkinliğin doğru çıkma oranı MiniLM'de %53 (çıplak adla %44), e5-small'da %65. MiniLM çıplak adda farklı yetkinlikleri de çok yakın buluyor (Vite–Vitest 0,95, Redux–Redis 0,93; 62 farklı çift ≥ 0,80).
- **Eşik (T-042 için):** e5 skorları dar bir aralıkta (0,85–0,95), bu yüzden kabul kriterindeki 0,80 bu modelde her şeyi eşler. Leave-one-out'ta eşik 0,90: doğru eşleşmelerin %38'i yakalanır, yanlış en yakın aday %3; 0,88: %55 / %10. Örnekler: Express → Express.js 0,92, React.js → React 0,95; Room, DNS, TryHackMe, Plastic SCM, Manuel test için en yakın aday ≤ 0,89 (eşleşmez, doğru). Kısaltmalar (k8s, py) vektörle bulunamaz; onları sözlük eşleyicisi (`extraction`) yakalıyor, vektör sadece sözlükte olmayan adlar için.
- **Hız (CPU):** 374 yetkinlik ~1 sn; ilan 19/sn (6.600 ilanın ilk yüklemesi ~6 dk, gece artışı birkaç saniye). Model yükleme ~10 sn.
- **Uçtan uca deneme (10.11.2026):** Postgres 16 + pgvector, `skills`/`job_postings` modeldeki sütunlar ve migration 0003'teki HNSW indeksiyle; taksonomi `skills.csv`'den, 600 sentetik ilan (60'ı pasif). `python -m embedding`: 374 yetkinlik 2,1 sn, 540 aktif ilan 4,4 sn; ikinci çalışma 0 satır (sadece eksikler); pasif ilanlar boş kaldı. İlan sorgusu `ORDER BY embedding <=> :v` HNSW indeksini kullanıyor (2,7 ms). Veritabanı testi `TEST_DATABASE_URL` ile çalışır (CI'ın AI işinde Postgres yok, orada atlanıyor).

### `extraction` — yetkinlik çıkarımı v1 (T-031)

```python
from extraction import extract_skills, to_present_skills

skills = extract_skills(masked_text, "tr")  # maskelenmiş CV metni (pii.mask)
skills[0].skill, skills[0].level, skills[0].years, skills[0].confidence  # "Python", "advanced", 4, 0.95
to_present_skills(skills)  # contracts/analysis_result.schema.json → present_skills
```

- **Sözlük:** `scraper/taxonomy/skills.csv` (başka yol için `CAREERAI_TAXONOMY`). İlan ETL'i (`scraper/etl/skills.py`) de aynı `Matcher`'ı kullanır; kural değişikliği iki tarafı etkiler. Kurallar: kelime sınırı ("Java" ≠ "JavaScript"), "C++"/"Node.js"/".NET", harf duyarlı adlar ("Go", "SOLID"), Türkçe harf katlama, çakışmada uzun ad ("Spring Boot" > "Spring"). LLM gerektirmez; LLM çalışmazsa yedek yoldur.
- **CV kuralları** (`eval/etiketleme-kilavuzu.md` ile aynı): istek cümlesi ("ileride Go öğrenmek istiyorum", "Next.js öğreniyorum") ve ders listesi ("Dersler: Kriptografi") alınmaz; "DevOps: Docker, …" başlığı yetkinlik sayılmaz; konuşulan dil sadece Diller bölümünde veya seviyesiyle ("İngilizce: B2") alınır.
- **Seviye:** adın hemen yanındaki ipucu: "Python (ileri düzey)", "Java — orta", "ileri düzey SQL", CEFR (A1–A2 beginner, B1–B2 intermediate, C1–C2/ana dil advanced). Yoksa `unknown`.
- **Deneyim yılı:** ipucundan ("(4 yıl)") veya aynı cümle parçasındaki "N yıl/yıllık/yıldır/years"; "2022 – 2026" gibi tarih aralıkları sayılmaz.
- **Güven:** sözlük eşleşmesi kesin olduğu için güven, yetkinliğin CV'de ne kadar desteklendiğini gösterir: 0,6 + Yetenekler bölümünde 0,15 + 2 kez geçiyorsa 0,1 + seviye/yıl varsa 0,1 (en çok 0,95). `verified` her zaman `true`.
- **Ölçüm** (10 TR sentetik CV, T-018'deki geçici referans): kesinlik 0,98, duyarlılık 0,97; Llama 3.1 8B tek başına duyarlılık 0,69. Referans da sözlükle üretildiği için bu sayılar iyimser; T-019 gold etiketleriyle tekrar ölçülecek. Kalan fark çoğunlukla referanstan: "GitHub Actions" içindeki GitHub'ı ayrıca sayması gibi.

