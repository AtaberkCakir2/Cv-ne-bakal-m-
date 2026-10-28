# 20. Bilişim Kongresi: sunum metni ve demo planı (T-027)

Bu belge poster başındaki 3 dakikalık anlatımın metnini, 2 dakikalık yedek demo videosunun çekim planını ve sık gelecek sorulara verilecek cevapları içerir. Kabul kriteri: herkes anlatımı tek başına yapabilmeli, demo videosu hazır olmalı.

Köşeli parantezli yerler (`[…]`) kongreden önce gerçek değerle doldurulur. Ölçülmemiş bir sayı söylenmez.

## 1. Üç dakikalık anlatım

Yaklaşık 400 kelime; normal hızda 3 dakika. Her bölümün yanında posterde gösterilecek alan yazıyor.

**Açılış (20 sn) · posterde: başlık ve problem**

> Merhaba, biz CareerAI ekibiyiz. Bir soruyla başlayalım: bir öğrenci backend geliştirici olmak istiyor. İnternette binlerce saatlik ücretsiz eğitim var. Ama hangisinden başlamalı? Sektör bugün gerçekten neyi istiyor ve o öğrenci bunun neresinde?

**Problem (30 sn) · posterde: problem ve mevcut çözümler**

> Müfredatlar sektörün hızına yetişemiyor. LinkedIn, Kariyer.net gibi platformlar ise işverenin tarafında: adayı eler, ama adaya "şunu eksik, şuradan öğren" demez. Kariyer koçluğu da öğrenci bütçesine uygun değil. Biz sistemi adayın tarafına koyduk: bir eleme aracı değil, bir gelişim aracı.

**Çözüm ve akış (60 sn) · posterde: akış diyagramı ve arayüz prototipi**

> Öğrenci hedef pozisyonunu seçiyor ve CV'sini PDF olarak yüklüyor. Sistem dört adımda çalışıyor:
> Birincisi, PDF'ten metni çıkarıyor; taranmış CV'lerde OCR devreye giriyor.
> İkincisi, ad, telefon, adres gibi kişisel verileri maskeliyor ve yerel dil modeliyle yetkinlikleri çıkarıyor.
> Üçüncüsü, her gece toplanan güncel Türkiye ilanlarıyla karşılaştırıyor ve o pozisyonda en çok aranan yetkinlikleri buluyor.
> Dördüncüsü, eksikleri talep sırasına göre listeliyor ve her biri için kurs, video veya makale öneriyor.
> Sonuç şöyle bir cümle: "İncelediğimiz [N] backend ilanının %[X]'i Docker istiyor; CV'nde Docker yok. Şu kaynakla başlayabilirsin."

**Mimari ve KVKK (40 sn) · posterde: mimari diyagram**

> Teknik tarafta web, masaüstü ve Android istemcileri tek bir FastAPI servisine bağlanıyor. Analiz uzun sürdüğü için kuyruğa alınıyor; kullanıcı ilerlemeyi ekranda izliyor. Yapay zeka tarafında hiçbir dış API kullanmıyoruz: model, kendi sunucumuzda Ollama ile çalışıyor. CV dosyası ve ham metin hiçbir yerde saklanmıyor, sadece çıkarılan yetkinlikler kalıyor. Bu hem KVKK uyumu hem de sıfır API maliyeti demek.

**Durum ve kapanış (30 sn) · posterde: benchmark ve yol haritası**

> Model karşılaştırmamızda [model adı] seçtik: [benchmark sonucu, ör. F1 / analiz süresi]. Şu an kimlik doğrulama, arayüz ve veri toplama altyapısı çalışıyor; analiz akışını uçtan uca bağlayıp Ocak 2027'de web, masaüstü ve Android'de yayına alacağız. Kendi CV'nizi denemek isterseniz sizi bekleme listesine yazalım. Sorularınızı almaktan memnuniyet duyarız.

### Anlatırken

- Herkes metnin tamamını anlatabilmeli; soru gelince modülün sahibi devralır (scraper/veri: Ataberk, yapay zeka: Burak, backend/arayüz: Anıl).
- Ezber değil, sıra önemli: **problem → aday tarafı → 4 adım → yerel model/KVKK → durum**.
- Dinleyen kısa zamanlıysa 1 dakikalık sürüm: açılış sorusu + "aday tarafında" + örnek sonuç cümlesi + "CV saklanmıyor, model yerel".

## 2. İki dakikalık yedek demo videosu

Stantta internet veya sunucu sorun çıkarırsa bu video oynatılır. Tam analiz akışı kongre tarihinde henüz bitmiş olmayacağı için video iki kaynaktan çekilir ve bu açıkça söylenir:

- **Çalışan kısım:** gerçek web uygulaması (`web/`): kayıt, KVKK onayları, giriş, profil.
- **Tasarım kısmı:** tıklanabilir prototip (`web/prototip/index.html`): hedef pozisyon, CV yükleme, analiz bekleme, sonuç panosu, kaynak detayı.

| Süre | Ekran | Kaynak | Seslendirme / alt yazı |
|---|---|---|---|
| 0:00–0:10 | Başlık kartı | Video düzenleyici | "CareerAI: CV'ni güncel ilanlarla karşılaştır, eksiğini gör, nereden öğreneceğini bil." |
| 0:10–0:30 | Kayıt ekranı, 3 onay kutusu, "E-postanı kontrol et" | Gerçek uygulama | "Kayıtta KVKK aydınlatması ve açık rıza ayrı ayrı alınıyor." |
| 0:30–0:40 | Giriş → Profil | Gerçek uygulama | "Oturum güvenli token yenilemeyle korunuyor." |
| 0:40–0:55 | Hedef pozisyon seçimi | Prototip | "Öğrenci hedefini seçiyor: Backend Developer." |
| 0:55–1:10 | CV yükleme → analiz ediliyor | Prototip | "CV yükleniyor; kişisel veriler maskeleniyor, dosya saklanmıyor." |
| 1:10–1:45 | Sonuç panosu: uyum skoru, eksik yetkinlikler, talep çubukları | Prototip | "Eksikler ilanlardaki talebe göre sıralı. Docker ilanların %[X]'inde isteniyor." |
| 1:45–1:55 | Kaynak detayı pop-up'ı | Prototip | "Her eksik için ücretsiz kaynak önerisi." |
| 1:55–2:00 | Kapanış kartı: ekip, GitHub, QR | Video düzenleyici | "Yerel yapay zeka · KVKK uyumlu · Ocak 2027'de yayında." |

### Çekim notları

- Sadece sahte hesap (`…@example.com`) ve `contracts/examples/` altındaki anonim CV kullanılır. Gerçek CV, gerçek e-posta, tarayıcı yer imleri veya bildirimler kadrajda olmamalı.
- Çözünürlük 1920×1080, tarayıcı yakınlaştırması %125, açık tema (stantta ekran parlak ortamda daha iyi okunur).
- Prototip ekranlarında köşeye küçük bir "Tasarım prototipi" etiketi konur; jüriye çalışan kısımla tasarımı karıştırmış gibi görünmeyiz.
- Ses kaydı ayrı alınır, video sessiz ortamda da anlaşılsın diye alt yazı eklenir.
- Video MP4 olarak hem stanttaki bilgisayarda yerel olarak hem de bir USB bellekte durur; internete bağlı olmadan oynatılabilmeli.

## 3. Sık gelecek sorular

| Soru | Cevap | Kim cevaplar |
|---|---|---|
| ChatGPT'ye CV'mi yapıştırsam aynısını yapmaz mı? | Genel bir model güncel Türkiye ilanlarını bilmez ve "ilanların yüzde kaçı istiyor" diye sayı veremez. Biz her gece topladığımız ilanlardan istatistik çıkarıyoruz. Ayrıca CV'niz dışarıdaki bir şirkete gitmiyor. | Burak |
| İlanları nereden alıyorsunuz, yasal mı? | Herkese açık ilan sayfalarından, kullanım koşullarına ve robots.txt'ye uyarak, hız sınırıyla. Kişisel veri toplamıyoruz; sadece ilan metnindeki yetkinlikleri. Engellenirsek açık veri setleriyle devam edebiliyoruz. | Ataberk |
| Yetkinlik çıkarımı ne kadar doğru? | [Benchmark sonucu]. Model çıktısını sabit bir yetkinlik sözlüğüyle eşleştiriyoruz; sözlükte olmayan bir yetkinlik "doğrulanmamış" diye işaretleniyor. Önerilen kaynak linklerini de model üretmiyor, sadece bizim veritabanımızdaki listeden seçiyor; uydurma link çıkamaz. | Burak |
| Analiz ne kadar sürüyor? | CPU'lu sunucuda yaklaşık 1–2 dakika; bu yüzden kuyruk ve ilerleme ekranı var. [Ölçülen süre varsa onu söyle.] | Anıl |
| CV'm saklanıyor mu? | Hayır. Dosya diske yazılmıyor, ham metin hiçbir yerde tutulmuyor; sadece çıkarılan yetkinlikler ve dosyanın parmak izi (hash) kalıyor. Hesabınızı silince hepsi siliniyor. | Anıl |
| Sadece yazılım mı? | İlk sürüm yazılım pozisyonlarıyla başlıyor; yetkinlik sözlüğü genişletilerek başka alanlara açılabilir. | Ataberk |
| Ücretli mi olacak? | Hayır; bitirme projesi ve TÜBİTAK 2209-A kapsamında öğrencilere ücretsiz. | Herkes |
| LinkedIn'den farkı? | LinkedIn işverenin aracı; size "eksiksin" der, nereden öğreneceğinizi söylemez. Biz eksik listesini ilan verisine dayandırıp öğrenme kaynağıyla birlikte veriyoruz. | Herkes |

## 4. Prova ve stant listesi

**Kongreden önce**

- [ ] Köşeli parantezli yerler dolduruldu (benchmark, ilan sayısı, yüzde, model adı). Ölçülmemiş sayı varsa cümle çıkarıldı.
- [ ] Her ekip üyesi anlatımı en az bir kez tek başına, süre tutarak yaptı (hedef 2:45–3:15).
- [ ] Demo videosu çekildi, ekipçe izlendi, iki ayrı yerde (bilgisayar + USB) duruyor.
- [ ] Canlı demo için stant bilgisayarında web uygulaması yerelde (`127.0.0.1`) çalışıyor; internet gerekmiyor.
- [ ] Bekleme listesi için QR kod ve e-posta toplama yöntemi belirlendi (KVKK: sadece e-posta, amacı yazılı).

**Stantta**

- [ ] Poster asıldı (T-026'da teslim alınan baskı).
- [ ] Bilgisayar şarjda, ekran kilidi ve bildirimler kapalı, video açık sekmede hazır.
- [ ] Sahte hesap girişli; gerçek hesap/e-posta açık değil.
- [ ] Gelen önemli sorular ve geri bildirimler not alınıyor (kongre sonrası `docs/kararlar.md` veya görev dosyalarına işlenir).

**Canlı demo bozulursa:** "İnternet bağlantısı yüzünden kayıtlı demoyu göstereyim" deyip videoya geç; hatayı stantta ayıklamaya çalışma.
