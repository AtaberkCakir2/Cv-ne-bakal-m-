# Operasyon runbook'u (T-088)

Production'da en sık karşılaşılacak altı durum için adım adım prosedür: deploy, geri dönüş (rollback), Ollama, disk dolu, kuyruk birikmesi, kişisel veri ihlali şüphesi. Olayların özeti ve diğer olaylar (tünel, PC kapandı, sunum B planı) `docs/go-live.md` "Olay prosedürleri" tablosunda; PC tamamen kaybolursa `docs/runbook/felaket-kurtarma.md`.

Hepsi production PC'sinde, repo kökünde **Git Bash** ile çalışır. Komutlarda kısaltma:

```bash
C="docker compose -p careerai-prod --env-file infra/pc/.env.prod -f infra/pc/compose.yml"
```

**Genel kurallar**

- Production veritabanına yazan her komuttan (silme, güncelleme, downgrade) önce yedek: `make backup-now`.
- Olay sırasında ne yapıldığını saatiyle not edin (WhatsApp grubu yeterli); olay bitince kök nedeni `docs/kararlar.md`'ye veya ilgili görevin **Not** satırına yazın.
- Sırlar (`.env.prod`) komut satırına, loglara veya sohbete yapıştırılmaz.

| Durum | Uyarı (Grafana, `infra/monitoring/prometheus/alerts.yml`) | Sorumlu | Hedef süre |
|---|---|---|---|
| [1. Deploy](#1-deploy) | — | Ataberk | ~10 dk |
| [2. Geri dönüş](#2-geri-dönüş-rollback) | `ApiHazirDegil`, smoke test başarısız, 5xx artışı | Ataberk | ≤ 15 dk (go-live #49) |
| [3. Ollama](#3-ollama-yanıt-vermiyor) | `AnalizHatalari`, `RamYuksek` | Burak | ≤ 30 dk |
| [4. Disk dolu](#4-disk-dolmak-üzere) | `DiskAz` (C: boş < %10) | Ataberk | ≤ 1 saat |
| [5. Kuyruk birikmesi](#5-kuyruk-birikmesi) | `AnalizKuyruguBirikti`, `VeriKuyruguBirikti` | Anıl (analiz), Ataberk (veri) | ≤ 30 dk |
| [6. Veri ihlali şüphesi](#6-kişisel-veri-ihlali-şüphesi) | — (bildirim, logda kişisel veri, şüpheli erişim) | Burak (koordinasyon), herkes | ilk adımlar ≤ 1 saat, KVK Kurulu ≤ 72 saat |

---

## 1. Deploy

Sürüm alma tek komuttur; betik imajları indirir, migration öncesi döküm alır, migration'ı uygular, rolleri günceller ve sağlık kontrolü başarısız olursa önceki imajlara kendisi döner (`infra/pc/deploy.sh`, ayrıntı `infra/pc/deploy.md`).

1. **Önce kontrol (GitHub):** deploy edilecek commit main'de, CI yeşil ve "Deploy" iş akışı o commit için imajları üretmiş olmalı (Actions → Deploy → başarılı). Yeni migration varsa: `make backup-migration-test` (son yedeğin kopyasında geri alma testi, ~1 dk).
2. **Duyuru:** kısa kesinti olabilir; sunum/demo saatinde deploy yapılmaz.
3. **Deploy:**
   ```bash
   git fetch --tags origin
   bash infra/pc/deploy.sh v1.0.0          # veya: bash infra/pc/deploy.sh origin/main
   ```
   Çıktıda `Döküm: ~/careerai-yedek/deploy-…dump` satırını not edin (geri dönüşte gerekebilir).
4. **Smoke test:**
   ```bash
   curl -s https://api.cvnebakalim.com/api/v1/health/ready      # "status":"ready"; değilse checks içinde ok:false olan bileşen
   make prod-ps                                                   # hepsi running / healthy
   ```
   Tarayıcıdan: giriş yap → CV yükle → sonuç geliyor mu. Grafana'da (`http://127.0.0.1:3000`) 10 dk boyunca 5xx ve süre grafikleri normal mi.
5. **Veri komutu gerekiyorsa** (PR açıklamasında yazar; ör. taksonomi değişti):
   ```bash
   $C exec worker-data python -m collector seed-taxonomy
   $C exec worker-data python -m collector normalize
   $C exec worker-data python -m collector refresh-stats
   ```
6. Deploy tamam: sürümü ve saati gruba yazın.

## 2. Geri dönüş (rollback)

**Ne zaman:** deploy sonrası smoke test başarısız, `ApiHazirDegil` uyarısı veya 5xx artışı. Hedef 15 dk; önce dön, sonra kök nedeni ara.

1. **Betik zaten döndüyse** (çıktıda `Önceki sürüme dönüldü`): 1. bölümün 4. adımıyla kontrol edin, sonra 5. adıma geçin.
2. **Elle dönüş (imaj):** önceki sürümün etiketi veya commit'i ile deploy edin. Her servisin son 3 imajı PC'de durur, indirme gerekmez:
   ```bash
   bash infra/pc/deploy.sh v0.9.0          # önceki etiket; etiket yoksa önceki commit: git log --oneline origin/main
   ```
   Migration'lar önceki sürümle uyumlu yazıldığı için (sütun silme ayrı PR'da) çoğu durumda bu yeterlidir.
3. **Migration da geri alınacaksa** (yeni migration önceki kodu bozuyorsa). Önce yedek, sonra bir adım geri:
   ```bash
   make backup-now
   U=$(sed -n 's/^POSTGRES_USER=//p' infra/pc/.env.prod | tr -d '\r'); P=$(sed -n 's/^POSTGRES_PASSWORD=//p' infra/pc/.env.prod | tr -d '\r'); D=$(sed -n 's/^POSTGRES_DB=//p' infra/pc/.env.prod | tr -d '\r')
   DATABASE_URL="postgresql+psycopg://$U:$P@postgres:5432/$D" $C run --rm --no-deps -e DATABASE_URL api alembic -c app/db/alembic.ini downgrade -1
   unset U P D
   ```
   Not: `api` o anda hangi imajdaysa onun migration'larını bilir; downgrade'i **yeni** sürüm çalışırken (2. adımdan önce) yapın, sonra 2. adımla eski imaja dönün. Gerçek veriyle prova: `make backup-migration-test` (18.11.2026: 0004 → 0003 → 0004, 7 sn, satır sayıları aynı).
4. **Veri bozulduysa:** deploy öncesi döküm `~/careerai-yedek/deploy-<tarih>-<sha>.dump` (son 5 tutulur). Yükleme adımları `infra/backup/README.md` "Gerçek geri yükleme" (o dosyada restic yerine bu döküm kullanılır). Dökümden sonra kaydolan kullanıcılar ve analizler kaybolur: aralığı not edin.
5. **Sonrası:** hatalı commit'i geri alan PR (revert) veya düzeltme PR'ı; main'e girmeden tekrar deploy yok.

## 3. Ollama yanıt vermiyor

**Belirti:** `/api/v1/health/ready` çıktısında `checks.ollama.ok` false (`status: not_ready`), analizler zaman aşımında, `AnalizHatalari` uyarısı.

1. Durum:
   ```bash
   $C ps ollama
   $C exec ollama ollama list          # model indirilmiş mi
   $C exec ollama ollama ps            # bellekte yüklü model ve RAM'i
   docker stats --no-stream            # ollama mem_limit 8g; sınıra dayandıysa OOM ile yeniden başlıyordur
   ```
2. Yeniden başlatma (veri kaybı yok, model diskte kalır; ilk istekte ~30 sn yükleme):
   ```bash
   $C restart ollama
   curl -s https://api.cvnebakalim.com/api/v1/health/ready
   ```
3. Model yoksa (volume silinmiş/yeni kurulum): `make prod-model` (varsayılan `llama3.1:8b`, ~5 GB; `.env.prod`'daki `OLLAMA_MODEL` neyse o).
4. RAM yetmiyorsa (`RamYuksek`): Görev Yöneticisi'nde Docker dışı ağır uygulamaları kapatın; geçici olarak izleme profilini kapatmak ~1 GB kazandırır (`COMPOSE_PROFILES`'tan `monitoring`'i çıkarıp `$C up -d --remove-orphans`).
5. Düzelmezse: `$C logs --tail 200 ollama` çıktısıyla Burak'a haber verin. Bu sürede analizler başarısız işaretlenir; kullanıcı daha sonra tekrar dener.

## 4. Disk dolmak üzere

**Belirti:** `DiskAz` (C: boş alan < %10), Docker hataları ("no space left on device"). Postgres disk dolarsa yazamaz: önce bu bölümü bitirin.

1. Ne yer kaplıyor:
   ```bash
   docker system df
   powershell -c "Get-PSDrive C | Select-Object Used,Free"
   du -sh ~/careerai-yedek
   ```
2. **Güvenli temizlik** (çalışan sistemi etkilemez):
   ```bash
   docker builder prune -f           # derleme önbelleği (genelde en büyük kalem)
   docker image prune -f             # etiketsiz imajlar; önceki sürüm etiketleri (…-previous, son 3 sha) silinmez
   ```
   Deploy dökümleri `~/careerai-yedek` altında son 5 tanesiyle sınırlı; gerekirse en eskileri silinebilir (PC dışı yedek restic'te).
3. **Asla:** `docker volume prune`, `docker system prune --volumes`, `$C down -v` — veritabanı, model ve yedek durumu volume'larda.
4. Konteyner logları zaten 10 MB × 3 ile sınırlı (`compose.yml` `x-logging`); Loki 14 gün tutar.
5. Docker Desktop'ın sanal diski (`%LOCALAPPDATA%\Docker\wsl\disk\docker_data.vhdx`) içinden silinen veri Windows'a kendiliğinden geri verilmez; `docker system df` küçüldüğü hâlde C: boşalmadıysa sebep budur. Sanal diski küçültmek bakım penceresinde yapılır (production ~10 dk kapalı; 20.11.2026'da denendi, 40,6 → 22,8 GB):
   ```bash
   make backup-now
   docker run --rm --privileged --pid=host alpine:3.21 nsenter -t 1 -m -- fstrim -av   # boş blokları işaretle
   $C stop && docker desktop stop && wsl --shutdown
   ```
   Sonra **yönetici** PowerShell'de: `Optimize-VHD -Path "$env:LOCALAPPDATA\Docker\wsl\disk\docker_data.vhdx" -Mode Full` (Hyper-V modülü yoksa `diskpart` → `select vdisk file=…` → `compact vdisk`). Ardından `docker desktop start` ve `$C up -d --no-build --wait`. Docker Desktop'taki **"Clean / Purge data"** düğmesine basılmaz: tüm volume'ları (veritabanı dahil) siler.
6. Kalıcı çözüm gerekiyorsa (sürekli doluyorsa) Ollama modeli veya imajlar için başka sürücü planlayın ve `docs/kararlar.md`'ye yazın.

## 5. Kuyruk birikmesi

İki kuyruk var (Redis listesi): `analysis` (CV analizleri; analiz işçisi `worker-analysis` tüketir, AI paketini o çağırır) ve `data` (gece toplaması, kaynak arama, link kontrolü; `worker-data` tek eşzamanlı tüketir).

1. Derinlik ve işçiler:
   ```bash
   $C exec redis redis-cli llen analysis
   $C exec redis redis-cli llen data
   $C ps
   $C logs --tail 100 worker-data
   ```
   Not: analiz işçisi (`worker-analysis`, T-057) production compose'a eklenene kadar `analysis` kuyruğunu tüketen servis yoktur; birikme beklenir.
2. **Analiz kuyruğu** (`AnalizKuyruguBirikti`: ≥ 6 iş, 10 dk): analiz işçisi (`worker-analysis`) ayakta mı, Ollama sağlıklı mı (3. bölüm). İşçi takıldıysa yeniden başlatın. `processing`'de takılı kalan analizler 65 dk sonra (`ANALYSIS_STALE_AFTER_S=3900`) kullanıcı sonucu açtığında otomatik `failed` olur; elle veritabanı değişikliği gerekmez. Yoğunluk sürüyorsa analiz sınırını geçici düşürmek Anıl'ın kararı (API ayarı).
3. **Veri kuyruğu** (`VeriKuyruguBirikti`: > 50 iş, 30 dk): gece toplaması kilitli (`careerai:lock:nightly`) olduğu için üst üste binmez; birikme genelde işçinin uzun süre kapalı kalmasından olur. İşçi açıkken kendiliğinden erir. Gereksiz biriken işleri boşaltmak (bekleyenler silinir, çalışan iş etkilenmez; kaçan gece toplaması ve link kontrolü işçi açılışında tekrar kuyruğa girer):
   ```bash
   $C exec worker-data celery -A collector.tasks purge -Q data -f
   $C restart worker-data
   ```
4. Analiz kuyruğunu boşaltmak (`redis-cli del analysis`) kullanıcıların bekleyen analizlerini siler; sadece Anıl ile birlikte ve gruba yazarak yapılır. Sonrasında elle temizlik gerekmez: silinen işlerin analizleri 65 dk sonra kendiliğinden `failed` olur, CV'ler `cv-redis`'te süre aşımıyla (`ANALYSIS_CV_TTL_S=3600`) silinir.

## 6. Kişisel veri ihlali şüphesi

**Ne sayılır:** yetkisiz erişim (panelde/DB'de tanımadığınız giriş), loglarda veya repoda kişisel veri, sır sızıntısı (`.env.prod`, tünel token'ı, yedek parolası), dışarıdan gelen sızıntı bildirimi. Şüphe yeterlidir; emin olmayı beklemeyin.

**Bizde ne var:** e-posta, parola hash'i (argon2), rıza kayıtları (IP'nin anahtarlı hash'i), analizlerden çıkan yetkinlikler, CV'nin SHA-256 hash'i. **CV dosyası ve CV metni hiçbir yerde saklanmaz** (karar #9): ihlal analizinde bu kapsam dışıdır.

1. **İlk saat — erişimi kes:**
   - Sızıntı dış erişimden geliyorsa tüneli durdurun (site kapanır, veri korunur): `$C stop cloudflared`.
   - Hangi sır sızdıysa yenileyin (`openssl rand -hex 32`), `.env.prod`'a yazın ve uygulayın:
     | Sır | Yenileme |
     |---|---|
     | `JWT_SECRET` | `.env.prod` → `$C up -d api` (tüm erişim token'ları geçersiz). Oturumları da kapatmak için önce `make backup-now`, sonra `$C exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DELETE FROM refresh_tokens"'` |
     | `APP_DB_PASSWORD`, `MONITOR_DB_PASSWORD` | `.env.prod` → `bash infra/pc/deploy.sh <çalışan sürüm>` (roller yeni şifreyle güncellenir) |
     | `POSTGRES_PASSWORD` | `$C exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` içinde `\password`, sonra `.env.prod` |
     | `REDIS_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` | `.env.prod` → `$C up -d` |
     | `TUNNEL_TOKEN` | Cloudflare Zero Trust → Networks → Tunnels → tünel → token'ı yenile; `.env.prod` → `$C up -d cloudflared` |
     | `RESTIC_PASSWORD` / B2 anahtarı | B2'de anahtarı iptal edip yenisini oluşturun; restic için `restic key add` + `restic key remove` (`infra/backup/README.md`) |
     | Yönetim paneli | Cloudflare Access politikası "ekip"ten şüpheli e-postayı çıkarın; `make prod-admin EMAIL=… REVOKE=--revoke` |
   - Parola yöneticisindeki `.env.prod` kaydını güncelleyin (felaket-kurtarma.md 0. adım).
2. **Kanıtı koru:** logları silmeyin. Loki 14 gün tutar; ilgili aralığı Grafana → Explore'dan dışa aktarın. Yönetim paneli işlemleri `audit_logs` tablosunda (sadece eklenebilir).
3. **Etki analizi (ilk 24 saat):** hangi veri (yukarıdaki liste), kaç kişi (`SELECT count(*) FROM users`), hangi zaman aralığında, veri gerçekten dışarı çıktı mı. Sonucu yazılı not edin.
4. **Bildirim:**
   - Danışman hoca ve üniversite: hemen (etki analizi bitmeden de).
   - **KVK Kurulu: öğrenildiği andan itibaren en geç 72 saat içinde**, Kurul'un internet sitesindeki "Veri İhlali Bildirim Formu" ile. Bilgiler eksikse eldekiyle bildirilir, sonra tamamlanır.
   - Etkilenen kullanıcılar: makul en kısa sürede, kayıtlı e-postalarına; ne oldu, hangi veri, ne yaptık, onlar ne yapmalı (ör. aynı parolayı başka yerde kullanıyorsa değiştirsin).
5. **Sonrası:** kök neden ve alınan önlem `docs/kararlar.md`'ye; ilgili kod düzeltmesi PR ile. Tünel kapatıldıysa düzeltme sonrası `$C start cloudflared`.

---

**Bakım:** bu dosya her prosedür değişikliğinde (yeni servis, yeni sır, yeni uyarı kuralı) aynı PR'da güncellenir. Ekip okuduğunu go-live #44 için onaylar.
