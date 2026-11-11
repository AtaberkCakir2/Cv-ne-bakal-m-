# Yedekleme (T-068)

Postgres her gün 02:00'de yedeklenir: `pg_dump` → [restic](https://restic.net) → PC dışındaki şifreli depo (karar #30). PC o saatte kapalıysa veya uykudaysa kaçan yedek açıldıktan sonraki ilk 10 dakikada alınır (risk R-18). Saklama 7 günlük + 4 haftalık; haftada bir depo doğrulanır (son kontrol tarihi `/state/last-check`; PC o gün kapalıysa sonraki yedekte). Hedefler (`docs/go-live.md`): RPO ≤ 24 saat, RTO ≤ 4 saat, aylık geri yükleme testi.

Windows'ta systemd/cron olmadığı için yedek, production compose'unda (`infra/pc/compose.yml`) kendi zamanlayıcısıyla çalışan `backup` konteyneridir.

| Dosya | Ne yapar |
|---|---|
| `Dockerfile` | restic 0.18 + Postgres 16 istemcisi; `deploy.sh` yerelde derler (`careerai/backup:local`) |
| `scheduler.sh` | Konteynerin ana süreci: 10 dakikada bir son başarılı yedeğe bakar, 02:00'den sonra yedek yoksa `backup.sh`'ı çalıştırır; başarısızsa 30 dk sonra yeniden dener |
| `backup.sh` | Döküm diske yazılmadan restic'e akar; eski yedekleri siler; başarıda `/state/last-success`, haftalık kontrolde `/state/last-check` yazar |
| `restore-test.sh [ortam] [snapshot]` | PC'de (Git Bash) yedeği geçici bir Postgres kapsayıcısına yükler, satır sayılarını canlıyla karşılaştırır. Canlı veritabanına yazmaz |

**Yedekte ne var, ne yok:** Sadece Postgres (kullanıcılar, rızalar, analiz sonuçları, ilanlar, kaynaklar). CV dosyası ve ham metni veritabanında olmadığı için yedekte de yoktur. Redis (geçici kuyruk) ve Ollama modelleri yedeklenmez, yeniden kurulur. `infra/pc/.env.prod` ve restic parolası yedeğe girmez, ekibin parola yöneticisinde durur: onlar olmadan yedek açılamaz.

## Depo: Backblaze B2

Depo PC'den ayrı bir yerde olmalı. Veritabanı küçük (Kasım 2026: ~6,5 MB döküm), ücretsiz 10 GB yeter.

**Kuruldu (06.11.2026, Ataberk):** hesap EU Central bölgesinde, bucket `cvnebakalim-yedek`, uygulama anahtarı `careerai-pc`; anahtarlar ve hesap bilgileri parola yöneticisinde. Yeniden kurmak gerekirse:

1. backblaze.com → **Sign Up** (B2 Cloud Storage), bölge **EU Central**. Hesapta iki adımlı doğrulama açılır.
2. **Caps & Alerts:** bütün sınırlar **$0** (ücretsiz kota aşılırsa ücret yerine işlem durur, uyarı e-postası gelir).
3. **Buckets → Create a Bucket:** **Private**, Default Encryption **Enable**, Object Lock kapalı. Ardından **Lifecycle Settings → Keep only the last version of the file** (silinen eski yedekler gizlice birikmesin; saklamayı restic yönetir).
4. **Application Keys → Add a New Application Key:** ad `careerai-pc`, sadece bu bucket, **Read and Write**. Gösterilen `keyID` ve `applicationKey` yalnızca bir kez görünür.
5. `infra/pc/.env.prod`:

   ```
   RESTIC_REPOSITORY=b2:cvnebakalim-yedek:/careerai
   RESTIC_PASSWORD=<openssl rand -base64 32 çıktısı>
   B2_ACCOUNT_ID=<keyID>
   B2_ACCOUNT_KEY=<applicationKey>
   COMPOSE_PROFILES=tunnel,backup
   ```

   `RESTIC_PASSWORD`'ü hemen ekibin parola yöneticisine de kaydedin.

## Kurulum (bir kez, Git Bash)

```bash
make backup-init                      # restic deposunu oluşturur
bash infra/pc/deploy.sh v1.0.0        # backup konteyneri de başlar (ilk yedeği hemen alır)
make backup-list                      # snapshot görünmeli
```

## Kontrol

```bash
make backup-now                                         # şimdi bir yedek al
make prod-logs                                          # "Yedek tamam" satırları (backup servisi)
docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml logs --tail 20 backup
make backup-list
```

## Geri yükleme testi (aylık)

```bash
bash infra/backup/restore-test.sh production
```

Yükleme süresini ve tablo sayılarını DR tatbikatı notuna yazın (T-087). Canlı sayılar yedekten sonra biraz değişmiş olabilir; temel tablolar boşsa test başarısızdır. 06.11.2026'da prova ortamında dev verisiyle denendi: 6,5 MB yedek ~3 sn, geri yükleme 11 sn, 11 tablonun sayıları eşleşti.

## Gerçek geri yükleme (veri kaybında)

Önce `docs/go-live.md` "Veri tabanı bozulması" adımları: uygulamayı durdurun, kayıp aralığını not edin. Sonra Git Bash'te:

```bash
C="docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml"
$C stop api worker-data
$C exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
$C exec -T backup sh -c 'restic dump --tag "$BACKUP_TAG" latest "/careerai-$BACKUP_TAG.dump"' \
  | $C exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error'
$C up -d
```

`dropdb` geri alınamaz: önce `restore-test.sh` ile yedeğin açıldığını görün. Deploy öncesi alınan yerel dökümler de `~/careerai-yedek` altındadır (`infra/pc/deploy.sh`).

**PC tamamen bozulursa (T-087):** başka bir bilgisayara repo + Docker Desktop kurulur, `.env.prod` parola yöneticisinden yeniden yazılır, `deploy.sh` ile sistem açılır ve yukarıdaki adımlarla son yedek yüklenir. Tünel token'ı aynı kaldığı için alan adı yeni bilgisayara bağlanır.

## Henüz yok

- **Uyarı:** Yedek başarısız olursa şimdilik sadece konteyner loguna yazılır. İzleme (T-066) `/state/last-success` 26 saatten eskiyse uyarı verecek.
