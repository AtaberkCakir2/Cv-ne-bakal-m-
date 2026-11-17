# Güvenlik incelemesi (T-064)

**Tarih:** 15.11.2026 · **Yapan:** Ataberk · **Kapsam:** `main` (ca22474) + açık PR'lar #86–#89, production imajları (`careerai/api:production`, `careerai/worker-data:production`, `careerai/backup`)

Taramalar artık her PR'da, `main`'e her push'ta ve her pazartesi otomatik çalışıyor (`.github/workflows/security.yml`); Dependabot her hafta güncelleme PR'ı açıyor (`.github/dependabot.yml`); Dependabot uyarıları ve güvenlik güncellemeleri repoda açık. Yerelde aynı komutlar: [`infra/guvenlik.md`](../infra/guvenlik.md).

## Özet

| # | Bulgu | Seviye | Durum | Sahibi |
|---|---|---|---|---|
| G-1 | Yedek imajında 5 kritik + 98 yüksek açık (restic 0.18.0, Alpine 3.21, OpenSSL/musl) | Kritik | **Düzeltildi** (restic 0.19.1 + `apk upgrade`; 0 kritik, 0 işletim sistemi açığı) | Ataberk |
| G-2 | Yedek imajında restic ikilisinin Go kütüphanelerinde 23 yüksek açık kaldı | Yüksek | **Kabul edildi, 15.01.2027'ye kadar** (`infra/backup/.trivyignore`, gerekçe dosyada) | Ataberk |
| G-3 | Web: `react-router-dom` (→ `@remix-run/router`) 3 yüksek açık: açık yönlendirme / XSS | Yüksek | Açık: `npm audit fix` ile yamalı sürüm var | Anıl |
| G-4 | API ve veri işçisi imajında `zlib1g` 2 yüksek açık (Debian taban imajı) | Yüksek | Açık: imajlar yeniden derlenince kapanır (`--pull`); sonraki deploy | Ataberk |
| G-5 | API güvenlik başlıkları göndermiyor (HSTS, CSP, X-Content-Type-Options, X-Frame-Options) | Orta | **Düzeltildi** (Cloudflare kuralları; securityheaders.com **A+**) | Ataberk |
| G-6 | Swagger arayüzü (`/docs`) ve `openapi.json` production'da herkese açık | Düşük | Açık: production'da kapatılması önerildi | Anıl |
| G-7 | Web dev bağımlılıkları: `typescript-eslint` / `minimatch` 7 orta açık | Düşük | Açık: sadece geliştirme aracı, imaja girmiyor; Dependabot yükseltir | Anıl |
| G-8 | `mobile/package-lock.json` yok: bağımlılıklar denetlenemiyor, kurulum tekrarlanabilir değil | Düşük | Açık | Burak |

Temiz çıkanlar: **gitleaks** (213 commit, tüm yerel dallar): gerçek sır yok; 18 eşleşmenin hepsi OpenAPI örneği veya test parolası, değerleriyle istisna yazıldı (`.github/gitleaks.toml`). **pip-audit** (backend, scraper, ai `pyproject.toml`): bilinen açık yok. Production API imajındaki Python paketleri de güncel (pypdf 7.0.0, dnspython 2.9.2).

## Bulgular

### G-1 / G-2 · Yedek imajı (düzeltildi / kabul edildi)

`restic/restic:0.18.0` tabanı Mart 2025'ten kalmaydı: OpenSSL (`libcrypto3`, `libssl3`), `musl` ve `libpq`'da yamalı sürümü olan 5 kritik, 98 yüksek açık. `infra/backup/Dockerfile` → `restic/restic:0.19.1` (Temmuz 2026, son sürüm) ve `apk upgrade`. Yeni imaj production'da çalışıyor: B2 deposu açıldı, `restic check` hatasız.

Kalan 23 açık restic'in kendi derlenmiş ikilisinde (Go stdlib, `x/net`, `x/crypto`, `grpc`, `klauspost/compress`); daha yeni restic sürümü olmadığı için bizim düzeltebileceğimiz bir şey değil. Risk düşük: konteynerin dışarı açık portu yok, sadece Postgres'e ve B2'ye TLS ile bağlanır, yedek restic tarafında şifreli ve kimlik doğrulamalı (araya giren okuyamaz/değiştiremez); açıkların çoğu DoS ve kullanılmayan yollarda (ssh, gRPC xDS, html/template). İstisnaların süresi **15.01.2027**'de doluyor: go-live'dan (18.01) önce tarama tekrar kırmızı olur ve yeni restic sürümüne bakılır.

### G-3 · Web: react-router

`npm audit --omit=dev`: `react-router-dom` üzerinden `@remix-run/router` ve `react-router`'da 3 yüksek açık ("XSS via Open Redirects", `//` ile başlayan yolun dış adrese yönlendirmesi). Kullanıcıya gösterilen her sayfaya giriyor. **Anıl için:** `web/` içinde `npm audit fix` (aynı ana sürüm içinde yamalı sürüm var), `npm run lint && npx tsc -b`, uygulamayı bir tur deneyip PR. Güvenlik iş akışının `npm (web)` adımı bu yapılana kadar kırmızı kalır.

### G-4 · Debian zlib

`zlib1g 1:1.3.dfsg+really1.3.1-1+b1` → `…-1+deb13u1`. Bizim kodumuz değil; `python:3.12-slim` güncellenince kapanıyor. Deploy iş akışı imajı her seferinde sıfırdan derlediği için sonraki `main` birleşmesiyle production imajı da yamalı olur; güvenlik iş akışı `--pull` ile derleyip doğruluyor.

### G-5 · Güvenlik başlıkları

`api.cvnebakalim.com` yanıtlarında HSTS, CSP, `X-Content-Type-Options` yok (uygulama göndermiyor; eskiden Caddy veriyordu, karar #30 ile Caddy kalktı). HSTS Cloudflare'in **Edge Certificates** ayarıyla (deploy.md §3), diğerleri bir **Response Header Transform Rule** ile eklenir: kod değişikliği gerekmez, admin paneli ve ileride web için de geçerli olur. Adımlar ve doğrulama: [`infra/guvenlik.md`](../infra/guvenlik.md) §3. **15.11.2026'da kuruldu:** `api.cvnebakalim.com` yanıtlarında HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` ve (`/admin`, `/docs` hariç) CSP geliyor; securityheaders.com notu **A+**. Canlıda yabancı kaynaktan CORS ön isteği `400`, izin başlığı yok. API'de ayrıca middleware gerekmez.

### G-6 · `/docs` production'da açık

`docs_url="/docs"` ve `openapi_url` her ortamda açık (`backend/app/main.py`). Saldırgana tüm uç noktaları ve şemaları hazır veriyor (OWASP A05). Sır sızdırmıyor ama gereksiz. **Anıl için:** `environment == "production"` iken `docs_url=None, openapi_url=None`; sözleşme zaten `contracts/` ve `docs/api/openapi.json`'da. Ayrıca Swagger arayüzü dosyalarını CDN'den yüklediği için kapalı olması katı CSP'yi de kolaylaştırır.

### CORS (bulgu yok)

`CORSMiddleware` sadece `CORS_ORIGINS` listesindeki adreslere izin veriyor, joker yok. Denendi: izinli adres → `200` + `Access-Control-Allow-Origin`; yabancı adres ve `null` → `400`, başlık yok. Production'da liste şu an boş (`[]`), web yayında olmadığı için doğru. Web arayüzünün yeri kesinleşince (deploy.md "Henüz eksik") `.env.prod`'a sadece o adres yazılır, ör. `CORS_ORIGINS=["https://app.cvnebakalim.com"]`; Electron `app://careerai` kaynağından istek atacaksa o da eklenir.

## OWASP Top 10 (2021) kontrolü

Kodun okunarak ve yukarıdaki taramalarla yapılan kısa kontrol; sızma testi değildir.

| Başlık | Bakılan | Sonuç |
|---|---|---|
| A01 Erişim kontrolü | Admin paneli rolü her istekte veritabanından yeniden okuyor; `/admin` ayrıca Cloudflare Access arkasına alınacak (karar #33) | Uygun; kullanıcı verisinin sahiplik kontrolleri Anıl'ın testlerinde |
| A02 Kriptografi | Parolalar argon2, JWT HS256 + 15 dk ömür, TLS Cloudflare'de, yedek restic ile şifreli | Uygun; HSTS → G-5 |
| A03 Enjeksiyon | Tüm sorgular SQLAlchemy ORM; kullanıcı girdisiyle ham SQL yok | Uygun |
| A04 Güvensiz tasarım | Hız sınırı (genel + giriş), yükleme boyutu sınırı, CV hiçbir yerde saklanmıyor | Uygun |
| A05 Yanlış yapılandırma | Başlıklar, `/docs`, CORS | G-5, G-6 |
| A06 Güncel olmayan bileşenler | pip-audit, npm audit, Trivy, Dependabot | G-1…G-4, G-7, G-8 |
| A07 Kimlik doğrulama | Giriş hız sınırı (429), kısa erişim jetonu, admin oturumu 8 saat / `SameSite=Strict` | Uygun |
| A08 Yazılım bütünlüğü | İmajlar CI'da derlenip commit SHA'sıyla GHCR'a; Actions sadece resmi/doğrulanmış yayıncılardan, Dependabot güncelliyor | Uygun |
| A09 Log ve izleme | İstek kimliği her yanıtta, JSON log; maskeleme ve saklama T-067'de | T-067 |
| A10 SSRF | API kullanıcıdan gelen adrese istek atmıyor; toplayıcı sabit kaynak listesine gidiyor | Uygun |

## go-live listesine etkisi

- **#7** (repoda sır yok): gitleaks temiz. "Production sırları güçlü ve yeni üretilmiş" kısmı T-075'te kontrol edilir.
- **#8** (kritik/yüksek açık yok): G-3 ve G-4 kapanınca sağlanır; G-2 gerekçeli istisna.
- **#12** (CORS + başlıklar): sağlandı (securityheaders.com A+, 15.11.2026); web arayüzü yayına girince onun adresi için de tekrar bakılır.
