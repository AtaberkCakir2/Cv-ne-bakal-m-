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
mypy parsing tests eval/scripts
```

Testler gerçek CV kullanmaz; PDF'ler test sırasında bellekte üretilir.

## Modüller

| Modül | Görev | Durum |
|---|---|---|
| `parsing/` | PDF → metin (T-020) | ✅ |
| `ocr/` | Taranmış CV için OCR (T-029) | — |
| `pii/` | Kişisel veri maskeleme (T-030) | — |
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
