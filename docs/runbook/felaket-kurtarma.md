# Felaket kurtarma: production'ı başka bir bilgisayara taşımak (T-087)

**Ne zaman:** Production PC'si (karar #30) uzun süre kullanılamıyor: donanım arızası, çalınma, disk bozulması, PC'ye erişim yok. Kısa kesintide (elektrik, internet, Windows güncellemesi) bu prosedür **uygulanmaz**; PC geri gelince sistem kendiliğinden açılır ve kaçan toplama/yedek telafi edilir (R-18).

**Hedef:** RTO < 4 saat (karar anından `api.cvnebakalim.com` yeniden yanıt verene kadar), RPO < 24 saat (en fazla bir günlük veri kaybı; yedek her gece 02:00). Kaynak: `docs/go-live.md` SLO tablosu ve go-live #20.

**Kim:** Ataberk yürütür. Ataberk yoksa Cloudflare ve parola yöneticisine erişimi olan yedek kişi (`docs/mimari.md`, Ortamlar: "Ataberk + 1 yedek kişi"; kim olduğu henüz yazılı değil).

Tatbikat (T-087) bu dosyayı adım adım izler, her adımın süresini aşağıdaki tabloya yazar. Gerçek bir felakette de aynı adımlar uygulanır.

---

## 0. Önceden hazır olması gerekenler (felaketten önce)

Bunlar yoksa sistem geri getirilemez. Tatbikattan önce ve her üç ayda bir kontrol edilir.

| # | Ne | Nerede | Kontrol |
|---|---|---|---|
| 0.1 | `infra/pc/.env.prod` dosyasındaki **bütün** değerler (aşağıdaki liste) | Ekibin parola yöneticisi, "careerai-prod .env" kaydı | Kayıttaki anahtar listesi `.env.example` ile aynı mı? |
| 0.2 | `RESTIC_PASSWORD` | Parola yöneticisi (ayrı kayıt da olabilir) | Yoksa **yedek açılamaz**; şifreleme geri döndürülemez |
| 0.3 | Backblaze B2 hesabı ve uygulama anahtarı (`B2_ACCOUNT_ID`, `B2_ACCOUNT_KEY`) | Parola yöneticisi; B2 hesabında 2FA | B2 paneline girilebiliyor mu? |
| 0.4 | Cloudflare hesabı (alan adı, tünel) | Ataberk + yedek kişi, 2FA açık | Zero Trust → Tunnels → `careerai-pc` görünüyor mu? |
| 0.5 | GitHub erişimi (repo + GHCR'den imaj çekme) | Yeni bilgisayarı kuran kişinin GitHub hesabı | `read:packages` yetkili token üretebiliyor mu? |
| 0.6 | Hedef bilgisayar | Burak'ın veya Anıl'ın bilgisayarı | ≥ 16 GB RAM (tercihen 32), ≥ 40 GB boş disk, Windows 10/11 + WSL2 veya Linux/macOS |

`.env.prod` anahtarları (hepsi parola yöneticisinde olmalı):

```
APP_ENVIRONMENT  COMPOSE_SUBNET  POSTGRES_USER  POSTGRES_DB  POSTGRES_PASSWORD  APP_DB_PASSWORD
REDIS_PASSWORD  JWT_SECRET  IP_HASH_SECRET  CORS_ORIGINS  FRONTEND_URL  YOUTUBE_API_KEY  TUNNEL_TOKEN
RESTIC_REPOSITORY  RESTIC_PASSWORD  B2_ACCOUNT_ID  B2_ACCOUNT_KEY
GRAFANA_ADMIN_PASSWORD  GRAFANA_PORT  MONITOR_DB_PASSWORD  COMPOSE_PROFILES  LOCAL_API_PORT
```

**Neden aynı değerler:** `JWT_SECRET` değişirse bütün oturumlar düşer (kullanıcılar yeniden giriş yapar, veri kaybı yok). `IP_HASH_SECRET` değişirse eski rıza kayıtlarındaki IP özetleri yenileriyle karşılaştırılamaz. `POSTGRES_PASSWORD` ve diğer DB şifreleri yeni kurulumda yeniden yazılır, ama aynı tutmak işi basitleştirir. `TUNNEL_TOKEN` aynı kalırsa alan adı ayarına dokunmak gerekmez.

---

## 1. Karar ve eski PC'nin tünelden ayrılması

| Adım | Ne yapılır |
|---|---|
| 1.1 | Kesinti başlangıcını ve kararı not edin (saat). RTO bu andan ölçülür. |
| 1.2 | **Eski PC hâlâ açıksa** `cloudflared`'i durdurun: `docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml stop cloudflared`. Aynı tünel token'ıyla iki bilgisayar bağlanırsa Cloudflare istekleri **ikisine bölüştürür**: kullanıcılar iki farklı veritabanı görür. |
| 1.3 | Eski PC'ye erişim yoksa: Cloudflare → Zero Trust → Networks → Tunnels → `careerai-pc` → **Connectors** sekmesinde eski bağlantı görünüyorsa, yeni PC bağlanınca o bağlantı da trafik alır. Bu durumda **yeni bir tünel** açın (`infra/pc/deploy.md` 3. bölüm), yeni token'ı `.env.prod`'a yazın ve eski tüneli silin. |

Tatbikatta production'ı bozmamak için 1.2 yerine bunu yapın: eski PC çalışmaya devam eder, yeni bilgisayar **geçici bir tünelle** (`dr-test` adıyla, `dr.cvnebakalim.com` hostname'i) açılır. Ölçülen süre aynıdır; sadece son adımda alan adı farklıdır.

## 2. Yeni bilgisayarın hazırlanması

| Adım | Komut / yer | Not |
|---|---|---|
| 2.1 | Docker Desktop (WSL2) kurulumu, `.wslconfig` ile en fazla 20 GB (`infra/pc/README.md`) | Windows'ta WSL için gerçek bir yeniden başlatma gerekir |
| 2.2 | Git + Git Bash, `git clone` ve `git checkout vX.Y.Z` (son production etiketi) | Etiket yoksa `main` |
| 2.3 | `docker login ghcr.io -u <github-kullanıcısı>` (`read:packages` token) | `infra/pc/deploy.md` 1. bölüm |
| 2.4 | `infra/pc/.env.prod`'u parola yöneticisinden yazın; Windows'ta dosyayı sadece kendi kullanıcınız okuyabilsin (`icacls infra\pc\.env.prod /inheritance:r /grant:r "%USERNAME%:F"`) | Repoya **eklenmez** (`.gitignore`) |
| 2.5 | `make prod-model` (Ollama modeli, ~5 GB) | **En uzun adım.** İndirme sürerken 3. adıma geçilebilir (paralel) |

## 3. Sistemin açılması ve verinin geri yüklenmesi

```bash
# 3.1 Boş sistem: imajlar, migration, DB rolleri, servisler (yedek konteyneri de başlar)
bash infra/pc/deploy.sh vX.Y.Z production

# 3.2 Yedeğin açıldığını gör (geçici kapsayıcıda; canlı veritabanına yazmaz)
make backup-list
bash infra/backup/restore-test.sh production

# 3.3 Gerçek geri yükleme: boş veritabanını son yedekle değiştir
C="docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml"
$C stop api worker-data
$C exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
$C exec -T backup sh -c 'restic dump --tag "$BACKUP_TAG" latest "/careerai-$BACKUP_TAG.dump"' \
  | $C exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error'

# 3.4 Rolleri ve yetkileri yeniden ver, servisleri aç (deploy tekrar çalıştırılabilir)
bash infra/pc/deploy.sh vX.Y.Z production
```

`deploy.sh` 3.4'te boş olmayan veritabanının dökümünü de alır; bu beklenen bir şeydir. 3.1'deki ilk deploy olmadan 3.3 yapılamaz: `backup` konteyneri ve veritabanı rolleri deploy ile gelir.

## 4. Doğrulama

| Adım | Kontrol | Beklenen |
|---|---|---|
| 4.1 | `curl -s https://api.cvnebakalim.com/api/v1/health/ready` (tatbikatta `dr.` adresi) | 200, `"status":"ready"` |
| 4.2 | `make prod-ps` | Bütün servisler `healthy` |
| 4.3 | Satır sayıları: 3.2'deki `restore-test.sh` çıktısı ile canlı karşılaştırma | Aynı (yedekten sonraki gece toplaması hariç) |
| 4.4 | Test hesabıyla giriş → profil → geçmiş analizler | Eski analizler görünüyor |
| 4.5 | Grafana `http://127.0.0.1:3000` | Hedefler `up`, `DisErisimYok` uyarısı yok |
| 4.6 | `make backup-now` ve `make backup-list` | Yeni bilgisayardan yedek B2'ye gidiyor |

**RTO bitişi:** 4.1'in 200 döndüğü an.

## 5. Sonrası

- Gerçek felakette: kayıp aralığını (son yedek saati → kesinti) not edin; veri ihlali şüphesi varsa (PC çalındı) `docs/go-live.md` "Kişisel veri ihlali şüphesi" olay prosedürü (72 saat içinde KVK Kurulu'na bildirim, go-live #39).
- Eski PC geri gelirse **production'ı orada açmayın**: önce `cloudflared` ve `backup` servislerinin kapalı olduğundan emin olun; iki yedekleyici aynı restic deposuna aynı etiketle yazar.
- Bu dosyada eksik veya yanlış çıkan adımı düzeltin (PR).

---

## Tatbikat kaydı

Her tatbikatta bir satır eklenir. "Toplam" 1.1'den 4.1'e kadar geçen süredir.

| Tarih | Hedef bilgisayar | Yürüten | Yedek saati → geri yükleme | 2.1–2.4 | 2.5 model | 3.1 deploy | 3.3 geri yükleme | Toplam (RTO) | Veri kaybı (RPO) | Sorunlar |
|---|---|---|---|---|---|---|---|---|---|---|
| _(henüz yapılmadı)_ | | | | | | | | | | |

**Ön ölçümler (production PC'sinde, 18.11.2026):** 1,97 MB yedekten geçici kapsayıcıya geri yükleme 12 sn, 11 tablonun sayıları canlıyla aynı (`restore-test.sh production`). `deploy.sh` (imajlar hazırken) birkaç dakika. Model indirme süresi ağ hızına bağlı (~5 GB): 100 Mbit/s'de ~7 dk, 20 Mbit/s'de ~35 dk.
