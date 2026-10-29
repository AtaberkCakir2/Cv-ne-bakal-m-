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
| `pii/` | Kişisel veri maskeleme (T-030) | Devam ediyor (kurallar hazır; NER modeli kararı açık) |
| `extraction/` | Yetkinlik çıkarımı (T-031, T-032) | — |
| `eval/` | Etiketli değerlendirme seti ve araçları (T-019) | Devam ediyor |

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

result = mask(cv_text, "tr")  # LLM'e sadece result.text gider
result.counts  # {Kind.EMAIL: 1, Kind.PHONE: 1, Kind.NAME: 3, ...} — loglanabilir, kişisel veri içermez
mask_text(text, "en")  # sadece metin; scraper/etl/pipeline.py NameMasker imzasıyla aynı
```

| Tür | Etiket | Nasıl |
|---|---|---|
| E-posta | `[E-POSTA]` | düzenli ifade |
| Telefon | `[TELEFON]` | +90/0090/0 önekli 10 hane (cep ve sabit), parantez/nokta/tire; yurt dışı `+` numaralar |
| TCKN | `[TCKN]` | 11 haneli her sayı (sağlama kontrolü yapılmaz: kaçırmaktansa fazla maskele) |
| IBAN | `[IBAN]` | TR IBAN |
| Bağlantı | `[BAĞLANTI]` | http/www ve küçük harfli alan adları; "Node.js", "ASP.NET", "socket.io" dokunulmaz |
| Doğum tarihi | `[DOĞUM TARİHİ]` | "Doğum Tarihi:", "D.T.", "Date of birth" sonrası; ayrıca yılı 1950–2012 olan her tam tarih |
| Adres | `[ADRES]` | "Adres:" etiketi; Mah./Sok./Cad./Bulvarı/Street… içeren alan; posta kodu + il |
| Ad soyad | `[AD SOYAD]` | etiketli alan, belgenin ilk satırları, unvanlı adlar (Dr., Prof. Dr.…), bilinen ilk adla başlayan grup; bulunan adın kelimeleri metnin her yerinde (ör. "Mert'in") |

- **Kabul kriteri:** telefon, e-posta, TCKN %100. Testler 12 telefon biçimi × 6 bağlam, 4 e-posta × 6 bağlam ve 500 rastgele TCKN × 4 bağlamla bunu doğrular; ayrıca yetkinlik metninin bozulmadığını (`KEEP` örnekleri) ve sentetik CV'lerde ad/iletişim kalmadığını (PDF → metin → maske) test eder.
- **Ad tespiti şimdilik kurallarla.** Kabul kriterindeki NER için `mask(text, lang, detector=...)` bağlantı noktası hazır; hangi yerel modelin kullanılacağı (ör. Türkçe BERT NER) açık bir karar: bellek bütçesi (worker-ai 2 GB) ve CPU süresi ölçülerek verilecek.
