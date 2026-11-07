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
