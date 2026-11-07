import { useSyncExternalStore } from "react";

import { hasSession, subscribe } from "./session";

/** Oturum açık mı; giriş ve çıkışta bileşeni yeniden çizer. */
export function useSession(): boolean {
  return useSyncExternalStore(subscribe, hasSession);
}
