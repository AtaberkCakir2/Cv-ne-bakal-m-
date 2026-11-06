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

## `main` koruması (T-006)

Repo → **Settings** → **Branches** → `main` kuralı (GitHub Pro, Student Pack ile):

- **PR zorunlu, 1 onay:** `main`'e doğrudan push yok. Yeni commit gelince eski onay düşer.
- **Zorunlu kontroller:** `Backend (ruff, mypy, pytest + migration)`, `Scraper (ruff, mypy, pytest)`, `Web (eslint, tsc)`, `Docker (compose + imaj build)`. `AI` işi `main`'de yeşile dönünce, `Mobil` ilk kez çalışınca listeye eklenir.
- **Dal güncel olmalı:** PR, `main`'in son hâlini içermeden birleşmez (PR sayfasında **Update branch**).
- **Yöneticiler dahil atlanamaz;** force push ve `main`'i silme kapalı.

`.github/CODEOWNERS` her PR'a ilgili klasörün sahibini otomatik inceleyici ekler. "Sahibin onayı zorunlu" açık değil: kişi kendi klasöründeki PR'ı kendisi onaylayamayacağı için her PR'da herhangi 1 ekip üyesinin onayı yeter.

## Deploy (T-036)

`.github/workflows/deploy.yml`: `main`'de CI yeşil olunca `api` ve `worker-data` imajlarını `ghcr.io/ataberkcakir2/careerai-*:<sha>` olarak gönderir, sunucuda `infra/staging/deploy.sh <sha>` çalıştırır. Betik migration ve smoke test yapar; başarısız olursa önceki imajlara döner (migration'lar geri alınmaz, önceki sürümle uyumlu yazılmalı).

Sunucu hazır olunca:

1. **Settings → Environments → New environment:** adı `staging`. *Deployment branches and tags* → *Selected branches* → `main`. Sırlar repo düzeyinde değil burada durur: başka dallardaki workflow'lar okuyamaz.
2. Kendi bilgisayarınızda sadece CI için bir anahtar üretin: `ssh-keygen -t ed25519 -N "" -C careerai-ci -f ci_key`
3. `ci_key.pub` içeriğini sunucuda `/home/deploy/.ssh/authorized_keys` dosyasına **şu önekle** ekleyin (tek satır):

   ```
   restrict,command="bash /home/deploy/careerai/infra/staging/ci-deploy.sh" ssh-ed25519 AAAA... careerai-ci
   ```

   Bu anahtar sadece `main`'deki bir commit'i deploy edebilir; kabuk, `sudo` ve port yönlendirme açmaz (`infra/staging/ci-deploy.sh`).
4. Ayarları girin, sonra `ci_key` dosyasını silin:

| Yer | Ad | Değer |
|---|---|---|
| Secrets and variables → Actions → Variables | `STAGING_DEPLOY` | `true` (tanımsızken otomatik deploy kapalı) |
| Environments → staging → Environment secrets | `STAGING_HOST` | Sunucu IP'si veya adı |
| Environments → staging → Environment secrets | `STAGING_SSH_KEY` | `ci_key` içeriği |
| Environments → staging → Environment secrets | `STAGING_KNOWN_HOSTS` | `ssh-keyscan <sunucu-ip>` çıktısı |

Deploy sadece bu repodaki `main`'e yapılan push'un CI'ı yeşil olunca çalışır; fork'tan gelen PR'lar tetiklemez.

İmaj kısmı sunucusuz denenebilir: Actions → Deploy → Run workflow sadece imajları derleyip gönderir. Bu özel repoda GHCR depolaması kotalıdır; her imajın son 5 sürümü tutulur. Sunucuda her servisin son 3 imajı kalır.
