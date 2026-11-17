# CareerAI API rehberi (T-080)

Bu sayfa istemci yazan (web, masaüstü, mobil) veya API'yi deneyen biri içindir. Uçların tam tanımı (alanlar, tipler, örnekler) [`openapi.json`](openapi.json) dosyasındadır. Aynı tanım çalışan sunucuda iki yerde de görülebilir:

- Etkileşimli arayüz: `http://127.0.0.1:8000/docs`
- Ham tanım: `http://127.0.0.1:8000/api/v1/openapi.json`

Uçların listesi ve modüller arası sözleşme [`contracts/api.md`](../../contracts/api.md), analiz sonucunun biçimi [`contracts/analysis_result.schema.json`](../../contracts/analysis_result.schema.json) dosyasındadır. Bu sayfa onların yerini tutmaz, nasıl kullanılacaklarını anlatır.

## Temel bilgiler

| Konu | Değer |
|---|---|
| Kök yol | `/api/v1` (lokalde `http://127.0.0.1:8000/api/v1`) |
| Gövde biçimi | JSON. Sadece CV yükleme `multipart/form-data` |
| Kimlik doğrulama | `Authorization: Bearer <access_token>` |
| Hata biçimi | RFC 7807, `application/problem+json` (aşağıda) |
| İstek kimliği | Her yanıtta `X-Request-ID` başlığı var. Hata bildirirken bunu iletin |
| Zaman | ISO 8601, UTC (`2026-11-20T10:00:00Z`) |
| Sayfalama | `GET /analyses?limit=20&offset=0` → `{items, total}` (`limit` 1-100, varsayılan 20) |

Windows'ta adreslerde `localhost` yerine `127.0.0.1` yazın (`localhost` önce IPv6'ya gider).

## Kimlik doğrulama

1. `POST /auth/register`: e-posta, şifre (8-128 karakter) ve üç zorunlu onay (`kvkk_aydinlatma`, `acik_riza`, `kullanim_kosullari`). Doğrulama bağlantısı e-postayla gider. E-postayı doğrulamadan da giriş yapılabilir.
   - **Şimdilik gerçek e-posta gönderilmiyor** (e-posta servisi seçilmedi). `ENVIRONMENT=local` iken doğrulama ve sıfırlama bağlantıları API loguna yazılır.
2. `POST /auth/login` → `access_token` (15 dk), `refresh_token` (7 gün), `expires_in` (saniye).
3. Korumalı her istekte: `Authorization: Bearer <access_token>`.
4. Access token'ın süresi dolunca veya 401 gelince `POST /auth/refresh` ile yeni bir çift alınır.
   - Refresh token **tek kullanımlıktır**; her yenilemede yenisi gelir, eskisi saklanmamalıdır.
   - Kullanılmış bir refresh token tekrar gönderilirse (ör. çalınmışsa) kullanıcının bütün oturumları kapanır.
   - Aynı anda iki yenileme isteği gönderilmemelidir (web istemcisi bunu `web/src/auth/session.ts`'te tek seferde yapar).
5. `POST /auth/logout`: refresh token iptal edilir. Access token süresi dolana kadar geçerli kalır; istemci onu siler.

Şifre sıfırlama: `POST /auth/forgot-password` (e-posta kayıtlı olsun olmasın 202 döner) → e-postadaki token ile `POST /auth/reset-password`. Şifre değişince bütün oturumlar kapanır.

## Uçtan uca örnek akış

Sadece sahte veriyle deneyin: `@example.com` e-postası ve sahte/anonim bir CV. Gerçek CV kullanılmaz.

```bash
API=http://127.0.0.1:8000/api/v1

# 1) Giriş (kalıcı test kullanıcısı: backend/README.md → "Kalıcı test kullanıcısı")
TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d "{\"email\": \"$E2E_TEST_EMAIL\", \"password\": \"$E2E_TEST_PASSWORD\"}" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2) Hedef pozisyonlar (giriş gerekmez)
curl -s $API/roles

# 3) CV yükle → 202 {"analysis_id": "...", "status": "queued"}
curl -s -X POST $API/analyses -H "Authorization: Bearer $TOKEN" \
  -F "file=@sahte-cv.pdf;type=application/pdf" -F "target_role_id=1"

# 4) Durumu yokla (queued → processing → done / failed); web 3 sn'de bir sorar
curl -s $API/analyses/<analysis_id> -H "Authorization: Bearer $TOKEN"

# 5) Geri bildirim (sadece status=done iken)
curl -s -X POST $API/analyses/<analysis_id>/feedback -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"rating": 4, "comment": "İşime yaradı."}'
```

Analiz bitince `GET /analyses/{id}` yanıtı [`contracts/examples/analysis_result.example.json`](../../contracts/examples/analysis_result.example.json) biçimindedir. API buna bir alan ekler: geri bildirim verildiyse `feedback: {rating, comment}`.

İlerleme için SSE (`/analyses/{id}/events`, sözleşmede var) yapılmadı; yoklama kullanılır.

## CV yükleme kuralları

| Kural | Hata |
|---|---|
| Dosya en fazla 5 MB | 413, `code: PDF_TOO_LARGE` (çok büyük istekler gövde okunmadan reddedilir) |
| `Content-Length` başlığı zorunlu | 411 |
| Dosya PDF olmalı (`%PDF-` imzası) | 415, `code: PDF_UNREADABLE` |
| Bozuk veya şifreli PDF | 422, `code: PDF_UNREADABLE` |
| En fazla 5 sayfa | 422, `code: PDF_TOO_LARGE` |
| `target_role_id` bilinmeyen bir pozisyon | 422, "Pozisyon bulunamadı." (`code` yok) |
| Açık rıza geri alınmışsa analiz başlamaz | 403, `code: CONSENT_WITHDRAWN` |
| Kuyruk dolu | 503 + `Retry-After` |

CV dosyası diske yazılmaz ve saklanmaz. Kalıcı olarak sadece SHA-256 özeti, sayfa sayısı ve çıkarılan yetkinlikler tutulur. Analiz başarısız olursa `error.code` şunlardan biridir: `PDF_UNREADABLE`, `PDF_TOO_LARGE`, `NO_TEXT_FOUND`, `LLM_TIMEOUT`, `INTERNAL`. `error.message` kullanıcıya gösterilebilir.

## Hatalar

Tüm 4xx/5xx yanıtları aynı biçimdedir (OpenAPI'de `Problem` şeması). Tek istisna `GET /health/ready`: 503'te de hazırlık gövdesini döner.

```json
{
  "type": "about:blank",
  "title": "Doğrulama hatası",
  "status": 422,
  "detail": "İstekteki bazı alanlar geçersiz.",
  "instance": "/api/v1/auth/register",
  "request_id": "7f9c2b1e4a5d4c3b8e6f0a1b2c3d4e5f",
  "errors": [{ "field": "email", "message": "value is not a valid email address" }]
}
```

- `detail` Türkçedir ve kullanıcıya gösterilebilir. `errors[].message` pydantic'ten gelir (İngilizce); alanın yanına Türkçe genel bir metin yazmak daha iyidir.
- `code` bazı hatalarda bulunur (yukarıdaki tablo) ve istemcide farklı mesaj göstermek için kullanılır.
- Başkasının analizine erişim 403 değil **404** döner; kaydın var olup olmadığı belli edilmez.
- 500'de iç ayrıntı (stack trace, SQL) gösterilmez; `request_id` ile loglarda aranır.

## İstek sınırları

| Sınır | Değer | Anahtar |
|---|---|---|
| Genel (sadece `/health` hariç; `/health/ready` dahil) | 100 / dk | IP |
| Giriş, kayıt, e-posta doğrulama, şifremi unuttum, şifre sıfırlama (ortak) | 10 / dk | IP |
| Analiz başlatma | 5 / saat | kullanıcı |

Aşılınca `429` ve `Retry-After` (saniye) döner. İstemci bu süre dolmadan tekrar denememelidir.

## Önbellek

Katalog uçları (`/roles`, `/roles/{slug}/skills`, `/skills/{slug}/resources`) giriş istemez ve 5 dakika önbelleklenebilir (`Cache-Control`). Pozisyon istatistikleri her gece yenilenir.

## Tanımı güncelleme

Endpoint eklenince veya değişince (backend/ klasöründe):

```bash
python scripts/export_openapi.py         # docs/api/openapi.json ve web/src/api/openapi.json
cd ../web && npm run gen:api             # web tipleri (src/api/schema.d.ts)
```

Üç dosya birlikte commit'lenir. Unutulursa `tests/test_openapi.py` CI'da kırılır. Aynı test her ucun özet ve açıklaması, her JSON gövdesinin örneği ve hata şemasının olup olmadığını da denetler.
