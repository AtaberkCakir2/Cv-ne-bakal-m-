# Production PC'si — kurulum ve kontrol listesi (T-009)

Karar #30: CareerAI için sunucu kiralanmaz. Production Ataberk'in bilgisayarında Docker Compose ile çalışır ve alan adına Cloudflare Tunnel ile bağlanır. Bu dosya PC'nin sunucu gibi çalışması için gerekenleri anlatır. Sırlar (tünel token'ı, şifreler) burada yazmaz; sadece PC'deki `.env` dosyasında durur.

| Özellik | Değer (06.11.2026) |
|---|---|
| Model | Casper Excalibur G770 |
| İşlemci | Intel i7-9750H, 6 çekirdek / 12 iş parçacığı |
| Bellek | 32 GB |
| Ekran kartı | NVIDIA GTX 1650 (4 GB) + Intel UHD 630 |
| Disk | 476 GB SSD, C: üzerinde ~71 GB boş |
| İşletim sistemi | Windows 10 Pro 19045 |
| Pil | Algılanmıyor: elektrik kesilince PC kapanır |

## 1. Güç ve uyku

- [ ] Denetim Masası → Güç Seçenekleri → seçili planın yanında **Plan ayarlarını değiştir**: "Bilgisayarı uyku moduna geçir" → **Hiçbir zaman**.
- [ ] Aynı yerde **Gelişmiş güç ayarlarını değiştir** → Uyku → "Sonra hazırda beklet" → **Hiçbir zaman**.
- [ ] Güç Seçenekleri → sol menü **Kapağı kapatma eyleminin ne yapacağını seçin** → Prize takılı: **Hiçbir şey yapma**.
- [ ] Ekranın kapanması serbesttir (ekran kapalıyken sistem çalışır).

## 2. Windows Update

- [ ] Ayarlar → Güncelleştirme ve Güvenlik → Windows Update → **Etkin saatleri değiştir**: 09:00–23:00.
- [ ] Sunum veya demo haftasında aynı ekrandan **Güncelleştirmeleri 7 gün duraklat**.
- [ ] Ayda bir, sunum olmayan bir günde güncellemeleri elle yükle ve yeniden başlat; sonra 5. bölümdeki kontrolü yap.

## 3. Güvenlik

- [ ] Windows hesabının güçlü bir şifresi var; otomatik oturum açma kapalı.
- [ ] Ayarlar → Güncelleştirme ve Güvenlik → Cihaz şifrelemesi / **BitLocker** C: için açık. Kurtarma anahtarı PC dışında saklanır (repoda değil).
- [ ] Windows Güvenlik Duvarı açık. Modemde port yönlendirme **yok**; dış erişim sadece Cloudflare Tunnel ile.
- [ ] Production compose'da hiçbir servis `ports:` ile host'a açılmaz (`docker compose -p careerai-prod config` ile kontrol).
- [ ] Production `.env` sadece bu PC'de; Windows'ta sadece bu kullanıcı okuyabilir.

## 4. Docker Desktop

- [ ] Docker Desktop → Settings → General → **Start Docker Desktop when you sign in** açık.
- [ ] `%UserProfile%\.wslconfig` dosyası:

  ```ini
  [wsl2]
  memory=20GB
  ```

  Değiştirdikten sonra PowerShell'de `wsl --shutdown`, ardından Docker Desktop'u yeniden başlat.
- [ ] Production servislerinde `restart: unless-stopped` ve `mem_limit` var (`docs/mimari.md` servis tablosu).
- [ ] Docker log rotasyonu: Settings → Docker Engine'de `"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}`.
- [ ] Geliştirme (`careerai`) ve production (`careerai-prod`) ayrı compose projeleridir. Production'a dokunan her komut `-p careerai-prod` ile yazılır. Production açıkken geliştirme ortamının Ollama'sı kapatılır.

## 5. Yeniden başlatma sonrası kontrol

PC her açıldığında (elektrik kesintisi, güncelleme):

1. Windows oturumu aç; Docker Desktop kendisi başlar.
2. `docker compose -p careerai-prod ps`: bütün servisler `healthy`.
3. Tarayıcıda `https://api.cvnebakalim.com/health/ready` açılıyor.
4. Gece toplaması ve yedek kaçtıysa açılışta çalıştığını kontrol et (`scrape_runs` son kaydı; restic snapshots).

## 6. Sunum günü

- [ ] PC prize takılı; mümkünse kablolu internet.
- [ ] Sunumdan 1 saat önce 5. bölümdeki kontrol.
- [ ] B planı: alan adı açılmazsa aynı sistemi sadece bu PC'ye (127.0.0.1) açan ek compose dosyasıyla devam (T-075'te eklenecek; ağdan erişilemez); internet giderse telefondan internet paylaşımı (tünel kendisi yeniden bağlanır).

Ayrıntılı olay adımları: `docs/go-live.md` → Olay prosedürleri.
