import * as SecureStore from "expo-secure-store";

/**
 * Refresh token cihazın güvenli deposunda (Android Keystore / iOS Keychain) tutulur; access token sadece bellekte.
 * Web'deki localStorage'ın karşılığı; diğer uygulamalar ve yedekleme okuyamaz.
 */
const KEY = "cvnebakalim.refresh";

const options: SecureStore.SecureStoreOptions = {
  // Cihaz kilidi açıkken okunur; yedeğe ve başka cihaza taşınmaz.
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export async function readRefresh(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(KEY, options);
  } catch {
    return null;
  }
}

export async function writeRefresh(token: string | null): Promise<void> {
  try {
    if (token) await SecureStore.setItemAsync(KEY, token, options);
    else await SecureStore.deleteItemAsync(KEY, options);
  } catch {
    // Saklanamazsa oturum sadece uygulama açıkken sürer.
  }
}
