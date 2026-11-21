# ADR-0002 · Vektör arama: PostgreSQL + pgvector

- **Durum:** Kabul (karar #12)
- **Tarih:** 24.10.2026 (ölçüm 29.10.2026, T-013)
- **Sahibi:** Ataberk (veritabanı) · Etkilenen: Burak (embedding, eşleştirme)

## Bağlam

Eşleştirmede iki yerde benzerlik araması gerekir: CV'deki taksonomi dışı bir yetkinlik adını en yakın taksonomi yetkinliğine bağlamak (`skills.embedding`) ve ilanlar arasında anlamsal arama (`job_postings.embedding`). Vektörler 384 boyutlu ve normalize (sentence-transformers). Veri küçük: 374 yetkinlik, birkaç bin aktif ilan; iki yıl içinde en kötü ihtimalle onbinler. Asıl veri (kullanıcılar, analizler, ilanlar, talep istatistikleri) zaten PostgreSQL'de. Production tek PC, operasyonu tek kişi yürütüyor.

## Seçenekler

| Seçenek | Artı | Eksi |
|---|---|---|
| **pgvector** (PostgreSQL eklentisi) | Vektör, satırın yanında: `JOIN`, `WHERE`, transaction ve yedek ortak; ek servis yok; HNSW indeksi | Çok büyük ölçekte özel motorlardan yavaş; süzgeçli aramada dikkat gerekir |
| Qdrant / Weaviate / Milvus | Vektöre özel, süzgeçli arama güçlü, ölçeklenir | Ayrı servis, ayrı bellek, ayrı yedek; iki veritabanı arasında tutarlılık (ilan silinince vektör de silinmeli) |
| Python içinde bellek (numpy / FAISS) | Çok hızlı, basit | Her işçi süreci tüm vektörleri yükler; kalıcılık ve güncelleme elle |

## Karar

- Vektörler PostgreSQL'de, `vector(384)` sütunlarında tutulur (`skills.embedding`, `job_postings.embedding`).
- İndeks **HNSW, kosinüs** (`vector_cosine_ops`, `m = 16`, `ef_construction = 64`; migration `0003`). Sorgu `ORDER BY embedding <=> :v LIMIT k` biçiminde yazılır; aksi hâlde indeks kullanılmaz (`docs/veritabani.md`, "Vektör indeksleri").
- Seçici süzgeçli aramada `SET LOCAL hnsw.iterative_scan = relaxed_order` (pgvector 0.8.7).
- Embedding modeli şemayı bağlamaz: boyut 384 kaldıkça model değişikliği (MiniLM → e5-small önerisi, Burak) migration gerektirmez.

## Sonuçlar

**İyi:**
- Ölçüm (T-013, 200 sorgu, top-10): 6.422 ilanda p95 12,3 ms, 50.000 ilanda 6,2 ms; recall@10 0,989–1,000. Hedef < 50 ms.
- Tek yedek (`pg_dump` + restic, T-068) vektörleri de kapsar; geri yüklemede ayrıca vektör veritabanı kurulmaz.
- İlan pasifleşince veya silinince vektörü aynı transaction'da gider; iki sistem arasında tutarsızlık olmaz.

**Bedeli:**
- İndeksli tabloya toplu yazım yavaş (50.000 vektör ~163 sn); ilk büyük yüklemede indeks düşürülüp sonra kurulur.
- İndeks belleği (50.000 ilanda ~98 MB) PostgreSQL'in 2 GB sınırı içinde kalmalı.
- Küçük `skills` tablosunda planlayıcı sıralı taramayı seçer; bu doğru ve daha hızlı, indeks kullanılmıyor diye "düzeltilmemeli".

## Ne zaman yeniden bakılır

- Aktif ilan sayısı 100.000'i geçerse veya p95 50 ms'yi aşarsa: önce `hnsw.ef_search` ve PostgreSQL belleği, sonra ayrı vektör motoru.
- Gerçek embedding'lerle (T-041) recall düşük çıkarsa ölçüm tekrarlanır.
