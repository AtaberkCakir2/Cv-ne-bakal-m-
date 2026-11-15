# scraper/ — Sahibi: Ataberk

İlan toplama (resmi API'ler, açık veri setleri, izin veren siteler), ETL/normalizasyon, yetkinlik taksonomisi, eğitim kaynağı havuzu.

Çıktı formatı: `contracts/job_posting.schema.json`

Hangi kaynaktan veri çekilebileceği ve uyulacak kurallar: [kaynak-uygunluk.md](kaynak-uygunluk.md). Yeni kaynak eklemeden önce oraya satır eklenir.

## Kurulum

Python 3.12. Modeller backend paketinden geldiği için ikisi birlikte kurulur (`scraper/` içinde):

```bash
python -m venv C:\venv\careerai      # Windows'ta kısa yol (uzun yol hatası olmasın)
C:\venv\careerai\Scripts\activate    # macOS/Linux: source .venv/bin/activate
pip install -e ../backend -e ../ai -e ".[dev]"   # ai: ilan maskeleme (pii)
```

Veritabanı: repo kökünde `make up`, sonra `backend/` içinde `alembic -c app/db/alembic.ini upgrade head`. Adres `.env`'deki `DATABASE_URL`.

## İlan havuzu (T-015)

```bash
python -m collector import hn --months 6        # Hacker News "Who is hiring?", ~2.000 ilan, ~8 dk
python -m collector import himalayas --pages 5  # 10 yazılım araması × 5 sayfa, ~2 dk
python -m collector import remoteok
python -m collector import remotive             # günde en fazla birkaç kez
python -m collector import jobicy
python -m collector import arbeitnow
python -m collector import pythonorg             # Playwright; pip install -e ".[browser]" && playwright install chromium --only-shell
python -m collector import emscad --csv data/fake_job_postings.csv   # yedek veri seti, pasif yüklenir
python -m collector stats                       # kaynak başına ilan sayısı
```

| Kaynak | `job_sources.name` | Ne | Not |
|---|---|---|---|
| Hacker News | `hacker-news` | Aylık "Ask HN: Who is hiring?" yorumları | Yorumu yazanın kullanıcı adı okunmaz |
| Himalayas | `himalayas` | Yazılım aramaları (Developer, Data Science) | Anahtarsız: istekler arası 2 sn |
| Remote OK | `remote-ok` | Güncel uzaktan ilanlar | Follow link + kaynak adı zorunlu |
| Remotive | `remotive` | Yazılım kategorisi | Ücretsiz API az ilan veriyor (~10) |
| Jobicy | `jobicy` | Yazılım, veri, DevOps, güvenlik, test | Sadece son 7 gün; kaynak adı zorunlu |
| Arbeitnow | `arbeitnow` | Avrupa ilanları (yazılım başlıkları) | Almanca ilanlar elenir; Arbeitnow.com'a link zorunlu |
| Python.org | `pythonorg` | Python iş ilanları (HTML) | Playwright PoC'si; ~20 ilan; gece akışında yok |
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
| Kişisel veri | `etl/pipeline.py` | Burak'ın T-030 maskeleyicisi `pii.mask_posting` (kurallar, NER yok): işe alımcının adı, telefon, TCKN, IBAN → `[AD SOYAD]`, `[TELEFON]`… `description_clean` üzerine yazılır. `mask_posting_once` önceki etiketlere dokunmaz, her gece tekrar çalışmak güvenli. 30.10.2026: 6.632 ilandan 338'inde maskeleme, 2 yetkinlik bağı kaybı. |

Eşleyiciler (`etl/text.py`, `etl/skills.py`, `etl/roles.py`, `etl/dedup.py`) veritabanı kullanmaz: taksonomiyi `collector/taxonomy_rows.py`'den okur, backend paketi ve SQLAlchemy olmadan çalışır (AI worker T-031'de kullanacak; test: `test_matchers_do_not_import_the_database_layer`).

Türkçe büyük harf: "İ" → "i", Türkçe metinde "I" hem "ı" hem "i" olarak denenir ("PROGRAMCISI", "FastAPI").

26.10.2026, 2.002 aktif ilan: pozisyonu belli %39,6 (792), yetkinlik bulunan %88 (ilan başına 7,5), 46 benzer ilan pasife alındı.

## Pozisyon-yetkinlik istatistikleri (T-045)

```bash
python -m collector refresh-stats          # role_skill_stats'ı yeniler (normalize sonunda kendiliğinden çalışır)
python -m collector role-stats --top 5     # pozisyon başına ilan sayısı ve en çok istenen yetkinlikler
```

`role_skill_stats` bir materialized view (tanımı `docs/veritabani.md`): son 6 ayın **aktif ve pozisyonu belli** ilanlarından pozisyon × yetkinlik → `posting_count`, `total_postings`, `demand_ratio`. Pasif ilanlar (EMSCAD, benzer kopyalar) girmez. Yenileme `CONCURRENTLY` yapılır, yani yenileme sırasında API eski veriyi okumaya devam eder. Okuma için `etl/stats.py`: `top_skills(session, role_slug)` ve `summaries(session)`. 50'den az ilanı olan pozisyon `low_data` olarak işaretlenir.

Sıra: `import` → `normalize` (sonunda `refresh-stats`). Gece zamanlaması T-034'te (aşağıda). Toplama durursa ilanlar 6 ay içinde istatistikten düşer.

## Gece toplaması (T-034)

Her gece **03:00 (İstanbul)** Celery beat `collector.nightly` görevini başlatır (`collector/tasks.py`, kuyruk `data`). Zincir `collector/nightly.py`'de:

1. Kaynaklar sırayla: Hacker News (son 2 aylık başlık, sadece veritabanında olmayan yorumlar), Himalayas (10 arama × 2 sayfa), Remote OK, Remotive (gecede 1 çağrı). EMSCAD gece çalışmaz.
2. Yeni ilan geldiyse `normalize`.
3. Her durumda `role_skill_stats` yenilenir (6 aylık pencere her gün kayar).

| Kural | Nasıl |
|---|---|
| İstekler arası 3–5 sn rastgele bekleme | `PoliteClient(jitter=(3, 5))`; kaynağın kendi alt sınırı daha büyükse o (Remotive 30 sn) |
| Üstel geri çekilme | 429/5xx ve ağ hatalarında 5 → 10 → 20 → 40 sn (+ %50'ye kadar rastgele), en çok 4 tekrar; `Retry-After` varsa o (en çok 10 dk) |
| User-Agent | Kimliğini belirten **tek** UA (`CvneBakalim-Bot/…`). Dönüşümlü/sahte UA kullanılmaz: `kaynak-uygunluk.md` kural 3-4 |
| Bir kaynak düşerse | Diğerleri devam eder; her kaynak `scrape_runs`'a ayrı yazılır (`success` / `partial` / `failed`) |
| 403 veya tekrarlara rağmen 429 | Kaynak `job_sources.is_active = false` yapılır ve sonraki geceler atlanır (kural 3). Durum incelenip elle açılır: `UPDATE job_sources SET is_active = true WHERE name = '…'` |
| Üst üste binme | Redis kilidi: elle tetikleme ile beat çakışırsa ikincisi atlanır. Süre sınırı 3 saat |

**Elle çalıştırma** (Celery olmadan, aynı zincir):

```bash
python -m collector nightly              # 3-5 sn beklemeyle
python -m collector nightly --no-jitter  # sadece kaynağın alt sınırı (hızlı deneme)
```

**İşçi** (Linux/Docker'da işçi + beat tek süreç):

```bash
docker compose --profile data up -d worker-data          # repo kökünde; imaj scraper/Dockerfile
celery -A collector.tasks worker -B -Q data --concurrency 1 --loglevel INFO
```

Windows'ta `-B` çalışmaz; işçi ve beat ayrı başlatılır: `celery -A collector.tasks worker -Q data --pool solo` ve `celery -A collector.tasks beat`. Elle tetikleme: `celery -A collector.tasks call collector.nightly --queue data`.

`make up` worker-data'yı **başlatmaz**: üç geliştiricinin bilgisayarı her gece aynı kaynaklara gitmesin. Sunucuda (staging/production, T-035) `--profile data` ile açılır.

### Sentetik CV şablon girdisi (T-019)

```bash
python -m collector export-template        # → exports/template_input.json (--top 30: pozisyon başına yetkinlik)
```

Burak'ın `ai/eval` şablon betiği için: her pozisyonun unvanları (`titles`), ilan sayısı, `low_data` bayrağı ve talep oranına göre ilk 30 yetkinlik (`demand_ratio`, `tier`: core ≥ 0,30 / common ≥ 0,10 / rare; eş anlamlılar CV'de kısaltma ve yazım farkı üretmek için). Sadece toplu oranlar içerir, ilan metni yok. `exports/template_input.json` repoda tutulur; `ai/eval/dataset/template_input.json`'a kopyalamak `ai/` sahibinin işidir. Yetkinlik listesi etiketleme için cevap anahtarı değildir.

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

## Eğitim kaynağı havuzu (T-046)

Öneri linkleri sadece `resources` tablosundan gelir (karar #10). İki kaynak: elle derlenen `taxonomy/resources.csv` ve YouTube Data API.

```bash
python -m collector resources-seed            # CSV → resources (aynı URL tekrar eklenmez)
python -m collector resources-youtube --limit 10  # YouTube araması; --limit olmadan kota dolana kadar
python -m collector resources-export          # bulunan videolar → taxonomy/resources_youtube.csv
python -m collector resources-import          # o dosyayı yeni ortama yükle (arama kotası harcamaz)
python -m collector resources-check           # ölü linkler + YouTube bilgilerini yenileme
python -m collector resources-report          # toplam ve 3'ten az kaynağı olan yetkinlikler
```

- `.env`'de `YOUTUBE_API_KEY` gerekir; boşsa arama atlanır.
- Günde en fazla 100 arama (Türkçe ve İngilizce ayrı arama). Kota Pasifik saatiyle gece yarısı (TR ~10:00) yenilenir. Aramalar talebi yüksek yetkinlikten başlar, durum `data/youtube_searched.json`'da.
- `resources_youtube.csv` sadece video kimliği, yetkinlik, dil ve seviye tutar. Başlık ve süre repoya yazılmaz (30 gün kuralı), yüklerken API'den alınır; silinen video atlanır.
- `worker-data` her gün 06:00'da aramaya devam eder, pazar 07:00'de linkleri kontrol eder.
- Filtre: 10 dk–12 sa, TR ≥ 1.000 / EN ≥ 10.000 izlenme, başlıkta yetkinlik adı ve öğretim ipucu var, tanıtım kelimesi yok. Seviye başlıktan okunur, ipucu yoksa `beginner`.
