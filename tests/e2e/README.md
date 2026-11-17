# Uçtan uca testler (T-071)

Playwright, gerçek tarayıcıda kritik kullanıcı akışını dener: **kayıt → CV yükle → sonuç → kaynak aç → hesap sil** (`kritik-akis.spec.ts`).

Yığın docker compose ile her seferinde **boş** kurulur ve sonra silinir (karar #30: ayrı staging sunucusu yok). CI'da her gece 03:30'da `main`'e karşı çalışır (`.github/workflows/e2e.yml`); başarısız olursa rapor ve izler (trace) Actions sayfasında `e2e-rapor` artifact'ında.

## Yerelde çalıştırma

Git Bash, repo kökünde. Docker Desktop açık olmalı. Geliştirme ortamıyla aynı portları kullandığı için önce `make down`.

```bash
bash tests/e2e/ortam.sh up            # ~2-5 dk: imajlar, migration, taksonomi ve kaynak seed'i
(cd web && npm ci)                    # bir kez
cd tests/e2e && npm ci && npx playwright install chromium   # bir kez
npx playwright test                   # web'i derleyip 127.0.0.1:5173'te açar, testi çalıştırır
npx playwright test --headed          # tarayıcıyı görerek
cd ../.. && bash tests/e2e/ortam.sh down   # her şeyi siler
```

Hata olursa: `npx playwright show-trace test-results/<test>/trace.zip` adım adım ekran görüntüsü ve ağ isteklerini gösterir; servis logları `bash tests/e2e/ortam.sh logs`.

## Nasıl çalışıyor

| Parça | Ne yapar |
|---|---|
| `ortam.sh up` | `docker-compose.yml` + `compose.e2e.yml` ile `careerai-e2e` projesi: postgres, redis, cv-redis, api, analiz işçisi. `alembic upgrade head`, `collector seed-taxonomy` (pozisyonlar), `collector resources-seed` (kaynaklar) |
| `compose.e2e.yml` | `ENVIRONMENT=test` ve CORS'u sabitler: geliştiricinin kendi `.env`'i sonucu değiştirmez |
| `playwright.config.ts` | Web'i `VITE_API_URL=http://127.0.0.1:8000` ile derler, `vite preview` ile 5173'te açar |
| `yardimci/pdf.ts` | Sahte, anonim, tek sayfalık CV PDF'ini çalışma anında üretir (repoda CV dosyası yok, kural 4) |
| `yardimci/veritabani.ts` | Test veritabanına SQL (`ortam.sh psql`) |

Her çalıştırma `e2e-<zaman>@example.com` adlı yeni bir kullanıcı açar ve sonunda onu siler; `@example.com`'a e-posta gitmez.

**Analiz:** `ENVIRONMENT=test`'te analiz işçisi AI modülü yerine sözleşmedeki örnek skoru yazar (`backend/app/services/analyzer.py`, `ExampleAnalyzer`). Bu örnek eksik yetkinlik ve kaynak üretmediği için **geçici olarak** test, "kaynak aç" adımından önce analize sözleşme örneğindeki biçimde bir eksik yetkinlik ve kaynak ekler (`eksikYetkinlikVeKaynakEkle`). Gerçek AI akışı (T-057) bağlanınca veya `ExampleAnalyzer` örnekteki `missing_skills`'i de yazınca bu adım silinir.

**Dış bağlantı:** "Kaynağa git" bağlantısının yeni sekmede doğru adrese gittiği doğrulanır ama dış siteye istek atılmaz (Playwright o adresi yerel bir sayfayla karşılar).
