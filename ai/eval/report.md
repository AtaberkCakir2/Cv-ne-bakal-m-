# Model değerlendirme raporu (T-055)

> **Durum: ön sonuç (27.11.2026).** Gold etiketleri şu an Claude'un etiketleri (karar #40); ekibin kontrolü
> (kişi başı 3–4 CV) bitince ölçüm aynı komutla tekrarlanır ve bu rapor güncellenir. Öneri alakalılığı ve
> production gecikmesi henüz ölçülmedi (aşağıda "Eksikler").

## Özet

| Ölçüt | Hedef (T-055) | Sonuç | |
|---|---|---|---|
| Yetkinlik çıkarımı F1, 50 CV | ≥ 0,80 | **0,83** | ✓ (taranmış 6 CV boş sayıldı) |
| Yetkinlik çıkarımı F1, metinli 44 PDF | ≥ 0,80 | **0,88** | ✓ |
| Seviye doğruluğu | — | %35 | zayıf, aşağıda |
| Öneri alakalılığı (3 değerlendirici, 1–5) | ≥ 4,0 | ölçülmedi | |
| Gecikme p50 / p95 (çıkarıma kadar, geliştirme makinesi) | analiz < 180 sn | 5,5 / 8,8 sn | production ayrıca ölçülecek |

## Kurulum

| | |
|---|---|
| Zincir | Üretimdeki `pipeline.analyze_cv`'nin ilk üç adımı aynen: PDF → `parsing.extract_text` → `pii.mask` (BERTurk ad tespitiyle) → `extraction.llm.extract_skills_v2` (v1 sözlük + LLM birleşimi) |
| Model | `llama3.1:8b` (46e0c10c039e, q4_K_M; karar #26), prompt `skill_extraction` v2, JSON şeması zorunlu, temperature 0.1, seed 42 |
| Ollama | 0.40.18 (yerel kurulum; production'daki sabit sürüm 0.40.13, #45) |
| Donanım | i7-13700H, 32 GB RAM, RTX 4060 Laptop 8 GB (model tamamı GPU'da) |
| Veri | `eval/dataset`: 50 sentetik CV (karar #20), 25 Türkçe / 25 İngilizce, 21'i çok sütunlu, 6'sı taranmış |
| Gold | `eval/dataset/gold/*.json`, 822 yetkinlik; şu an hepsi Claude etiketi (karar #40), ekip kontrolü sürüyor |
| Komut | `python eval/scripts/evaluate.py run --tag 2026-11-27-llama3.1-8b` ve `... report --tag ...` (ai/ klasöründe) |
| Ham sonuç | [`results/2026-11-27-llama3.1-8b.jsonl`](results/2026-11-27-llama3.1-8b.jsonl): sadece çıkarılan adlar, seviyeler, süreler; CV metni yok |

**Puanlama:** yetkinlik adı büyük/küçük harf ve gold'daki `?` işareti (taksonomi dışı) yok sayılarak karşılaştırılır.
Mikro ortalama: 50 CV'deki bütün yetkinlikler tek havuzda sayılır. "Taksonomi içi" satırı sadece gold'da `?`
olmayan ve modelin taksonomiye doğruladığı (`verified`) yetkinlikleri sayar; eşleştirme bu yetkinlikleri kullanır.
Taranmış CV'ler: OCR (T-029) henüz olmadığı için üretim `NO_TEXT_FOUND` döner; burada da yetkinlik çıkmaz.

## Yetkinlik çıkarımı

| Kapsam | CV | Kesinlik | Duyarlılık | F1 | Doğru | Fazla | Eksik |
|---|---|---|---|---|---|---|---|
| Tüm CV'ler (taranmış = boş) | 50 | 0,87 | 0,79 | **0,83** | 650 | 100 | 172 |
| Metinli PDF'ler | 44 | 0,87 | 0,90 | **0,88** | 650 | 100 | 71 |
| Metinli, sadece taksonomi içi | 44 | 0,92 | 0,94 | **0,93** | 597 | 50 | 39 |

| Grup (metinli PDF'ler) | CV | Kesinlik | Duyarlılık | F1 |
|---|---|---|---|---|
| Türkçe | 22 | 0,90 | 0,88 | 0,89 |
| İngilizce | 22 | 0,83 | 0,93 | 0,88 |
| Tek sütun | 25 | 0,88 | 0,92 | 0,90 |
| Çok sütun | 19 | 0,84 | 0,88 | 0,86 |
| Yeni mezun | 15 | 0,91 | 0,93 | 0,92 |
| Stajyer | 14 | 0,85 | 0,93 | 0,89 |
| Deneyimli | 15 | 0,84 | 0,86 | 0,85 |

T-018 benchmark'ında (10 CV, sadece LLM, taslak referans) F1 0,83'tü. v1 + LLM birleşimi duyarlılığı 0,70'ten
0,90'a çıkardı; T-032'deki birleşim kararının beklenen etkisi bu. Referanslar farklı olduğu için (taslak referans
ve gold) karşılaştırma yaklaşıktır.

**Hata analizi:**

- **Taranmış CV'ler (6/50) tamamen kaçıyor.** Tüm CV'lerdeki 172 eksiğin 101'i bu 6 CV'den. OCR (T-029)
  gelince 50 CV'de F1'in metinli PDF'lerdeki değere (~0,88) yaklaşması beklenir.
- **Soyut / dolaylı yetkinlikler kaçıyor:** Performans Optimizasyonu (7), Liderlik (4), Kod İnceleme (3),
  Test Otomasyonu (3), CI/CD (3). Bunlar CV'de kavram olarak değil, cümle içinde anlatılıyor.
- **Fazla bulunanların çoğu tartışmalı, uydurma değil:** Gözlemlenebilirlik (6), DevOps (5), Makine Öğrenmesi (5),
  UI/UX Tasarım (5). Model genel alanı ayrıca yazıyor, gold yazmıyor. Kontrol eden ekip üyeleri kılavuza
  göre karar verince bu sayı değişebilir.
- **Taksonomi dışı adlar:** sertifikalar (OSCP, Certified ScrumMaster, ISTQB) ve Türkçe açıklamalar ("Ekip
  liderliği", "Çok oyunculu ağ kodu") `verified: false` olarak geliyor. Eşleştirme bunları sadece anlamsal
  benzerlikle kullanıyor; kesinliği en çok düşüren grup bu (taksonomi içi kesinlik 0,92).
- **"Express" → Express.js eşlenmiyor (3 CV).** Taksonomide `Express.js`'in eş anlamlısı sadece `expressjs`.
  `scraper/taxonomy/skills.csv`'ye `express` eş anlamlısı eklenmeli (Ataberk'e iletilecek).

## Seviye

Doğru bulunan 650 yetkinliğin 482'sinde gold seviyesi belli; model bunların **%35**'inde aynı seviyeyi verdi.

| Gold \ Model | beginner | intermediate | advanced | unknown |
|---|---|---|---|---|
| beginner | 42 | 50 | 15 | 125 |
| intermediate | 0 | 50 | 29 | 44 |
| advanced | 1 | 4 | 77 | 45 |
| unknown | 1 | 17 | 30 | 120 |

- Hatanın çoğu **"unknown" demek** (214 yetkinlik). Özellikle kılavuzun "kişisel projede veya 6 aydan kısa işte
  kullanıldıysa temel" kuralı modelde yok: gold'da beginner olan 232 yetkinliğin 125'ine model unknown diyor.
- Model ters yönde de hata yapıyor: beginner → intermediate (50) ve intermediate → advanced (29).
- Seviye arayüzde gösteriliyor ama eşleştirme puanını etkilemiyor (T-042). Yine de rapor ve sunumda seviyenin
  "tahmini" olduğu söylenmeli.
- İyileştirme önerisi (ayrı iş): kılavuzdaki süre kurallarını prompt v3'e eklemek ve bu betikle tekrar ölçmek.

## Gecikme

Geliştirme makinesinde (GPU), metinli 44 PDF:

| Adım | p50 | p95 | en fazla |
|---|---|---|---|
| PDF → metin | 0,1 | 0,2 | 0,3 |
| Maskeleme (BERTurk dahil) | 0,7 | 0,9 | 19,0 |
| Çıkarım (v1 + LLM) | 4,7 | 7,7 | 52,3 |
| Toplam (1–3) | 5,5 | 8,8 | 71,4 |

"En fazla" sütunu ilk CV'dir: NER modelinin (19 sn) ve Ollama'da LLM'in (~45 sn) ilk yüklenmesi. İşçi açıkken
modeller bellekte kalır. Eşleştirme ve öneri adımları veritabanı istediği için burada yok. Analizin tamamı
production'da ölçülmeli: production'da Ollama GTX 1650'de çalışıyor (#168), ve kabul kriteri p50/p95 bunun üzerinden
verilmeli.

## Eksikler (T-055 bitmeden)

1. **Gold kontrolü (T-019, karar #40):** ekip 3–4'er CV kontrol edecek. Bitince `evaluate.py report` tekrar
   çalıştırılır; `run` tekrarı gerekmez, çünkü model çıktısı değişmez.
2. **Öneri alakalılığı:** 3 değerlendirici, 1–5 ölçeği, hedef ≥ 4,0. Analiz işçisi production'da çalışınca
   (go-live #25) 10 CV'nin öneri listesi puanlanacak.
3. **Production gecikmesi:** tüm zincirin (eşleştirme ve öneri dahil) p50/p95 değerleri production'da ölçülecek.
4. **OCR (T-029):** Tesseract kurulunca taranmış 6 CV ile tekrar ölçülecek.
