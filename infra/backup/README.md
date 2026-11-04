# Yedekleme (T-068)

Postgres her gece 02:00'de yedeklenir: `pg_dump` → [restic](https://restic.net) → sunucu dışındaki şifreli depo. Saklama 7 günlük + 4 haftalık; pazar günleri depo doğrulanır. Hedefler (`docs/go-live.md`): RPO ≤ 24 saat, RTO ≤ 4 saat, aylık geri yükleme testi.

| Dosya | Ne yapar |
|---|---|
| `backup.sh <ortam> <compose-klasörü>` | Döküm diske yazılmadan restic'e akar; eski yedekleri siler; başarıda `/var/lib/careerai/backup-<ortam>.last-success` yazar |
| `restore-test.sh <ortam> <compose-klasörü> [snapshot]` | Yedeği geçici bir Postgres kapsayıcısına yükler, satır sayılarını canlıyla karşılaştırır. Canlı veritabanına yazmaz |
| `careerai-backup@.service`, `careerai-backup@.timer` | systemd zamanlayıcısı; örnek adı ortamdır (`@staging`) |
| `backup.env.example` | Depo ve parola ayarları (`/etc/careerai/backup.env`) |

**Yedekte ne var, ne yok:** Sadece Postgres (kullanıcılar, rızalar, analiz sonuçları, ilanlar, kaynaklar). CV dosyası ve ham metni veritabanında olmadığı için yedekte de yoktur. Redis (geçici kuyruk) ve Ollama modelleri yedeklenmez, yeniden kurulur. `.env` dosyaları ve restic parolası yedeğe girmez, ekibin parola yöneticisinde durur: onlar olmadan yedek açılamaz.

## Depo seçimi

Depo, sunucuyla aynı yerde olmamalı. Veritabanı küçük olduğu için en küçük paket yeter.

- **Hetzner Storage Box:** SFTP, port 23. Sunucu başka sağlayıcıda olsa da kullanılabilir.
- **Backblaze B2:** S3 benzeri; anahtar sadece bu kovaya yetkili oluşturulur.

## Kurulum (sunucuda, bir kez)

```bash
sudo apt-get install -y restic
sudo restic self-update            # Ubuntu 24.04'teki 0.16 eski; en az 0.17 gerekli
restic version

sudo install -d -m 700 /etc/careerai
sudo cp ~/careerai/infra/backup/backup.env.example /etc/careerai/backup.env
sudo chmod 600 /etc/careerai/backup.env
sudo nano /etc/careerai/backup.env
openssl rand -base64 32 | sudo tee /etc/careerai/restic-password >/dev/null
sudo chmod 600 /etc/careerai/restic-password
```

Parolayı hemen ekibin parola yöneticisine de kaydedin (`sudo cat /etc/careerai/restic-password`).

Storage Box kullanılıyorsa root'un SSH anahtarı Storage Box'a eklenir ve port tanımlanır:

```bash
sudo ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519
sudo cat /root/.ssh/id_ed25519.pub   # Hetzner Console → Storage Box → SSH keys
printf 'Host *.your-storagebox.de\n  Port 23\n' | sudo tee -a /root/.ssh/config
```

Depoyu oluşturup zamanlayıcıyı açın:

```bash
sudo bash -c 'set -a; . /etc/careerai/backup.env; restic init'
sudo cp ~/careerai/infra/backup/careerai-backup@.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now careerai-backup@staging.timer
```

## Kontrol

```bash
sudo systemctl start careerai-backup@staging.service     # şimdi bir yedek al
journalctl -u careerai-backup@staging.service -n 20
systemctl list-timers 'careerai-backup@*'
sudo bash -c 'set -a; . /etc/careerai/backup.env; restic snapshots'
```

## Geri yükleme testi (aylık)

```bash
sudo bash -c 'set -a; . /etc/careerai/backup.env; ~/careerai/infra/backup/restore-test.sh staging ~/careerai/infra/staging'
```

Yükleme süresini ve tablo sayılarını DR tatbikatı notuna yazın (T-087). Canlı sayılar yedekten sonra biraz değişmiş olabilir; temel tablolar boşsa test başarısızdır.

## Gerçek geri yükleme (veri kaybında)

Önce `docs/go-live.md` "Veri tabanı bozulması" adımları: uygulamayı durdurun, kayıp aralığını not edin. Sonra staging klasöründe:

```bash
docker compose stop api worker-data
docker compose exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
sudo bash -c 'set -a; . /etc/careerai/backup.env; restic dump --tag staging latest /careerai-staging.dump' \
  | docker compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error'
docker compose up -d
```

`dropdb` geri alınamaz: önce `restore-test.sh` ile yedeğin açıldığını görün.

## Henüz yok

- **Uyarı:** Yedek başarısız olursa şimdilik sadece journal'a yazılır. İzleme (T-066) `.last-success` dosyasının 26 saatten eski olmasını uyarı yapacak.
- **Production:** T-075'te `careerai-backup@production.timer` eklenir; aynı depo, ayrı etiket.
