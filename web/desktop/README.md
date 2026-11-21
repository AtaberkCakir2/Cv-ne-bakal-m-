# web/desktop/ — Masaüstü uygulaması (Electron, T-059) — Sahibi: Anıl

Web arayüzünün derlenmiş hâlini (`web/dist`) bir masaüstü penceresinde açar. Ayrı bir arayüz kodu yok: web'de yapılan her değişiklik bir sonraki masaüstü sürümüne girer.

## Nasıl çalışıyor?

- **Adres:** Sayfalar `file://` yerine `app://careerai` adresinden sunulur (`main.cjs` → `serve`). React Router olduğu gibi çalışır, oturum (`localStorage`) bu kökene bağlı kalır. Bilinmeyen yol `index.html`'e düşer; `web/dist` dışına çıkılamaz.
- **Güvenlik (Electron güvenlik kontrol listesi):**
  - `contextIsolation` açık, `nodeIntegration` kapalı, `sandbox` açık. Preload yok; sayfanın Node erişimi yok.
  - CSP her yanıtta: betikler sadece uygulamanın kendisinden; tema için olan satır içi betiğe özetle izin verilir. Bağlantılar sadece HTTPS (geliştirmede `127.0.0.1` de).
  - Uygulama dışındaki bağlantılar (kaynak siteleri, ilan kaynakları) sistem tarayıcısında açılır. Yeni pencere ve webview açılamaz.
  - Kamera, mikrofon, konum ve bildirim izinleri reddedilir.
  - Paketli uygulamada Electron Fuses ile `ELECTRON_RUN_AS_NODE`, `NODE_OPTIONS` ve `--inspect` kapalı. Geliştirme adresi (`CAREERAI_DEV_URL`) okunmaz.
- **Güncelleme:** Paketlenmiş uygulama açılışta GitHub Releases'ı kontrol eder (`electron-updater`). Yeni sürümü indirir ve uygulama kapanınca kurar. Kayıt dosyası Windows'ta `%APPDATA%/CareerAI/logs/updater.log`, macOS'ta `~/Library/Logs/CareerAI/updater.log`.
  - **Windows:** Çalışır.
  - **macOS:** Squirrel.Mac imzasız uygulamayı güncellemez. Apple Developer imzası ve notarization yapılana kadar Mac kullanıcıları yeni sürümü Releases sayfasından elle indirir. Güncelleme için gereken `zip` hedefi şimdiden üretiliyor.

## Komutlar

```bash
cd web && npm ci && cd desktop   # web'in bağımlılıkları da kurulu olmalı
npm ci
npm run web        # web/dist'i derler (VITE_API_URL derlemeye gömülür)
npm start          # pencereyi açar
npm run smoke      # açar, sayfayı kontrol eder, "SMOKE OK" yazıp kapanır
```

`npm run smoke` şunları denetler:
- ana sayfa çiziliyor mu, derin bir yol (`/giris`) doğrudan açılıyor mu
- sayfada Node erişimi var mı
- `web/dist` dışına çıkılabiliyor mu, CSP her dosyada var mı
- konsolda hata (ör. CSP ihlali) var mı

Arayüz geliştirirken Vite sunucusunu açmak için: `CAREERAI_DEV_URL=http://127.0.0.1:5173 npm start` (önce `web/` içinde `npm run dev`).

## Kurulum dosyası

`VITE_API_URL` zorunlu ve `https://` ile başlamalı; `check-api.cjs` bunu kontrol eder. Verilmezse uygulama sunucuya bağlanamaz.

```bash
VITE_API_URL=https://api.cvnebakalim.com npm run dist:win   # release/CvneBakalim-Setup-<sürüm>.exe (NSIS)
VITE_API_URL=https://api.cvnebakalim.com npm run dist:mac   # release/*.dmg ve *.zip (sadece macOS'ta)
```

PowerShell'de: `$env:VITE_API_URL="https://api.cvnebakalim.com"; npm run dist:win`

- **Sürüm:** `package.json` → `version`. Her yayında artırılır; güncelleme bu numaraya bakar.
- **Yayın:** `release:win` / `release:mac` kurulum dosyasını ve `latest.yml`'yi GitHub Releases'a **taslak** olarak yükler. Bunun için `GH_TOKEN` ortam değişkeni gerekir. Taslak, Releases sayfasında "Publish release" ile yayımlanmadan kullanıcılara güncelleme gitmez; yanlış dosya yüklenirse bu adım bir güvenlik kapısıdır.
- **Güncelleme güvenliği:** İmza olmadığı için güncellemenin bütünlüğü sadece Releases'taki `latest.yml` özetine dayanır. Repoya yazabilen biri tüm kullanıcılara dosya dağıtabilir. Bu yüzden:
  - yayın yetkisi tek kişide olmalı;
  - `GH_TOKEN` sadece bu repo için `contents: write` yetkili, süreli (fine-grained) bir token olmalı.
- **macOS:** `.dmg` ve `.zip` sadece Mac'te üretilebilir. İmzasız uygulama ilk açılışta Gatekeeper uyarısı verir (sağ tık → Aç). Hem Intel (`x64`) hem Apple Silicon (`arm64`) için ayrı `.dmg` ve `.zip` üretilir (`mac.target` → `arch`); kurulum rehberi (`docs/kurulum/masaustu-kurulum.md`) bu dosya adlarını anlatır.
- **Windows:** İmzasız kurulum SmartScreen uyarısı verir ("Ek bilgi → Yine de çalıştır"). Kod imzalama sertifikası bütçede yok.

## Canlıya çıkmadan önce

- **CORS:** Masaüstü uygulamasının istekleri `app://careerai` kökeninden gelir. Backend'in varsayılan listesinde var (`backend/app/core/config.py`); production'da `infra/pc/.env.prod`'daki `CORS_ORIGINS`'e de yazılmalı (ör. `["https://app.cvnebakalim.com","app://careerai"]`). Eksikse giriş ekranı "Sunucuya ulaşılamadı" der.
- **Otomatik güncelleme ve özel repo:** Repo özel olduğu sürece `electron-updater` sürümleri token'sız indiremez. İki seçenek var:
  - Repo yayından önce herkese açık yapılır (fizibilite raporundaki açık kaynak planı).
  - Kurulum dosyaları ayrı, herkese açık bir "releases" reposuna yüklenir ve `package.json` → `build.publish` o repoya çevrilir.
- **Simge:** `resources/icon.png` (1024×1024, şeffaf köşeli). electron-builder Windows `.ico` ve macOS `.icns` dosyalarını bundan üretir. Klasör `build/` değil `resources/`, çünkü kök `.gitignore` `build/`'i yok sayıyor.
