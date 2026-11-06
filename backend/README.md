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

## Endpoint'ler

| Metot | Yol | Durum |
|---|---|---|
| GET | `/api/v1/health` | ✅ |
| GET | `/api/v1/health/ready` | ✅ |
| POST | `/api/v1/analyses` | ✅ CV doğrulama (≤ 5 MB, ≤ 5 sayfa, PDF imzası, şifreli/bozuk PDF), SHA-256 · kimlik doğrulama henüz yok (T-048 ile eklenecek) |
| GET | `/api/v1/analyses/{id}` | ✅ sonuç · liste/silme/geri bildirim T-048 |

**Geliştirme modu (geçici):** Analizler bellekte tutulur (sunucu kapanınca silinir) ve kuyruk hemen `contracts/examples/analysis_result.example.json` örnek sonucunu döner. Böylece web ve mobil ekranlar AI modülünü beklemeden geliştirilebilir. Gerçek veritabanı deposu T-012 (Ataberk), gerçek kuyruk T-039 ile gelecek.

Örnek:

```bash
curl -F "file=@ozgecmis.pdf;type=application/pdf" -F target_role_id=1 http://localhost:8000/api/v1/analyses
curl http://localhost:8000/api/v1/analyses/<analysis_id>
```

### CV diske yazılmaz

Starlette, 1 MB'ı aşan yüklemeleri varsayılan olarak geçici disk dosyasına yazar. `app/core/uploads.py` bu eşiği izin verilen en büyük istek boyutunun üstüne çeker ve 5 MB + 64 KB'tan büyük istekleri gövde okunmadan reddeder (`Content-Length` zorunlu). `tests/test_analyses_upload.py::test_upload_is_never_written_to_disk` bunu doğrular. Production'da önde Caddy yok (karar #30): istek Cloudflare'den (ücretsiz planda 100 MB sınırı) cloudflared üzerinden gelir, bu yüzden 5 MB sınırını sadece bu ara katman uygular.

## Kimlik doğrulama (T-037)

| Metot | Yol | Not |
|---|---|---|
| POST | `/api/v1/auth/register` | Üç KVKK onayı zorunlu; doğrulama e-postası gider |
| POST | `/api/v1/auth/login` | `{access_token, refresh_token, token_type, expires_in}` |
| POST | `/api/v1/auth/refresh` | Refresh token tek kullanımlık; kullanılmış token tekrar gelirse bütün oturumlar kapanır |
| POST | `/api/v1/auth/logout` | Refresh token iptali |
| POST | `/api/v1/auth/verify-email` · `/forgot-password` · `/reset-password` | Tek kullanımlık bağlantılar; şifre sıfırlanınca bütün oturumlar kapanır |
| GET | `/api/v1/users/me` | `Authorization: Bearer <access_token>` |
| DELETE | `/api/v1/users/me/consents/acik_riza` | Açık rızayı geri alır (KVKK md. 11); kayıt silinmez, `withdrawn_at` dolar. Diğer türler 422 |

- Parolalar argon2id; access token 15 dk (JWT, HS256), refresh token 7 gün (veritabanında sadece SHA-256 hash'i).
- Korumalı uç yazarken: `user: CurrentUser` (oturum açmış kullanıcı) veya `user: AdminUser` (yönetici) — `app/api/deps.py`. Rol her istekte veritabanından okunur.
- **Lokal geliştirmede `.env`'e `ENVIRONMENT=local` yazın.** Ortam açıkça `local`/`test` yazılmazsa ve `JWT_SECRET` verilmezse giriş/kayıt çalışmaz (repodaki geliştirme anahtarıyla token üretilmez); `/health` açık kalır. `ENVIRONMENT=production` iken `JWT_SECRET` verilmezse uygulama hiç açılmaz.
- Production'da `.env`: `JWT_SECRET` ve `IP_HASH_SECRET` (ikisi de en az 32 karakter, farklı, rastgele).
- Bilinen sınırlar: aynı refresh token'la eşzamanlı iki yenileme oturumları kapatır (istemci yenilemeyi tek seferde yapmalı); ayrıntı `app/services/auth.py` başında.
- **E-posta:** Gerçek e-posta servisi henüz yok. İletiler bellekte tutulur (`OutboxEmailSender`, en fazla son 100 ileti; gitmez, staging'de doğrulama ve sıfırlama e-postası ulaşmaz); `ENVIRONMENT=local` iken doğrulama ve sıfırlama bağlantıları API loguna yazılır.

### Kalıcı test kullanıcısı

Uçtan uca testlerde her seferinde kayıt olmamak için, `.env`'e `E2E_TEST_EMAIL` (`@example.com` ile bitmeli) ve `E2E_TEST_PASSWORD` ekleyip:

```bash
python scripts/seed_test_user.py
```

Kullanıcı doğrulanmış ve KVKK onayları verilmiş olarak oluşturulur; tekrar çalıştırmak şifreyi günceller. Sadece local/test ortamında çalışır. Yüklenecek CV her zaman `contracts/examples/` altındaki sahte CV'dir.

## İstek sınırları (T-050)

| Sınır | Varsayılan | Anahtar | Ayar |
|---|---|---|---|
| Genel (sadece `/health` hariç; `/health/ready` dahil) | 100 / dk | IP | `RATE_LIMIT_GENERAL_PER_MINUTE` |
| Giriş, kayıt, e-posta doğrulama, şifremi unuttum, şifre sıfırlama (ortak sayaç) | 10 / dk | IP | `RATE_LIMIT_AUTH_PER_MINUTE` |
| Analiz oluşturma | 5 / saat | kullanıcı | `RATE_LIMIT_ANALYSES_PER_HOUR` |

- Aşılınca `429` + `Retry-After` (saniye), gövde RFC 7807. Sayaçlar Redis'te (`REDIS_URL`); IP açık yazılmaz, tuzlu özeti anahtar olur.
- Redis'e ulaşılamazsa sınır uygulanmaz, `rate_limit_store_unavailable` uyarısı loglanır ve 10 sn Redis denenmez. Tamamen kapatmak için `RATE_LIMIT_ENABLED=false`.
- **Production (T-075, karar #30):** API cloudflared arkasında. uvicorn'a `FORWARDED_ALLOW_IPS=<compose ağının alt ağı>` verilir (`infra/pc/compose.yml`, `COMPOSE_SUBNET`). Verilmezse bütün kullanıcılar cloudflared'in IP'siyle tek sayacı paylaşır. `*` verilirse istemcinin uydurduğu `X-Forwarded-For` kullanılır ve sınırlar aşılabilir: Cloudflare gelen başlığı silmez, gerçek IP'yi sona ekler, uvicorn da `*` iken ilk adresi alır. Redis ≥ 7 gerekli.
- Analiz sınırı (`AnalysesRateLimit`, `app/api/rate_limits.py`) analiz oluşturma ucu kimlik doğrulamaya bağlanınca o uca eklenir.

## Sıradaki işler

T-039 analiz kuyruğu · T-048 sonuç ve katalog endpoint'leri (analiz uçlarına kimlik doğrulama ve analiz sınırı bununla gelir).
