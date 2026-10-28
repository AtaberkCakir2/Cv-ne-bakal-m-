# web/ — Sahibi: Anıl

React + Vite + TypeScript arayüzü. Electron masaüstü uygulaması da bu kodu kullanacak.

- **Yönlendirme:** React Router 6 (`src/routes.tsx`). Ekran adları wireframe ile aynı (`prototip/`, T-021).
- **Veri çekme:** TanStack Query 5 (`src/main.tsx`).
- **API istemcisi:** `openapi-fetch` + backend'in OpenAPI tanımından üretilen tipler (`src/api/`). Yol, gövde ve yanıt tipleri derleme anında kontrol edilir.

## Çalıştırma

Backend `127.0.0.1:8000`'de çalışıyor olmalı (`backend/README.md`).

```bash
cd web
npm ci
npm run dev        # http://127.0.0.1:5173 — /durum sayfası backend'e bağlantıyı gösterir
```

`npm run lint`, `npm run build` (tip kontrolü + üretim derlemesi) CI'da da çalışır.

## Ortam değişkenleri

Vite sadece `VITE_` ile başlayan değişkenleri arayüze açar; bunlar tarayıcıda herkes tarafından görülür, **sır koymayın**.

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend adresi |

Değiştirmek için `web/.env.local` dosyası oluşturun (commit'lenmez), ör. `VITE_API_URL=http://127.0.0.1:8001`. Windows'ta `localhost` yerine `127.0.0.1` yazın.

## API tiplerini güncelleme

Backend'de endpoint eklendiğinde veya değiştiğinde (backend çalışırken):

```bash
curl http://127.0.0.1:8000/openapi.json -o src/api/openapi.json
npm run gen:api    # src/api/schema.d.ts yeniden üretilir; ikisini de commit'leyin
```

Sonra `npm run build`: tiplerle uyuşmayan kod burada derlenmez.

Sorgularda hata yanıtını yakalamak için `unwrap` kullanın (openapi-fetch hata fırlatmaz):

```ts
const me = useQuery({ queryKey: ["me"], queryFn: async () => unwrap(await api.GET("/api/v1/users/me")) });
```

Hatalar backend'in RFC 7807 biçimindedir; kullanıcıya `problemMessage(error)` gösterin.

## Notlar

- Yayına alınırken statik sunucu bilinmeyen yolları `index.html`'e yönlendirmeli (SPA fallback), yoksa `/analiz/123` gibi doğrudan linkler 404 verir.
- Electron `file://` ile açacağı için orada `createHashRouter` kullanılacak.
- Renk ve tipografi T-022 (tasarım sistemi) ile gelecek; şimdilik `src/index.css` sade.
