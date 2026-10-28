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

> **Windows:** `.env`'deki servis adreslerinde `localhost` değil **`127.0.0.1`** yazın (`DATABASE_URL`, `REDIS_URL`, `OLLAMA_URL`). Windows'ta `localhost` önce IPv6'ya (`::1`) çözülür, docker-compose portları ise sadece `127.0.0.1`'e açıktır; her bağlantı ~2 sn bekler ve `/health/ready` Redis için zaman aşımı verir. (24.10.2026'da gerçek servislerle doğrulandı.)

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

## Sıradaki işler

T-038 CV yükleme endpoint'i · T-037 kimlik doğrulama · T-039 analiz kuyruğu. AI modülü hazır olana kadar analiz sonucu olarak `contracts/examples/analysis_result.example.json` döndürülür.
