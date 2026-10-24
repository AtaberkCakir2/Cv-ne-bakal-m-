# CareerAI — Claude için proje kuralları

Bu dosyayı ekipteki herkesin Claude'u her oturumda okur. Kurallar değişirse bu dosyayı PR ile güncelleyin.

## Proje

CareerAI, öğrencinin CV'sini (PDF) okuyup hedef pozisyon için güncel iş ilanlarıyla karşılaştıran, eksik yetkinlikleri bulan ve bu eksikleri kapatacak eğitim kaynakları öneren bir sistemdir. Bitirme projesidir (3 kişi). Hedef: 18.01.2027'de v1.0.0 ile canlıya çıkış.

Akış: İstemci (web / Electron / React Native) → FastAPI → Redis kuyruğu → AI worker (PDF → kişisel veri maskeleme → yetkinlik çıkarımı → embedding → eşleştirme → kaynak önerisi, Ollama) → PostgreSQL + pgvector. Ayrı bir toplayıcı her gece ilanları toplar ve istatistikleri yeniler.

## Klasör sahipliği

| Klasör | Sahibi | İçerik |
|---|---|---|
| `scraper/` | Ataberk | İlan toplama, ETL, yetkinlik taksonomisi, kaynak havuzu |
| `infra/` | Ataberk | Sunucu, Docker, CI/CD, izleme, yedekleme |
| `backend/app/db/` | Ataberk | SQLAlchemy modelleri, Alembic migration'ları |
| `ai/` | Burak | PDF/OCR, PII maskeleme, yetkinlik çıkarımı, eşleştirme, öneri, Ollama |
| `mobile/` | Burak | React Native (Expo) uygulaması |
| `backend/` (db hariç) | Anıl | FastAPI, kimlik doğrulama, kuyruk, endpoint'ler |
| `web/` | Anıl | React arayüzü (Electron da bunu kullanır) |
| `contracts/` | Ortak | Modüller arası veri formatları — değişiklik 3 kişinin onayıyla |
| `docs/` | Ortak | Kararlar, diyagramlar, raporlar |

## Claude için kurallar

1. **Sadece kullanıcının kendi klasöründe değişiklik yap.** Başka birinin klasöründe değişiklik gerekiyorsa yapma; ne değişmesi gerektiğini ve nedenini yaz, kullanıcı sahibine iletsin.
2. **`contracts/` altındaki formatlara uy.** Kod sözleşmeyle çelişiyorsa sözleşmeyi değil kodu düzelt. Sözleşmenin değişmesi gerektiğini düşünüyorsan öner, kendin değiştirme.
3. **Başka modül henüz hazır değilse sahte veri kullan.** Sahte veriler `contracts/examples/` altındaki örneklerle birebir aynı formatta olmalı.
4. **Sır ve kişisel veri yok.** `.env`, şifre, API anahtarı, gerçek CV veya kişisel veri içeren dosyaları asla commit'leme. Testlerde sadece sahte/anonim CV kullan.
5. **CV dosyası ve ham CV metni hiçbir yerde saklanmaz** (veri tabanı, disk, log). Sadece SHA-256 hash ve çıkarılan yetkinlikler tutulur. LLM'e gitmeden önce kişisel veriler maskelenir.
6. **Dış yapay zeka API'si kullanılmaz** (OpenAI, Claude API vb.). Tüm LLM çağrıları yerel Ollama üzerinden yapılır.
7. **`main` dalına doğrudan commit yok.** Her iş ayrı branch'te (`isim/kisa-aciklama`, ör. `anil/auth-endpoint`) yapılır ve PR ile birleştirilir.
8. Commit mesajları Türkçe ve kısa olabilir; conventional commits öneki kullan: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## Teknoloji

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, Celery + Redis
- PostgreSQL 16 + pgvector
- Ollama (Llama 3.x 8B Instruct veya Gemma; benchmark sonrası kesinleşecek)
- Embedding: sentence-transformers (çok dilli, 384 boyut)
- PDF: pdfplumber + PyMuPDF; OCR: Tesseract (tur + eng)
- Web: React + Vite + TypeScript; masaüstü: Electron; mobil: React Native (Expo)
- Python kod stili: ruff + mypy. TypeScript: eslint + prettier.

## Çalıştırma

Altyapı servisleri (Postgres, Redis, Ollama): `docker compose up -d` — ayrıntılar `README.md` içinde.
