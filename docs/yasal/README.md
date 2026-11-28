# Yasal metinler (T-065) — TASLAK

Bu klasördeki metinler **taslaktır** ve hukuki görüş değildir. Yayına almadan önce danışman ve üniversitenin hukuk birimi kontrol etmelidir (T-065 kabul kriteri). Metinler `docs/veritabani.md`, `docs/kararlar.md` ve `docs/go-live.md`'de yazan veri işleme biçimine göre hazırlandı. Sistem değişirse (yeni tablo, yeni hizmet sağlayıcı, farklı saklama süresi) metin de aynı PR'da güncellenmelidir.

| Dosya | Ne için | Uygulamadaki karşılığı |
|---|---|---|
| [aydinlatma-metni.md](aydinlatma-metni.md) | KVKK md. 10 aydınlatma yükümlülüğü | `consents.consent_type = kvkk_aydinlatma` |
| [acik-riza.md](acik-riza.md) | CV analizi için açık rıza | `acik_riza` |
| [kullanim-kosullari.md](kullanim-kosullari.md) | Hizmet sözleşmesi | `kullanim_kosullari` |
| [gizlilik-politikasi.md](gizlilik-politikasi.md) | Herkese açık özet; mağazaların istediği gizlilik URL'si | Onay alınmaz, link verilir |
| [hesap-silme.md](hesap-silme.md) | Uygulama dışından hesap silme yolu (Google Play şartı) | Onay alınmaz, link verilir |

## Sürümleme

Her metnin başında bir sürüm satırı var (`Sürüm: 2026-12-taslak`). Kullanıcının onayladığı sürüm `consents.version` sütununa yazılır. Metin değişince sürüm değişir ve kullanıcıdan yeni sürüm için tekrar onay alınır; eski onay satırı silinmez. Web'deki sabit (`CONSENT_VERSION`, `web/src/auth/consents.ts`; #72 ile, öncesinde `RegisterPage.tsx`) yayın sürümüyle aynı olmalı.

## Yayından önce kesinleşmesi gerekenler

Metinlerde `[…]` ile işaretli yerler. Ölçülmemiş veya kararlaştırılmamış bilgi metne yazılmaz.

1. **Veri sorumlusu kim?** Ekip üyeleri mi (gerçek kişiler), üniversite mi? İletişim adresi ve başvuru e-postası buna göre yazılır. Danışmana sorulacak ilk soru bu.
2. **Hizmet sağlayıcıların ülkesi.** Karar #30 ile uygulama ekip üyesinin Türkiye'deki bilgisayarında çalışıyor; barındırma şirketi yok. Ama trafiğin tamamı (CV dosyası dahil) Cloudflare (ABD) üzerinden geçiyor ve HTTPS orada açılıyor: bu kesin olarak **yurt dışına aktarım**. Metinlere böyle yazıldı, dayanak boş bırakıldı. Yedek deposu Backblaze B2'nin AB bölgesinde (EU Central, Amsterdam; şirket ABD merkezli, Ataberk 27.11.2026); e-posta gönderim servisi de yurt dışındaysa aynı kapsamda. Dış hata izleme servisi kullanılmıyor (karar #32). Bu, KVKK md. 9 kapsamında **yurt dışına aktarım**dır ve ayrıca değerlendirilmelidir: yeterlilik kararı veya uygun güvence (ör. standart sözleşme; imzadan sonra Kurum'a 5 iş günü içinde bildirim, teyit edilmeli). 2024 değişikliğinden sonra düzenli aktarımda açık rıza tek başına dayanak olmaz. Cloudflare için veri işleme şartları (DPA) ve standart sözleşme seçeneği danışmanla değerlendirilmeli; diğer sağlayıcılar Ataberk (altyapı) ile netleştirilecek.
3. **Açık rıza zorunlu tutulabilir mi?** Taslaklar CV analizi için "sözleşmenin ifası"nı (md. 5/2-c) varsayıyor; `acik-riza.md` sadece alternatif. Kayıt ekranı (`RegisterPage.tsx`) ise şu an üç onayı da zorunlu istiyor; karar çıkınca ekran buna göre değişir (Anıl). KVK Kurulu'nun yaklaşımına göre açık rıza hizmetin ön şartı yapılamaz ("bağlı rıza"); aydınlatma metni de "onay" değil "okudum" bildirimidir. Önerilen düzen:
   - Kayıtta: aydınlatma metni okundu bildirimi + kullanım koşulları kabulü.
   - CV yükleme ekranında: CV analizine açık rıza (ayrı kutu; verilmezse analiz başlamaz ama hesap kullanılabilir). Rıza geri alınabilir olmalı.
   - Alternatif: CV analizini hizmetin kendisi saymak ve hukuki sebebi "sözleşmenin ifası" (md. 5/2-c) yapmak; o zaman açık rıza sadece özel nitelikli veri ihtimali için gerekir. Hangisi seçilirse `docs/kararlar.md`'ye yazılmalı.
4. **Özel nitelikli veri.** CV'lerde fotoğraf, sağlık, din, dernek üyeliği gibi özel nitelikli veriler bulunabilir. Bunlar maskeleme ve yetkinlik çıkarımı dışında işlenmez ve saklanmaz; yine de metin kullanıcıyı CV'ye bu tür bilgi koymaması yönünde uyarıyor. Burak'ın PII maskeleme modülü (T-030) hangi alanları maskeliyorsa metindeki liste onunla aynı olmalı. md. 6 için "yeterli önlemler" (Kurul Kararı 2018/10: erişim yetkisi, şifreleme, kayıt tutmama) uygulanmalı; teyit edilmeli.
   - **"CV kalıcı olarak saklanmaz" sözünün kodda karşılığı olmalı:** CV baytları API'den worker'a Redis kuyruğuyla gidiyorsa Redis kalıcılığı kapalı olmalı (`save ""`, `appendonly no`) veya CV kuyruğa konmamalı; FastAPI `UploadFile` 1 MB üstünü geçici dosyaya yazar (tmpfs veya kesin silme). AI tarafı doğrulandı (Burak, 27.11.2026): `ai/parsing` PDF'i bellekten açar (pdfplumber `io.BytesIO`, PyMuPDF `stream=`), diske geçici dosya yazılmaz; OCR (T-029) birleşince yeniden doğrulanacak. CV Redis'i kalıcılığı kapalı ayrı bir Redis (`--save ""`, `--appendonly no`, `/data` tmpfs; Ataberk); production'a analiz işçisiyle aynı ayarla gelecek. `UploadFile` kısmı Anıl'da (T-038/T-039).
   - **Hata izleme:** Dış servis kullanılmıyor (karar #32: Sentry ve bilgisayar dışı izleyici yok); metinlerden çıkarıldı. Kullanılmaya başlanırsa `send_default_pii=False` ve CV parçalarını temizleyen `before_send` gerekir, metinler de güncellenir.
   - **Süresi dolan oturum kayıtları** (`refresh_tokens`) için temizlik işi yok; metindeki [X] gün buna göre yazılacak.
   - **İşlem kayıtları** (`audit_logs`) için 180 günlük temizlik işi de henüz yok; metinlerde 180 gün `[180 gün: temizlik işi yazılınca]` diye işaretli. İş yazılınca işaret kaldırılır.
   - **Disk şifrelemesi** (R-17'deki BitLocker önlemi) henüz teyit edilmedi; gizlilik politikasında işaretli.
5. **Yedek saklama süresi.** Silinen hesabın verisi veritabanından 30 gün sonra kalıcı silinir, ama şifreli yedeklerde yedek saklama süresi dolana kadar kalır. T-068'deki (#57) restic politikası 7 günlük + 4 haftalık yedek tutuyor, yani en eski yedek en fazla 35 günlük. Metinlere "hesabın kapatılmasından en geç 65 gün" yazıldı. Bu ancak şu koşullarla doğru: her çalıştırmada `restic forget --prune` (#57'de var) ve B2 kovasında yaşam döngüsü kuralı "sadece son sürümü tut" (B2 varsayılanı silinen dosyaların eski sürümlerini süresiz saklar). Politika değişirse metin de değişmeli.
6. **VERBİS.** Küçük ölçekli ve ana faaliyeti özel nitelikli veri işlemek olmayan veri sorumluları Kurul kararıyla kayıttan muaf tutulabiliyor (2018/87 ve sonraki değişiklikler; çalışan sayısı ve bilanço eşikleri değişti). Güncel karar kvkk.gov.tr'den teyit edilmeli, sonuç `docs/kararlar.md`'ye yazılmalı. Muafiyet aydınlatma, güvenlik ve silme yükümlülüklerini kaldırmaz.
6a. **Google Play:** Data safety formunda uygulama dışından erişilebilen bir hesap silme bağlantısı istenir; [hesap-silme.md](hesap-silme.md) bu iş için (talimat + e-postayla talep). Form, gizlilik politikasıyla birebir uyumlu doldurulur.
7. **Yaş sınırı.** Hedef kitle üniversite öğrencisi; kullanım koşulları 18 yaş sınırı koyuyor. Farklı karar alınırsa (ör. 16+ ve veli onayı) metinler değişir.

## Yayın (Cloudflare Pages)

Karar #30'a göre tanıtım ve yasal sayfalar uygulamanın çalıştığı bilgisayardan bağımsız olarak Cloudflare Pages'te durur; bilgisayar kapalıyken de açılır (go-live #52). Google Play'e gizlilik politikası ve hesap silme adresleri buradan verilir (go-live #42); web, masaüstü ve mobil uygulama da aynı adreslere link verir.

Sayfalar bu klasördeki Markdown dosyalarından üretilir; elle HTML yazılmaz, böylece metin tek yerde kalır:

```bash
cd web
npm run build:yasal   # çıktı: web/yasal-site/dist/
```

| Sayfa | Kaynak |
|---|---|
| `/` | Tanıtım ve sayfa listesi (`web/yasal-site/build.mjs` içinde) |
| `/aydinlatma/` | aydinlatma-metni.md |
| `/gizlilik/` | gizlilik-politikasi.md |
| `/kullanim-kosullari/` | kullanim-kosullari.md |
| `/hesap-silme/` | hesap-silme.md |
| `/acik-riza/` | acik-riza.md (sadece madde 3'te açık rıza seçilirse yayımlanır) |

Dosyalar arasındaki `.md` bağlantıları bu adreslere çevrilir. Metin "TASLAK" satırı içerdiği sürece her sayfanın üstünde taslak uyarısı görünür ve arama motorlarına kapalıdır (`noindex`). Cloudflare Pages ayarı: derleme komutu `cd web && npm ci && npm run build:yasal`, çıktı klasörü `web/yasal-site/dist`, ortam değişkenleri `NODE_VERSION=22` ve `APP_URL` (uygulamanın adresi; varsayılan `https://app.cvnebakalim.com`, alt alan adı Ataberk'le teyit edilecek).

**Yayından önce:** karar #30 kabul edilmiş olmalı (#67); Profil ekranında verileri indirme ve hesap silme düğmeleri bulunmalı, çünkü metinler "Profil → Verilerim / Hesabını sil" yolunu anlatıyor ve Google Play incelemesi bu yolu arar; metinlerde `[…]` kalmamalı.
