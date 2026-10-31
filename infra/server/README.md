# Sunucu kurulumu (T-009, T-035)

Hetzner CX43 (8 vCPU, 16 GB RAM, 160 GB disk, Ubuntu 24.04). Sırlar bu dosyaya yazılmaz.

## 1. Sunucuyu oluşturma (Hetzner Console)

1. Kendi bilgisayarınızda anahtar yoksa oluşturun: `ssh-keygen -t ed25519`
2. **Security → SSH Keys → Add SSH Key:** `~/.ssh/id_ed25519.pub` içeriğini yapıştırın.
3. **Add Server:** Cost-Optimized → CX43, Ubuntu 24.04, **Primary IPv4 açık**, az önce eklenen SSH anahtarı seçili. Konum: stokta olan (FSN1, NBG1 veya HEL1).
4. **Firewalls → Create Firewall:** gelen 22/tcp, 80/tcp, 443/tcp, 443/udp. Sunucuya uygulayın. Sunucudaki ufw'ye ek bir katmandır; Docker portları ufw'yi atlayabildiği için önemlidir.

## 2. Sertleştirme

```bash
ssh root@<sunucu-ip>
curl -fsSLO https://raw.githubusercontent.com/AtaberkCakir2/Cv-ne-bakal-m-/main/infra/server/harden.sh
```

Repo özel olduğu için bu adres çalışmazsa kendi bilgisayarınızdan kopyalayın: `scp infra/server/harden.sh root@<sunucu-ip>:`

```bash
bash harden.sh
```

**Bitince pencereyi kapatmayın.** İkinci terminalden deneyin:

```bash
ssh deploy@<sunucu-ip>
sudo whoami     # root yazmalı
docker ps       # hata vermemeli
```

Giriş olmazsa ilk penceredeki root oturumundan düzeltin; kapattıysanız Hetzner Console'daki Console düğmesi kurtarma yoludur.

Kontrol: `sudo ufw status`, `sudo fail2ban-client status sshd`, `swapon --show`, `timedatectl`.

## 3. Staging'i kurma

DNS'te `staging-api.<alanadi>` A kaydı sunucu IP'sini göstermeli (T-010); yoksa sertifika alınamaz.

Sunucuda bir deploy anahtarı oluşturup GitHub'a ekleyin (repo → Settings → Deploy keys, yazma izni kapalı):

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
git clone git@github.com:AtaberkCakir2/Cv-ne-bakal-m-.git careerai
cd careerai/infra/staging
cp .env.example .env
chmod 600 .env
nano .env
```

Parolalar ve anahtarlar için `openssl rand -hex 32` kullanın. Her alana ayrı değer girin.

İlk deploy GitHub Actions ile yapılır, önce `infra/ci.md` "Deploy" bölümündeki ayarları tamamlayın. Actions → Deploy → Run workflow çalışıp yeşil olunca sunucuda:

```bash
docker compose exec ollama ollama pull llama3.1:8b
docker compose run --rm worker-data python -m collector seed-taxonomy
docker compose run --rm worker-data python -m collector resources-seed
docker compose run --rm worker-data python -m collector resources-import
```

Model adı kök `.env.example`'daki `OLLAMA_MODEL` ile aynı olmalı. `resources-import` ve kalıcı arama durumu için T-046 (`ataberk/kaynak-havuzu`) `main`'e birleşmiş olmalı; yoksa `worker-data` `data/` klasörüne yazamaz.

Kontrol: `curl https://staging-api.<alanadi>/api/v1/health/ready` → `"status":"ready"`

## Bellek

`mem_limit` değerleri üst sınırdır, boşta çok daha azını kullanırlar:

| Servis | Staging sınırı |
|---|---|
| ollama | 8 GB |
| postgres | 1 GB |
| worker-data | 1 GB |
| worker-ai (`ai/Dockerfile` gelince) | 2 GB |
| api | 512 MB |
| caddy, redis | 128 MB + 128 MB |
| **Toplam** | **~12,8 GB** |

Production gelince (T-075, ~15,5 GB) iki ortam 16 GB'a birlikte sığmaz. Plan: Ollama ve Caddy ortak olur, staging günlük açık kalmaz, sadece deploy ve prova öncesi başlatılır. Ayrıntı T-075'te kesinleşecek.

## Yerelde deneme

`.env`'de `STAGING_API_DOMAIN=staging.localhost`, `HTTP_PORT=18080`, `HTTPS_PORT=18443` verin; Caddy kendi sertifikasını üretir.

```bash
curl -k --resolve staging.localhost:18443:127.0.0.1 https://staging.localhost:18443/api/v1/health/ready
```
