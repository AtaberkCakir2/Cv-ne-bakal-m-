# LLM benchmark raporu (T-018)

**Sonuç:** kazanan **Llama 3.1 8B Instruct (q4_K_M)**, yedek **Gemma 2 9B**. Üretimde Ollama'nın JSON şeması (structured output) zorunlu (karar önerisi: `docs/kararlar.md` #26).

Tarih: 29.10.2026 · Ölçen: Burak (Claude Code ile) · Script: [`../scripts/benchmark_llm.py`](../scripts/benchmark_llm.py) · Ham sonuçlar: [`results/`](results/)

## Kurulum

| | |
|---|---|
| Donanım | Intel i7-13700H (14 çekirdek / 20 iş parçacığı), 32 GB RAM, NVIDIA RTX 4060 Laptop 8 GB |
| Yazılım | Windows 11, Ollama 0.40.13 (yerel kurulum; Docker'daki sabit sürüm de 0.40.13, #45) |
| Modeller | `llama3.1:8b` (46e0c10c039e), `gemma2:9b` (ff02c3702f32), `qwen2.5:7b` (845dbda0ea48); Ollama varsayılanları: Llama ve Qwen q4_K_M, Gemma Q4_0 (Gemma için `gemma2:9b-instruct-q4_K_M` ayrıca çekilmeli) |
| Ayarlar | temperature 0.1, seed 42, num_ctx 8192. CPU ölçümü `num_gpu: 0` ile |
| Veri | 10 Türkçe sentetik CV (`syn-004`…`syn-013`, 10 pozisyondan 1'er; 3 çok sütunlu, 2 taranmış) |
| Akış | PDF → `parsing.extract_text` → `pii.mask` → Ollama → JSON → taksonomiye eşleme. Taranmış 2 CV'de OCR (T-029) henüz olmadığı için metin CV tanımından alındı |
| Prompt | Sistem mesajı `prompts/skill_extraction/v1.txt`: sadece açıkça geçen yetkinlikler; istek cümleleri ve ders adları alınmaz; seviye + yıl |

**Referans:** ekibin etiketi (T-019 gold) henüz yok. [`reference_draft.json`](reference_draft.json), CV metninin taksonomiyle sözlük eşlemesi ve etiketleme kılavuzuna göre elle düzeltilmesiyle Claude tarafından hazırlandı (10 CV, 196 yetkinlik). İnsan etiketi değildir; gold gelince ölçüm tekrarlanmalı. Seviye doğruluğu bu yüzden ölçülmedi.

**Metrikler:** model çıktısındaki ad taksonomiye eşlenir (eş anlamlılar, "Express" → Express.js, "TensorFlow/Keras" → iki yetkinlik). Kesinlik/duyarlılık/F1 taksonomiye eşlenen adlar üzerinden (mikro ortalama). "Taksonomi dışı" = eşlenemeyen ad oranı (DNS, LoRA, CompTIA Security+ gibi; çoğu gerçek ama taksonomide olmayan kavram). Bellek = Ollama'nın modele ayırdığı (`/api/ps`).

## Sonuçlar

| Model | Cihaz | JSON geçerli | Kesinlik | Duyarlılık | F1 | Taksonomi dışı | Üretim tok/sn | CV başına sn | Bellek (GB) |
|---|---|---|---|---|---|---|---|---|---|
| **Llama 3.1 8B** | CPU | 10/10 | **1,00** | 0,69 | 0,82 | 9% | **6,7** | **53** | 5,8 |
| Gemma 2 9B | CPU | 10/10 | **1,00** | **0,74** | **0,85** | 9% | 5,9 | 71 | 6,1 |
| Qwen 2.5 7B | CPU | 10/10 | 0,98 | 0,72 | 0,83 | 16% | 6,1 | 73 | **5,1** |
| **Llama 3.1 8B** | GPU | 10/10 | 1,00 | 0,70 | 0,83 | 10% | 46,7 | 8,6 | 5,4 (tamamı GPU) |
| Gemma 2 9B | GPU | 10/10 | 0,99 | 0,73 | 0,84 | 10% | 16,3 | 21,2 | 6,7 (4,8 GPU) |
| Qwen 2.5 7B | GPU | 10/10 | 0,98 | 0,73 | 0,84 | 19% | 48,1 | 10,4 | 4,8 (tamamı GPU) |

CV başına ortalama ~700 girdi, ~280–380 çıktı token'ı. Modelin ilk yüklenmesi CPU'da ~21–28 sn, GPU'da ~11–15 sn (bir kez).

**JSON uyumu, şemasız (sadece prompt ile, GPU):** Llama 8/10, Gemma 8/10, Qwen 6/10 geçerli. JSON'un kendisi neredeyse hep doğru (Qwen bir kez kod bloğu içinde verdi); bozan şey `level` alanına `B2`, `C1`, `native`, `basic` gibi izin verilmeyen değer yazılması. Ollama'nın `format` (JSON şeması) parametresiyle üç modelde de 30/30 geçerli → üretimde şema zorunlu.

## Gözlemler

- **Kesinlik çok yüksek, duyarlılık ~0,7.** Modeller yetkinlik uydurmuyor ama dolaylı geçenleri kaçırıyor: "REST servisleri" → REST API, "izleme" → Gözlemlenebilirlik, "Active Directory" → Windows Server, "makine öğrenmesi modelleri" → Makine Öğrenmesi; GitHub, Firebase gibi cümle içinde geçenler. Bunlar tam olarak sözlük tabanlı v1'in (T-031) yakaladığı türden; T-032'deki "v1 + LLM birleşimi" planı doğru.
- **Kural uyumu:** Llama ve Gemma (CPU) hiç yanlış pozitif vermedi. Qwen "Kriptografi"yi ders adından, "Next.js"i "öğreniyorum" cümlesinden aldı; taksonomi dışı adları da en çok o üretti (ders adları, "Veri Bilimci" unvanı, "Java 17").
- **Prompt örneği modeli yanıltıyor.** İlk denemede örnek JSON'da `"Python"` ve kurallarda `"İngilizce"` yazıyordu: üç model de İngilizce geçmeyen bir CV'ye İngilizce, Gemma 4 CV'ye Python ekledi (10 yanlış pozitif). Örnek yer tutucuyla (`<yetkinlik adı>`) değiştirilince bunlar kayboldu. T-044 (prompt versiyonlama) ve T-074 için not: örneklerde gerçek yetkinlik adı kullanılmamalı.
- **8 GB GPU'ya Gemma sığmıyor** (num_ctx 8192 ile ~1,9 GB CPU'ya taşıyor), bu yüzden GPU'da yavaş. Llama ve Qwen tamamen sığıyor.
- **F1 farkları küçük** (0,82–0,85; 10 CV, ~196 yetkinlik): istatistiksel olarak ayırt edici değil. Seçim hız, kural uyumu ve bellekle yapıldı.

## Karar

| | Model | Neden |
|---|---|---|
| Kazanan | **Llama 3.1 8B Instruct q4_K_M** | Üretim sunucusu GPU'suz (karar #13): CPU'da en hızlı (53 sn/CV, diğerlerinden %25–30 hızlı), yanlış pozitif 0, kural uyumu iyi, 5,8 GB ile Ollama'nın 8 GB limitine rahat sığıyor. |
| Yedek | **Gemma 2 9B (ölçülen Q4_0)** | En yüksek duyarlılık/F1, yanlış pozitif 0; ama CPU'da %35 daha yavaş ve daha çok bellek. |
| Elendi | Qwen 2.5 7B | En küçük bellek ama kurallara en az uyan (ders adı, istek cümlesi) ve en çok taksonomi dışı ad üreten model. |

## Riskler ve sonraki adımlar

- **Süre:** bu makinenin CPU'sunda yalnızca yetkinlik çıkarımı ~53 sn. 8 vCPU'lu VPS'te daha yavaş olacak (tahmin ~1,5–2×, ölçülmedi); analiz hedefi 1–2 dk (karar #11). Kaynak önerisi (T-043) ikinci bir LLM çağrısı ekleyecek. VPS'te tekrar ölçülmeli (T-056); gerekirse: daha kısa çıktı (sadece ad + seviye), `num_ctx` 4096, küçük model (Llama 3.2 3B) denemesi.
- **Referans geçici:** T-019 gold etiketleri gelince `python eval/scripts/benchmark_llm.py run …` ile tekrar ölçülmeli; İngilizce CV'ler (25 adet) henüz yok.
- **Taranmış CV'ler:** OCR (T-029) gelince 2 taranmış CV gerçek akıştan geçirilmeli.
- Ölçüm Ollama 0.40.13 ile yapıldı; `docker-compose.yml` de bu sürüme sabitlendi (#45), VPS ölçümü aynı sürümle yapılır.

## Tekrar üretmek

```bash
# Ollama çalışırken, ai/ klasöründe
ollama pull llama3.1:8b && ollama pull gemma2:9b && ollama pull qwen2.5:7b
python eval/scripts/benchmark_llm.py run --models llama3.1:8b gemma2:9b qwen2.5:7b --device gpu --mode schema --tag gpu-schema
python eval/scripts/benchmark_llm.py run --models llama3.1:8b gemma2:9b qwen2.5:7b --device gpu --mode free --tag gpu-free
python eval/scripts/benchmark_llm.py run --models llama3.1:8b gemma2:9b qwen2.5:7b --device cpu --mode schema --tag cpu-schema
python eval/scripts/benchmark_llm.py report
```

Sonuçlar `results/*.jsonl` dosyalarına eklenir (yeniden ölçmeden önce eski dosyaları silin). Satırlarda CV metni yok; sadece yetkinlik adları ve süreler var.
