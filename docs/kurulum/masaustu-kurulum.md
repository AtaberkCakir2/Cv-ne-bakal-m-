# Masaüstü uygulamasını kurma (Windows ve macOS)

Cv'ne Bakalım! masaüstü uygulaması, web sitesiyle aynı hesabı ve aynı ekranları kullanır. Tarayıcıdan kullanmak istiyorsanız kurulum gerekmez.

> **Neden uyarı çıkıyor?** Uygulama ücretli bir kod imzalama sertifikasıyla imzalanmadı (bitirme projesi bütçesinde yok). Windows ve macOS, imzasız uygulamaları ilk açılışta "tanınmayan uygulama" diye uyarır. Uyarı, uygulamada virüs bulunduğu anlamına gelmez. Yine de dosyayı **sadece aşağıdaki resmi indirme adresinden** indirin ve isterseniz §3'teki gibi doğrulayın.

Resmi indirme adresi: _(sürüm yayın yeri kesinleşince eklenecek, karar #36)_

## 1. Windows 10 / 11

1. `CvneBakalim-Setup-<sürüm>.exe` dosyasını indirin.
2. Dosyayı açın. **"Windows bilgisayarınızı korudu"** penceresi çıkarsa **Ek bilgi**'ye, sonra **Yine de çalıştır**'a tıklayın.
   - Tarayıcı indirmeyi "yaygın olarak indirilmiyor" diye engellerse indirilenler listesinde dosyanın menüsünden **Sakla** seçeneğini seçin.
3. Kurulum yalnızca sizin kullanıcı hesabınıza yapılır, yönetici şifresi istemez. İsterseniz kurulum klasörünü değiştirebilirsiniz.
4. Kurulum bitince uygulama Başlat menüsünde **Cv'ne Bakalım!** adıyla bulunur.

**Güncelleme:** Uygulama açılışta yeni sürüm olup olmadığına bakar. Yeni sürüm varsa arka planda indirir ve uygulamayı kapattığınızda kurar. Sizin bir şey yapmanız gerekmez.

**Kaldırma:** Ayarlar → Uygulamalar → **Cv'ne Bakalım!** → Kaldır. Bu işlem bilgisayardaki oturum bilgisini de siler. **Hesabınız ve analizleriniz silinmez.** Hesabınızı silmek için uygulamada veya web sitesinde **Profil → Hesabını sil** adımlarını izleyin.

## 2. macOS

1. `CvneBakalim-<sürüm>-<mimari>.dmg` dosyasını indirin. Apple Silicon (M1 ve sonrası) için `arm64`, Intel işlemcili Mac için `x64` dosyasını seçin. Hangisinin sizde olduğunu **Apple menüsü → Bu Mac Hakkında** ekranında görebilirsiniz.
2. `.dmg` dosyasını açın ve uygulamayı **Uygulamalar** (Applications) klasörüne sürükleyin.
3. İlk açılışta "geliştiricisi doğrulanamadığı için açılamıyor" uyarısı çıkar:
   - Uygulamalar klasöründe uygulamaya **sağ tıklayın (veya Control + tık) → Aç**, açılan pencerede yine **Aç**'a tıklayın.
   - Bu seçenek görünmüyorsa (yeni macOS sürümleri): **Sistem Ayarları → Gizlilik ve Güvenlik** sayfasının altındaki uyarıda **Yine de Aç**'a tıklayın ve onaylayın.
4. Bu adım bir kez yapılır; sonraki açılışlarda uyarı çıkmaz.

**Güncelleme:** macOS imzasız uygulamaların kendiliğinden güncellenmesine izin vermez. Yeni sürüm çıktığında `.dmg` dosyasını indirip uygulamayı Uygulamalar klasöründekinin üzerine sürükleyin. Oturumunuz ve ayarlarınız korunur.

**Kaldırma:** Uygulamayı Uygulamalar klasöründen Çöp Sepeti'ne sürükleyin. Hesabınızı silmek için yukarıdaki **Profil → Hesabını sil** notuna bakın.

## 3. İndirilen dosyayı doğrulama (isteğe bağlı)

Her sürümün indirme sayfasında dosyaların SHA-256 özeti yazar. Bilgisayarınızda hesaplanan özet sayfadakiyle aynıysa dosya yolda değişmemiştir.

- **Windows (PowerShell):** `Get-FileHash .\CvneBakalim-Setup-<sürüm>.exe -Algorithm SHA256`
- **macOS (Terminal):** `shasum -a 256 ~/Downloads/CvneBakalim-<sürüm>-<mimari>.dmg`

Özetler farklıysa dosyayı açmayın, `iletisim@cvnebakalim.com` adresine bildirin.

## 4. Sorun giderme

| Belirti | Ne yapılmalı |
|---|---|
| Giriş ekranında "Sunucuya ulaşılamadı" | İnternet bağlantınızı kontrol edin. Sorun sürüyorsa sunucu geçici olarak kapalı olabilir. Web sitesinin açılıp açılmadığına bakın, açılmıyorsa bir süre sonra tekrar deneyin. |
| Antivirüs programı dosyayı karantinaya aldı | İmzasız uygulamalarda olabilir. Dosyayı §3'teki gibi doğrulayın, eşleşiyorsa antivirüste istisna ekleyin. Emin değilseniz uygulamayı web sitesinden kullanın. |
| Windows'ta güncelleme gelmiyor | Uygulamayı tamamen kapatıp yeniden açın. Güncelleme kaydı `%APPDATA%\CareerAI\logs\updater.log` dosyasındadır; hata bildirirken bu dosyayı ekleyebilirsiniz. |
| Başka bir sorun | Uygulamanın altındaki **Hata bildir** bağlantısını kullanın. |

---

_Ekip için:_ Teknik ayrıntılar (derleme, yayın, güvenlik) [`web/desktop/README.md`](../../web/desktop/README.md) dosyasındadır. Her sürüm yayımlanırken indirme sayfasına dosya adları ve SHA-256 özetleri eklenir (T-089). Bu metin yasal site üretildikten sonra (`web/yasal-site`, #71) indirme sayfası olarak da yayımlanabilir.
