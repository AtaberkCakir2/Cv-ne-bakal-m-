# Tanıtım sayfası (T-070)

`cvnebakalim.com` kök adresindeki tanıtım sayfası. Karar #30: PC'den bağımsız, Cloudflare Pages'te; PC kapalıyken de açılır.

| Dosya | İçerik |
|---|---|
| `index.html`, `landing.css`, `favicon.svg` | Sayfa. Saf HTML + CSS, JavaScript yok; renkler `web/src/ui/tokens.css`'ten (uygulamayla aynı, açık/koyu tema) |
| `img/sonuc.png`, `img/telefon.png` | Ekran görüntüleri (sahte CV, E2E ortamı); `ekran-goruntuleri.mjs` üretir |
| `build.sh` | Sayfayı Pages çıktısının köküne koyar |

## Yasal sayfalarla aynı Pages projesi

Kök alan adı tek bir Pages projesine bağlanır. Yasal metinler (Anıl, T-065, `web/yasal-site/`) aynı projede alt yollardadır: `/aydinlatma/`, `/gizlilik/`, `/kullanim-kosullari/`, `/hesap-silme/`. Tanıtım sayfası onların derlemesinden sonra köke yazılır (yasal sitenin kendi ana sayfasının yerine). Güvenlik başlıkları (`_headers`, sıkı CSP: sadece aynı kökenden stil ve görsel) yasal site derlemesinden gelir; o yoksa `build.sh` aynısını yazar. Sayfa bu yüzden satır içi stil, betik ve dış kaynak kullanmaz.

**Cloudflare Pages ayarı** (Workers & Pages → Create → Pages → Connect to Git → bu repo):

| Ayar | Değer |
|---|---|
| Production branch | `main` |
| Build command | `cd web && npm ci && npm run build:yasal && cd .. && bash infra/landing/build.sh` |
| Build output directory | `web/yasal-site/dist` |
| Ortam değişkenleri | `NODE_VERSION=22`, `APP_URL=https://app.cvnebakalim.com` |
| Custom domains | `cvnebakalim.com` (ve `www` → kök yönlendirmesi) |

Yasal site (`web/yasal-site`, #71) main'e girmeden önce sadece tanıtım sayfası denenecekse: Build command `bash infra/landing/build.sh dist`, output `dist` (yasal bağlantılar o zaman 404).

## Yerelde bakmak

```bash
bash infra/landing/build.sh /tmp/landing && start /tmp/landing/index.html    # Git Bash
```

## Ekran görüntülerini yenilemek

Arayüz değişince. Sahte kullanıcı ve sahte CV ile, E2E ortamında (`tests/e2e/README.md`):

```bash
bash tests/e2e/ortam.sh up
(cd web && VITE_API_URL=http://127.0.0.1:8000 npm run build && npx vite preview --host 127.0.0.1 --port 5173) &
node infra/landing/ekran-goruntuleri.mjs
bash tests/e2e/ortam.sh down
```

Örnek analiz (ENVIRONMENT=test) sözleşme örneğindeki eksik yetkinlikleri yazar; örnekteki kaynak kimlikleri veri tabanında olmadığı için betik her eksiğe veri tabanından bir kaynak ekler (sadece E2E veri tabanında).

## Metin değişince

İddialar gerçek davranışla aynı kalmalı: dosya sınırları (`backend/app/core/uploads.py`), saatlik analiz sınırı, pozisyon sayısı (`scraper/taxonomy/roles.csv`), indirme adresleri (karar #36, `AtaberkCakir2/cvnebakalim-surumler`). Android bağlantısı Play'de yayına girince (T-095) eklenir. ESCO atıf cümlesi alt bilgide kalmalı (`scraper/taxonomy/README.md`).
