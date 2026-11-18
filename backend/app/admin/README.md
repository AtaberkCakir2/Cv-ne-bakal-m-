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

1. Cloudflare paneli → **Zero Trust** → **Access** → **Applications** → **Add an application** → **Self-hosted**.
2. **Application name:** `Cv'ne Bakalım! admin`. **Session duration:** 8 hours.
3. **Add public hostname:** Subdomain `api`, Domain `cvnebakalim.com`, Path `admin`.
4. **Policy:** ad `ekip`, Action **Allow**, Include → **Emails**: ekip üyelerinin e-postaları.
5. **Login methods:** **One-time PIN** (e-postaya kod gelir; ayrıca hesap gerekmez).
6. Kaydedin. **Kontrol:** gizli pencerede `https://api.cvnebakalim.com/admin/login` açılınca panel değil Cloudflare'in e-posta ekranı gelmeli. `https://api.cvnebakalim.com/api/v1/health` ise eskisi gibi doğrudan açılmalı.

Ücretsiz plan 50 kullanıcıya kadar yeterlidir.

## Testler

`backend/tests/auth/test_admin_panel.py` (gerçek PostgreSQL ister; Docker açıksa testcontainers kurar).
