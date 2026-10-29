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

## Normalizasyon / ETL (T-033)

```bash
python -m collector normalize                                   # role_id, job_posting_skills, benzer ilanlar
python -m collector export-postings --out postings.jsonl        # contracts/job_posting.schema.json biçimi
```

İçe aktarmadan veya `seed-taxonomy`'den sonra çalıştırılır; tekrar çalıştırmak aynı sonucu verir. Kod `etl/` altında:

| Adım | Dosya | Kural |
|---|---|---|
| Pozisyon | `etl/roles.py` | Başlık parçalanır (`Şirket \| Pozisyon \| Yer`), kıdem/teknoloji adları atılır, `roles.csv` eş anlamlılarıyla eşlenir. "Software Engineer" gibi genel başlıklar `role_id = NULL` kalır ve pozisyon istatistiğine girmez. |
| Yetkinlik | `etl/skills.py` | Taksonomi + eş anlamlılar, kelime sınırıyla; `case_sensitive` adlar sadece o yazımla. "Nice to have" / "tercih sebebi" bölüm ve cümlelerindekiler `preferred`. |
| Benzer ilan | `etl/dedup.py` | Aynı şirket + pozisyonda metni %90 benzeyenlerden en yenisi kalır, diğerleri `is_active=false` (silinmez). |
| Kişi adı | `etl/pipeline.py` | `mask_names` bağlantı noktası; Burak'ın T-030 maskeleyicisi bağlanacak. |

Eşleyiciler (`etl/text.py`, `etl/skills.py`, `etl/roles.py`, `etl/dedup.py`) veritabanı kullanmaz: taksonomiyi `collector/taxonomy_rows.py`'den okur, backend paketi ve SQLAlchemy olmadan çalışır (AI worker T-031'de kullanacak; test: `test_matchers_do_not_import_the_database_layer`).

Türkçe büyük harf: "İ" → "i", Türkçe metinde "I" hem "ı" hem "i" olarak denenir ("PROGRAMCISI", "FastAPI").

26.10.2026, 2.002 aktif ilan: pozisyonu belli %39,6 (792), yetkinlik bulunan %88 (ilan başına 7,5), 46 benzer ilan pasife alındı.

## Pozisyon-yetkinlik istatistikleri (T-045)

```bash
python -m collector refresh-stats          # role_skill_stats'ı yeniler (normalize sonunda kendiliğinden çalışır)
python -m collector role-stats --top 5     # pozisyon başına ilan sayısı ve en çok istenen yetkinlikler
```

`role_skill_stats` bir materialized view (tanımı `docs/veritabani.md`): son 6 ayın **aktif ve pozisyonu belli** ilanlarından pozisyon × yetkinlik → `posting_count`, `total_postings`, `demand_ratio`. Pasif ilanlar (EMSCAD, benzer kopyalar) girmez. Yenileme `CONCURRENTLY` yapılır, yani yenileme sırasında API eski veriyi okumaya devam eder. Okuma için `etl/stats.py`: `top_skills(session, role_slug)` ve `summaries(session)`. 50'den az ilanı olan pozisyon `low_data` olarak işaretlenir.

Sıra: `import` → `normalize` (sonunda `refresh-stats`). Gece zamanlaması T-034'te. Toplama durursa ilanlar 6 ay içinde istatistikten düşer.

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
mypy .
```

Testler ağa çıkmaz; kaynaklar uydurma JSON ile denenir.
