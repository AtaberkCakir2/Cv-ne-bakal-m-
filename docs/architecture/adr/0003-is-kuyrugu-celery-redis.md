# ADR-0003 · Analiz ve toplama iş kuyruğu: Celery + Redis

- **Durum:** Kabul (karar #11)
- **Tarih:** 24.10.2026
- **Sahibi:** Anıl (API, analiz kuyruğu) · Etkilenen: Burak (worker-ai), Ataberk (worker-data, Redis)

## Bağlam

Bir CV analizi CPU'da 8B modelle ~1–2 dakika sürer (ADR-0001). HTTP isteğini bu kadar açık tutmak Cloudflare'in zaman aşımına, istemci kopmalarına ve API süreçlerinin tükenmesine yol açar. Ayrıca her gece ilan toplama, temizleme ve istatistik yenileme çalışmalı; PC kapalı kaldıysa açılışta telafi edilmeli (R-18). Aynı anda en fazla bir analiz çalışabilir (Ollama tek model, tek paralel).

## Seçenekler

| Seçenek | Artı | Eksi |
|---|---|---|
| Senkron istek (API içinde analiz) | En basit | Dakikalık istek; zaman aşımı; API süreçleri bloke olur; yeniden deneme yok |
| FastAPI `BackgroundTasks` | Ek servis yok | İş API süreciyle ölür; yeniden deneme, eşzamanlılık sınırı, zamanlanmış görev yok |
| **Celery + Redis** | Olgun; ayrı kuyruklar, eşzamanlılık sınırı, `acks_late` ile yeniden teslim, beat ile zamanlama; Python | Ağır bir kütüphane; yapılandırma inceliği (visibility timeout) |
| RQ / Dramatiq | Daha hafif | Zamanlayıcı ve izleme ek paket ister; ekipte deneyim az |

## Karar

- CV analizi **kuyruk işidir**: API dosyayı diske yazmadan kuyruğa atar, hemen `202 {analysis_id}` döner; istemci ilerlemeyi SSE veya polling ile izler.
- Broker ve sonuç taşıyıcı **Redis 7**; iki ayrı kuyruk ve işçi:
  - `analysis` → worker-ai (Burak): `--concurrency 1`, `task_acks_late=True`, `visibility_timeout=600` (görev üst sınırı 200 sn).
  - `data` → worker-data (Ataberk): gece toplama, ETL, istatistik yenileme; Celery beat aynı süreçte (`-B`), 03:00 Europe/Istanbul; açılışta kaçan toplama telafi edilir (T-075).
- Kuyruktaki CV baytları ayrı, kalıcılığı kapalı bir Redis'te (`cv-redis`, tmpfs) durur; diske veya AOF'a yazılmaz (karar #9). Kuyruk Redis'i AOF ile kalıcı ve şifreli.

## Sonuçlar

**İyi:** API hızlı kalır (p95 hedefi 300 ms analiz dışı uçlarda); işçi çökerse iş yeniden teslim edilir; analiz ve veri işleri birbirini beklemez; zamanlama kodla birlikte sürümlenir (crontab yok, Windows'ta da çalışır).

**Bedeli:**
- Analizler sıraya girer: aynı anda N kullanıcı gelirse sonuncusu ~N × 1–2 dk bekler. Kullanıcı başına sınır (5/saat) ve ilerleme ekranı bunun için var.
- Redis tek nokta: düşerse yeni analiz alınmaz (API 503 döner), toplama durur. İzleme panosunda kuyruk birikmesi uyarısı var (karar #32).
- Visibility timeout görev süresinden kısa olursa iş iki kez çalışır; görev süresi değişirse bu değer de güncellenmeli.

## Ne zaman yeniden bakılır

- Kuyrukta bekleme süresi düzenli olarak 5 dakikayı aşarsa: Ollama'yı GPU'ya almak ve worker-ai eşzamanlılığı.
- Celery'nin Windows/Docker dışı bir ortamda çalışması gerekirse (şu an gerek yok).
