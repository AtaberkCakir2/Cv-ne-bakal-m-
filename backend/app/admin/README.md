# Yönetim paneli (T-063)

Sahibi: Ataberk. FastAPI uygulamasının içinde, `/admin` altında çalışan [SQLAdmin](https://aminalaee.github.io/sqladmin/) paneli.

| Ekran | Ne yapılır |
|---|---|
| İstatistikler | Aktif ilan, son 7 günde eklenen ilan, kaynak başına ilan ve son toplama, yayındaki/kırık kaynak, 3'ten az kaynaklı yetkinlik, son 24 saat ve 7 günün analiz durumları, kullanıcı sayısı |
| Kaynaklar | Eğitim kaynağı ekleme ve düzenleme (sadece `https://` bağlantı). Silme yok: kaynak geçmiş önerilere bağlı, kaldırmak için **Yayında** kapatılır |
| İlan kaynakları | Aç/kapa ve istek aralığı. Kullanım şartları incelenmemiş (`tos_checked = false`) kaynak açılamaz. Panelden yeni kaynak eklenemez, kaynak silinemez (silmek ilanlarını da siler) |
| Toplama çalışmaları | Gece toplamalarının listesi ve hata kayıtları, sadece okuma |

Kişisel veri ekranı yok: kullanıcılar, analizler, CV özetleri ve rızalar panelde gösterilmez (karar #5, KVKK).

## Güvenlik

- **Sadece `role = admin`.** Giriş uygulamadaki e-posta ve paroladır. Admin olmayan kullanıcı "Invalid credentials" alır, böylece hangi e-postanın admin olduğu belli olmaz. Rol her istekte veritabanından okunur; rolü geri alınan kişi bir sonraki tıklamada dışarı atılır.
- **Varsayılan admin hesabı yok** (go-live #14). Admin yapmak için aşağıdaki komut kullanılır.
- **Oturum çerezi:** `careerai_admin`, `path=/admin`, `SameSite=Strict`, `HttpOnly`, production ve staging'de `Secure`. Ömrü 8 saattir. İmza anahtarı `JWT_SECRET`'ten türetilir; ayrı bir sır yok.
- **Giriş denemesi sınırı:** IP başına dakikada `RATE_LIMIT_AUTH_PER_MINUTE` (varsayılan 10). Genel istek sınırı da geçerlidir.
- **Denetim kaydı:** girişler (`admin.login`), paneldeki her ekleme ve düzenleme (`admin.create`, `admin.update`) ve rol değişiklikleri (`admin.grant`, `admin.revoke`) `audit_logs`'a yazılır.
- **İkinci kilit, production:** `/admin` yolu tünelde Cloudflare Access ile korunur. Önce ekip e-postasına gelen kodla Cloudflare girişi, sonra panelin kendi girişi yapılır. Kurulum aşağıda.
- **Access belgesi panelde de doğrulanır** (`access.py`): Cloudflare, Access'ten geçen isteğe imzalı `Cf-Access-Jwt-Assertion` ekler; panel imzayı (Cloudflare'in açık anahtarları), AUD ve yayıncıyı kontrol eder, yoksa **403**. Access ayarı bozulsa veya atlatılsa da panel kapalı kalır. Ayar `infra/pc/.env.prod`'da `CF_ACCESS_TEAM_DOMAIN` ve `CF_ACCESS_AUD`; production'da boşsa panel **503** döner (kilit sessizce kalkmasın). Yerel/test/provada ayar yoksa kontrol yapılmaz. Sonuç: production panele sadece tünelden girilir; `compose.local.yml` ile `127.0.0.1`'den açılan api'de `/admin` 403 verir.

## Admin yapmak

Kişi önce uygulamadan normal kayıt olur ve parolasını kendisi belirler. Sonra:

```bash
# yerelde (backend/ klasöründe, .env'deki veritabanı)
python -m app.admin.promote ad@ornek.com
python -m app.admin.promote ad@ornek.com --revoke

# production (bu PC)
make prod-admin EMAIL=ad@ornek.com
```

## Cloudflare Access (production, bir kez)

**Durum: kuruldu (18.11.2026, Ataberk).** Zero Trust ekip adı `old-firefly-f6cd` (Free plan). Değiştirmek için: Cloudflare → Zero Trust → Access controls → Applications → `Cv'ne Bakalım! admin`.

| Ayar | Değer |
|---|---|
| Uygulama | Self-hosted, ad `Cv'ne Bakalım! admin` |
| Korunan adres | `api.cvnebakalim.com/admin` (alt yollar dahil) |
| Politika | `ekip`, Allow, Include → Emails: üç ekip üyesinin e-postası |
| Giriş yöntemi | Cloudflare (e-postaya tek kullanımlık kod) |
| Oturum | 6 saat (panelde 8 saat seçeneği yok) |

Yeni ekip üyesi: `ekip` politikasına e-postası eklenir, sonra `make prod-admin EMAIL=…`.

### Kodlanmış eğik çizgi kuralı (WAF)

Access yolu `/admin` ile karşılaştırır, ama uvicorn `%2F`'yi `/`'ye çevirir: `/admin%2Flogin` Access'e takılmadan panelin giriş sayfasına ulaşıyordu (18.11.2026'da denendi). Bu yüzden alan adında bir WAF özel kuralı var: Security → Security rules → `Kodlanmış eğik çizgi engeli (admin Access atlatma)`, eylem **Block**:

```
(http.host eq "api.cvnebakalim.com" and (raw.http.request.uri.path contains "%2F" or raw.http.request.uri.path contains "%2f" or raw.http.request.uri.path contains "%5C" or raw.http.request.uri.path contains "%5c"))
```

API'nin hiçbir yolu `%2F`/`%5C` kullanmaz (slug'larda `/` yok). Bu kural silinirse Access atlatılabilir.

### Kontrol (değişiklikten sonra)

```bash
for p in /admin/login /ADMIN/login /%61dmin/login //admin/login /admin%2Flogin /admin%5Clogin /api/v1/health; do
  printf "%-18s " "$p"; curl -s -o /dev/null --path-as-is -w "%{http_code}
" "https://api.cvnebakalim.com$p"
done
```

Beklenen: `/admin…` varyantları **302** (Cloudflare giriş ekranı), `%2F`/`%5C` olanlar **403**, `/api/v1/health` **200** (production kapalıysa 530).

Ücretsiz plan 50 kullanıcıya kadar yeterlidir.

## Testler

`backend/tests/auth/test_admin_panel.py` (gerçek PostgreSQL ister; Docker açıksa testcontainers kurar).
