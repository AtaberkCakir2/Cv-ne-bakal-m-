# Alınan kararlar

Her önemli karar buraya tarih, karar ve gerekçeyle eklenir. **Buraya yazılmayan karar, ekibin diğer üyeleri ve onların Claude'ları için yok sayılır.** Yeni karar PR ile eklenir; bir karar değişirse eski satır silinmez, durumu "Değişti → #N" yapılır.

| # | Tarih | Karar | Gerekçe | Durum |
|---|---|---|---|---|
| 1 | 24.10.2026 | Dış yapay zeka API'si (OpenAI, Claude API vb.) kullanılmaz; LLM yerel Ollama ile çalışır. | KVKK: CV'ler dış sunuculara gitmez; API maliyeti 0. Fizibilite raporunun taahhüdü. | Geçerli |
| 2 | 24.10.2026 | Mobil için React Native (Expo); Flutter değil. | Web ve Electron ile aynı dil (TypeScript) ve ortak API istemcisi; EAS ile iOS için Mac gerekmez. | Geçerli |
| 3 | 24.10.2026 | v1.0 kapsamı: web + Windows/macOS (Electron) + Android. iOS v1.1'e ertelendi. | Takvim ve Apple geliştirici hesabı maliyeti. | Geçerli |
| 4 | 24.10.2026 | İş bölümü: Ataberk = veri, veritabanı, DevOps · Burak = AI/NLP, mobil · Anıl = backend API, web/masaüstü, proje yönetimi. | İş yükü ~270-280 saat/kişi olacak şekilde dengelendi. Ayrıntı: `docs/gorevler/`. | Geçerli |
| 5 | 24.10.2026 | Paralel geliştirme sözleşmelerle yapılır: modüller `contracts/` formatlarına uyar, diğer modül hazır değilse `contracts/examples/` sahte verisi kullanılır. `contracts/` değişikliği 3 kişinin onayını ister. | Kimse kimseyi beklemesin; entegrasyon sorunları erken yakalansın. | Geçerli |
| 6 | 24.10.2026 | `main`'e doğrudan commit yok; her iş `isim/kisa-aciklama` branch'inde yapılır, PR ile ve en az 1 onayla birleşir. Herkes sadece kendi klasöründe değişiklik yapar. | Çakışmaları ve birbirinin işini bozmayı önlemek. (İlk başlangıç commit'i bu kuraldan önce yapıldı.) | Geçerli |
| 7 | 24.10.2026 | Görev durumlarının tek doğru kaynağı `docs/gorevler/<isim>.md`. `docs/plan/` altındaki Excel/PDF başlangıç planıdır, güncellenmez. | Excel'i üç kişi aynı anda güncellerse git'te birleştirilemez; kişi bazlı Markdown dosyalarında çakışma olmaz. | Geçerli |
| 8 | 24.10.2026 | İlan verisi önceliği: resmi API'ler → açık veri setleri (Kaggle) → kullanım koşulları izin veren siteler. Scraping'i yasaklayan sitelerden (ör. LinkedIn) veri çekilmez; engeli aşmaya çalışılmaz. | Hukuki risk ve etik. Açık veri seti, scraping çalışmasa bile sistemin çalışmasını garanti eder. | Geçerli |
| 9 | 24.10.2026 | CV dosyası ve ham CV metni hiçbir yerde (DB, disk, log, yedek) saklanmaz; sadece SHA-256 hash ve çıkarılan yetkinlikler tutulur. Kişisel veriler LLM'e gitmeden önce maskelenir. | KVKK; fizibilite raporundaki taahhüt. | Geçerli |
| 10 | 24.10.2026 | Eğitim kaynağı linkleri sadece veritabanından gelir; LLM link üretmez, sadece listeden seçip gerekçe yazar (RAG). | Halüsinasyon/uydurma link riskini sıfırlamak. | Geçerli |
| 11 | 24.10.2026 | CV analizi senkron istek değil, kuyruk işidir (Celery + Redis); istemci ilerlemeyi SSE/polling ile izler. | 16 GB RAM'li CPU sunucuda 8B model ile analiz ~1-2 dk sürer. | Geçerli |
| 12 | 24.10.2026 | Vektör arama için ayrı veritabanı yok; PostgreSQL + pgvector kullanılır. | Tek sistem, tek yedek, daha az operasyon yükü. | Geçerli |
| 13 | 24.10.2026 | Altyapı: tek Linux VPS (8 vCPU / 16 GB) üzerinde Docker Compose; Kubernetes yok. SSL Caddy + Let's Encrypt ile ücretsiz. | Bitirme projesi ölçeği için yeterli; bütçe raporla uyumlu. | Geçerli |
| 14 | 24.10.2026 | Kullanılacak LLM benchmark sonrası seçilecek. Aday: Llama 3.x 8B Instruct (q4_K_M); yedek: Gemma / Qwen. | Türkçe CV'lerde doğruluk, JSON uyumu ve hız ölçülmeden karar verilmemeli (görev T-018). | Açık |
| 15 | 24.10.2026 | Google Play kapalı testi en geç 21.12.2026'da başlar. | Yeni kişisel geliştirici hesapları, üretime çıkmadan önce en az 12 testçiyle 14 gün kapalı test yapmak zorunda. | Geçerli |
| 16 | 24.10.2026 | Canlıya çıkış 18.01.2027 (v1.0.0); Go/No-Go 15.01.2027. Kritik (★) Go-Live maddeleri bitmeden canlıya çıkılmaz. | Ayrıntı: `docs/go-live.md`. | Geçerli |
| 17 | 24.10.2026 | Oturumlar arası süreklilik repodan sağlanır: gün sonunda "bitiriyorum" rutiniyle görev dosyasına **Devam notu** yazılır ve yarım iş kişinin kendi branch'ine (`wip:` commit'iyle) push edilir. "Başlıyorum" rutini kararları, görev dosyasını, `contracts/` ve `docs/mimari.md`'yi eksiksiz okur ve yarım işten devam eder. | Claude önceki sohbetleri hatırlamaz; iş başka gün veya başka bilgisayarda kaldığı yerden devam edebilmeli. | Geçerli |
| 18 | 27.10.2026 | TÜBİTAK 2209-A başvuru dosyası (T-028) Burak'tan Ataberk'e devredildi; Burak ve Anıl destek. #4'teki iş bölümünün diğer kısmı aynı. | Burak'ın talebi; Ataberk bu PR'ı onaylayarak kabul eder. | Geçerli |
