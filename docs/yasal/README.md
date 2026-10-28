# Yasal metinler (T-065) — TASLAK

Bu klasördeki metinler **taslaktır** ve hukuki görüş değildir. Yayına almadan önce danışman ve üniversitenin hukuk birimi kontrol etmelidir (T-065 kabul kriteri). Metinler `docs/veritabani.md`, `docs/kararlar.md` ve `docs/go-live.md`'de yazan veri işleme biçimine göre hazırlandı. Sistem değişirse (yeni tablo, yeni hizmet sağlayıcı, farklı saklama süresi) metin de aynı PR'da güncellenmelidir.

| Dosya | Ne için | Uygulamadaki karşılığı |
|---|---|---|
| [aydinlatma-metni.md](aydinlatma-metni.md) | KVKK md. 10 aydınlatma yükümlülüğü | `consents.consent_type = kvkk_aydinlatma` |
| [acik-riza.md](acik-riza.md) | CV analizi için açık rıza | `acik_riza` |
| [kullanim-kosullari.md](kullanim-kosullari.md) | Hizmet sözleşmesi | `kullanim_kosullari` |
| [gizlilik-politikasi.md](gizlilik-politikasi.md) | Herkese açık özet; mağazaların istediği gizlilik URL'si | Onay alınmaz, link verilir |

## Sürümleme

Her metnin başında bir sürüm satırı var (`Sürüm: 2026-12-taslak`). Kullanıcının onayladığı sürüm `consents.version` sütununa yazılır. Metin değişince sürüm değişir ve kullanıcıdan yeni sürüm için tekrar onay alınır; eski onay satırı silinmez. Web kayıt ekranındaki sabit (`CONSENT_VERSION`, `web/src/pages/auth/RegisterPage.tsx`) yayın sürümüyle aynı olmalı.

## Yayından önce kesinleşmesi gerekenler

Metinlerde `[…]` ile işaretli yerler. Ölçülmemiş veya kararlaştırılmamış bilgi metne yazılmaz.

1. **Veri sorumlusu kim?** Ekip üyeleri mi (gerçek kişiler), üniversite mi? İletişim adresi ve başvuru e-postası buna göre yazılır. Danışmana sorulacak ilk soru bu.
2. **Sunucunun ve hizmet sağlayıcıların ülkesi.** VPS, sunucu dışı yedek deposu, e-posta gönderim servisi ve hata izleme (Sentry) yurt dışındaysa bu, KVKK md. 9 kapsamında **yurt dışına aktarım**dır ve ayrıca değerlendirilmelidir: yeterlilik kararı veya uygun güvence (ör. standart sözleşme; imzadan sonra Kurum'a 5 iş günü içinde bildirim, teyit edilmeli). 2024 değişikliğinden sonra düzenli aktarımda açık rıza tek başına dayanak olmaz. Mümkünse Türkiye'de veya aktarım gerektirmeyen sağlayıcı seçmek metni ve süreci sadeleştirir. Ataberk (altyapı) ile netleştirilecek.
3. **Açık rıza zorunlu tutulabilir mi?** Taslaklar CV analizi için "sözleşmenin ifası"nı (md. 5/2-c) varsayıyor; `acik-riza.md` sadece alternatif. Kayıt ekranı (`RegisterPage.tsx`) ise şu an üç onayı da zorunlu istiyor; karar çıkınca ekran buna göre değişir (Anıl). KVK Kurulu'nun yaklaşımına göre açık rıza hizmetin ön şartı yapılamaz ("bağlı rıza"); aydınlatma metni de "onay" değil "okudum" bildirimidir. Önerilen düzen:
   - Kayıtta: aydınlatma metni okundu bildirimi + kullanım koşulları kabulü.
   - CV yükleme ekranında: CV analizine açık rıza (ayrı kutu; verilmezse analiz başlamaz ama hesap kullanılabilir). Rıza geri alınabilir olmalı.
   - Alternatif: CV analizini hizmetin kendisi saymak ve hukuki sebebi "sözleşmenin ifası" (md. 5/2-c) yapmak; o zaman açık rıza sadece özel nitelikli veri ihtimali için gerekir. Hangisi seçilirse `docs/kararlar.md`'ye yazılmalı.
4. **Özel nitelikli veri.** CV'lerde fotoğraf, sağlık, din, dernek üyeliği gibi özel nitelikli veriler bulunabilir. Bunlar maskeleme ve yetkinlik çıkarımı dışında işlenmez ve saklanmaz; yine de metin kullanıcıyı CV'ye bu tür bilgi koymaması yönünde uyarıyor. Burak'ın PII maskeleme modülü (T-030) hangi alanları maskeliyorsa metindeki liste onunla aynı olmalı. md. 6 için "yeterli önlemler" (Kurul Kararı 2018/10: erişim yetkisi, şifreleme, kayıt tutmama) uygulanmalı; teyit edilmeli.
   - **"CV kalıcı olarak saklanmaz" sözünün kodda karşılığı olmalı:** CV baytları API'den worker'a Redis kuyruğuyla gidiyorsa Redis kalıcılığı kapalı olmalı (`save ""`, `appendonly no`) veya CV kuyruğa konmamalı; FastAPI `UploadFile` 1 MB üstünü geçici dosyaya yazar, OCR/PyMuPDF de geçici dosya kullanabilir (tmpfs veya kesin silme). Anıl (T-038/T-039), Burak (`ai/`) ve Ataberk (Redis ayarı) doğrulayacak.
   - **Hata izleme:** Sentry'de `send_default_pii=False` ve istek gövdesini/hata mesajındaki CV parçalarını temizleyen `before_send` olmalı (go-live #24).
   - **Süresi dolan oturum kayıtları** (`refresh_tokens`) için temizlik işi yok; metindeki [X] gün buna göre yazılacak.
5. **Yedek saklama süresi.** Silinen hesabın verisi veritabanından 30 gün sonra kalıcı silinir, ama şifreli yedeklerde yedek saklama süresi dolana kadar kalır. restic saklama politikası (ör. 30 gün) belirlenip metne yazılmalı.
6. **VERBİS.** Küçük ölçekli ve ana faaliyeti özel nitelikli veri işlemek olmayan veri sorumluları Kurul kararıyla kayıttan muaf tutulabiliyor (2018/87 ve sonraki değişiklikler; çalışan sayısı ve bilanço eşikleri değişti). Güncel karar kvkk.gov.tr'den teyit edilmeli, sonuç `docs/kararlar.md`'ye yazılmalı. Muafiyet aydınlatma, güvenlik ve silme yükümlülüklerini kaldırmaz.
6a. **Google Play:** Data safety formunda uygulama dışından erişilebilen bir hesap silme bağlantısı istenir; `/yasal/hesap-silme` sayfası (giriş gerektirmeyen talep formu veya talimat) yapılmalı. Form, gizlilik politikasıyla birebir uyumlu doldurulur.
7. **Yaş sınırı.** Hedef kitle üniversite öğrencisi; kullanım koşulları 18 yaş sınırı koyuyor. Farklı karar alınırsa (ör. 16+ ve veli onayı) metinler değişir.

## Uygulamaya aktarma

Metinler kesinleşince web arayüzünde `/yasal/aydinlatma`, `/yasal/acik-riza`, `/yasal/kullanim-kosullari`, `/yasal/gizlilik` sayfaları olarak yayımlanır (Anıl, T-065). Gizlilik politikası giriş yapmadan açılabilmeli; Play Console'a bu URL girilir (go-live #42). Mobil uygulama aynı URL'lere link verir.
