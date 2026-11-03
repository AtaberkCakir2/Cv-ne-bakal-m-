# CareerAI

Yapay zeka destekli kariyer ve eğitim yönlendirme sistemi. Öğrencinin CV'sini hedef pozisyondaki güncel iş ilanlarıyla karşılaştırır, eksik yetkinlikleri bulur ve bu eksikleri kapatacak eğitim kaynaklarını önerir.

**Ekip:** Ataberk (veri, veri tabanı, DevOps) · Burak (yapay zeka / NLP, mobil) · Anıl (backend API, web/masaüstü)

## Kurulum (yaklaşık 10 dakika + model indirme)

**1. Gerekenler** (Windows'ta PowerShell'e yapıştırın; kuruluysa geçin):

```powershell
winget install Git.Git Docker.DockerDesktop Python.Python.3.12 OpenJS.NodeJS.LTS ezwinports.make
```

Docker Desktop'ı bir kez açın, lisansı kabul edin ve sol altta "Engine running" yazana kadar bekleyin (ilk açılışta WSL kurulumu ve yeniden başlatma isteyebilir). macOS'ta aynı araçları Homebrew ile kurun; `make` zaten vardır.

**2. Repo ve ortam değişkenleri:**

```bash
git clone -c core.longpaths=true https://github.com/AtaberkCakir2/Cv-ne-bakal-m-.git
cd Cv-ne-bakal-m-
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
```

`.env` içindeki `POSTGRES_PASSWORD` değerini (iki yerde: kendisi ve `DATABASE_URL`) değiştirin. Lokalde `JWT_SECRET` boş kalır ve `ENVIRONMENT=local` satırı silinmez: backend o zaman kendi geliştirme anahtarını kullanır. Staging ve production'da `JWT_SECRET` zorunludur (en az 32 karakter). Lokal ortamda herkes kendi şifresini seçer, paylaşmaya gerek yoktur. **`.env` repoya yüklenmez** (`.gitignore` engeller); sunucu şifreleri WhatsApp grubunda değil, özel mesajla paylaşılır.

**3. Servisleri başlatın:**

```bash
make up       # Postgres, Redis, Ollama başlar; hepsi sağlıklı olana kadar bekler
make model    # LLM modelini indirir (ilk seferde ~5 GB, bir kez yapılır)
make ps       # Hepsinin durumu "healthy" olmalı
```

`make help` tüm komutları listeler. `make` kurmadıysanız her komutun karşılığı `Makefile` içinde yazılı (ör. `make up` = `docker compose up -d --wait`).

`backend/Dockerfile` ve `ai/Dockerfile` eklendiğinde `make up` API'yi ve AI worker'ını da otomatik başlatır.

| Servis | Adres | Not |
|---|---|---|
| PostgreSQL 16 + pgvector | `127.0.0.1:5432` | `make psql` ile konsol |
| Redis 7 | `127.0.0.1:6379` | `make redis-cli` ile konsol |
| Ollama | `127.0.0.1:11434` | Model: `.env` içindeki `OLLAMA_MODEL` |
| API | `127.0.0.1:8000` | `/docs` ile API dokümanı |

Portlar sadece kendi bilgisayarınıza açıktır. Veriler Docker volume'larında durur; `make down` silmez, `make reset` her şeyi siler.

**Sık sorunlar:**
- `.env dosyasında POSTGRES_USER yok` hatası: 2. adımı yapmadınız.
- `port is already allocated`: Bilgisayarınızda zaten çalışan bir PostgreSQL/Redis var. Onu durdurun.
- `make model` çok yavaş: Model ~5 GB, bir kez indirilir; `make reset` yapmadıkça tekrar inmez.
- Windows'ta veritabanına her bağlantı ~2 dakika sürüyor: `.env`'deki adreslerde `localhost` yerine `127.0.0.1` yazın (eski `.env.example`'dan kopyaladıysanız). `localhost` önce IPv6'yı dener.

## Klasörler

| Klasör | Sahibi | İçerik |
|---|---|---|
| `contracts/` | Ortak | Modüller arası veri formatları ve API listesi |
| `scraper/` | Ataberk | İlan toplama ve veri hazırlama |
| `infra/` | Ataberk | Sunucu, deploy, izleme, yedekleme |
| `ai/` | Burak | CV analizi ve öneri motoru |
| `mobile/` | Burak | Mobil uygulama |
| `backend/` | Anıl (db modelleri: Ataberk) | FastAPI |
| `web/` | Anıl | Web ve Electron arayüzü |
| `docs/` | Ortak | Kararlar ve dokümanlar |

## Çalışma şekli

1. Her gün işe başlamadan: `git checkout main && git pull`
2. Yeni iş için branch aç: `git checkout -b isim/kisa-aciklama`
3. Sadece kendi klasörünüzde çalışın. Başka klasörde değişiklik gerekiyorsa sahibine haber verin.
4. İş bitince push edip PR açın; bir kişi inceleyip onaylasın.
5. `contracts/` değişiklikleri için üç kişinin de onayı gerekir.

Kurallar ve Claude talimatları: [CLAUDE.md](CLAUDE.md)

## Görevler ve plan

- Kişi bazlı görev listeleri (durumların tek doğru kaynağı): [docs/gorevler/](docs/gorevler/)
- Başlangıç planı (Excel + PDF, referans): [docs/plan/](docs/plan/)

Claude Code'u repo klasöründe açıp **"başlıyorum"** demeniz yeterli: repoyu günceller, dokümanları okur, ekipteki değişiklikleri özetler, yarım kalan işinizi bulur ve günün görevini önerir. Gün sonunda **"bitiriyorum"** deyin: nerede kaldığınızı görev dosyanıza not eder ve yarım işi kendi branch'inize gönderir, ertesi gün oradan devam edilir.
