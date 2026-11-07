# Ara sınav raporu: biçim kuralları ve açık sorular

Teslim: **12 Kasım 2026 saat 13.30**, imza karşılığı, Umut veya Ezgi hocaya (Yaşar hocanın duyurusu).

Kaynak: [İstanbul Nişantaşı Üniversitesi LEE Tez ve Proje Yazım Kılavuzu](https://lee.nisantasi.edu.tr/wp-content/uploads/2024/12/aTEZ-YAZIM-KILAVUZU-2024-1.pdf) (kapak tarihi Eylül 2022, 46 sayfa). Kılavuz lisansüstü tez ve projeler için yazılmış; bitirme raporuna nasıl uygulanacağı duyuruda ayrıntılı değil.

## Dosyalar

- `ara-sinav-raporu.md`: metnin tek kaynağı. Düzeltme buraya yapılır.
- `cikti/CareerAI_Ara_Sinav_Raporu.pdf`: baskıya hazır çıktı.
- `cikti/CareerAI_Ara_Sinav_Raporu.docx`: düzenlenebilir sürüm. Sayfa numaraları dizinlere PDF'ten yazıldı; Word'de düzenlenirse dizinler elle güncellenmeli.
- `img/` ve `diyagram/`: şekiller. Şekil 2 ve 4, 8 punto okunabilsin diye `docs/diagrams/` altındaki tam sürümlerin sadeleştirilmiş halidir; Şekil 4'te `user_tokens`, `analysis_unverified_skills` da var.
- Yeniden üretmek için repo kökünde: `python docs/ara-rapor/uret.py` (pymupdf, python-docx, Chrome gerekir).
- **Basılacak kopya:** öğrenci numaraları kişisel veri olduğu için repoya girmez. Repo dışında bir klasöre `kapak.json` koyun (`{"Ataberk ÇAKIR": "<no>", "Burak DOĞAN": "<no>", "Anıl AKYIL": "<no>"}`) ve `python docs/ara-rapor/uret.py --teslim <klasör>` çalıştırın. Numaralı PDF ve Word o klasöre üretilir. Betik, klasör repo içindeyse durur.

## Hocaya sorulacaklar

1. **Ekler:** Kılavuz örnek kapak, etik beyan ve diğer şablonları Ek 1–24'e bırakıyor ama yayımlanan PDF'te ekler yok. Özellikle Ek 1 (dış kapak), Ek 2 (iç kapak), Ek 5 (etik beyan) gerekli.
2. **Kapak bilgileri:** Lisansüstüne özgü "Enstitü, Anabilim Dalı" satırları yerine Fakülte ve Bölüm yazılsın mı? Üç öğrenci adı kapakta nasıl yer alsın?
3. **Cilt ve kopya:** Kılavuzun ciltli 3 nüsha, 2 mm mukavva kapak, kırmızı/mavi kapak rengi, CD/USB kuralları ara rapor için de geçerli mi? Yoksa tek basılı kopya yeterli mi? Rapor grup başına tek mi?
4. **Kabul ve onay:** Savunma olmadığı için taslağa konmadı (kılavuz projelerde de istemiyor). Doğru mu?
5. **Yapay zekâ beyanı:** Kılavuzda yapay zekâ ve benzerlik oranı kuralı yok. Bölüm 3.6'daki beyanın biçimini ve etik beyanla uyumunu soralım.
6. **Kaynakçada `&` mi `ve` mi:** Kılavuz madde 2.13 `&` istiyor, Bölüm 4.4'teki örnekler `ve` kullanıyor. Taslakta madde 2.13'e uyuldu (`&`).

## Word'e aktarırken uygulanacak biçim

| Konu | Kural |
|---|---|
| Kâğıt | A4, 75–80 g/m², beyaz, tek yüz, lazer yazıcı; basımdan sonra düzeltme kabul edilmez |
| Kenar boşluğu | Kapaklar: sol-sağ 3 cm, üst-alt 2 cm. Diğer sayfalar: sol 4 cm, sağ 2 cm, üst-alt 3 cm |
| Yazı | Times New Roman, siyah, 12 punto; dipnot 10; tablo, şekil ve denklemde gerekirse en az 8 |
| Satır aralığı | Metin 1,5. Başlık, kapak, etik beyan, teşekkür, özetler, dizinler, kaynaklar, ekler, tablo içi 1 |
| Paragraf | İki yana yaslı, önce ve sonra 6 punto, ilk satır girintisiz, araya boş satır yok, dul ve yetim satır yok |
| Sayfa numarası | Kapaklarda yok; sonra Giriş'e kadar i, ii, iii; Giriş'ten itibaren 1, 2, 3. Alttan 1,5 cm, sağa hizalı |
| 1. derece başlık | `1. BAŞLIK`: yeni sayfa, kalın, tamamı büyük, sola hizalı |
| 2. derece başlık | `1.1. Başlık`: kalın, her kelimenin ilk harfi büyük |
| Diğer başlıklar | Etik beyan, teşekkür, özet, dizinler, kaynaklar: büyük, kalın, ortalı, sonrasında 24 punto |
| Tablo | Başlık üstte, `Tablo 1. Başlık`, kalın, ortalı. Hücre dolgusu yok; başlık satırının üstü ve altı ile son satırın altı 0,75 punto çizgi; hücreler yatay ortalı; en fazla 15 cm genişlik |
| Şekil | Başlık altta, `Şekil 1. Başlık`, kalın, ortalı; en fazla 15 × 23,7 cm; gerekirse renkli |
| Liste | `•` ve `–`; madde imi 0,75 cm, metin 1,50 cm; kalın ve italik yok |
| URL | Kaynaklar dahil bütün köprüler kaldırılır (düz metin) |
| Kaynaklar | APA 7, alfabetik, 1 cm asılı paragraf |
| Özet ve Abstract | 150–250 kelime; atıf, tablo, şekil yok; 3–8 anahtar kelime (ilki büyük harfle başlar) |
| İçindekiler | Üç dereceye kadar; 2. derece 0,5 cm, 3. derece 1 cm girinti; noktalı sekme |

Bilinen sapma: Tam sayfa şekillerden önceki sayfalarda alt boşluk, kılavuzun 2,5 cm sınırını aşıyor (Bölüm 3). Üçüncü derece başlık kullanılmadı.

Metinde kılavuza göre zaten uygulananlar: bölüm sırası, Giriş ve Sonuç'ta alt başlık olmaması, başlıklarda noktalama olmaması, tablo ve şekillere sırayla numara ve önceden atıf, vurgu için kalın kullanılmaması, 10'dan küçük sayıların yazıyla yazılması, `gg Ay yyyy` tarih biçimi, `%40` yazımı.

## Teslimden önce kontrol

- [ ] `[DOLDUR]` kalmadı
- [ ] Ataberk: Bölüm 4.1, 4.2, 5.1, 6.1 ve güncel ilan, kaynak sayıları (2.208 ve 447, 30 Ekim tarihli; #48)
- [ ] Burak: Bölüm 3.5, 4.3, 5.2, 5.3
- [ ] Anıl: Bölüm 4.4, 4.5, 6.2; görev, test ve değişiklik isteği sayıları teslim tarihine göre güncellendi
- [ ] Word dosyası Word'de açılıp kapak konumları, sayfa numaraları ve yatay sayfalar kontrol edildi (Word ve LibreOffice olmayan bilgisayarda üretildi, görsel olarak denenmedi)
- [ ] Logo eklendi; `[DOLDUR]` vurguları PDF'te kalmadı
- [ ] Bütün ekip metni okudu ve anlatabiliyor
- [ ] Basım en geç 11 Kasım 2026
