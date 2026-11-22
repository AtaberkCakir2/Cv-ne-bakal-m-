import type { Middleware } from "openapi-fetch";

import { API_URL } from "../config";
import { readRefresh, writeRefresh } from "./tokenStore";

/**
 * Oturum (web/src/auth/session.ts ile aynı kurallar, T-051):
 *
 * - Access token (15 dk) sadece bellekte; uygulama yeniden açılınca refresh token ile yeniden alınır.
 * - Refresh token (7 gün, tek kullanımlık) expo-secure-store'da (tokenStore.ts).
 * - Yenileme tek seferde yapılır (single-flight): aynı anda 401 alan istekler tek bir /auth/refresh bekler. Backend aynı
 *   refresh tokenın iki kez kullanılmasını saldırı sayıp tüm oturumları kapattığı için zorunlu. Mobilde tek uygulama
 *   süreci olduğu için web'deki sekmeler arası kilide gerek yok.
 */

interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

/** Süresine bu kadar kala access token istekten önce yenilenir. */
const EARLY_REFRESH_MS = 30_000;

let accessToken: string | null = null;
let accessExpiresAt = 0;
let refreshToken: string | null = null;
let loaded: Promise<void> | null = null;
let refreshing: Promise<boolean> | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  listeners.forEach((l) => l());
}

/** Güvenli depodaki refresh token bir kez okunur. */
function load(): Promise<void> {
  loaded ??= readRefresh().then((t) => {
    refreshToken ??= t;
  });
  return loaded;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export async function hasSession(): Promise<boolean> {
  await load();
  return accessToken !== null || refreshToken !== null;
}

export async function setTokens(pair: TokenPair): Promise<void> {
  accessToken = pair.access_token;
  accessExpiresAt = Date.now() + pair.expires_in * 1000;
  refreshToken = pair.refresh_token;
  await writeRefresh(pair.refresh_token);
  notify();
}

export async function clearSession(): Promise<void> {
  accessToken = null;
  accessExpiresAt = 0;
  refreshToken = null;
  await writeRefresh(null);
  notify();
}

/** Çıkışta backend'e gönderilecek refresh token. */
export async function currentRefreshToken(): Promise<string | null> {
  await load();
  return refreshToken;
}

async function doRefresh(): Promise<boolean> {
  await load();
  const token = refreshToken;
  if (!token) return false;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }),
    });
    if (!res.ok) {
      if (res.status === 401 || res.status === 422) await clearSession();
      return false;
    }
    await setTokens((await res.json()) as TokenPair);
    return true;
  } catch {
    return false; // ağ hatası geçici olabilir: oturum silinmez
  }
}

/** Refresh token ile yeni çift alır; aynı anda gelen çağrılar aynı isteği bekler. */
export function refreshSession(): Promise<boolean> {
  refreshing ??= doRefresh().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

/** Süren bir yenileme varsa bitmesini bekler (çıkış, yenilemeyle yarışıp eski tokenı göndermesin). */
export function pendingRefresh(): Promise<unknown> {
  return refreshing ?? Promise.resolve();
}

/** Geçerli access token; yoksa veya bitmek üzereyse önce yeniler. */
async function validAccessToken(): Promise<string | null> {
  if (accessToken && Date.now() < accessExpiresAt - EARLY_REFRESH_MS) return accessToken;
  await load();
  if (!refreshToken) return accessToken;
  await refreshSession();
  return accessToken;
}

// Kimlik doğrulama uçları token taşımaz; 401'leri "şifre yanlış" gibi anlamlıdır, yenileme denenmez.
const isAuthPath = (url: string) => new URL(url).pathname.startsWith("/api/v1/auth/");

const retryCopies = new Map<string, Request>();

/** İsteklere `Authorization` ekler; 401 gelirse bir kez yenileyip isteği tekrarlar. */
export const authMiddleware: Middleware = {
  async onRequest({ request, id }) {
    if (isAuthPath(request.url)) return request;
    const token = await validAccessToken();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    retryCopies.set(id, request.clone()); // gövde fetch ile tükenir; tekrar için kopya
    return request;
  },
  async onResponse({ request, response, id }) {
    const copy = retryCopies.get(id);
    retryCopies.delete(id);
    if (response.status !== 401 || !copy || isAuthPath(request.url)) return response;
    const sentWith = request.headers.get("Authorization");
    const alreadyRenewed = accessToken !== null && sentWith !== `Bearer ${accessToken}`;
    if (!alreadyRenewed && (!(await refreshSession()) || !accessToken)) return response;
    copy.headers.set("Authorization", `Bearer ${accessToken}`);
    return fetch(copy);
  },
  onError({ id }) {
    retryCopies.delete(id);
  },
};
