# mobile/ — Sahibi: Burak

Cv'ne Bakalım! mobil uygulaması: React Native (Expo SDK 58) + TypeScript. API istemcisi ve tipler web ile ortaktır.

## Çalıştırma

```bash
cd mobile
npm ci
npm start            # Expo Go ile telefonda QR kodu, veya `a` ile Android emülatörü
```

API adresi `EXPO_PUBLIC_API_URL` ile verilir (`mobile/.env.local`, commit'lenmez). Verilmezse Android emülatöründe
`http://10.0.2.2:8000`, iOS simülatöründe `http://127.0.0.1:8000`. Gerçek telefonda bilgisayarın yerel ağ adresi
gerekir (ör. `EXPO_PUBLIC_API_URL=http://192.168.1.20:8000`) ve backend'in o adreste dinlemesi gerekir. Uygulama
tarayıcı olmadığı için CORS ayarı gerekmez.

## Yapı

| Dosya | İş |
|---|---|
| `src/api/client.ts` | `openapi-fetch` istemcisi, `unwrap`, `problemMessage` (web/src/api/client.ts ile aynı) |
| `src/api/schema.d.ts` | **Üretilir.** Tek kaynak `web/src/api/openapi.json`: `npm run gen:api` |
| `src/auth/session.ts` | Access token bellekte, 401'de tek seferlik yenileme (web ile aynı kurallar, T-051) |
| `src/auth/tokenStore.ts` | Refresh token `expo-secure-store`'da (Android Keystore / iOS Keychain), sadece bu cihaz |
| `src/config.ts` | API adresi |
| `App.tsx` | Şimdilik backend sağlık ekranı; giriş, KVKK onayı ve CV yükleme T-061'de |

Backend değişince: web'deki `openapi.json` güncellenir (Anıl), burada `npm run gen:api` ve `npm run typecheck`.

## Derleme (EAS Build)

`eas.json` profilleri: `preview` (Android APK, ekip içi deneme) ve `production` (Play Store için AAB). İkisinde de API
`https://api.cvnebakalim.com`. Derleme Expo hesabıyla yapılır (`npx eas-cli build -p android --profile preview`);
Expo hesabı ve `eas init` (proje kimliği `app.json`'a yazılır) ilk derlemede ekipçe yapılacak.

## Kontroller

```bash
npm run typecheck    # tsc --noEmit
npm audit            # güvenlik raporu G-8: package-lock.json artık var
```
