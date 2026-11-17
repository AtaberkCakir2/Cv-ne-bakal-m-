# Beta / UAT planı (T-078)

Bu plan T-082'nin (beta yürütme, 28.12.2026 – 10.01.2027) nasıl yapılacağını tanımlar. Yöntem, TÜBİTAK taslağındaki kullanılabilirlik çalışmasıyla ([2209a-basvuru-taslagi.md §2.6](../tubitak/2209a-basvuru-taslagi.md)) ve karar #21 ile aynıdır. Böylece beta verisi iki yerde de kullanılabilir.

| | |
|---|---|
| Sorumlu | Anıl (destek: Burak, Ataberk) |
| Katılımcı | 20–30 gönüllü öğrenci |
| Ortam | Production (`cvnebakalim.com`), web ve Windows masaüstü; mobil için Play kapalı testi (T-076) ayrıca |
| Toplanan veri | Yalnızca anonim anket yanıtları, görev tamamlama durumu ve süresi. CV ve analiz sonucu araştırma verisi olarak kaydedilmez (karar #21) |
| Çıkış ölçütü (T-082) | Açık P0 hata = 0, ortalama SUS ≥ 70, analiz başarı oranı ≥ %95 |

## 1. Takvim

| Tarih | İş | Sorumlu |
|---|---|---|
| 01.12 – 15.12 | Etik kurul onayı veya muafiyet yazısı (TÜBİTAK taslağı B1 #5). Gelmezse beta yalnızca hata bulma testi olarak yürür, SUS sonuçları araştırmada kullanılmaz | Burak |
| 15.12 – 21.12 | Katılımcı duyurusu (§2), kayıt formu, onam formu ve anketin son hali | Anıl |
| 21.12 | Play kapalı testi başlar (T-076, en az 12 testçi). Testçiler bu listeden seçilir | Anıl |
| 27.12 | Prova: ekipten biri tüm senaryoları production'da baştan sona dener. Senaryo metinlerindeki belirsizlikler düzeltilir | Anıl, Burak |
| 28.12 – 10.01 | Beta oturumları (§4), her gün hata triyajı (§6) | Anıl |
| 28.12 – 10.01 | Hata düzeltmeleri (T-084 ve ekibin ilgili görevleri) | Herkes |
| 10.01 | Beta raporu (§7) ve çıkış kararı | Anıl |

## 2. Katılımcı toplama

- **Kimler:** Bilgisayar ve yazılım alanında okuyan, staj veya ilk iş arayan öğrenciler (ürünün hedef kitlesi). En az üç farklı hedef pozisyon temsil edilir (ör. backend, veri, frontend).
- **Kanal:** Bölüm duyuru grupları, danışman hoca aracılığıyla ders duyurusu ve kariyer merkezi (TÜBİTAK taslağı R7).
- **Kayıt:** Ad-soyad istenmez. Kayıt formunda sadece iletişim için e-posta, okuduğu bölüm ve sınıf, kullanacağı cihaz (Windows / macOS / Android) ve uygun olduğu oturum günü sorulur. Kayıt e-postaları anket yanıtlarıyla eşleştirilmez ve beta bitince silinir.
- **Hedef:** 30 kayıt. Gelmeme payı nedeniyle 20 tamamlanmış oturum için bu sayı gerekir. 21.12'ye kadar 15'in altında kayıt varsa duyuru tekrarlanır ve çevrim içi oturum seçeneği eklenir.

Duyuru metni:

> **Cv'ne Bakalım! beta testine katılır mısın?**
> CV'ni hedeflediğin pozisyonun güncel ilanlarıyla karşılaştırıp eksik yetkinliklerini ve bunlar için ücretsiz kaynakları gösteren bitirme projemizi deniyoruz. 30–40 dakikalık bir oturumda uygulamayı kullanıp kısa bir anket dolduruyorsun. CV'n kaydedilmiyor; ister kendi CV'ni ister bizim verdiğimiz örnek CV'yi kullanabilirsin. Kayıt: _(form bağlantısı)_

## 3. Onam

Oturumdan önce katılımcı, aydınlatma metnini ve bilgilendirilmiş onam formunu okur ve onaylar (TÜBİTAK taslağı Ek 1, Burak ve Anıl). Formda şunlar açıkça yazar:

- Özgeçmiş kaydedilmez. Alınan veriler yalnızca anonim anket yanıtları ve görev süreleridir.
- Katılım gönüllüdür; katılımcı istediği an bırakabilir.
- Uygulamada açtığı hesabı Profil sayfasından kendisi silebilir. Beta bitince ekip, beta hesaplarının silinmesini hatırlatır.

Katılımcı kendi CV'sini paylaşmak istemezse `contracts/examples/` altındaki sahte CV'lerden biri verilir.

## 4. Oturum akışı

Yüz yüze veya ekran paylaşımlı çevrim içi oturum, yaklaşık 35 dakika. Gözlemci sadece not alır; katılımcı takılırsa 3 dakika sonra ipucu verir ve görev "yardımla tamamlandı" sayılır.

1. Onam (3 dk)
2. Altı görev senaryosu (§5, 20 dk). Gözlemci her görevin sonucunu ve süresini forma yazar. Analizin bekleme süresi ayrı ölçülür (sistem süresi kullanıcı süresiyle karışmasın, TÜBİTAK taslağı §2.6).
3. SUS ve ek sorular (§8, 7 dk)
4. Serbest yorum (5 dk)

Katılımcılar web ve Windows masaüstü uygulaması arasında dağıtılır. Uygun Android cihazı olanlar ayrıca Play kapalı testine eklenir.

## 5. Görev senaryoları

Senaryolar TÜBİTAK taslağıyla aynıdır. Başarı ölçütü önceden yazılıdır; gözlemci yorum yapmaz.

| # | Görev (katılımcıya okunan metin) | Tamamlandı sayılması için |
|---|---|---|
| G1 | "Uygulamaya kayıt ol ve e-posta adresini doğrula." | Hesap açıldı ve doğrulama bağlantısıyla giriş yapıldı |
| G2 | "Staj aradığın pozisyonu hedef olarak seç." | Katılımcının söylediği pozisyon seçili |
| G3 | "CV'ni yükle ve analizin bitmesini bekle." | Sonuç ekranı açıldı (bekleme süresi ayrıca not edilir) |
| G4 | "Sonucuna bakarak bana söyle: uyum puanın kaç, en öncelikli eksik yetkinliğin ne, bu yetkinlik ilanların yüzde kaçında isteniyor?" | Üç cevabın üçü de ekrandakiyle aynı |
| G5 | "Bu eksik yetkinlik için önerilen bir kaynağı aç." | Önerilen kaynaklardan biri yeni sekmede açıldı |
| G6 | "Daha önce yaptığın analizi bul, sonra hesabına ait verileri indir veya sil." | Geçmiş listesinden analiz açıldı ve veri indirme ya da silme tamamlandı |

Hedef: her görevde tamamlanma oranı ≥ %90 (yardımsız). Bir görevde %70'in altına düşülürse o ekran için iyileştirme P1 olarak açılır.

## 6. Hata bildirme ve triyaj

**Kanallar:**

- **Uygulama içi:** Web ve masaüstünde her sayfanın altında **Hata bildir** bağlantısı var. Bağlantı `iletisim@cvnebakalim.com` adresine, sayfa ve tarayıcı bilgisi doldurulmuş bir e-posta açar (`web/src/support.ts`). Ekrandaki hata kodu (`request_id` ilk 8 karakter) e-postaya yazılırsa API loglarında ilgili istek bulunur. Mobil uygulamaya aynı bağlantının eklenmesi Burak'a önerilir.
- **Oturum sırasında:** Gözlemcinin notları.
- **Play kapalı testi:** Play Console'daki testçi geri bildirimleri.

Gelen her bildirim GitHub'da `beta` etiketli bir issue olur. Bildirimdeki e-posta adresi ve kişisel bilgi issue'ya yazılmaz.

**Önem dereceleri:**

| Derece | Tanım | Hedef |
|---|---|---|
| P0 | Ana akış çalışmıyor (kayıt, giriş, yükleme, sonuç), veri kaybı, güvenlik veya kişisel veri sızıntısı | Aynı gün düzeltme; beta çıkışı için 0 |
| P1 | Bir görev yardımsız tamamlanamıyor ya da yanlış bilgi gösteriliyor (yanlış skor, ölü link) | Beta içinde düzeltme |
| P2 | Rahatsız edici ama işi engellemeyen sorun (metin, yerleşim, yavaşlık) | Zaman kalırsa; yoksa v1.1 |
| P3 | Öneri | v1.1 yol haritasına (T-100) |

**Günlük triyaj** (beta günlerinde 15 dakika, Anıl yönetir): yeni issue'lara derece ve sahip (klasör sahipliğine göre) atanır. Production Grafana panosundaki analiz hata oranına bakılır. P0 varsa ekibe hemen haber verilir.

## 7. Ölçümler ve beta raporu

| Ölçüm | Nasıl | Hedef |
|---|---|---|
| SUS | Katılımcı başına 0–100 puan (§8), ortalama ve %95 güven aralığı; Bangor vd. (2008) ölçeğiyle yorum | Ortalama ≥ 70 |
| Görev tamamlama | Görev başına yardımsız / yardımla / tamamlanamadı oranı | Her görevde yardımsız ≥ %90 |
| Görev süresi | Görev başına medyan; G3'te bekleme süresi hariç | Bilgi amaçlı |
| Analiz başarı oranı | Beta döneminde production'da `done` / (`done` + `failed`) analiz sayısı (Grafana analiz paneli veya `analyses` tablosu, kişisel veri içermeyen sayım) | ≥ %95 |
| Sonucun doğruluğu (katılımcı görüşü) | Ek soru E1, 1–5 ortalama | Bilgi amaçlı (TÜBİTAK taslağı §2.6) |
| Açık hata | Derecelere göre `beta` issue sayısı | P0 = 0 |

10.01'de `docs/uat/beta-raporu.md` yazılır: katılımcı sayısı, yukarıdaki tablo, en sık yaşanan 5 sorun ve ne yapıldığı, v1.1'e kalanlar. Rapor go-live kararına (T-093) ve final raporuna (T-098) girdi olur.

**Çıkış kararı:** Ölçütler sağlanmazsa 11.01'de ekip toplanır. Kalan P0 için v1.0.0 kod dondurmasından (T-092, 13.01) önce düzeltme planı yapılır. SUS 70'in altındaysa en düşük puan alan görevlerin ekranları önceliklendirilir; canlıya çıkış ertelenmez, sonuç raporda tartışılır.

## 8. Anket

Anket, kayıt formuyla bağlantısı olmayan ayrı bir çevrim içi formdur. Ayarlarında e-posta toplama ve giriş zorunluluğu kapalıdır. Hangi form aracının kullanılacağına ekip karar verir.

**Sistem Kullanılabilirlik Ölçeği (SUS, Brooke 1996).** 1 = Kesinlikle katılmıyorum … 5 = Kesinlikle katılıyorum. Aşağıdaki ifadeler çalışma çevirisidir. Etik kurul başvurusundan önce Burak ile birlikte yayımlanmış bir Türkçe uyarlamayla karşılaştırılıp kesinleşir (TÜBİTAK taslağı Ek 2).

1. Bu uygulamayı sık sık kullanmak isterim.
2. Uygulamayı gereksiz yere karmaşık buldum.
3. Uygulamanın kullanımı kolaydı.
4. Bu uygulamayı kullanabilmek için teknik bilgisi olan birinin yardımına ihtiyaç duyarım.
5. Uygulamadaki işlevlerin birbiriyle iyi bütünleştiğini düşünüyorum.
6. Uygulamada çok fazla tutarsızlık olduğunu düşünüyorum.
7. Çoğu insanın bu uygulamayı çok çabuk öğreneceğini düşünüyorum.
8. Uygulamayı kullanmayı çok zahmetli buldum.
9. Uygulamayı kullanırken kendimden emin hissettim.
10. Bu uygulamayı kullanmaya başlamadan önce birçok şey öğrenmem gerekti.

**Puanlama:** Tek numaralı maddelerde katkı = cevap − 1, çift numaralı maddelerde katkı = 5 − cevap. Toplam katkı × 2,5 = 0–100 arası SUS puanı. Bir maddesi boş kalan anket SUS ortalamasına katılmaz.

**Ek sorular:**

- E1. Sonuçta gösterilen mevcut ve eksik yetkinlikler sana ne kadar doğru geldi? (1–5)
- E2. Önerilen kaynaklar eksiklerini kapatmak için işine yarar mı? (1–5)
- E3. Bu uygulamayı bir arkadaşına önerir misin? (Evet / Belki / Hayır)
- E4. Hangi platformu kullandın? (Web / Windows / macOS / Android)
- E5. En çok zorlandığın şey neydi? (serbest metin)
- E6. Eklenmesini istediğin bir şey var mı? (serbest metin)

Serbest metin cevaplarında kişisel bilgi varsa rapora alınmadan silinir.

## 9. Açık kararlar

| Konu | Kim karar verir | Ne zamana |
|---|---|---|
| Etik kurul onayı mı muafiyet mi | Burak (danışmanla) | 15.12 |
| Kayıt ve anket formu aracı | Ekip | 15.12 |
| Oturumların yüz yüze mi çevrim içi mi yapılacağı | Ekip | 21.12 |
| `iletisim@cvnebakalim.com` gelen kutusunu kimin okuyacağı (beta ve hypercare) | Ekip, go-live #47 | 21.12 |
