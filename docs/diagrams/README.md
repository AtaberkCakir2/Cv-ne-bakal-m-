# UML diyagramları (T-024)

Poster (T-025), TÜBİTAK başvurusu (T-028) ve final raporu (T-098) için sistemin dört görünümü. Diyagramlar [Mermaid](https://mermaid.js.org/) ile yazıldı: GitHub'da dosyayı açınca çizilmiş hali görünür, metin olduğu için PR'da değişiklikleri satır satır incelenebilir.

| Diyagram | Dosya | Neyi gösterir |
|---|---|---|
| Use Case | [use-case.md](use-case.md) | Kim sistemle ne yapar (öğrenci, yönetici, zamanlanmış toplayıcı) |
| Sequence | [sequence-cv-analiz.md](sequence-cv-analiz.md) | CV yüklemeden sonuca kadar bir analizin adımları |
| Component / Deployment | [component-deployment.md](component-deployment.md) | Bileşenler, aralarındaki bağlantılar ve sunucudaki container'lar |
| ERD | [erd.md](erd.md) | Veritabanı tabloları ve ilişkileri |

**Kaynaklar:** `docs/mimari.md`, `docs/veritabani.md`, `contracts/api.md`, `contracts/analysis_result.schema.json`. Bunlardan biri değişirse ilgili diyagram aynı PR'da güncellenir.

**ERD durumu:** `docs/veritabani.md`'den çizildi. Ataberk'in şeması (T-011) kesinleşince onunla karşılaştırılıp güncellenecek.

## Poster / rapor için görsel almak

1. Diyagramın Mermaid kodunu (```` ```mermaid ```` bloğunun içini) kopyalayın.
2. <https://mermaid.live> adresine yapıştırın.
3. "Actions" → **SVG** (baskı için, kalite kaybı yok) veya **PNG** indirin.
