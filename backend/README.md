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

Testler hiçbir servis (Postgres, Redis, Ollama) çalışmadan geçer. Veritabanı isteyen testler (`tests/db`, `tests/auth`) sadece `TEST_DATABASE_URL` verilince çalışır; boş test veritabanı için `app/db/README.md` → "Testler". CI bunları her PR'da çalıştırır.

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

## Kimlik doğrulama (T-037)

| Metot | Yol | Not |
|---|---|---|
| POST | `/api/v1/auth/register` | Üç KVKK onayı zorunlu; doğrulama e-postası gider |
| POST | `/api/v1/auth/login` | `{access_token, refresh_token, token_type, expires_in}` |
| POST | `/api/v1/auth/refresh` | Refresh token tek kullanımlık; kullanılmış token tekrar gelirse bütün oturumlar kapanır |
| POST | `/api/v1/auth/logout` | Refresh token iptali |
| POST | `/api/v1/auth/verify-email` · `/forgot-password` · `/reset-password` | Tek kullanımlık bağlantılar; şifre sıfırlanınca bütün oturumlar kapanır |
| GET | `/api/v1/users/me` | `Authorization: Bearer <access_token>` |

- Parolalar argon2id; access token 15 dk (JWT, HS256), refresh token 7 gün (veritabanında sadece SHA-256 hash'i).
- Korumalı uç yazarken: `user: CurrentUser` (oturum açmış kullanıcı) veya `user: AdminUser` (yönetici) — `app/api/deps.py`. Rol her istekte veritabanından okunur.
- `JWT_SECRET` local/test dışında `.env`'de mutlaka ayarlanmalı (en az 32 karakter); ayarlanmazsa uygulama açılmaz.
- **E-posta:** Gerçek e-posta servisi henüz yok. İletiler bellekte tutulur (`OutboxEmailSender`); `ENVIRONMENT=local` iken doğrulama ve sıfırlama bağlantıları API loguna yazılır.

### Kalıcı test kullanıcısı

Uçtan uca testlerde her seferinde kayıt olmamak için, `.env`'e `E2E_TEST_EMAIL` (`@example.com` ile bitmeli) ve `E2E_TEST_PASSWORD` ekleyip:

```bash
python scripts/seed_test_user.py
```

Kullanıcı doğrulanmış ve KVKK onayları verilmiş olarak oluşturulur; tekrar çalıştırmak şifreyi günceller. Sadece local/test ortamında çalışır. Yüklenecek CV her zaman `contracts/examples/` altındaki sahte CV'dir.

## Sıradaki işler

T-039 analiz kuyruğu · T-048 sonuç ve katalog endpoint'leri · T-049 profil ve KVKK endpoint'leri · T-050 rate limit (giriş/kayıt uçları için).
