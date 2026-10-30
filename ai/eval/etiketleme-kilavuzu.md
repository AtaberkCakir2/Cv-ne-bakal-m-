# Etiketleme kılavuzu

İki kişinin aynı CV'ye aynı etiketi vermesi için ortak kurallar. Bir durumda kararsız kalırsanız **notes** alanına yazın ve kuralı bu dosyaya eklemeyi önerin.

## Ne etiketlenir

CV sahibinin **sahip olduğunu** CV'den makul biçimde anlayabildiğiniz her yetkinlik.

- ✅ "Python, Django ile REST API geliştirdim" → `Python`, `Django`, `REST API`
- ✅ Proje açıklamasında geçen teknoloji ("Flutter ile mobil uygulama") → `Flutter`, `Dart` **değil** (yazmıyorsa çıkarım yapma)
- ✅ Sertifika/kurs adı yetkinliği açıkça veriyorsa ("AWS Certified Cloud Practitioner") → `AWS`
- ❌ Hedef/istek cümleleri ("Kubernetes öğrenmek istiyorum") → etiketlenmez
- ❌ Ders adı tek başına ("Veri Yapıları dersi aldım") → etiketlenmez; ders içinde araç geçiyorsa ("C ile veri yapıları") → `C`
- ❌ Çok genel ifadeler ("bilgisayar kullanımı", "MS Office") → etiketlenmez. Excel açıkça yazıyorsa `Microsoft Excel`.

**Kural: çıkarım yapma, yazanı etiketle.** React yazıyor ama JavaScript yazmıyorsa sadece `React`.

## Ad nasıl yazılır

- Taksonomideki (`scraper/taxonomy/skills.csv`, Ataberk, T-017) `canonical_name`'i birebir kullanın. Eş anlamlılar (`synonyms`) için de standart ad yazılır: "Postgres" → `PostgreSQL`, "k8s" → `Kubernetes`.
- Aynı yetkinlik bir kez yazılır.
- Eş anlamlı veya küçük/büyük harf farklı bir ad yazarsanız (ör. `"Postgres"`) `check_labels.py` hata verir ve doğru adı önerir.
- **Listede yoksa:** adı CV'de yazdığı gibi yazın ve başına `?` koyun (ör. `"?Temporal"`). `check_labels.py` bunları ayrı listeler; hafta sonunda listeye eklenip eklenmeyeceğine birlikte karar verilir.

## Seviye (`level`)

| Değer | Ne zaman |
|---|---|
| `advanced` | "ileri düzey", "uzman", "advanced", "proficient" yazıyor **veya** iş deneyiminde ≥ 3 yıl kullanılmış |
| `intermediate` | "orta", "iyi derecede", "intermediate", "good" **veya** 1–3 yıl iş/staj deneyiminde kullanılmış |
| `beginner` | "temel", "başlangıç", "basic", "familiar" **veya** sadece okul/kişisel projede geçiyor |
| `unknown` | Seviyeyi gösteren hiçbir ipucu yok (sadece yetenek listesinde adı geçiyor) |

- Yazılı ifade ile süre çelişirse **yazılı ifade** kazanır.
- Yıldız/çubuk gibi görsel ölçekler: 5 üzerinden 1–2 → `beginner`, 3 → `intermediate`, 4–5 → `advanced`.
- Yabancı dil için CEFR: A1–A2 → `beginner`, B1–B2 → `intermediate`, C1–C2 / "akıcı" → `advanced`.

## Yıl (`years`)

Sadece CV'de **açıkça** yazıyorsa ("3 yıl Java", "2021–2024 arası Python ile...") sayı yazın. Tarih aralığından hesaplıyorsanız tam yıla aşağı yuvarlayın. Emin değilseniz `null`.

## Yapılmayacaklar

- Etiketlerken diğer etiketleyicinin dosyasına **bakmayın**.
- `notes` alanına CV'den **alıntı, isim, şirket adı veya kişiyi tanıtabilecek bilgi yazmayın**. Bu dosyalar repoya girer.
- Taranmış CV'yi okuyamıyorsanız tahmin etmeyin; `notes`'a "okunamadı" yazın.

## Hakem (3. kişi) için

`agreement.py --write-gold` anlaşılan yetkinlikleri `gold/` taslağına yazar ve anlaşmazlıkları `"_karar_bekleyen"` listesine koyar. Her anlaşmazlık için CV'ye bakıp bu kılavuza göre karar verin, kabul ettiklerinizi `skills`'e taşıyın ve `"_karar_bekleyen"`'i silin. Kılavuz bir durumu kapsamıyorsa kuralı buraya ekleyin.
