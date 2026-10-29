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
mypy parsing pii tests eval/scripts
```

Testler gerçek CV kullanmaz; PDF'ler test sırasında bellekte üretilir.

## Modüller

| Modül | Görev | Durum |
|---|---|---|
| `parsing/` | PDF → metin (T-020) | ✅ |
| `ocr/` | Taranmış CV için OCR (T-029) | — |
| `pii/` | Kişisel veri maskeleme (T-030) | ✅ |
| `extraction/` | Yetkinlik çıkarımı (T-031, T-032) | — |
| `eval/` | Etiketli değerlendirme seti ve araçları (T-019) | Devam ediyor |
| `eval/benchmark/` | Yerel LLM benchmark'ı (T-018): Llama 3.1 8B seçildi, karar #26 | ✅ |

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
