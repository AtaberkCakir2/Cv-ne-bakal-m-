import createClient from "openapi-fetch";

import { authMiddleware } from "../auth/session";
import { API_URL } from "../config";
import type { paths } from "./schema";

/**
 * Backend'in OpenAPI tanımından üretilmiş tiplerle çalışan istemci (web ile aynı kütüphane ve aynı tanım).
 * Tek kaynak `web/src/api/openapi.json`; tipler `npm run gen:api` ile buraya üretilir. Backend değişip tipler yeniden
 * üretildiğinde uyumsuz kod derlenmez (`npm run typecheck`).
 */
export const api = createClient<paths>({ baseUrl: API_URL });
api.use(authMiddleware);

/** Backend'in RFC 7807 hata biçimi (backend/app/core/errors.py). */
export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  request_id?: string;
  code?: string;
  errors?: { field: string; message: string }[];
}

/** openapi-fetch hata fırlatmaz; `unwrap(await api.GET(...))` hata yanıtını Problem olarak fırlatır. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || result.data === undefined) {
    throw result.error ?? { type: "about:blank", title: "Boş yanıt", status: result.response.status };
  }
  return result.data;
}

/** Kullanıcıya gösterilecek Türkçe hata metni; request_id destek için eklenir. */
export function problemMessage(error: unknown): string {
  const p = error as Partial<Problem> | undefined;
  if (error instanceof TypeError) return "Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.";
  const text = p?.detail ?? p?.title ?? "Beklenmeyen bir hata oluştu.";
  return p?.request_id ? `${text} (Hata kodu: ${p.request_id.slice(0, 8)})` : text;
}
