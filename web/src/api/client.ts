import createClient from "openapi-fetch";

import { API_URL } from "../config";
import type { paths } from "./schema";

/**
 * Backend'in OpenAPI tanımından üretilmiş tiplerle çalışan istemci.
 * Yollar, istek gövdeleri ve yanıtlar derleme anında kontrol edilir: backend değişip tipler yeniden
 * üretildiğinde (`npm run gen:api`) uyumsuz kod derlenmez.
 */
export const api = createClient<paths>({ baseUrl: API_URL });

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

/**
 * openapi-fetch 4xx/5xx'te hata fırlatmaz, `{ data, error }` döndürür. TanStack Query sorgularında
 * `unwrap(await api.GET(...))` kullanın: hata yanıtı Problem olarak fırlatılır ve `isError` olur.
 */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || result.data === undefined) {
    throw result.error ?? { type: "about:blank", title: "Boş yanıt", status: result.response.status };
  }
  return result.data;
}

/** 4xx kalıcı bir hatadır (yanlış istek, yetki); sadece ağ ve 5xx hataları yeniden denenir. */
export function isRetryable(error: unknown): boolean {
  const status = (error as Partial<Problem> | undefined)?.status;
  return typeof status !== "number" || status >= 500;
}

/** Kullanıcıya gösterilecek Türkçe hata metni; request_id destek için eklenir. */
export function problemMessage(error: unknown): string {
  const p = error as Partial<Problem> | undefined;
  const text = p?.detail ?? p?.title ?? "Beklenmeyen bir hata oluştu.";
  return p?.request_id ? `${text} (Hata kodu: ${p.request_id.slice(0, 8)})` : text;
}
