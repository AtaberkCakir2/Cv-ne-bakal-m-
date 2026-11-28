# Cv'ne Bakalım! Gizlilik Politikası

**Sürüm:** 2026-12-taslak · **Son güncelleme:** [yayın tarihi]

> TASLAK — hukuki inceleme bekliyor. Bu sayfa giriş yapmadan açılabilmeli; Google Play'e gizlilik politikası URL'si olarak bu sayfa verilir. Ayrıntılı ve bağlayıcı metin [Aydınlatma Metni](aydinlatma-metni.md)'dir; ikisi çelişmemeli.

## Kısaca

- **CV'nizi kalıcı olarak saklamıyoruz.** Dosya sadece analiz sırasında işlenir ve analiz biter bitmez silinir; veritabanına, kayıtlara veya yedeklere yazılmaz.
- **CV'niz yapay zeka şirketlerine gitmiyor.** Analiz, hizmeti barındırdığımız bilgisayarda (Türkiye) çalışan yerel bir modelle yapılır; CV'niz OpenAI, Google gibi üçüncü taraf yapay zeka hizmetlerine gönderilmez. Kişisel bilgileriniz (ad, telefon, e-posta, adres vb.) modele verilmeden önce otomatik olarak maskelenir; otomatik maskelemenin hata payı olabilir.
- **Verilerinizi satmıyoruz, işverenlerle paylaşmıyoruz, reklam göstermiyoruz.**
- **Kontrol sizde.** Verilerinizi indirebilir, analizlerinizi veya hesabınızı istediğiniz an silebilirsiniz.

## Hangi verileri tutuyoruz?

- **Hesap:** e-posta, (isteğe bağlı) ad soyad, şifrenizin geri döndürülemez özeti, hedef pozisyonunuz.
- **Analiz sonuçları:** CV'nizden çıkarılan yetkinlikler, uyum skoru, önerilen kaynaklar, hesabınızla ilişkili olarak CV dosyasının parmak izi (içerik bu özetten geri elde edilemez) ve sayfa sayısı.
- **Güvenlik:** oturum kayıtları, tarayıcı/cihaz bilgisi, IP adresinin tuzlanmış özeti (açık IP tutulmaz), işlem kayıtları.
- **Onaylar:** hangi metni, hangi sürümünü, ne zaman onayladığınız.
- **Geri bildirim:** isteğe bağlı puan ve yorum.

Ayrıntılar, amaçlar ve hukuki sebepler: [Aydınlatma Metni](aydinlatma-metni.md).

## Kimlerle paylaşıyoruz?

Uygulama, proje ekibinden bir üyeye ait, Türkiye'de bulunan bir bilgisayarda çalışır; ayrı bir barındırma şirketi yoktur. Sadece hizmeti çalıştıran tedarikçilerle, gereken ölçüde paylaşıyoruz: alan adı, HTTPS ve erişim tüneli için Cloudflare (ABD; trafiğin tamamı, CV dosyası dahil, Cloudflare üzerinden geçer: HTTPS bağlantısı Cloudflare'de açılıp tünelle yeniden şifrelenir), şifreli yedek depolama için Backblaze B2 (AB, Amsterdam bölgesi; şirket ABD merkezli) ve e-posta gönderim servisi [ad, ülke]. Ayrıntı: [Aydınlatma Metni, bölüm 4](aydinlatma-metni.md#4-kimlere-aktarılıyor).

## YouTube API Hizmetleri

Eksik yetkinlikleriniz için önerilen eğitim videolarının bir kısmı YouTube API Hizmetleri kullanılarak bulunur. Bu arama sunucumuzda, sizden bağımsız olarak yapılır: YouTube'a veya Google'a sizin hesabınız, CV'niz ya da kişisel verileriniz gönderilmez ve YouTube hesabınıza erişmeyiz. Önerilen bir videoyu açtığınızda YouTube'a geçersiniz; orada YouTube'un kendi koşulları geçerlidir. YouTube içeriği kullanıldığı için YouTube Hizmet Şartları (https://www.youtube.com/t/terms) ve Google Gizlilik Politikası (https://policies.google.com/privacy) da uygulanır.

## Çerezler ve cihazda saklanan bilgiler

Reklam, analitik veya izleme çerezi kullanmıyoruz; dış bir hata izleme servisi de kullanılmaz. Web uygulaması tarayıcınızda sadece çalışması için gereken bilgileri saklar:

| Ne | Neden | Ne zaman silinir |
|---|---|---|
| Oturum yenileme anahtarı (localStorage) | Sayfayı yenilediğinizde tekrar giriş yapmanız gerekmesin | Çıkış yaptığınızda silinir; 7 gün sonra geçersiz olur |
| Tema tercihi (localStorage) | Açık/koyu tema seçiminiz hatırlansın | Tarayıcı verilerini temizlediğinizde |

Mobil ve masaüstü uygulamalar aynı bilgileri cihazın güvenli depolamasında tutar.

## Ne kadar saklıyoruz?

Hesabınız açık olduğu sürece. Hesabınızı veya bir analizi sildiğinizde veriler 30 gün sonra kalıcı olarak silinir; şifreli yedeklerden silindiği tarihten itibaren en geç 65 gün içinde çıkar. İşlem kayıtları [180 gün: temizlik işi yazılınca] tutulur.

## Hesabınızı ve verilerinizi silme

Uygulamada **Profil → Hesabını sil**. Uygulamaya erişemiyorsanız [Hesap silme](hesap-silme.md) sayfasındaki adımlarla veya kayıtlı e-posta adresinizden [kvkk@alanadi] adresine yazarak silme isteyebilirsiniz. Hesap bilgileri, analizler ve onay kayıtları 30 gün içinde, işlem kayıtları [180 gün: temizlik işi yazılınca] içinde, yedekler en geç 65 gün içinde silinir; süreler hesabın kapatıldığı tarihten itibaren işler. Tablo halinde: [Aydınlatma Metni, bölüm 5](aydinlatma-metni.md#5-ne-kadar-süre-saklıyoruz).

## Güvenlik

Bağlantılar HTTPS ile şifrelenir. Şifreler argon2id ile özetlenerek saklanır. Oturum anahtarları kısa ömürlüdür ve veritabanında sadece özetleri tutulur. Yedekler şifrelenmiş olarak bu bilgisayarın dışında saklanır. [Disk şifrelemesi teyit edilecek: Bilgisayarın diski şifrelidir.] Uygulamaya erişim yetkisi en az kişiyle sınırlıdır; uygulama internete port açılmadan, sadece şifreli tünel üzerinden erişilebilir. Veri ihlali olursa, ihlalin öğrenilmesinden itibaren en geç 72 saat içinde Kişisel Verileri Koruma Kurulu'na, etkilenen kişilere ise en kısa sürede bildirim yapılır (KVKK md. 12; Kurul Kararı 2019/10).

## Çocuklar

Hizmet 18 yaş ve üzeri kullanıcılar içindir.

## Haklarınız ve iletişim

Veri sorumlusu: [ad / unvan, adres]. KVKK md. 11 kapsamındaki haklarınız ve başvuru yolu: [Aydınlatma Metni, bölüm 6](aydinlatma-metni.md#6-haklarınız-kvkk-md-11). Sorularınız için: [kvkk@alanadi].

## Değişiklikler

Politika değişirse bu sayfada yeni sürüm yayımlanır; önemli değişiklikleri e-postayla veya uygulama içinde bildiririz.
