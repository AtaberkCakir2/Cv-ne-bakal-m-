# backend/ — Sahibi: Anıl (db modelleri ve migration'lar: Ataberk)

FastAPI uygulaması: kimlik doğrulama, CV yükleme, analiz kuyruğu (Celery + Redis), endpoint'ler.

Sözleşmeler: `contracts/api.md`, `contracts/analysis_result.schema.json`

İlk işler: FastAPI iskeleti (/health), CV yükleme endpoint'i. AI modülü hazır olana kadar `contracts/examples/analysis_result.example.json` sahte sonuç olarak döndürülür.
