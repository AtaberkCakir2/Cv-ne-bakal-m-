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
| `src/auth/useSession.ts` | Oturum durumu (`useSignedIn`) ve çıkış |
| `src/auth/consents.ts`, `validation.ts` | KVKK onayları (sürümü web ile aynı) ve form kuralları (web ile aynı) |
| `src/analysis/cvFile.ts` | Yüklemeden önce dosya kontrolü (PDF, 5 MB) |
| `src/analysis/ResultView.tsx`, `format.ts` | Sonuç panosu, geri bildirim, ilan/YouTube kaynak atfı; metinler web ile aynı |
| `src/screens/` | Giriş, kayıt + KVKK onayları, CV yükleme, analiz bekleme (T-061); sonuç, kaynak detayı, geçmiş, profil ve hesap silme (T-062) |
| `src/ui/` | Ortak bileşenler (alan, düğme, onay kutusu, uyarı) ve açık/koyu tema renkleri |
| `src/config.ts` | API adresi, yasal metinlerin sitesi |
| `App.tsx` | Gezinme (React Navigation): oturum yoksa giriş/kayıt, varsa yükleme, analiz, kaynak, geçmiş, profil |

Verileri JSON olarak indirme (KVKK) şimdilik sadece web uygulamasında; profil ekranı oraya yönlendirir.

**CV dosyası:** `expo-document-picker` ile seçilir, uygulamanın geçici önbelleğindeki kopyasıyla gönderilir; uygulama
dosyayı ya da içeriğini saklamaz, okumaz (CLAUDE.md kural 5). Asıl kontrol (sayfa sayısı, şifreli/bozuk PDF) backend'de.

Backend değişince: web'deki `openapi.json` güncellenir (Anıl), burada `npm run gen:api` ve `npm run typecheck`.

## Derleme (EAS Build)

`eas.json` profilleri: `preview` (Android APK, ekip içi deneme) ve `production` (Play Store için AAB). İkisinde de API
`https://api.cvnebakalim.com`. Derleme Expo hesabıyla yapılır (`npx eas-cli build -p android --profile preview`);
Expo hesabı ve `eas init` (proje kimliği `app.json`'a yazılır) ilk derlemede ekipçe yapılacak.

## Kontroller

```bash
npm run lint         # eslint (eslint-config-expo)
npm run typecheck    # tsc --noEmit
npm audit            # güvenlik raporu G-8: package-lock.json artık var
npx expo-doctor      # Expo SDK ile paket sürümleri uyumlu mu
```

TypeScript bilerek 5.9'da (`openapi-typescript` 7 TypeScript 5 istiyor); `package.json` → `expo.install.exclude` bu yüzden
`typescript` içerir.
