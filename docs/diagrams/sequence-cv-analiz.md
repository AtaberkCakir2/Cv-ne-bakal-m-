# Sequence diyagramı: CV yükleme → sonuç

Bir analizin baştan sona akışı. CV dosyası ve ham metin hiçbir adımda diske, veritabanına veya loga yazılmaz (karar #9); worker'a bellekte iletilir ve iş bitince bellekten atılır.

```mermaid
sequenceDiagram
    autonumber
    actor O as Öğrenci
    participant C as İstemci<br/>(Web / Electron / Mobil)
    participant A as FastAPI
    participant Q as Redis kuyruğu
    participant W as AI worker
    participant L as Ollama (yerel LLM)
    participant D as PostgreSQL + pgvector

    O->>C: Hedef pozisyon seç, CV (PDF) yükle
    C->>A: POST /analyses (PDF + target_role_id)
    A->>A: Doğrula: PDF mi, ≤ 5 MB, ≤ 5 sayfa, saatlik sınır
    A->>D: analyses kaydı (status=queued, cv_sha256)
    A->>Q: İş ekle (analysis_id + PDF baytları)
    A-->>C: 202 {analysis_id, status: "queued"}
    C->>A: GET /analyses/{id}/events (SSE)

    Q->>W: İşi al (eşzamanlılık = 1)
    W->>D: status=processing
    W->>W: PDF → metin (pdfplumber / PyMuPDF)
    opt Metin < 200 karakter (taranmış CV)
        W->>W: OCR (Tesseract tur+eng)
    end
    W->>W: Kişisel veriyi maskele (ad, telefon, e-posta, TCKN...)
    W->>W: Yetkinlik çıkarımı v1 (sözlük + kural)
    W->>L: Yetkinlik çıkarımı v2 (maskelenmiş metin, JSON şeması)
    alt LLM cevap verdi
        L-->>W: Yetkinlikler (JSON)
        W->>W: v1 + v2 birleştir, taksonomide olmayanı "doğrulanmamış" işaretle
    else Zaman aşımı / hata
        W->>W: Sadece v1 sonucuyla devam et
    end
    W->>D: Pozisyonun talep istatistikleri (role_skill_stats) + vektör benzerliği
    W->>W: Uyum skoru (0-100), eksikleri talep oranına göre sırala
    W->>D: Eksik yetkinlikler için aday kaynaklar (resources)
    W->>L: Adaylar arasından seç + Türkçe gerekçe yaz
    L-->>W: Seçilen resource_id'ler + gerekçe
    W->>D: Sonucu kaydet (analysis_skills, analysis_recommendations, status=done)
    W->>W: PDF ve metni bellekten at

    A-->>C: SSE: status=done
    C->>A: GET /analyses/{id}
    A->>D: Sonucu oku
    A-->>C: analysis_result.schema.json
    C-->>O: Uyum skoru, eksik yetkinlikler, kaynak kartları
```

## Hata durumları

| Durum | Ne olur | `error.code` |
|---|---|---|
| PDF değil / bozuk / şifreli | API veya worker reddeder, `status=failed` | `PDF_UNREADABLE` |
| > 5 MB veya > 5 sayfa | API reddeder, kuyruğa girmez | `PDF_TOO_LARGE` |
| OCR'dan sonra da metin yok | `status=failed` | `NO_TEXT_FOUND` |
| LLM cevap vermiyor | Sözlük (v1) sonucuyla devam eder, analiz yine `done` olur | — |
| Görevin toplam süresi aşıldı (T-057) | `status=failed` | `LLM_TIMEOUT` |
| Beklenmeyen hata | Kullanıcıya genel mesaj; ayrıntı sadece logda (kişisel veri maskeli) | `INTERNAL` |

Kodlar `contracts/analysis_result.schema.json` ile aynıdır.
