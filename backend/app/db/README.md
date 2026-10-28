# app/db — Sahibi: Ataberk

SQLAlchemy 2.0 modelleri, oturum ve Alembic migration'ları. Şema kaynağı [`erd.dbml`](erd.dbml) ve [`docs/veritabani.md`](../../../docs/veritabani.md).

```
base.py        # Base (kısıt adlandırma kuralı, timestamptz), zaman damgası ve soft delete mixin'leri
enums.py       # PostgreSQL enum'ları (contracts/ ile aynı değerler)
models/        # user, catalog, jobs, analysis, audit
session.py     # get_engine(), get_sessionmaker() — repository'ler buradan oturum alır
alembic.ini
migrations/    # env.py + versions/
erd.dbml, erd.svg
```

## Migration komutları

`backend/` klasöründen; adres `.env`'deki `DATABASE_URL`'den okunur (`-x url=...` ile ezilebilir).

```bash
alembic -c app/db/alembic.ini upgrade head        # şemayı en son sürüme getir
alembic -c app/db/alembic.ini downgrade -1        # son migration'ı geri al
alembic -c app/db/alembic.ini current             # veritabanı hangi sürümde
alembic -c app/db/alembic.ini check               # modeller ile migration'lar uyumlu mu
alembic -c app/db/alembic.ini upgrade head --sql  # bağlanmadan SQL çıktısı
```

## Model değiştirirken

1. `models/` altında değişikliği yap.
2. Boş bir veritabanına `upgrade head` uygula, sonra: `alembic -c app/db/alembic.ini revision --autogenerate -m "kisa aciklama"`
3. Üretilen dosyayı **mutlaka elle oku**. Autogenerate şunları yakalamaz veya yanlış yapar:
   - Birden fazla tabloda kullanılan enum'u iki kez oluşturmaya çalışır (`0001`'deki `ENUMS` / `enum()` kalıbını kullan).
   - Materialized view (`role_skill_stats`), eklenti ve veri taşıma adımları elle yazılır.
   - Enum'a değer eklemek: `op.execute("ALTER TYPE ... ADD VALUE ...")`.
4. `upgrade` → `downgrade` → `upgrade` dene; `pytest tests/db` geçmeli.
5. `erd.dbml` ve `docs/veritabani.md` aynı PR'da güncellenir.

## Testler

`tests/db/` gerçek PostgreSQL ister ve sadece `TEST_DATABASE_URL` verilince çalışır (yoksa atlanır). Testler o veritabanında `downgrade base` çalıştırır, bu yüzden **ayrı ve boş** bir veritabanı verin:

```bash
docker run --rm -d --name careerai-test-db -p 127.0.0.1:55432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=careerai_test pgvector/pgvector:pg16
```

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:test@127.0.0.1:55432/careerai_test pytest tests/db
```

PowerShell'de: `$env:TEST_DATABASE_URL = "postgresql+psycopg://postgres:test@127.0.0.1:55432/careerai_test"; pytest tests/db`

## Kurallar

- CV dosyası ve ham CV metni hiçbir sütunda tutulmaz (karar #9); `test_no_cv_content_columns` bunu denetler.
- Kullanıcıya bağlı silmeler DB'deki `ON DELETE CASCADE` ile olur (`passive_deletes=True`); ORM ilişkileri tek tek yüklemez.
- `updated_at` ORM güncellemelerinde otomatik değişir; elle SQL ile güncellerken siz verin.
- HNSW vektör indeksleri T-013'te ayrı migration ile gelir.
