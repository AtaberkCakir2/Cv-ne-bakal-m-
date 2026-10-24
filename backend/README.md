# backend/ — Sahibi: Anıl (db modelleri ve migration'lar: Ataberk)

FastAPI uygulaması: kimlik doğrulama, CV yükleme, analiz kuyruğu (Celery + Redis), endpoint'ler.

Sözleşmeler: `contracts/api.md`, `contracts/analysis_result.schema.json`

## Kurulum ve çalıştırma

Python 3.12 gerekir. `backend/` klasöründe:

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

- API dokümanı (OpenAPI): http://localhost:8000/docs
- Canlılık: http://localhost:8000/api/v1/health
- Hazırlık (DB, Redis, Ollama): http://localhost:8000/api/v1/health/ready → servisler çalışmıyorsa **503** döner; bu normaldir. Servisleri başlatmak için repo kökünde `docker compose up -d`.

Ayarlar repo kökündeki `.env` dosyasından okunur (değişkenler kök `README.md`'de). `.env` yoksa yerel geliştirme varsayılanları kullanılır.

> Windows'ta "Filename too long" veya benzeri yol hatası alırsanız sanal ortamı kısa bir yolda oluşturun (ör. `python -m venv C:\venv\careerai`).

## Test ve kod kalitesi

```bash
pytest
ruff check . && ruff format --check .
mypy app tests
```

Testler hiçbir servis (Postgres, Redis, Ollama) çalışmadan geçer.

## Yapı

```
app/
  main.py              # create_app(): middleware, hata işleyicileri, router'lar
  core/
    config.py          # Ayarlar (pydantic-settings)
    logging.py         # JSON log, istek kimliği, e-posta/telefon maskeleme
    middleware.py      # X-Request-ID, istek logu, beklenmeyen hatalar → 500
    errors.py          # RFC 7807 hata formatı (application/problem+json)
  api/routers/         # HTTP katmanı: sadece istek/yanıt, iş mantığı yok
  services/            # İş mantığı
  repositories/        # Veri erişimi (SQL/ORM); modeller app/db/ altında (Ataberk)
  schemas/             # Pydantic istek/yanıt modelleri
tests/
```

Kurallar:
- Router → service → repository yönünde çağrı yapılır; router veritabanına doğrudan erişmez.
- Tüm endpoint'ler `/api/v1` altında; hatalar her zaman RFC 7807 biçiminde döner (`{type, title, status, detail?, instance, request_id, errors?}`).
- Her yanıtta `X-Request-ID` başlığı vardır; hata bildirirken bu kimliği isteyin, loglarda aynı kimlikle aranır.
- Loglara e-posta, telefon veya CV içeriği yazılmaz (karar #9). Maskeleme filtresi ikinci güvenlik katmanıdır, ilk katman değil.

## Endpoint'ler

| Metot | Yol | Durum |
|---|---|---|
| GET | `/api/v1/health` | ✅ |
| GET | `/api/v1/health/ready` | ✅ |
| POST | `/api/v1/analyses` | ✅ CV doğrulama (≤ 5 MB, ≤ 5 sayfa, PDF imzası, şifreli/bozuk PDF), SHA-256 · kimlik doğrulama yok (T-037) |
| GET | `/api/v1/analyses/{id}` | ✅ sonuç · liste/silme/geri bildirim T-048 |

**Geliştirme modu (geçici):** Analizler bellekte tutulur (sunucu kapanınca silinir) ve kuyruk hemen `contracts/examples/analysis_result.example.json` örnek sonucunu döner. Böylece web ve mobil ekranlar AI modülünü beklemeden geliştirilebilir. Gerçek veritabanı deposu T-012 (Ataberk), gerçek kuyruk T-039 ile gelecek.

Örnek:

```bash
curl -F "file=@ozgecmis.pdf;type=application/pdf" -F target_role_id=1 http://localhost:8000/api/v1/analyses
curl http://localhost:8000/api/v1/analyses/<analysis_id>
```

### CV diske yazılmaz

Starlette, 1 MB'ı aşan yüklemeleri varsayılan olarak geçici disk dosyasına yazar. `app/core/uploads.py` bu eşiği izin verilen en büyük istek boyutunun üstüne çeker ve 5 MB + 64 KB'tan büyük istekleri gövde okunmadan reddeder (`Content-Length` zorunlu). `tests/test_analyses_upload.py::test_upload_is_never_written_to_disk` bunu doğrular. Production'da Caddy'de de istek gövdesi sınırı (`request_body max_size 6MB`) olmalı (T-075, Ataberk).

## Sıradaki işler

T-037 kimlik doğrulama · T-039 analiz kuyruğu (Celery + Redis) · T-048 sonuç ve katalog endpoint'leri.
