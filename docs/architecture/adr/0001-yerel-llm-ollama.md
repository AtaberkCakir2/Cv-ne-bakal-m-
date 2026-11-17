# ADR-0001 · Yerel LLM: Ollama

- **Durum:** Kabul (kararlar #1, #14 → #26, #10)
- **Tarih:** 24.10.2026 (model seçimi 29.10.2026)
- **Sahibi:** Burak (AI) · Etkilenen: Ataberk (altyapı, bellek bütçesi)

## Bağlam

Sistem, öğrencinin CV'sinden yetkinlik çıkarır ve eksik yetkinlikler için Türkçe gerekçeli kaynak önerisi yazar. Bu iki adım bir dil modeli ister. CV kişisel veri içerir; fizibilite raporunda jüriye "CV'ler dış sunuculara gitmez" ve "API maliyeti yok" sözü verildi. Bütçe yok denecek kadar az, production tek bir bilgisayar (ADR-0004).

## Seçenekler

| Seçenek | Artı | Eksi |
|---|---|---|
| Dış LLM API'si (OpenAI, Claude API vb.) | En iyi kalite, kurulum yok, hızlı | CV metni üçüncü tarafa gider (KVKK, rapordaki taahhüt); kullanım başına ücret; anahtar yönetimi |
| **Ollama** (yerel, llama.cpp tabanlı) | Tek komutla model indirme/çalıştırma, HTTP API, JSON şeması (`format`) desteği, CPU'da quantize model; Docker imajı var | CPU'da yavaş (CV başına ~1 dk); 8B modelle kalite sınırlı |
| llama.cpp server | Daha az katman, ince ayar | Model yönetimi elle; ekipte deneyim yok |
| vLLM | Yüksek verim | GPU şart; production PC'sinde 4 GB GTX 1650 yetmez |

## Karar

- Tüm LLM çağrıları **yerel Ollama** üzerinden yapılır; dış yapay zeka API'si kullanılmaz (#1).
- Model **Llama 3.1 8B Instruct (q4_K_M)**, yedeği Gemma 2 9B (#26, T-018 benchmark'ı: F1 0,82–0,85 aralığında üç model; Llama CPU'da en hızlı, 53 sn/CV, 5,8 GB).
- Her çağrıda JSON şeması (`format`) zorunlu: şemasız geçerli JSON oranı 6–8/10, şemayla 30/30.
- LLM'e giden metin önce maskelenir (ad, telefon, e-posta, adres; #9, #24). LLM link üretmez; kaynaklar veritabanından gelir, LLM sadece listeden seçip gerekçe yazar (#10).
- Ollama sürümü sabittir (`ollama/ollama:0.40.13`, benchmark sürümü); yükseltme PR ile yapılır.

## Sonuçlar

**İyi:** CV ve maskelenmiş metin bile PC'den çıkmaz; API faturası ve anahtarı yok; çevrimdışı geliştirme mümkün.

**Bedeli:**
- Analiz CPU'da ~1–2 dakika sürer → istek-yanıt yerine kuyruk gerekir (ADR-0003).
- Bellek: Ollama konteyneri 8 GB sınırla production bütçesinin en büyük kalemi. `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1`; aynı anda tek analiz.
- Kalite 8B model sınırında. Yanlış pozitifi azaltmak için taksonomideki yetkinlikler sözlük eşleyicisinden (v1, #28) gelir; LLM bunların seviye/yılını tamamlar ve taksonomide olmayan, metinde geçen adları "doğrulanmamış" olarak ekler (`ai/extraction/llm.py`). LLM yanıt vermezse v1 sonucu döner: Ollama düşse de analiz tamamlanır.
- Ollama dışarıya **kesinlikle** açılmaz (production'da host'a port yok); yerel geliştirmede sadece `127.0.0.1:11434`.

## Ne zaman yeniden bakılır

- Analiz süresi SLO'yu aşarsa (`docs/go-live.md`): önce GTX 1650'de kısmi GPU katmanı, sonra daha küçük model.
- T-019 gold setiyle ölçülen F1 belirgin şekilde düşükse yedek modele (Gemma 2 9B) geçilir; değişiklik `docs/kararlar.md`'ye yeni satır olarak yazılır.
