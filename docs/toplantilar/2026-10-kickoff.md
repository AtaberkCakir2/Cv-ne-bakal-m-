# Kick-off Toplantısı

- **Tarih / saat:** ____ (öneri: 25 veya 26.10.2026, en geç bu hafta sonu)
- **Süre:** 75 dakika
- **Katılımcılar:** Ataberk, Burak, Anıl (toplantıyı Anıl yönetir, not tutar)
- **Yer:** ____ (yüz yüze veya Meet/Discord; ekran paylaşımı gerekli)
- **Kapatılacak görevler:** T-001 (kick-off), T-003 (MVP kapsamı), T-004 (sözleşmeler)

## Toplantıdan önce (herkes, ~20 dk)

- [ ] Repoyu klonla veya `git pull` yap (kurulum adımları README'de)
- [ ] `docs/kapsam.md` oku — özellikle sondaki **Açık sorular**
- [ ] `contracts/` klasörünü oku — kendi modülünün girdi/çıktı formatına itirazın var mı?
- [ ] Kendi görev dosyana (`docs/gorevler/<isim>.md`) bak: Sprint 0 ve Sprint 1 görevlerin net mi?

## Gündem

| # | Konu | Süre | Sonuç |
|---|---|---|---|
| 1 | **Rol ve iş bölümü** — RACI matrisi (`docs/mimari.md` sonu) ve kişi başı görev yükleri. Takas istenen görev var mı? | 10 dk | RACI onayı |
| 2 | **Çalışma düzeni** — repo kuralları (branch + PR + 1 onay, herkes kendi klasörü), "başlıyorum" / "bitiriyorum" rutinleri, kararların `docs/kararlar.md`'ye yazılması | 10 dk | Kuralların onayı |
| 3 | **Toplantı ritmi** — haftalık kısa durum toplantısı günü/saati, sprint sonu demo (2 haftada bir), danışman görüşmesi (2 haftada bir), iletişim kanalı | 5 dk | Takvim |
| 4 | **MVP kapsamı** — `docs/kapsam.md`: Must / Should / Could / Won't listelerinin gözden geçirilmesi ve 6 açık sorunun karara bağlanması | 20 dk | Kapsam donduruldu |
| 5 | **Sözleşmeler** — `contracts/job_posting.schema.json` (Ataberk → Burak), `contracts/analysis_result.schema.json` (Burak → Anıl), `contracts/api.md`. Eksik/yanlış alan var mı? | 15 dk | Sözleşmeler onaylandı |
| 6 | **İlk iki hafta** — Sprint 0/1 görevleri, kurulumlar (Python 3.12, Docker, Ollama), GitHub Student Pack başvurusu ve ana dal koruması, Burak'ın repo daveti | 10 dk | Herkesin ilk 3 görevi net |
| 7 | **Kararlar ve aksiyonlar** — aşağıdaki tabloların doldurulması | 5 dk | Notlar repoda |

## Karara bağlanacaklar (toplantıda doldurulacak)

| # | Konu | Karar |
|---|---|---|
| 1 | RACI ve iş bölümü onaylandı mı? Değişiklik? | |
| 2 | Haftalık durum toplantısı günü/saati | |
| 3 | Sprint demo günü (2 haftada bir) | |
| 4 | Danışman görüşme periyodu ve ilk tarih | |
| 5 | İletişim kanalı (WhatsApp / Discord) | |
| 6 | Açık soru 1 — transkript analizi v1.0'da mı? | |
| 7 | Açık soru 2 — 10 hedef pozisyon | |
| 8 | Açık soru 3 — arayüz dili | |
| 9 | Açık soru 4 — misafir analiz | |
| 10 | Açık soru 5 — Apple hesabı | |
| 11 | MVP kapsamı donduruldu mu? | |
| 12 | Sözleşmelerde değişiklik var mı? (varsa kim, hangi PR) | |

## Aksiyonlar (toplantıda doldurulacak)

| Kim | Ne | Ne zamana |
|---|---|---|
| | | |
| | | |
| | | |

## Toplantıdan sonra

1. Anıl bu dosyadaki tabloları doldurur; alınan kararları `docs/kararlar.md`'ye ekler; açık soruların cevaplarını `docs/kapsam.md`'ye işler ve "TASLAK" ibaresini kaldırır.
2. Görev dosyalarında T-001, T-003 (Anıl) ve T-004 (Anıl) `Tamamlandı` yapılır.
3. Tek PR açılır; Ataberk ve Burak onaylar, birleştirilir.
4. Kapsam belgesi danışmana iletilir.
