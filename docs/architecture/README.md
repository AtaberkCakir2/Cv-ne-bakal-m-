# Mimari dokümanı ve ADR'ler (T-079)

Bu klasör, sistemin **neden böyle kurulduğunu** anlatır. Ne kurulduğu (bileşenler, servisler, ortamlar, sorumlular) `docs/mimari.md`'de; kısa karar kaydı `docs/kararlar.md`'de. ADR'ler o kararların uzun hâlidir: bağlam, değerlendirilen seçenekler, sonuç ve bedeli.

| Dosya | Ne anlatır |
|---|---|
| [deployment.md](deployment.md) | Production deployment diyagramı (PC + Cloudflare Tunnel), servisler, ağ sınırları, deploy ve yedek akışı |
| [adr/0001-yerel-llm-ollama.md](adr/0001-yerel-llm-ollama.md) | Neden yerel LLM ve Ollama (dış API yok) |
| [adr/0002-vektor-arama-pgvector.md](adr/0002-vektor-arama-pgvector.md) | Neden ayrı vektör veritabanı değil, PostgreSQL + pgvector |
| [adr/0003-is-kuyrugu-celery-redis.md](adr/0003-is-kuyrugu-celery-redis.md) | Neden CV analizi kuyruk işi ve neden Celery + Redis |
| [adr/0004-barindirma-pc-cloudflare-tunnel.md](adr/0004-barindirma-pc-cloudflare-tunnel.md) | Neden VPS değil, PC + Cloudflare Tunnel |

İlgili diyagramlar: bileşenler [`docs/diagrams/component-deployment.md`](../diagrams/component-deployment.md), CV analizi sırası [`docs/diagrams/sequence-cv-analiz.md`](../diagrams/sequence-cv-analiz.md), veritabanı [`docs/diagrams/erd.md`](../diagrams/erd.md).

## ADR nasıl yazılır

- Mimariyi etkileyen, geri alması pahalı bir karar (teknoloji, barındırma, veri saklama, modüller arası sınır) için yazılır. Küçük kararlar sadece `docs/kararlar.md`'ye yazılır.
- Dosya adı `adr/NNNN-kisa-ad.md`; numara sırayla artar, silinmez.
- Bölümler: **Durum** (Öneri / Kabul / Değişti → ADR-NNNN), **Bağlam**, **Seçenekler**, **Karar**, **Sonuçlar** (iyi ve kötü yanları), **Ne zaman yeniden bakılır**.
- Her ADR'nin `docs/kararlar.md`'de bir satırı olur ve ADR o satırın numarasını anar. Karar değişirse ADR silinmez; durumu "Değişti" yapılır ve yeni ADR yazılır.
- ADR PR ile eklenir; kendi alanı dışındaki bileşeni etkiliyorsa o alanın sahibinin onayı gerekir (CLAUDE.md, klasör sahipliği).
