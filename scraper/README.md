# scraper/ — Sahibi: Ataberk

İlan toplama (resmi API'ler, açık veri setleri, izin veren siteler), ETL/normalizasyon, yetkinlik taksonomisi, eğitim kaynağı havuzu.

Çıktı formatı: `contracts/job_posting.schema.json`

Hangi kaynaktan veri çekilebileceği ve uyulacak kurallar: [kaynak-uygunluk.md](kaynak-uygunluk.md). Yeni kaynak eklemeden önce oraya satır eklenir.

## Kurulum

Python 3.12. Modeller backend paketinden geldiği için ikisi birlikte kurulur (`scraper/` içinde):

```bash
python -m venv C:\venv\careerai      # Windows'ta kısa yol (uzun yol hatası olmasın)
C:\venv\careerai\Scripts\activate    # macOS/Linux: source .venv/bin/activate
pip install -e ../backend -e ".[dev]"
```

Veritabanı: repo kökünde `make up`, sonra `backend/` içinde `alembic -c app/db/alembic.ini upgrade head`. Adres `.env`'deki `DATABASE_URL`.

## İlan havuzu (T-015)

```bash
python -m collector import hn --months 6        # Hacker News "Who is hiring?", ~2.000 ilan, ~8 dk
python -m collector import himalayas --pages 5  # 10 yazılım araması × 5 sayfa, ~2 dk
python -m collector import remoteok
python -m collector import remotive             # günde en fazla birkaç kez
python -m collector import emscad --csv data/fake_job_postings.csv   # yedek veri seti, pasif yüklenir
python -m collector stats                       # kaynak başına ilan sayısı
```

| Kaynak | `job_sources.name` | Ne | Not |
|---|---|---|---|
| Hacker News | `hacker-news` | Aylık "Ask HN: Who is hiring?" yorumları | Yorumu yazanın kullanıcı adı okunmaz |
| Himalayas | `himalayas` | Yazılım aramaları (Developer, Data Science) | Anahtarsız: istekler arası 2 sn |
| Remote OK | `remote-ok` | Güncel uzaktan ilanlar | Follow link + kaynak adı zorunlu |
| Remotive | `remotive` | Yazılım kategorisi | Ücretsiz API az ilan veriyor (~10) |
| EMSCAD | `kaggle-emscad` | 2012–2014 Workable ilanları, CC0 | Tarih yok ve eski: `is_active=false` (son 6 ay istatistiğine girmez); `--active` sadece API'ler çalışmazsa |

EMSCAD dosyası repoya girmez (`data/` git dışı). [Kaggle sayfasından](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) indirip `fake_job_postings.csv`'yi `scraper/data/` altına koyun.

Her çalışma `scrape_runs`'a yazılır (okunan / eklenen / tekrar / hata). Aynı ilan iki kez eklenmez: aynı kaynakta aynı `external_id` veya herhangi bir kaynakta aynı metin (`content_hash`).

**Kişisel veri:** İlan metnindeki e-posta, telefon ve kişisel profil linkleri (`linkedin.com/in/…`) yazılmadan önce `[e-posta]`, `[telefon]`, `[profil]` ile maskelenir (`collector/clean.py`). Şirket adı ve şirket sitesi kalır.

Pozisyon eşleme (`role_id`) ve yetkinlik etiketleme T-033'te (ETL) yapılır; T-015 sadece temiz ham ilanları yükler.

## Yetkinlik taksonomisi (T-017)

```bash
python -m collector seed-taxonomy                       # taxonomy/*.csv → skills, roles
python -m collector export-taxonomy --out taxonomy.json # ai/eval biçiminde JSON
python -m collector map-esco --csv skills_en.csv        # ESCO URI eşlemesi (ESCO indirme dosyası)
```

374 yetkinlik, 12 pozisyon; kurallar ve kapsam analizi: [taxonomy/README.md](taxonomy/README.md).

## Test ve kod kalitesi

```bash
pytest                      # DB testleri sadece TEST_DATABASE_URL ile (backend/app/db/README.md)
ruff check . && ruff format --check .
mypy collector tests
```

Testler ağa çıkmaz; kaynaklar uydurma JSON ile denenir.
