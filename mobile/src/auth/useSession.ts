import { useEffect, useState } from "react";

import { api } from "../api/client";
import { clearSession, currentRefreshToken, hasSession, pendingRefresh, subscribe } from "./session";

/** Oturum var mı; güvenli depo okunana kadar undefined (açılış ekranı). */
export function useSignedIn(): boolean | undefined {
  const [signedIn, setSignedIn] = useState<boolean>();
  useEffect(() => {
    const update = () => void hasSession().then(setSignedIn);
    update();
    return subscribe(update);
  }, []);
  return signedIn;
}

/** Çıkış: refresh token backend'de iptal edilir; sunucuya ulaşılamasa da bu cihazdaki oturum kapanır. */
export async function logout(): Promise<void> {
  await pendingRefresh(); // yenileme sürerken eski token gönderilirse backend tüm oturumları kapatır
  const refresh_token = await currentRefreshToken();
  if (refresh_token) await api.POST("/api/v1/auth/logout", { body: { refresh_token } }).catch(() => undefined);
  await clearSession();
}

// Oturum kapanınca giriş ekranında bir kez gösterilecek bilgi (ör. hesap silindi). Ekranlar oturuma göre değiştiği için
// gezinme parametresiyle taşınamaz.
let signOutNotice: string | undefined;

export function setSignOutNotice(notice: string): void {
  signOutNotice = notice;
}

export function takeSignOutNotice(): string | undefined {
  const notice = signOutNotice;
  signOutNotice = undefined;
  return notice;
}
