# Cv'ne Bakalım! — Claude için proje kuralları

Bu dosyayı ekipteki herkesin Claude'u her oturumda okur. Kurallar değişirse bu dosyayı PR ile güncelleyin.

## Proje

Cv'ne Bakalım! (eski çalışma adı CareerAI; teknik adlarda `careerai` kalır, karar #34), öğrencinin CV'sini (PDF) okuyup hedef pozisyon için güncel iş ilanlarıyla karşılaştıran, eksik yetkinlikleri bulan ve bu eksikleri kapatacak eğitim kaynakları öneren bir sistemdir. Bitirme projesidir (3 kişi). Hedef: 18.01.2027'de v1.0.0 ile canlıya çıkış.

Akış: İstemci (web / Electron / React Native) → FastAPI → Redis kuyruğu → AI worker (PDF → kişisel veri maskeleme → yetkinlik çıkarımı → embedding → eşleştirme → kaynak önerisi, Ollama) → PostgreSQL + pgvector. Ayrı bir toplayıcı her gece ilanları toplar ve istatistikleri yeniler.

## Klasör sahipliği

| Klasör | Sahibi | İçerik |
|---|---|---|
| `scraper/` | Ataberk | İlan toplama, ETL, yetkinlik taksonomisi, kaynak havuzu |
| `infra/` | Ataberk | Sunucu, Docker, CI/CD, izleme, yedekleme |
| `backend/app/db/` | Ataberk | SQLAlchemy modelleri, Alembic migration'ları |
| `ai/` | Burak | PDF/OCR, PII maskeleme, yetkinlik çıkarımı, eşleştirme, öneri, Ollama |
| `mobile/` | Burak | React Native (Expo) uygulaması |
| `backend/` (db hariç) | Anıl | FastAPI, kimlik doğrulama, kuyruk, endpoint'ler |
| `web/` | Anıl | React arayüzü (Electron da bunu kullanır) |
| `contracts/` | Ortak | Modüller arası veri formatları — değişiklik 3 kişinin onayıyla |
| `docs/` | Ortak | Kararlar, diyagramlar, raporlar |

## Claude için kurallar

1. **Sadece kullanıcının kendi klasöründe değişiklik yap.** Başka birinin klasöründe değişiklik gerekiyorsa yapma; ne değişmesi gerektiğini ve nedenini yaz, kullanıcı sahibine iletsin.
2. **`contracts/` altındaki formatlara uy.** Kod sözleşmeyle çelişiyorsa sözleşmeyi değil kodu düzelt. Sözleşmenin değişmesi gerektiğini düşünüyorsan öner, kendin değiştirme.
3. **Başka modül henüz hazır değilse sahte veri kullan.** Sahte veriler `contracts/examples/` altındaki örneklerle birebir aynı formatta olmalı.
4. **Sır ve kişisel veri yok.** `.env`, şifre, API anahtarı, gerçek CV veya kişisel veri içeren dosyaları asla commit'leme. Testlerde sadece sahte/anonim CV kullan.
5. **CV dosyası ve ham CV metni hiçbir yerde saklanmaz** (veri tabanı, disk, log). Sadece SHA-256 hash ve çıkarılan yetkinlikler tutulur. LLM'e gitmeden önce kişisel veriler maskelenir.
6. **Dış yapay zeka API'si kullanılmaz** (OpenAI, Claude API vb.). Tüm LLM çağrıları yerel Ollama üzerinden yapılır.
7. **`main` dalına doğrudan commit yok.** Her iş ayrı branch'te (`isim/kisa-aciklama`, ör. `anil/auth-endpoint`) yapılır ve PR ile birleştirilir.
8. Commit mesajları Türkçe ve kısa olabilir; conventional commits öneki kullan: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
9. Kullanıcıyla Türkçe konuş.

## Nerede ne var

Bir konuda bilgi gerekirse tahmin etmeden önce bu dosyalara bak:

| Konu | Dosya |
|---|---|
| Proje neden var, jüriye ne söz verildi | `docs/fizibilite-raporu.md` |
| Alınmış kararlar ve gerekçeleri | `docs/kararlar.md` |
| Mimari, teknoloji seçimleri, ortamlar, sunucu servisleri, RACI | `docs/mimari.md` |
| Veritabanı tabloları ve sütunları | `docs/veritabani.md` |
| Modüller arası veri formatları, API listesi | `contracts/` |
| Görevler, tarihler, kabul kriterleri | `docs/gorevler/<isim>.md` |
| Canlıya çıkış listesi, SLO'lar, olay prosedürleri | `docs/go-live.md` |
| Riskler ve bütçe | `docs/riskler.md` |

Kullanıcıyla yeni bir karar alındığında (teknoloji seçimi, kapsam veya tarih değişikliği vb.) `docs/kararlar.md`'ye eklemeyi öner; yazılmayan karar ekibin diğer üyeleri için yoktur.

## Kim çalışıyor?

Oturumun başında kullanıcının kim olduğunu belirle: `git config user.name` ve `git config user.email` değerlerinde "Ataberk", "Burak" veya "Anıl/Anil" geçiyorsa (büyük/küçük harf ve Türkçe karakter farkını yok say) o kişidir. Belirlenemezse kullanıcıya sor. Kişinin görev dosyası:

| Kişi | Görev dosyası |
|---|---|
| Ataberk | `docs/gorevler/ataberk.md` |
| Burak | `docs/gorevler/burak.md` |
| Anıl | `docs/gorevler/anil.md` |

Görev durumlarının tek doğru kaynağı bu dosyalardır. `docs/plan/` altındaki Excel ve PDF başlangıç planıdır, referans olarak okunur, güncellenmez. Kullanıcının Claude'u sadece kullanıcının kendi görev dosyasını değiştirir.

## "Başlıyorum" rutini

Claude önceki oturumları hatırlamaz; sürekliliği repodaki dosyalar ve kullanıcının branch'leri sağlar. Kullanıcı "başlıyorum", "başlayalım" veya "işe başlıyorum" dediğinde sırayla:

1. **Repoyu güncelle:** `git fetch --prune`, sonra `git checkout main && git pull`. Commit'lenmemiş değişiklik varsa önce göster ve ne yapılacağını sor; kullanıcının işini asla silme veya üzerine yazma.
2. **Bağlamı eksiksiz yükle:** şu dosyaları baştan sona oku (özetten değil, dosyanın kendisinden): `docs/kararlar.md`, kullanıcının görev dosyası, `contracts/` altındaki tüm dosyalar ve `docs/mimari.md`. Bugünkü görevin alanına göre ilgili dokümanı da oku (veritabanı işi → `docs/veritabani.md`, canlıya çıkış/operasyon → `docs/go-live.md`, risk → `docs/riskler.md`). Okuduklarını kullanıcıya uzun uzun aktarma; sadece işle ilgili olanı kullan.
3. **Ekipte ne değişti:** son çalışmadan bu yana `main`'e gelen commit'leri yazarına ve konusuna göre kısaca özetle. `contracts/` veya `docs/kararlar.md` değiştiyse ayrıca vurgula ve kullanıcının işini nasıl etkilediğini söyle.
4. **Yarım kalan işi bul:** kullanıcının uzak branch'lerini listele (`git branch -r --list "origin/<isim>/*"`; isim: `ataberk`, `burak`, `anil`). Henüz `main`'e birleşmemiş branch varsa, o branch'teki görev dosyasında ilgili görevin **Devam notu** satırını oku (`git show origin/<branch>:docs/gorevler/<isim>.md`). Ayrıca o branch için açık PR olup olmadığını ve inceleme yorumlarını kontrol et (`gh` varsa). Yarım iş varsa önce onu öner: "Dün X'te kalmıştın, sıradaki adım Y" gibi.
5. **Ekip durumu:** üç görev dosyasındaki `Engellendi` görevleri ve kullanıcının görevlerini bekleten (bağımlılığı bitmemiş) görevleri listele.
6. **Bugünün görevi:** yarım iş yoksa kullanıcının görev dosyasından bugünün tarihini kapsayan veya bitişi geçmiş ve `Tamamlandı` olmayan görevleri listele (ID, başlık, bitiş, öncelik, bağımlılık durumu). Önce P0 ve bitişi en yakın olanı, bağımlılıkları bitmiş olanlar arasından öner.
7. **Branch'e geç:** yarım işe devam ediliyorsa o branch'i checkout et ve `git merge main` ile güncelle (çakışma olursa kullanıcıyla birlikte çöz). Yeni görevse `<isim>/kisa-aciklama` adıyla branch aç ve görev dosyasında durumu `Devam Ediyor` yap.
8. **Görevi birlikte yap:** görevin "Kabul kriteri" satırı iş tanımıdır. Diğer modüller hazır değilse `contracts/examples/` sahte verileriyle çalış. Sadece kullanıcının kendi klasörlerinde değişiklik yap.
9. **Görev bitince:** kabul kriterlerini tek tek kontrol et; görev dosyasında durumu `Tamamlandı` yap, **Devam notu** satırını sil ve işle aynı commit'e ekle. **Push ve PR açmadan önce yapılanların özetini göster ve kullanıcıdan onay al.** Onaydan sonra push et ve PR aç; `gh` girişi yoksa GitHub'daki PR oluşturma linkini ver.

Görev engellenirse durumu `Engellendi` yap, sebebini görevin **Not** satırına yaz ve kullanıcıya ekibe haber vermesini hatırlat.

## "Bitiriyorum" rutini (gün sonu devri)

Kullanıcı "bitiriyorum", "bugünlük bu kadar" veya "ara veriyorum" dediğinde, iş bitmemiş olsa bile ertesi gün (veya başka bir bilgisayarda) eksiksiz devam edilebilmesi için:

1. Görev dosyasında ilgili görevin altına şu satırı ekle veya güncelle:
   `- **Devam notu (GG.AA.YYYY):** Yapılan: … · Sıradaki adım: … · Açık sorular / engeller: … · Branch: <isim>/…`
   Not, bu konuşmayı hiç görmemiş birinin işe kaldığı yerden devam edebileceği kadar somut olmalı (hangi dosya, hangi fonksiyon, hangi test).
2. Yarım kodu ve notu commit'le (`wip: …` önekiyle; çalışmayan kod varsa nottaki "Sıradaki adım"da belirt).
3. Ne commit'lendiğini göster, kullanıcıdan onay alıp branch'i push et (`main`'e değil, kendi branch'ine). PR açma; PR sadece görev bitince açılır.
4. Kullanıcıya bir cümleyle nerede kalındığını ve yarın ilk ne yapılacağını söyle.

## Teknoloji

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, Celery + Redis
- PostgreSQL 16 + pgvector
- Ollama (Llama 3.x 8B Instruct veya Gemma; benchmark sonrası kesinleşecek)
- Embedding: sentence-transformers (çok dilli, 384 boyut)
- PDF: pdfplumber + PyMuPDF; OCR: Tesseract (tur + eng)
- Web: React + Vite + TypeScript; masaüstü: Electron; mobil: React Native (Expo)
- Python kod stili: ruff + mypy. TypeScript: eslint + prettier.

## Çalıştırma

Altyapı servisleri (Postgres, Redis, Ollama): `docker compose up -d` — ayrıntılar `README.md` içinde.
