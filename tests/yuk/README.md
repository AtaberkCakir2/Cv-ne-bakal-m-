# Yük testi (T-072)

Kabul kriteri (`docs/gorevler/ataberk.md`): 20 eşzamanlı kullanıcı, 30 dk; API p95 < 300 ms (analiz hariç), hata oranı < %1, RAM < %85; kuyruk birikme süresi ölçülür, worker sayısı buna göre ayarlanır.

## Çalıştırma (Git Bash, repo kökü)

```bash
make down                                   # geliştirme ortamı aynı portları kullanır
bash tests/yuk/calistir.sh                  # 20 kullanıcı, 30 dk
SURE=3m bash tests/yuk/calistir.sh          # kısa deneme
```

`calistir.sh` E2E ortamını (`tests/e2e/ortam.sh`, ayrı compose projesi `careerai-e2e`) **istek sınırı kapalı** kurar, k6'yı (`grafana/k6:1.3.0`) aynı Docker ağında çalıştırır, 30 sn'de bir `docker stats` kaydeder ve ortamı kaldırır. Sonuçlar `tests/yuk/sonuclar/<tarih>/` altında (`k6.txt`, `ozet.json`, `kaynak.tsv`; git'e girmez). Production'a dokunmaz.

Ayarlar ortam değişkeniyle: `VUS` (20), `SURE` (30m), `ANALIZ_ARALIK_SN` (bir kullanıcının iki analizi arası, 300), `ORTAMI_BIRAK=1` (bitince ortamı kaldırma).

## Senaryolar (`api.js`)

| Senaryo | Ne yapar | Eşik |
|---|---|---|
| `gezinme` | Her sanal kullanıcı giriş yapar (10 dk'da bir yeniden), pozisyonlar → pozisyonun yetkinlikleri → bir yetkinliğin kaynakları → profil → analiz geçmişi; 1–3 sn ara | `tip:api` p95 < 300 ms, hata < %1 |
| `analiz` | Aynı kullanıcılar ~5 dk'da bir sahte CV (anonim, çalışma anında üretilen PDF) yükler, `GET /analyses/{id}` ile bitmesini bekler | Hata < %1; süre `analiz_suresi`'nde |

Analiz yüklemesine `503 + Retry-After` gelirse hata sayılmaz, `analiz_kuyruk_dolu` sayacına yazılır: API bekleyen CV sayısını sınırlar (`analysis_queue_limit = 8`, karar #9 gereği CV'ler bellekte bekler).

## Sonuçlar

### 18.11.2026: API (analiz işçisi örnek sonuç döndürür)

Ortam: production PC'si (i7-9750H, Docker'a 19,5 GB), **production aynı anda açıktı**. E2E ortamı `ENVIRONMENT=test`: analiz işçisi gerçek AI yerine sözleşme örneğini yazar (T-057 henüz yok). Bu yüzden ölçüm API, veritabanı ve kuyruk altyapısı içindir; analiz süresi gerçek değildir.

| Ölçüt | Sonuç | Hedef |
|---|---|---|
| Süre / kullanıcı | 30 dk, 20 eşzamanlı | 30 dk, 20 |
| İstek | 69.589 (37,8/sn) | — |
| API p95 (analiz hariç) | **49,5 ms** (p99 102 ms, en yüksek 2,2 sn) | < 300 ms ✓ |
| Hata oranı | **%0** (0 / 69.589) | < %1 ✓ |
| Analiz | 240 yükleme, 240 bitti, kuyruk dolu 0; yükleme → sonuç p95 5,8 sn | — |
| RAM (Docker VM, production dahil) | en yüksek **%14,7** | < %85 ✓ |
| En yoğun konteyner | api CPU en yüksek ~%106 (tek uvicorn süreci, ~1 çekirdek); bellek 116 MB | — |

Yorum: API bu yükte rahat. api tek süreç çalıştığı için CPU'su bir çekirdeğe dayanıyor; kullanıcı sayısı artarsa ilk adım uvicorn işçi sayısını artırmak (Anıl, `backend/Dockerfile`).

### Yapılacak: gerçek analizle (T-057 sonrası)

Gerçek modelle bir analiz CPU'da ~1–2 dk sürer ve eşzamanlılık 1'dir: sistem saatte en fazla ~30–60 analiz işler. Varsayılan ayarda (20 kullanıcı × 5 dk'da bir = saatte 240 analiz) kuyruk dolacak ve `analiz_kuyruk_dolu` artacaktır; bu beklenen davranıştır. Ölçülecekler: kuyrukta bekleme süresi, 503 oranı, Ollama ile birlikte RAM. Sonuca göre `analysis_queue_limit`, kullanıcı başına analiz sınırı (5/saat) ve worker-ai eşzamanlılığı kararlaştırılır.
