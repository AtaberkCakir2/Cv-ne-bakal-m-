/**
 * Yüklemeden önce istemci tarafı kontrol (T-052). Asıl kontrol backend'de (backend/app/services/cv_validation.py):
 * sayfa sayısı, şifre ve bozuk dosya orada anlaşılır. Burada amaç kullanıcıyı boşuna beklememektir.
 */
export const MAX_CV_BYTES = 5 * 1024 * 1024;
export const MAX_CV_PAGES = 5;

/** Dosya uygunsa undefined, değilse kullanıcıya gösterilecek mesaj. İlk baytlar "%PDF-" olmalı (uzantı yetmez). */
export async function cvFileError(file: File): Promise<string | undefined> {
  if (file.size === 0) return "Dosya boş görünüyor.";
  if (file.size > MAX_CV_BYTES) return `Dosya ${formatSize(file.size)}; en fazla 5 MB olabilir.`;
  const head = new Uint8Array(await file.slice(0, 5).arrayBuffer());
  if (String.fromCharCode(...head) !== "%PDF-") return "Sadece PDF dosyası yükleyebilirsin.";
  return undefined;
}

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} MB`;
}

/** Retry-After (saniye) → "38 dakika" / "45 saniye". */
export function formatWait(seconds: number): string {
  if (seconds >= 90) return `${Math.ceil(seconds / 60)} dakika`;
  return `${Math.max(1, Math.round(seconds))} saniye`;
}
