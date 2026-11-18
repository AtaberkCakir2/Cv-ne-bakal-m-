# CI (GitHub Actions) — T-008

Tanım: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Her PR'da ve `main`'e her push'ta çalışır. Sonuçlar PR sayfasının altında ve GitHub'da **Actions** sekmesinde görünür.

## İşler

| İş | Ne zaman | Ne yapar |
|---|---|---|
| Modülleri bul | Her zaman | Hangi modüllerin kurulu olduğuna ve PR'da hangi dosyaların değiştiğine bakar |
| Backend | `backend/` değişince | `ruff check`, `ruff format --check`, `mypy app tests`, `pytest`. Postgres + pgvector servisiyle `tests/db` de çalışır: migration upgrade → downgrade → upgrade ve `alembic check` |
| Scraper | `scraper/`, `backend/` veya `ai/` değişince (scraper ikisini de kurar) | `ruff`, `mypy collector tests`, `pytest`; Postgres servisiyle içe aktarma testleri (şema backend migration'larıyla kurulur) |
| AI | `ai/` değişince | `ruff`, `mypy parsing tests eval/scripts`, `pytest` (ai/README.md'deki komutlar) |
| Web | `web/` değişince | `npm ci`, `npm run lint` (eslint), `npx tsc -b` |
| Mobil | `mobile/` değişince | `npm ci`, `npm run lint` (varsa), `npx tsc --noEmit` |
| Docker | `backend/`, `scraper/`, `ai/`, `docker-compose*.yml` veya `.env.example` değişince | `docker compose config`, API imajını build eder ve `/api/v1/health` ile açıldığını dener; `ai/Dockerfile` varsa worker imajını da build eder |

### Hangi iş ne zaman

"… değişince" sadece PR için geçerli: `main`'e her push'ta (yani her birleştirmede) bütün işler çalışır. `contracts/` veya `ci.yml` değişen PR'da da hepsi çalışır. Modülün dosyası yoksa (ör. `mobile/package.json`) işi hiç çalışmaz.

Neden: repo gizli, Actions dakikası ayda sınırlı (GitHub Pro: 3.000 dk). Kasım 2026'da her PR güncellemesinde ~18 iş çalıştığı için kota 17.11'de doldu ve CI durdu (iş başlamıyor, "spending limit" hatası). Atlanan zorunlu iş GitHub'da **başarılı** sayılır; sadece doküman değiştiren PR'da yalnızca "Modülleri bul" çalışır ve PR birleştirilebilir.

Dikkat: kota bittiğinde de bütün işler başlamadan düşer ve zorunlu işler "skipped" görünüp geçmiş sayılır. Actions sekmesinde işler saniyeler içinde kırmızıysa CI çalışmıyordur; birleştirmeden önce değişen modülü yerelde deneyin (`infra/guvenlik.md` ve modül README'leri). Kullanım: GitHub → Settings → Billing and licensing → Usage.

Güvenlik taramaları (`security.yml`) da aynı mantıkla çalışır: sır taraması her PR'da; pip-audit, npm audit ve Trivy PR'da/main'de sadece ilgili `pyproject.toml`, `package*.json`, Dockerfile veya `infra/backup/` değişince; haftalık (pazartesi) çalışmada hepsi.

Yeni modül eklemek için workflow'a dokunmak gerekmez: dosyası repoya girdiği anda ilgili iş devreye girer. Komutlar değişirse (ör. mypy yolları) hem modülün README'si hem `ci.yml` aynı PR'da güncellenir.

## CI kırmızıysa

1. PR sayfasında kırmızı işin yanındaki **Details**'e tıklayın, kırmızı adımı açın.
2. Aynı komutu kendi bilgisayarınızda modül klasöründe çalıştırın (komutlar modül README'lerinde).
3. Sık görülenler:
   - `ruff format --check` → `ruff format .` çalıştırıp commit'leyin.
   - "DB bağımlılıkları kurulu mu" → `backend/pyproject.toml`'a `sqlalchemy`, `alembic`, `pgvector` eklenmemiş.
   - `alembic check` → model değişmiş ama migration yazılmamış (`backend/app/db/README.md`).
   - `npm ci` → `package-lock.json` commit'lenmemiş.
   - **Yerelde geçiyor, CI'da düşüyor** → büyük ihtimalle araç sürümü farkı. CI her seferinde en güncel `ruff`/`mypy`'yi kurar (`pyproject.toml`'da `ruff>=0.8` yazıyor). Örnek: ruff 0.8 Markdown dosyalarını biçimlendirmez, 0.17 README'lerdeki Python kod bloklarını da kontrol eder. Çözüm: modül sahibi `pyproject.toml`'da sürümü sabitler (ör. `"ruff==0.17.2"`, `"mypy==<sürüm>"`) ve herkes `pip install -e ".[dev]"` ile günceller. Backend'de sabitlendi (#17: `ruff==0.17.2`, `mypy==2.4.0`); `ai/` için henüz açık uçlu.

## `main` koruması (T-006)

Repo → **Settings** → **Branches** → `main` kuralı (GitHub Pro, Student Pack ile):

- **PR zorunlu, 1 onay:** `main`'e doğrudan push yok. Yeni commit gelince eski onay düşer.
- **Zorunlu kontroller:** `Backend (ruff, mypy, pytest + migration)`, `Scraper (ruff, mypy, pytest)`, `Web (eslint, tsc)`, `Docker (compose + imaj build)`. `AI` işi `main`'de yeşile dönünce, `Mobil` ilk kez çalışınca listeye eklenir.
- **Dal güncel olmalı:** PR, `main`'in son hâlini içermeden birleşmez (PR sayfasında **Update branch**).
- **Yöneticiler dahil atlanamaz;** force push ve `main`'i silme kapalı.

`.github/CODEOWNERS` her PR'a ilgili klasörün sahibini otomatik inceleyici ekler. "Sahibin onayı zorunlu" açık değil: kişi kendi klasöründeki PR'ı kendisi onaylayamayacağı için her PR'da herhangi 1 ekip üyesinin onayı yeter.

## İmajlar ve deploy (T-036, karar #30)

`.github/workflows/deploy.yml`: `main`'de CI yeşil olunca `api` ve `worker-data` imajlarını `ghcr.io/ataberkcakir2/careerai-*:<commit>` olarak gönderir. Ayar veya sır gerekmez (`GITHUB_TOKEN` yeter). Her imajın son 20 sürümü tutulur (özel repoda GHCR depolaması kotalı).

Deploy CI'dan **yapılmaz**: production Ataberk'in PC'sinde çalışır ve PC'ye dışarıdan erişim açılmaz. Sürüm PC'de `bash infra/pc/deploy.sh vX.Y.Z` ile alınır; adımlar `infra/pc/deploy.md`'de.

Actions → Deploy → **Run workflow**: seçilen dalın son commit'inin imajlarını elle derleyip gönderir.
