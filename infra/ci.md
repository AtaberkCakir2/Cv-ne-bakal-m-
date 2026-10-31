# CI (GitHub Actions) — T-008

Tanım: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Her PR'da ve `main`'e her push'ta çalışır. Sonuçlar PR sayfasının altında ve GitHub'da **Actions** sekmesinde görünür.

## İşler

| İş | Ne zaman | Ne yapar |
|---|---|---|
| Modülleri bul | Her zaman | Hangi modüllerin kurulu olduğuna bakar (`ai/pyproject.toml`, `web/package.json` vb.) |
| Backend | Her zaman | `ruff check`, `ruff format --check`, `mypy app tests`, `pytest`. Postgres + pgvector servisiyle `tests/db` de çalışır: migration upgrade → downgrade → upgrade ve `alembic check` |
| Scraper | `scraper/pyproject.toml` varsa | `ruff`, `mypy collector tests`, `pytest`; Postgres servisiyle içe aktarma testleri (şema backend migration'larıyla kurulur) |
| AI | `ai/pyproject.toml` varsa | `ruff`, `mypy parsing tests eval/scripts`, `pytest` (ai/README.md'deki komutlar) |
| Web | `web/package.json` varsa | `npm ci`, `npm run lint` (eslint), `npx tsc -b` |
| Mobil | `mobile/package.json` varsa | `npm ci`, `npm run lint` (varsa), `npx tsc --noEmit` |
| Docker | Her zaman | `docker compose config`, API imajını build eder ve `/api/v1/health` ile açıldığını dener; `ai/Dockerfile` varsa worker imajını da build eder |

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

## "Kırmızı CI ile merge yok" kuralı (T-006, repo sahibi yapar)

GitHub bunu ancak branch protection ile zorunlu kılar. Özel (private) repolarda branch protection için GitHub Pro gerekir; GitHub Student Developer Pack ile ücretsizdir. Pack onaylanınca:

1. Repo → **Settings** → **Branches** → **Add branch ruleset** (veya *Add classic branch protection rule*), hedef: `main`.
2. **Require a pull request before merging** → *Required approvals: 1*.
3. **Require status checks to pass** → şunları ekleyin: `Backend (ruff, mypy, pytest + migration)`, `Docker (compose + imaj build)`; AI/Web/Mobil işleri ilk kez çalıştıktan sonra onları da ekleyin.
4. **Require branches to be up to date before merging** işaretleyin.
5. **Do not allow bypassing** (yöneticiler dahil) işaretleyin.

O zamana kadar kural ekip sözleşmesidir (karar #6): kırmızı CI'lı PR birleştirilmez.

## Deploy (T-036)

`.github/workflows/deploy.yml`: `main`'de CI yeşil olunca `api` ve `worker-data` imajlarını `ghcr.io/ataberkcakir2/careerai-*:<sha>` olarak gönderir, sunucuda `infra/staging/deploy.sh <sha>` çalıştırır. Betik migration ve smoke test yapar; başarısız olursa önceki imajlara döner (migration'lar geri alınmaz, önceki sürümle uyumlu yazılmalı).

Sunucu hazır olunca repo → Settings'te:

| Yer | Ad | Değer |
|---|---|---|
| Secrets and variables → Actions → Variables | `STAGING_DEPLOY` | `true` (tanımsızken otomatik deploy kapalı) |
| Actions secrets | `STAGING_HOST` | Sunucu IP'si veya adı |
| Actions secrets | `STAGING_SSH_KEY` | Sadece CI için üretilen özel anahtar (`ssh-keygen -t ed25519 -N "" -f ci_key`); `ci_key.pub` sunucuda deploy kullanıcısının `authorized_keys` dosyasına eklenir, `ci_key` sonra silinir |
| Actions secrets | `STAGING_KNOWN_HOSTS` | `ssh-keyscan <sunucu-ip>` çıktısı |

İmaj kısmı sunucusuz denenebilir: Actions → Deploy → Run workflow sadece imajları derleyip gönderir. Bu özel repoda GHCR depolaması kotalıdır; her imajın son 5 sürümü tutulur.
