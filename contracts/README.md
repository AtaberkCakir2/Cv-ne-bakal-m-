# Sözleşmeler (contracts)

Modüllerin birbirine hangi formatta veri verdiğini tanımlar. Herkes bu formatlara göre kod yazar; diğer modül hazır değilse `examples/` altındaki örnek dosyaları sahte veri olarak kullanır.

| Dosya | Kimden → Kime | İçerik |
|---|---|---|
| `job_posting.schema.json` | Ataberk → Burak | Temizlenmiş iş ilanı ve etiketlenmiş yetkinlikleri |
| `analysis_result.schema.json` | Burak → Anıl | CV analiz sonucu (mevcut/eksik yetkinlikler, uyum skoru, öneriler) |
| `api.md` | Anıl → istemciler | REST API endpoint listesi |
| `examples/` | Ortak | Her şemaya uygun örnek veri |

**Kural:** Bu klasördeki bir değişiklik, üç kişinin de PR'ı onaylamasıyla birleştirilir. Format değişirse etkilenen kodlar aynı hafta güncellenir.

Şemalar [JSON Schema 2020-12](https://json-schema.org/) formatındadır. Python tarafında Pydantic modelleri, TypeScript tarafında tipler bu şemalarla birebir uyumlu olmalıdır.
