import type { Middleware } from "openapi-fetch";

import { API_URL } from "../config";

/**
 * Oturum bilgisi (T-051).
 *
 * - Access token (15 dk) sadece bellekte tutulur; sayfa yenilenince refresh token ile yeniden alınır.
 * - Refresh token (7 gün, tek kullanımlık) localStorage'da: backend onu gövdede döndürüyor (cookie değil) ve Electron
 *   ile mobil de aynı API'yi kullanıyor. Bedeli: XSS olursa çalınabilir. Bu yüzden arayüzde dangerouslySetInnerHTML ve
 *   üçüncü taraf script yok; backend her yenilemede tokenı döndürür ve eski tokenın tekrar kullanılmasını tüm oturumları
 *   kapatma sebebi sayar (backend/app/services/auth.py).
 * - Yenileme tek seferde yapılır (single-flight): aynı anda 401 alan istekler tek bir /auth/refresh bekler. Backend
 *   aynı refresh tokenın iki kez kullanılmasını saldırı sayıp tüm oturumları kapattığı için bu zorunlu.
 */

const REFRESH_KEY = "careerai-refresh";
/** Süresine bu kadar kala access token istekten önce yenilenir. */
const EARLY_REFRESH_MS = 30_000;

interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

let accessToken: string | null = null;
let accessExpiresAt = 0;
let refreshing: Promise<boolean> | null = null;
const listeners = new Set<() => void>();

function readRefresh(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

function writeRefresh(token: string | null): void {
  try {
    if (token) localStorage.setItem(REFRESH_KEY, token);
    else localStorage.removeItem(REFRESH_KEY);
  } catch {
    // Saklanamazsa oturum sadece bu sekmede ve sayfa yenilenene kadar sürer.
  }
}

function notify(): void {
  listeners.forEach((l) => l());
}

/** Oturum açıldığında veya kapandığında çağrılır (useSession bunu dinler). */
export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function hasSession(): boolean {
  return accessToken !== null || readRefresh() !== null;
}

export function setTokens(pair: TokenPair): void {
  accessToken = pair.access_token;
  accessExpiresAt = Date.now() + pair.expires_in * 1000;
  writeRefresh(pair.refresh_token);
  notify();
}

export function clearSession(): void {
  accessToken = null;
  accessExpiresAt = 0;
  writeRefresh(null);
  notify();
}

/** Çıkışta backend'e gönderilecek refresh token. */
export function currentRefreshToken(): string | null {
  return readRefresh();
}

async function doRefresh(): Promise<boolean> {
  // Kilit alındıktan sonra okunur: başka sekme az önce yenilediyse onun bıraktığı yeni token kullanılır.
  const token = readRefresh();
  if (!token) return false;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }),
    });
    if (!res.ok) {
      if (res.status === 401 || res.status === 422) clearSession();
      return false;
    }
    setTokens((await res.json()) as TokenPair);
    return true;
  } catch {
    return false;
  }
}

/**
 * Refresh token ile yeni çift alır. Ağ ve 5xx hatasında oturumu silmez (geçici olabilir); 401'de siler.
 * Doğrudan fetch kullanır: api istemcisinin middleware'i burada tekrar devreye girmesin.
 * Sekmeler arası kilit (Web Locks): iki sekme aynı tokenı aynı anda gönderirse backend bunu tekrar kullanım sayıp
 * kullanıcının tüm oturumlarını kapatır. Kilit desteklenmiyorsa sadece sekme içi tek seferlik korunur.
 */
export function refreshSession(): Promise<boolean> {
  if (refreshing) return refreshing;
  if (!readRefresh()) return Promise.resolve(false);
  const run = navigator.locks ? navigator.locks.request(REFRESH_KEY, doRefresh) : doRefresh();
  refreshing = run.finally(() => {
    refreshing = null;
  });
  return refreshing;
}

/** Süren bir yenileme varsa bitmesini bekler (çıkış, yenilemeyle yarışıp eski tokenı göndermesin). */
export function pendingRefresh(): Promise<unknown> {
  return refreshing ?? Promise.resolve();
}

// Başka sekmede giriş/çıkış yapılınca bu sekme de güncellensin.
window.addEventListener("storage", (e) => {
  if (e.key !== REFRESH_KEY) return;
  if (!e.newValue) {
    accessToken = null;
    accessExpiresAt = 0;
  }
  notify();
});

/** Geçerli access token; yoksa veya bitmek üzereyse önce yeniler. */
async function validAccessToken(): Promise<string | null> {
  if (accessToken && Date.now() < accessExpiresAt - EARLY_REFRESH_MS) return accessToken;
  if (!readRefresh()) return accessToken;
  await refreshSession();
  return accessToken;
}

// Kimlik doğrulama uçları token taşımaz; 401'leri "şifre yanlış" gibi anlamlıdır, yenileme denenmez.
const isAuthPath = (url: string) => new URL(url).pathname.startsWith("/api/v1/auth/");

const retryCopies = new Map<string, Request>();

/**
 * İsteklere `Authorization` ekler; 401 gelirse bir kez yenileyip isteği tekrarlar. Yenileme reddedilirse oturum
 * kapanır ve 401 yanıtı çağırana iletilir (RequireAuth giriş ekranına yönlendirir).
 */
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
    // Başka bir istek token'ı bu arada yenilediyse tekrar yenilemeden yeni tokenla dene.
    const sentWith = request.headers.get("Authorization");
    const alreadyRenewed = accessToken !== null && sentWith !== `Bearer ${accessToken}`;
    // Yenileme başarısızsa 401 çağırana iletilir; oturumu refreshSession sadece backend 401/422 derse siler.
    if (!alreadyRenewed && (!(await refreshSession()) || !accessToken)) return response;
    copy.headers.set("Authorization", `Bearer ${accessToken}`);
    return fetch(copy);
  },
  onError({ id }) {
    retryCopies.delete(id);
  },
};
