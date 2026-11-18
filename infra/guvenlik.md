# Güvenlik taramaları ve ayarları (T-064)

Bulgular ve kararlar: [`docs/guvenlik-raporu.md`](../docs/guvenlik-raporu.md). Bu dosya taramaların nasıl çalıştığını ve elle yapılan ayarları anlatır.

## 1. Otomatik taramalar

`.github/workflows/security.yml` her PR'da, `main`'e her push'ta ve her pazartesi 08:00'de çalışır. Branch protection'da zorunlu **değildir**: yeni yayımlanan bir açık ilgisiz bir PR'ı kilitlemesin. Kırmızıysa ilgili modülün sahibi düzeltir (hangi iş kırmızıysa o klasörün sahibi, CLAUDE.md tablosu).

| İş | Araç | Neyi kırar |
|---|---|---|
| Sır taraması | gitleaks, tüm git geçmişi | Herhangi bir eşleşme. İstisnalar `.github/gitleaks.toml` (yol değil, değer yazılır) |
| Python bağımlılıkları | pip-audit, `backend` / `scraper` / `ai` `pyproject.toml` | Bilinen herhangi bir açık |
| npm bağımlılıkları | `npm audit --omit=dev --audit-level=high`, `web` / `mobile` | Üretim bağımlılığında yüksek veya kritik açık (lock dosyası yoksa atlanır) |
| İmaj taraması | Trivy: `api`, `worker-data`, `backup` | Yamalı sürümü olan yüksek/kritik açık. Yedek imajı istisnaları `infra/backup/.trivyignore` (süreli) |

`.github/dependabot.yml` her pazartesi pip, npm, Docker taban imajı ve GitHub Actions güncellemeleri için PR açar; küçük sürümler tek PR'da toplanır. PR'a inceleyici CODEOWNERS'tan gelir.

## 2. Yerelde aynı taramalar

Git Bash'te, repo kökünde. Docker Desktop açık olmalı.

```bash
export MSYS_NO_PATHCONV=1

# Sır taraması (tüm geçmiş)
docker run --rm -v "$(pwd -W):/repo" zricethezav/gitleaks:v8.24.3 git /repo --config /repo/.github/gitleaks.toml --redact --no-banner

# Python (venv içinde: pip install pip-audit)
python -m pip_audit backend && python -m pip_audit scraper && python -m pip_audit ai

# npm
(cd web && npm audit --omit=dev --audit-level=high)

# İmaj (önce imajı derleyin veya production imajını kullanın)
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache -v "$(pwd -W):/repo:ro" \
  aquasec/trivy:0.67.2 image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --ignorefile /repo/infra/backup/.trivyignore careerai/backup:local
```

`.trivyignore` süresi (`exp:`) dolunca: restic'in yeni sürümü var mı bakın (`infra/backup/Dockerfile`), yükseltip tekrar tarayın, kalanları gözden geçirip tarihi uzatın ve gerekçeyi rapora yazın.

## 3. Güvenlik başlıkları (Cloudflare, elle, bir kez)

API başlık göndermiyor; Cloudflare kenarda ekliyor (rapor G-5). Ücretsiz planda var, kod değişikliği gerekmez.

**HSTS:** `infra/pc/deploy.md` §3, 4. adım (SSL/TLS → Edge Certificates → HSTS). Yapıldıysa geçin.

**Başlık kuralı:**

1. Cloudflare paneli → `cvnebakalim.com` → sol menü **Rules** → **Overview** → **Create rule** → **Response Header Transform Rule**.
2. **Rule name:** `guvenlik-basliklari`.
3. **If incoming requests match…** → **Custom filter expression** → **Edit expression**'a tıklayıp yapıştırın:
   `(http.host eq "api.cvnebakalim.com")`
4. **Then…** bölümünde her satır için **Set static** seçip **Header name** / **Value** girin (**Set new header** ile satır ekleyin):

   | Header name | Value |
   |---|---|
   | `X-Content-Type-Options` | `nosniff` |
   | `X-Frame-Options` | `DENY` |
   | `Referrer-Policy` | `no-referrer` |
   | `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |

5. **Deploy**.
6. Aynı yoldan ikinci kural: **Rule name** `csp-api`, ifade:
   `(http.host eq "api.cvnebakalim.com" and not starts_with(http.request.uri.path, "/admin") and not starts_with(http.request.uri.path, "/docs"))`
   **Set static** → `Content-Security-Policy` = `default-src 'none'; frame-ancestors 'none'` → **Deploy**.
   (Admin paneli ve Swagger sayfa çizdiği için bu katı kuraldan muaf; JSON API'nin içerik yüklemesine gerek yok.)

**Doğrulama** (api açıkken):

```bash
curl -sI https://api.cvnebakalim.com/api/v1/health | grep -i -E "strict-transport|content-security|x-content-type|x-frame|referrer"
```

Beş başlık da görünmeli. Sonra <https://securityheaders.com> → `https://api.cvnebakalim.com/api/v1/health` → en az **A** (go-live #12).

## 4. GitHub ayarları (elle, bir kez)

Repo → **Settings** → sol menü **Security** altında **Advanced Security** (eski adı *Code security and analysis*):

1. **Dependabot alerts** → **Enable**.
2. **Dependabot security updates** → **Enable** (açık yayımlanınca haftayı beklemeden PR açar).
GitHub'ın kendi sır taraması (Secret Protection, push protection) private repolarda ücretli; repo private olduğu için açılmadı. Onun yerine gitleaks her PR'da tüm geçmişi tarıyor (§1). Repo public yapılırsa bu iki ayar ücretsiz olur, açılmalı.

Kontrol: repo → **Security** sekmesi → **Dependabot** sayfası açılıyor olmalı.
