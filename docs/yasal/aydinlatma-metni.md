# CareerAI Kişisel Verilerin İşlenmesine İlişkin Aydınlatma Metni

**Sürüm:** 2026-12-taslak · **Yürürlük:** [yayın tarihi]

> TASLAK — hukuki inceleme bekliyor. Açık noktalar: [README](README.md).

Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu'nun ("KVKK") 10. maddesi uyarınca, CareerAI uygulamasını (web, masaüstü ve Android) kullanırken kişisel verilerinizin nasıl işlendiğini açıklar.

## 1. Veri sorumlusu

[Veri sorumlusunun adı / unvanı]
Adres: [adres]
E-posta: [kvkk@alanadi]

CareerAI, [üniversite adı] [bölüm adı] bitirme projesi olarak geliştirilen ücretsiz bir hizmettir.

## 2. Hangi verileri işliyoruz?

| Veri kategorisi | Veriler | Nereden |
|---|---|---|
| Kimlik | Ad soyad (isteğe bağlı) | Siz |
| İletişim | E-posta adresi | Siz |
| Hesap güvenliği | Şifrenizin geri döndürülemez özeti (şifrenin kendisi saklanmaz), oturum kayıtları, oturumun açıldığı tarayıcı/cihaz bilgisi | Siz / sistem |
| İşlem güvenliği | IP adresinizin tuzlanmış özeti (açık IP saklanmaz), işlem kayıtları (giriş, analiz başlatma, hesap silme gibi) | Sistem |
| Onay kayıtları | Onayladığınız metinlerin türü, sürümü, tarihi ve IP adresinin tuzlanmış özeti | Sistem |
| Mesleki bilgi | CV'nizden çıkarılan yetkinlikler ve seviyeleri, seçtiğiniz hedef pozisyon, uyum skoru, size önerilen eğitim kaynakları | CV'niz / sistem |
| Analiz kaydı | Analizin durumu, süresi, hata kodu, kullanılan model sürümü | Sistem |
| Geri bildirim | Analize verdiğiniz puan ve yorum (isteğe bağlı) | Siz |

**CV dosyanızı ve CV'nizin metnini kalıcı olarak saklamıyoruz.** Dosya sadece analiz sırasında işlenir ve analiz biter bitmez silinir; veritabanına, kayıtlara (log) veya yedeklere yazılmaz. Analizden sonra sadece çıkarılan yetkinlikler, dosyanın sayfa sayısı ve dosyanın parmak izi (SHA-256 özeti) hesabınızla ilişkili olarak tutulur; dosya içeriği bu özetten geri elde edilemez.

CV'nizde yer alan ad, telefon, e-posta, adres, T.C. kimlik numarası ve doğum tarihi gibi kişisel veriler, yapay zeka modeline verilmeden önce otomatik olarak maskelenir; otomatik maskelemenin hata payı olabilir. [Liste T-030 ile kesinleşecek.] Analiz, hizmeti barındırdığımız bilgisayarda (Türkiye) çalışan yerel bir yapay zeka modeliyle yapılır; CV'niz OpenAI, Google gibi üçüncü taraf yapay zeka hizmetlerine gönderilmez.

**Lütfen CV'nize sağlık, din, etnik köken, siyasi görüş, dernek/sendika üyeliği gibi özel nitelikli kişisel verileri koymayın; fotoğraf da gerekmez.** Bunlar analiz için gerekmez. Bulunurlarsa da saklanmaz, yetkinlik çıkarımı dışında hiçbir amaçla kullanılmaz.

Verileriniz, uygulama arayüzünden doldurduğunuz formlar ve yüklediğiniz dosya yoluyla ve sistem tarafından otomatik yollarla, elektronik ortamda toplanır.

## 3. Hangi amaçla ve hangi hukuki sebeple?

| Amaç | Hukuki sebep (KVKK md. 5/2) |
|---|---|
| Hesap oluşturma, giriş, şifre sıfırlama, e-posta doğrulama | (c) Sözleşmenin kurulması ve ifası |
| CV analizi: yetkinlik çıkarımı, ilanlarla karşılaştırma, kaynak önerisi, geçmiş analizlerin gösterilmesi | (c) Sözleşmenin kurulması ve ifası [README madde 3: ekip kararı bekliyor] |
| Hesap ve sistem güvenliği, kötüye kullanımın önlenmesi, işlem kayıtları, uygulama hatalarının tespiti | (f) Meşru menfaat |
| Doğrulama ve şifre sıfırlama e-postalarının gönderilmesi | (c) Sözleşmenin kurulması ve ifası |
| Onaylarınızın ispatı, hukuki taleplere cevap | (e) Bir hakkın tesisi, kullanılması veya korunması |
| Hizmet kalitesinin ölçülmesi (puan/yorum, analiz süresi) | (f) Meşru menfaat |

Verileriniz pazarlama, reklam veya profil satışı amacıyla kullanılmaz. Analiz sonuçları bir işe alım kararı vermek için değil, size yol göstermek için üretilir; hiçbir işverenle paylaşılmaz.

## 4. Kimlere aktarılıyor?

Verileriniz satılmaz ve işverenlerle paylaşılmaz.

Uygulama ve veritabanı, proje ekibinden bir üyeye ait, Türkiye'de bulunan bir bilgisayarda çalışır; ayrı bir barındırma şirketi kullanılmaz. Verileriniz sadece hizmeti çalıştırmak için gereken ölçüde şu tedarikçilerle paylaşılır:

| Alıcı | Ne için | Hangi veri | Konum |
|---|---|---|---|
| Cloudflare, Inc. | Alan adı, DNS, HTTPS bağlantısı ve uygulamaya erişim tüneli (Cloudflare Tunnel); tanıtım ve yasal sayfaların yayını (Cloudflare Pages) | Uygulamayla aranızdaki trafiğin tamamı: IP adresiniz, istekleriniz ve yüklediğiniz CV dosyası dahil. Bağlantı şifrelidir; ancak HTTPS Cloudflare'in sunucularında açılıp tünelle yeniden şifrelendiği için içerik aktarım sırasında Cloudflare'in sistemlerinden geçer. Cloudflare bu içeriği hizmet dışında kullanmaz ve saklamaz [Cloudflare'in veri işleme şartlarıyla teyit edilecek]. | ABD; trafik Cloudflare'in size en yakın veri merkezinden geçer |
| Yedek depolama sağlayıcı [Backblaze B2 öngörülüyor; bölge seçilecek] | Şifreli günlük yedek | Veritabanı yedeği (bizim tarafımızda şifrelenir; sağlayıcı içeriği okuyamaz) | [ABD veya AB bölgesi] |
| E-posta gönderim servisi [henüz seçilmedi] | Doğrulama ve şifre sıfırlama e-postaları | E-posta adresi | [ülke] |
| Hata izleme servisi [henüz seçilmedi; kullanılmazsa satır çıkar] | Uygulama hatalarının tespiti | Hata kaydı (mümkün olduğunca kişisel veri içermeyecek şekilde yapılandırılır) | [ülke] |

Yetkili kamu kurum ve kuruluşlarına, kanunen zorunlu olduğu hallerde ve istenen ölçüde aktarılabilir.

Cloudflare ABD merkezli olduğu için bu paylaşım KVKK md. 9 kapsamında yurt dışına aktarımdır. Aktarımın dayanağı: [standart sözleşme / uygun güvence — hukuki inceleme bekliyor]. Yedek ve diğer sağlayıcılar yurt dışındaysa aynı kapsamdadır; sağlayıcı ve ülke yukarıdaki tablodadır.

## 5. Ne kadar süre saklıyoruz?

| Veri | Süre |
|---|---|
| CV dosyası ve CV metni | Saklanmaz (sadece analiz sırasında bellekte) |
| Hesap bilgileri, analiz sonuçları, onay kayıtları | Hesabınız açık olduğu sürece. Hesabınızı sildiğinizde 30 gün sonra kalıcı olarak silinir (onay kayıtları dahil). |
| Tek bir analizi sildiğinizde | 30 gün sonra kalıcı olarak silinir |
| Oturum kayıtları | 7 gün geçerli; süresi dolan kayıtlar en geç [X] gün içinde silinir |
| E-posta doğrulama / şifre sıfırlama bağlantıları | 24 saat / 1 saat geçerli; kullanıldıktan sonra geçersiz |
| İşlem kayıtları | [180 gün: temizlik işi yazılınca]. Hesabınız kalıcı silindiğinde kayıtların hesabınızla bağı koparılır; IP adresinin tuzlanmış özeti bu süre boyunca kayıtta kalabilir ve bu haliyle de kişisel veri sayılır. |
| Şifreli yedekler | En fazla 35 gün (son 7 günün günlük ve son 4 haftanın haftalık yedeği tutulur); silinen veriler, hesabın veya analizin silindiği tarihten itibaren en geç 65 gün içinde yedeklerden de çıkar |

## 6. Haklarınız (KVKK md. 11)

Veri sorumlusuna başvurarak:

- kişisel verilerinizin işlenip işlenmediğini öğrenme ve işlenmişse bilgi talep etme,
- işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme,
- yurt içinde veya yurt dışında aktarıldığı üçüncü kişileri bilme,
- eksik veya yanlış işlenmişse düzeltilmesini isteme,
- KVKK md. 7'deki şartlar çerçevesinde silinmesini veya yok edilmesini isteme,
- düzeltme ve silme işlemlerinin aktarılan üçüncü kişilere bildirilmesini isteme,
- münhasıran otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz etme,
- kanuna aykırı işleme sebebiyle zarara uğramanız halinde zararın giderilmesini talep etme

haklarına sahipsiniz.

Uygulama içinden de: **Profil → Verilerim** bölümünden verilerinizi indirebilir, analizlerinizi silebilir ve hesabınızı silebilirsiniz.

**Başvuru:** Talebinizi kayıtlı e-posta adresinizden [kvkk@alanadi] adresine veya yazılı olarak [adres] adresine iletebilirsiniz. Başvurunuzda adınız soyadınız, tebligat adresiniz veya e-posta adresiniz ve talep konunuz bulunmalıdır. Başvurunuz en geç 30 gün içinde ücretsiz olarak sonuçlandırılır (işlemin ayrıca bir maliyet gerektirmesi halinde Kurul'un belirlediği tarife uygulanabilir). Başvurunuzun reddedilmesi, cevabı yetersiz bulmanız veya süresinde cevap verilmemesi halinde, cevabı öğrendiğiniz tarihten itibaren 30 gün, her halde başvuru tarihinden itibaren 60 gün içinde Kişisel Verileri Koruma Kurulu'na şikâyette bulunabilirsiniz (KVKK md. 14).
